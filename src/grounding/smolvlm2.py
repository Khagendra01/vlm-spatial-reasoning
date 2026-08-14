"""SmolVLM2-2.2B wrapper for the R1 2B replication (frozen Paper-2 contract).

Mirrors the Qwen2VLClassifier interface so run_tier_a/b/c can swap model
families with `--model-family smolvlm2` while keeping the identical frozen
contract: same prompt, same preprocessing path (392px cap applied before the
processor via preprocess_for_vlm), same greedy generation (max_new_tokens=5),
same parser. SmolVLM2's own processor rounds images to its internal resolution;
that rounding is identical across checkpoints (zero-shot and General LoRA), so
within-R1 fairness is preserved, matching the reference implementation that
produced results/smolvlm2_*.csv on master.

Loading path: base HuggingFaceTB/SmolVLM2-2.2B-Instruct, bf16, eager attention;
LoRA applied unmerged via PeftModel (same pattern as the 7B classifier).
"""

import gc

import torch
from PIL import Image

from . import config

from transformers import AutoModelForImageTextToText, AutoProcessor
from transformers import AutoModelForCausalLM  # noqa: F401  (documented fallback)


class SmolVLM2Classifier:
    def __init__(self, model_id: str, adapter_path=None, device=None,
                 torch_dtype=torch.bfloat16, attn_implementation="eager",
                 quantize: str = None, max_new_tokens: int = None):
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
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_id, **load_kwargs
        )
        if self.device == "cuda":
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

        Matches the reference SmolVLM2 eval path on master (padding=True,
        no per-batch truncation flag; add_generation_prompt, tokenize).
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
    def from_checkpoint(checkpoint: dict, **kwargs) -> "SmolVLM2Classifier":
        return SmolVLM2Classifier(
            model_id=checkpoint["model_id"],
            adapter_path=checkpoint["adapter_path"],
            **kwargs,
        )
