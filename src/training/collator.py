"""
Data collator for LoRA training on VSR.

Handles image loading, prompt formatting, and tokenization for
SmolVLM2 fine-tuning with LoRA.

Approach: tokenize prompt with images, then manually append answer tokens.
"""

import hashlib
import torch
from pathlib import Path
from PIL import Image
from typing import Optional
from transformers import AutoProcessor


# Training prompt template — same as baseline but we train on the label
TRAIN_PROMPT = """Look at the image carefully.

Statement: "{statement}"

Is this statement true or false?

Answer with exactly one word: True or False."""


class VSRDataCollator:
    """
    Collates VSR examples into batches for SmolVLM2 training.

    Returns dict with:
        - input_ids: tokenized prompt + answer
        - attention_mask: attention mask
        - labels: loss targets (masked for prompt tokens)
        - pixel_values: image tensors
    """

    def __init__(
        self,
        processor: AutoProcessor,
        max_length: int = 2048,
        prompt_template: str = TRAIN_PROMPT,
        image_cache_dir: str = "/home/ubuntu/vlm-spatial-reasoning/data/image_cache",
    ):
        self.processor = processor
        self.max_length = max_length
        self.prompt_template = prompt_template
        self.tokenizer = processor.tokenizer
        self.image_cache_dir = Path(image_cache_dir)

        # Set padding side to right for training
        self.tokenizer.padding_side = "right"
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Cache answer token IDs
        self.true_tokens = self.tokenizer.encode(" True", add_special_tokens=False)
        self.false_tokens = self.tokenizer.encode(" False", add_special_tokens=False)

    def _load_image(self, url: str) -> Optional[Image.Image]:
        """Load image from local cache (fast) or URL (fallback)."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_path = self.image_cache_dir / f"{url_hash}.jpg"

        try:
            if cache_path.exists():
                return Image.open(cache_path).convert("RGB")
            # Fallback to URL if not cached
            import urllib.request
            from io import BytesIO
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            return None

    def _process_single(self, example: dict) -> Optional[dict]:
        """Process a single example into model inputs."""
        # Load image
        img = self._load_image(example["image"])
        if img is None:
            return None

        # Format prompt
        prompt = self.prompt_template.format(statement=example["statement"])

        # Build conversation with prompt only (for input)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Tokenize prompt with images
        prompt_inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,  # Adds assistant header
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )

        # Get prompt token IDs
        prompt_ids = prompt_inputs["input_ids"].squeeze(0)
        prompt_len = prompt_ids.shape[0]

        # Get answer token IDs
        if example["label"]:
            answer_ids = torch.tensor(self.true_tokens, dtype=prompt_ids.dtype)
        else:
            answer_ids = torch.tensor(self.false_tokens, dtype=prompt_ids.dtype)

        # Concatenate prompt + answer
        full_ids = torch.cat([prompt_ids, answer_ids])

        # Truncate if needed
        if full_ids.shape[0] > self.max_length:
            full_ids = full_ids[:self.max_length]

        # Create attention mask
        attention_mask = torch.ones_like(full_ids)

        # Create labels: mask prompt tokens with -100, only train on answer
        labels = torch.full_like(full_ids, -100)
        # Unmask answer tokens (they come after the prompt)
        answer_start = min(prompt_len, full_ids.shape[0])
        answer_end = full_ids.shape[0]
        labels[answer_start:answer_end] = full_ids[answer_start:answer_end]

        # Get pixel values from prompt inputs
        pixel_values = prompt_inputs.get("pixel_values", None)
        if pixel_values is not None:
            pixel_values = pixel_values.squeeze(0)

        return {
            "input_ids": full_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "pixel_values": pixel_values,
        }

    def __call__(self, batch: list[dict]) -> Optional[dict]:
        """
        Collate a batch of VSR examples.

        Each example has: statement, label, relation, family, image (URL)
        """
        processed = []
        for example in batch:
            result = self._process_single(example)
            if result is not None:
                processed.append(result)

        if not processed:
            return None

        # Pad sequences to same length
        max_len = min(
            max(p["input_ids"].shape[0] for p in processed),
            self.max_length
        )

        batch_input_ids = []
        batch_attention_mask = []
        batch_labels = []
        batch_pixel_values = []

        for p in processed:
            # Truncate
            input_ids = p["input_ids"][:max_len]
            attention_mask = p["attention_mask"][:max_len]
            labels = p["labels"][:max_len]

            # Pad
            pad_len = max_len - input_ids.shape[0]
            if pad_len > 0:
                input_ids = torch.cat([input_ids, torch.zeros(pad_len, dtype=input_ids.dtype)])
                attention_mask = torch.cat([attention_mask, torch.zeros(pad_len, dtype=attention_mask.dtype)])
                labels = torch.cat([labels, torch.full((pad_len,), -100, dtype=labels.dtype)])

            batch_input_ids.append(input_ids)
            batch_attention_mask.append(attention_mask)
            batch_labels.append(labels)

            if p["pixel_values"] is not None:
                batch_pixel_values.append(p["pixel_values"])

        result = {
            "input_ids": torch.stack(batch_input_ids),
            "attention_mask": torch.stack(batch_attention_mask),
            "labels": torch.stack(batch_labels),
        }

        if batch_pixel_values:
            # Pad pixel_values to max patches in batch
            max_patches = max(pv.shape[0] for pv in batch_pixel_values)
            padded = []
            for pv in batch_pixel_values:
                if pv.shape[0] < max_patches:
                    pad_size = max_patches - pv.shape[0]
                    pv = torch.cat([pv, torch.zeros(pad_size, *pv.shape[1:], dtype=pv.dtype, device=pv.device)], dim=0)
                padded.append(pv)
            result["pixel_values"] = torch.stack(padded)

        return result
