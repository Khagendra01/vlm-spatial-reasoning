"""
LoRA fine-tuning for SmolVLM2 on VSR spatial reasoning.

Standard LoRA setup for RTX A6000 (48GB VRAM).
No aggressive quantization — keeps experiment conventional.

Usage:
    python -m src.training.lora --manifest data/manifests/general_train.jsonl --output checkpoints/general_lora
    python -m src.training.lora --manifest data/manifests/targeted_train.jsonl --output checkpoints/targeted_lora
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoProcessor,
    AutoModelForImageTextToText,
    get_linear_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.training.collator import VSRDataCollator


def load_manifest(path: str) -> list[dict]:
    """Load JSONL manifest."""
    examples = []
    with open(path) as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def build_dataset(examples: list[dict]) -> Dataset:
    """Convert manifest to HuggingFace Dataset."""
    return Dataset.from_list(examples)


def setup_lora(model, rank: int = 8, alpha: int = 16, dropout: float = 0.05):
    """Apply LoRA to the model's attention layers."""
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=rank,
        lora_alpha=alpha,
        lora_dropout=dropout,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def train(
    manifest_path: str,
    output_dir: str,
    model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
    epochs: int = 2,
    lr: float = 1e-4,
    micro_batch_size: int = 4,
    grad_accum: int = 4,
    max_length: int = 2048,
    warmup_ratio: float = 0.1,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    seed: int = 42,
    eval_every: int = 100,
):
    """Run LoRA training."""
    os.makedirs(output_dir, exist_ok=True)
    effective_batch_size = micro_batch_size * grad_accum

    print(f"\n{'='*60}")
    print(f"LoRA TRAINING")
    print(f"{'='*60}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Output:   {output_dir}")
    print(f"  Model:    {model_name}")
    print(f"  Epochs:   {epochs}")
    print(f"  LR:       {lr}")
    print(f"  Micro BS: {micro_batch_size}")
    print(f"  Grad Accum: {grad_accum}")
    print(f"  Effective BS: {effective_batch_size}")
    print(f"  LoRA:     rank={lora_rank}, alpha={lora_alpha}, dropout={lora_dropout}")
    print(f"  Max Length: {max_length}")
    print(f"  Device:   {torch.cuda.get_device_name(0)}")
    print(f"  VRAM:     {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"{'='*60}\n")

    # Load data
    examples = load_manifest(manifest_path)
    print(f"Loaded {len(examples)} training examples")

    # Load processor and model
    print(f"Loading processor...")
    processor = AutoProcessor.from_pretrained(model_name)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "right"

    print(f"Loading model...")
    model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        dtype=torch.bfloat16,
        _attn_implementation="eager",
        low_cpu_mem_usage=True,
    ).to("cuda")

    # Apply LoRA
    print(f"Applying LoRA...")
    model = setup_lora(model, rank=lora_rank, alpha=lora_alpha, dropout=lora_dropout)

    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    # Build collator and dataset
    collator = VSRDataCollator(processor=processor, max_length=max_length)
    dataset = build_dataset(examples)

    # Split 95/5 for train/eval
    split = dataset.train_test_split(test_size=0.05, seed=seed)
    train_ds = split["train"]
    eval_ds = split["test"]

    print(f"Train: {len(train_ds)}, Eval: {len(eval_ds)}")

    # DataLoader
    train_loader = DataLoader(
        train_ds,
        batch_size=micro_batch_size,
        shuffle=True,
        collate_fn=collator,
        num_workers=0,
        pin_memory=True,
    )

    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs // grad_accum
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # Training loop
    print(f"\nStarting training ({total_steps} steps, {warmup_steps} warmup)...")
    model.train()
    global_step = 0
    epoch_losses = []
    step_times = []
    start_time = time.time()

    for epoch in range(epochs):
        epoch_loss = 0.0
        epoch_steps = 0

        for batch_idx, batch in enumerate(train_loader):
            if batch is None:
                continue

            # Move to device
            input_ids = batch["input_ids"].to("cuda")
            attention_mask = batch["attention_mask"].to("cuda")
            labels = batch["labels"].to("cuda")
            pixel_values = batch.get("pixel_values", None)
            if pixel_values is not None:
                pixel_values = pixel_values.to("cuda")

            # Forward pass
            with torch.cuda.amp.autocast(dtype=torch.bfloat16):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                    pixel_values=pixel_values,
                )
                loss = outputs.loss / grad_accum

            # Backward pass
            loss.backward()
            epoch_loss += loss.item() * grad_accum

            if (batch_idx + 1) % grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

                step_time = time.time() - start_time
                step_times.append(step_time)

                if global_step % eval_every == 0:
                    avg_loss = epoch_loss / max(1, epoch_steps)
                    lr_current = scheduler.get_last_lr()[0]
                    elapsed = time.time() - start_time
                    print(f"  Step {global_step}/{total_steps} | "
                          f"Loss: {avg_loss:.4f} | "
                          f"LR: {lr_current:.2e} | "
                          f"Elapsed: {elapsed:.0f}s")

                    # Save checkpoint
                    checkpoint_dir = os.path.join(output_dir, f"checkpoint-{global_step}")
                    os.makedirs(checkpoint_dir, exist_ok=True)
                    model.save_pretrained(checkpoint_dir)
                    processor.save_pretrained(checkpoint_dir)

            epoch_steps += 1

        avg_epoch_loss = epoch_loss / max(1, epoch_steps)
        epoch_losses.append(avg_epoch_loss)
        print(f"\nEpoch {epoch+1}/{epochs} complete | Avg Loss: {avg_epoch_loss:.4f}")

    # Save final model
    total_time = time.time() - start_time
    print(f"\nTraining complete in {total_time:.1f}s")

    final_dir = os.path.join(output_dir, "final")
    os.makedirs(final_dir, exist_ok=True)
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    print(f"Final model saved to: {final_dir}")

    # Save training log
    log = {
        "manifest": manifest_path,
        "model": model_name,
        "epochs": epochs,
        "lr": lr,
        "effective_batch_size": effective_batch_size,
        "lora_rank": lora_rank,
        "lora_alpha": lora_alpha,
        "lora_dropout": lora_dropout,
        "total_steps": total_steps,
        "epoch_losses": epoch_losses,
        "total_time_seconds": total_time,
        "train_size": len(train_ds),
        "eval_size": len(eval_ds),
        "device": torch.cuda.get_device_name(0),
        "timestamp": datetime.now().isoformat(),
    }
    log_path = os.path.join(output_dir, "training_log.json")
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"Training log: {log_path}")

    return model, processor


def main():
    parser = argparse.ArgumentParser(description="LoRA fine-tuning for VSR")
    parser.add_argument("--manifest", required=True, help="Path to training manifest JSONL")
    parser.add_argument("--output", required=True, help="Output directory for checkpoints")
    parser.add_argument("--model", default="HuggingFaceTB/SmolVLM2-2.2B-Instruct")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--micro-batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--eval-every", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train(
        manifest_path=args.manifest,
        output_dir=args.output,
        model_name=args.model,
        epochs=args.epochs,
        lr=args.lr,
        micro_batch_size=args.micro_batch_size,
        grad_accum=args.grad_accum,
        max_length=args.max_length,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        eval_every=args.eval_every,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
