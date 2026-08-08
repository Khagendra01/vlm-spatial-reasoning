"""
SmolVLM2-2.2B-Instruct model wrapper for spatial reasoning classification.

Loads the model, accepts an image + spatial statement, and returns True/False.
Supports batch inference for speed.
"""

import gc
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from typing import Optional
from PIL import Image


# Prompt template for spatial reasoning classification
SPATIAL_PROMPT = """Look at the image carefully.

Statement: "{statement}"

Is this statement true or false?

Answer with exactly one word: True or False."""


class SmolVLMClassifier:
    """
    SmolVLM2-Instruct wrapper for binary spatial reasoning classification.

    Supports batch inference for speed.
    """

    def __init__(
        self,
        model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
        device: Optional[str] = None,
        max_new_tokens: int = 5,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_new_tokens = max_new_tokens
        self.model_name = model_name

        print(f"Loading {model_name}...")
        self.processor = AutoProcessor.from_pretrained(model_name)
        # Fix padding side for decoder-only batch generation
        if hasattr(self.processor, "tokenizer"):
            self.processor.tokenizer.padding_side = "left"
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            _attn_implementation="eager",
            low_cpu_mem_usage=True,
        ).to(self.device)
        self.model.eval()
        print(f"Model loaded on {self.device}")

    def predict(self, image, statement: str) -> str:
        """Single example prediction."""
        prompt = SPATIAL_PROMPT.format(statement=statement)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.device, dtype=torch.bfloat16)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
            )

        generated_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0]

        return self._extract_answer(generated_text)

    def predict_batch(self, images: list, statements: list[str]) -> list[str]:
        """
        Batch prediction - processes multiple examples at once for speed.
        """
        if len(images) == 0:
            return []

        # Build messages for all examples
        batch_messages = []
        for image, statement in zip(images, statements):
            prompt = SPATIAL_PROMPT.format(statement=statement)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            batch_messages.append(messages)

        # Process batch through the processor
        inputs = self.processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            padding=True,
        ).to(self.device, dtype=torch.bfloat16)

        # Generate for all examples at once
        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
            )

        # Trim input tokens from generated output
        input_len = inputs["input_ids"].shape[1]
        generated_ids = generated_ids[:, input_len:]

        generated_texts = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )

        # Free batch memory immediately
        del inputs, generated_ids
        gc.collect()
        torch.cuda.empty_cache()

        return [self._extract_answer(text) for text in generated_texts]

    def _extract_answer(self, text: str) -> str:
        """Extract the True/False answer from generated text."""
        if "Assistant:" in text:
            text = text.split("Assistant:")[-1].strip()
        elif "assistant" in text.lower():
            lines = text.split("\n")
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip():
                    text = lines[i].strip()
                    break
        return text
