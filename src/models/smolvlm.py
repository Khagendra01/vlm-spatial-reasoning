"""
SmolVLM2-2.2B-Instruct model wrapper for spatial reasoning classification.

Loads the model, accepts an image + spatial statement, and returns True/False.
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from typing import Optional


# Prompt template for spatial reasoning classification
SPATIAL_PROMPT = """Look at the image carefully.

Statement: "{statement}"

Is this statement true or false?

Answer with exactly one word: True or False."""


class SmolVLMClassifier:
    """
    SmolVLM2-2.2B-Instruct wrapper for binary spatial reasoning classification.

    Uses mixed precision (bfloat16) and batch size 1 for 8GB GPU.
    """

    def __init__(
        self,
        model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
        device: Optional[str] = None,
        max_new_tokens: int = 10,
    ):
        """
        Initialize the classifier.

        Args:
            model_name: HuggingFace model name
            device: Device to use (auto-detects CUDA if None)
            max_new_tokens: Maximum tokens to generate (kept tiny for classification)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_new_tokens = max_new_tokens

        print(f"Loading {model_name}...")
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            dtype=torch.bfloat16,
            _attn_implementation="eager",  # Use eager for compatibility
        ).to(self.device)
        self.model.eval()
        print(f"Model loaded on {self.device}")

    def predict(self, image, statement: str) -> str:
        """
        Predict whether a spatial statement is true or false for the given image.

        Args:
            image: PIL Image or image path
            statement: Spatial statement to evaluate (e.g., "The cup is to the left of the plate.")

        Returns:
            Raw model output string
        """
        # Format the prompt
        prompt = SPATIAL_PROMPT.format(statement=statement)

        # Create messages in chat format
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Apply chat template
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.device, dtype=torch.bfloat16)

        # Generate with minimal tokens
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=self.max_new_tokens,
            )

        # Decode only the generated tokens
        generated_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0]

        # Remove the prompt from the output (keep only the response)
        # The response comes after the last assistant marker
        if "Assistant:" in generated_text:
            generated_text = generated_text.split("Assistant:")[-1].strip()
        elif "assistant" in generated_text.lower():
            # Try to find the response after the last role marker
            lines = generated_text.split("\n")
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip():
                    generated_text = lines[i].strip()
                    break

        return generated_text

    def predict_batch(self, images, statements: list[str]) -> list[str]:
        """
        Predict for a batch of images and statements.

        Args:
            images: List of PIL Images
            statements: List of spatial statements

        Returns:
            List of raw model output strings
        """
        return [self.predict(img, stmt) for img, stmt in zip(images, statements)]
