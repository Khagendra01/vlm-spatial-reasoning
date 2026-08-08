"""Quick test to check if model loads."""
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

model_name = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_name)
print("Processor loaded!")

print("Loading model...")
try:
    model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        dtype=torch.bfloat16,
        _attn_implementation="eager",
    ).to("cuda")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    import traceback
    traceback.print_exc()
