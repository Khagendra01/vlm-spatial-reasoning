"""
Evaluate LoRA-finetuned SmolVLM2 on VSR test set.

Reuses baseline infrastructure for consistent comparison.
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.datasets.vsr import load_vsr
from src.evaluation.parser import parse_true_false
from scripts.run_baseline import (
    RELATION_FAMILIES, prefetch_images, compute_global_metrics,
    compute_relation_metrics, compute_family_metrics, print_results,
)


class LoRAClassifier:
    """LoRA model wrapper with same interface as SmolVLMClassifier."""

    def __init__(self, base_model_name, lora_path, device="cuda", max_new_tokens=5):
        from transformers import AutoProcessor, AutoModelForImageTextToText
        from peft import PeftModel

        self.device = device
        self.max_new_tokens = max_new_tokens
        self.prompt_template = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'

        print(f"Loading base model: {base_model_name}")
        self.processor = AutoProcessor.from_pretrained(base_model_name)
        if hasattr(self.processor, "tokenizer"):
            self.processor.tokenizer.padding_side = "left"

        model = AutoModelForImageTextToText.from_pretrained(
            base_model_name, dtype=torch.bfloat16,
            _attn_implementation="eager", low_cpu_mem_usage=True,
        ).to(device)

        print(f"Loading LoRA: {lora_path}")
        self.model = PeftModel.from_pretrained(model, lora_path)
        self.model.eval()
        print(f"Model ready on {device}")

    def predict_batch(self, images, statements):
        batch_messages = []
        for image, statement in zip(images, statements):
            prompt = self.prompt_template.format(statement=statement)
            messages = [{"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ]}]
            batch_messages.append(messages)

        inputs = self.processor.apply_chat_template(
            batch_messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        ).to(self.device, dtype=torch.bfloat16)

        with torch.inference_mode():
            generated_ids = self.model.generate(**inputs, do_sample=False, max_new_tokens=self.max_new_tokens)

        input_len = inputs["input_ids"].shape[1]
        generated_ids = generated_ids[:, input_len:]
        generated_texts = self.processor.batch_decode(generated_ids, skip_special_tokens=True)

        del inputs, generated_ids
        torch.cuda.empty_cache()

        return [self._extract_answer(t) for t in generated_texts]

    def _extract_answer(self, text):
        if "Assistant:" in text:
            text = text.split("Assistant:")[-1].strip()
        elif "assistant" in text.lower():
            lines = text.split("\n")
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip():
                    text = lines[i].strip()
                    break
        return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lora-path", required=True)
    parser.add_argument("--base-model", default="HuggingFaceTB/SmolVLM2-2.2B-Instruct")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    lora_name = Path(args.lora_path).parent.name

    print(f"\n{'='*60}")
    print(f"EVALUATING: {lora_name}")
    print(f"{'='*60}")

    # Load model
    classifier = LoRAClassifier(args.base_model, args.lora_path)

    # Load data
    print("Loading VSR test data...")
    records = load_vsr(split="test")
    print(f"Test examples: {len(records)}")

    # Prefetch images from cache
    images = prefetch_images(records, max_workers=16)

    # Run evaluation
    print(f"\nRunning evaluation (batch_size={args.batch_size})...")
    results = []
    start_time = time.time()

    batch_images, batch_statements, batch_records = [], [], []

    def flush_batch():
        nonlocal batch_images, batch_statements, batch_records
        if not batch_images:
            return
        raw_outputs = classifier.predict_batch(batch_images, batch_statements)
        for j, raw_output in enumerate(raw_outputs):
            record = batch_records[j]
            prediction = parse_true_false(raw_output)
            correct = prediction == record["label"] if prediction is not None else False
            results.append({
                "id": len(results),
                "statement": record["statement"],
                "relation": record["relation"],
                "ground_truth": record["label"],
                "prediction": prediction,
                "correct": correct,
                "raw_output": raw_output,
                "image_url": record.get("image", ""),
            })
        batch_images.clear()
        batch_statements.clear()
        batch_records.clear()

    for i, record in enumerate(records):
        img = images[i]
        if img is None:
            results.append({
                "id": i, "statement": record["statement"], "relation": record["relation"],
                "ground_truth": record["label"], "prediction": None, "correct": False,
                "raw_output": "IMAGE_DOWNLOAD_FAILED", "image_url": record.get("image", ""),
            })
            continue

        batch_images.append(img)
        batch_statements.append(record["statement"])
        batch_records.append(record)

        if len(batch_images) >= args.batch_size:
            flush_batch()
            if (i + 1) % 200 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"  [{i+1}/{len(records)}] {rate:.1f} ex/s | {elapsed:.0f}s")

    flush_batch()
    total_time = time.time() - start_time

    # Compute metrics
    global_metrics = compute_global_metrics(results)
    relation_metrics = compute_relation_metrics(results)
    family_metrics = compute_family_metrics(results)

    # Save
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_file = os.path.join(args.output_dir, f"{lora_name}_predictions_{timestamp}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "statement", "relation", "ground_truth",
                                                "prediction", "correct", "raw_output", "image_url"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    metrics_file = os.path.join(args.output_dir, f"{lora_name}_metrics_{timestamp}.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump({"global": global_metrics, "by_relation": relation_metrics,
                    "by_family": family_metrics,
                    "config": {"model": lora_name, "lora_path": args.lora_path,
                               "num_examples": len(records), "total_time_seconds": total_time}},
                  f, indent=2, ensure_ascii=False)

    print_results(global_metrics, relation_metrics, family_metrics, csv_file)
    print(f"\nDone in {total_time:.1f}s ({total_time/len(records):.2f}s/example)")
    return global_metrics, relation_metrics, family_metrics


if __name__ == "__main__":
    main()
