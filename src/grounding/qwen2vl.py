"""Qwen2-VL-7B wrapper for the Tier-A audit.

Frozen run-fairness contract (protocol section 10):
- identical prompt, processor path, preprocessing, generation settings
  (greedy, max_new_tokens=5) for every condition and every checkpoint;
- identical within-backbone-transition settings: base zero-shot and both
  LoRA adapters use the same dtype / attention backend / quantization;
- `padding=True, truncation=True` required for batched chat templates
  (docs/TECHNIQUES.md section 6);
- OOM-safe ladder (336 -> 224 -> 160 -> 96 px) from docs/TECHNIQUES.md;
- no per-batch torch.cuda.empty_cache() (only on OOM).

Default modality is bf16 + eager attention, matching every prior 7B run in
this repo (the confirmatory modality on the A6000 box). A 4-bit option exists
strictly for local engineering validation on low-VRAM machines and must be
recorded in run metadata as a documented model-loading difference.
"""

import gc

import torch
from PIL import Image

from . import config

try:
    from transformers import Qwen2VLForConditionalGeneration
    _MODEL_CLS = Qwen2VLForConditionalGeneration
except Exception:
    from transformers import AutoModelForImageTextToText
    _MODEL_CLS = AutoModelForImageTextToText

from transformers import AutoProcessor


class Qwen2VLClassifier:
    def __init__(self, model_id: str, adapter_path=None, device=None,
                 torch_dtype=torch.bfloat16, attn_implementation="eager",
                 quantize: str = None, max_new_tokens: int = None):
        """quantize: None | "4bit" (engineering validation only; documented)."""
        self.model_id = model_id
        self.adapter_path = adapter_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.torch_dtype = torch_dtype
        self.attn_implementation = attn_implementation
        self.quantize = quantize
        self.max_new_tokens = max_new_tokens or config.MAX_NEW_TOKENS

        self.processor = AutoProcessor.from_pretrained(model_id)
        if hasattr(self.processor, "tokenizer"):
            self.processor.tokenizer.padding_side = "left"

        load_kwargs = dict(
            torch_dtype=torch_dtype,
            _attn_implementation=attn_implementation,
            low_cpu_mem_usage=True,
        )
        if quantize == "4bit":
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
            )
            load_kwargs["device_map"] = "auto"
        elif quantize is not None:
            raise ValueError(f"unsupported quantize mode: {quantize!r}")

        self.model = _MODEL_CLS.from_pretrained(model_id, **load_kwargs)
        if self.device == "cuda" and quantize is None:
            self.model = self.model.to(self.device)

        if adapter_path is not None:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, adapter_path)
        self.model.eval()

    # ------------------------------------------------------------------
    def _messages_for(self, image, statement):
        prompt = config.PROMPT_TEMPLATE.format(statement=statement)
        content = []
        if image is not None:
            content.append({"type": "image", "image": image})
        content.append({"type": "text", "text": prompt})
        return [{"role": "user", "content": content}]

    def predict_batch(self, images: list, statements: list, max_scale=None) -> list:
        """Greedy batched generation; returns raw decoded texts (verbatim).

        Images may contain None entries (text-only / unavailable image):
        those rows become text-only messages.
        """
        batch_messages = [
            self._messages_for(img, st) for img, st in zip(images, statements)
        ]
        inputs = self.processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        if self.device == "cuda":
            inputs = {
                k: (v.to(self.device, dtype=self.torch_dtype)
                    if v.dtype == torch.float32 else v.to(self.device))
                for k, v in inputs.items()
            }
        else:
            inputs = {
                k: (v.to(self.torch_dtype) if v.dtype == torch.float32 else v)
                for k, v in inputs.items()
            }

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                do_sample=config.DO_SAMPLE,
                max_new_tokens=self.max_new_tokens,
            )
        input_len = inputs["input_ids"].shape[1]
        generated = generated_ids[:, input_len:]
        texts = self.processor.batch_decode(generated, skip_special_tokens=True)

        del inputs, generated_ids, generated
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        return texts

    def predict_batch_oom_safe(self, images: list, statements: list) -> list:
        """Like predict_batch but retries with the documented scale ladder."""
        try:
            return self.predict_batch(images, statements)
        except torch.cuda.OutOfMemoryError:
            if self.device != "cuda" or all(img is None for img in images):
                raise
            for scale in config.OOM_SCALE_LADDER:
                print(f"  OOM at full scale; retrying batch at {scale}px...")
                try:
                    scaled = [
                        None if img is None else img.resize(
                            (scale, scale), Image.BILINEAR
                        )
                        for img in images
                    ]
                    gc.collect()
                    torch.cuda.empty_cache()
                    return self.predict_batch(scaled, statements)
                except torch.cuda.OutOfMemoryError:
                    continue
            raise

    # ------------------------------------------------------------------
    @staticmethod
    def from_checkpoint(checkpoint: dict, **kwargs) -> "Qwen2VLClassifier":
        return Qwen2VLClassifier(
            model_id=checkpoint["model_id"],
            adapter_path=checkpoint["adapter_path"],
            **kwargs,
        )
