#!/usr/bin/env python3
"""
Seed campaign training driver (campaign: seed_campaign_r1).

Frozen spec: configs/seed_campaign/SEED_CAMPAIGN.json
Verbatim recipe sources (master): scripts/run_7b_pipeline.py PHASE 2 train_lora
(collate_batch + TRAIN_PROMPT + loop), src/training/lora.py train() + collator.

Only intentional difference from seed-0 runs: explicit per-run seed via
torch.manual_seed / cuda / numpy at driver start (seed-0 was unseeded).
The 95/5 split mapping is frozen at seed=42 for every run.
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

MANIFEST = "data/manifests/general_train.jsonl"
CAMPAIGN_ID = "seed_campaign_r1"
SPEC_REF = "configs/seed_campaign/SEED_CAMPAIGN.json"

TRAIN_PROMPT = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'


def seed_rng(seed: int):
    import numpy as np
    import torch
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


def write_log(output_dir: str, extra: dict):
    log_path = os.path.join(output_dir, "training_log.json")
    log = json.load(open(log_path))
    log["campaign_id"] = CAMPAIGN_ID
    log["spec_ref"] = SPEC_REF
    log.update(extra)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)


def train_7b(seed: int, output_dir: str):
    """Verbatim copy of scripts/run_7b_pipeline.py PHASE 2 train_lora (general),
    with campaign seeding and training_log.json."""

    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, get_linear_schedule_with_warmup
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset
    from torch.utils.data import DataLoader
    from PIL import Image

    MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

    seed_rng(seed)

    with open(MANIFEST) as f:
        examples = [json.loads(l) for l in f]
    print(f"Manifest: {len(examples)} examples (campaign seed {seed})")

    def load_cached_image(url):
        h = hashlib.md5(url.encode()).hexdigest()
        p = Path("data/image_cache") / f"{h}.jpg"
        if p.exists():
            return Image.open(p).convert("RGB")
        return None

    def collate_batch(processor, batch_examples, max_length=2048):
        true_tokens = processor.tokenizer.encode(" True", add_special_tokens=False)
        false_tokens = processor.tokenizer.encode(" False", add_special_tokens=False)
        processor.tokenizer.padding_side = "right"
        if processor.tokenizer.pad_token is None:
            processor.tokenizer.pad_token = processor.tokenizer.eos_token

        processed = []
        for ex in batch_examples:
            img = load_cached_image(ex["image"])
            if img is None:
                continue
            prompt = TRAIN_PROMPT.format(statement=ex["statement"])
            answer = "True" if ex["label"] else "False"
            messages = [{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": prompt}
            ]}]
            prompt_inputs = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
            prompt_ids = prompt_inputs["input_ids"].squeeze(0)
            answer_ids = torch.tensor(true_tokens if ex["label"] else false_tokens, dtype=prompt_ids.dtype)
            full_ids = torch.cat([prompt_ids, answer_ids])[:max_length]
            attention_mask = torch.ones_like(full_ids)
            labels = torch.full_like(full_ids, -100)
            labels[prompt_ids.shape[0]:full_ids.shape[0]] = full_ids[prompt_ids.shape[0]:full_ids.shape[0]]

            pixel_values = prompt_inputs.get("pixel_values", None)
            if pixel_values is not None and pixel_values.dim() >= 2:
                pixel_values = pixel_values.squeeze(0) if pixel_values.dim() == 3 else pixel_values
            else:
                pixel_values = None
            image_grid_thw = prompt_inputs.get("image_grid_thw", None)
            if image_grid_thw is not None:
                image_grid_thw = image_grid_thw.squeeze(0) if image_grid_thw.dim() == 2 else image_grid_thw
            mm_tt = prompt_inputs.get("mm_token_type_ids", None)
            if mm_tt is not None:
                mm_tt = mm_tt.squeeze(0)
                extra_len = full_ids.shape[0] - mm_tt.shape[0]
                if extra_len > 0:
                    mm_tt = torch.cat([mm_tt, torch.zeros(extra_len, dtype=mm_tt.dtype)])
                mm_tt = mm_tt[:max_length]
            else:
                mm_tt = None

            processed.append({"input_ids": full_ids, "attention_mask": attention_mask,
                              "labels": labels, "pixel_values": pixel_values,
                              "image_grid_thw": image_grid_thw,
                              "mm_token_type_ids": mm_tt})

        if not processed:
            return None

        max_len = max(p["input_ids"].shape[0] for p in processed)
        batch_ids, batch_mask, batch_labels, batch_pv, batch_grid, batch_mm = [], [], [], [], [], []
        for p in processed:
            ids = p["input_ids"][:max_len]
            mask = p["attention_mask"][:max_len]
            labels = p["labels"][:max_len]
            pad = max_len - ids.shape[0]
            if pad > 0:
                ids = torch.cat([ids, torch.zeros(pad, dtype=ids.dtype)])
                mask = torch.cat([mask, torch.zeros(pad, dtype=mask.dtype)])
                labels = torch.cat([labels, torch.full((pad,), -100, dtype=labels.dtype)])
            batch_ids.append(ids)
            batch_mask.append(mask)
            batch_labels.append(labels)
            if p["pixel_values"] is not None:
                batch_pv.append(p["pixel_values"])
            if p["image_grid_thw"] is not None:
                batch_grid.append(p["image_grid_thw"])
            if p.get("mm_token_type_ids") is not None:
                batch_mm.append(p["mm_token_type_ids"].squeeze(0) if p["mm_token_type_ids"].dim() > 1 else p["mm_token_type_ids"])

        result = {"input_ids": torch.stack(batch_ids), "attention_mask": torch.stack(batch_mask),
                  "labels": torch.stack(batch_labels)}
        if batch_pv:
            if batch_pv[0].dim() == 2:
                max_dim0 = max(pv.shape[0] for pv in batch_pv)
                hidden_dim = batch_pv[0].shape[1]
                padded = []
                for pv in batch_pv:
                    if pv.shape[0] < max_dim0:
                        pad_size = max_dim0 - pv.shape[0]
                        pv = torch.cat([pv, torch.zeros(pad_size, hidden_dim, dtype=pv.dtype, device=pv.device)], dim=0)
                    padded.append(pv)
                result["pixel_values"] = torch.stack(padded)
            else:
                max_patches = max(pv.shape[0] for pv in batch_pv)
                padded = []
                for pv in batch_pv:
                    if pv.shape[0] < max_patches:
                        pad_size = max_patches - pv.shape[0]
                        pv = torch.cat([pv, torch.zeros(pad_size, *pv.shape[1:], dtype=pv.dtype)], dim=0)
                    padded.append(pv)
                result["pixel_values"] = torch.stack(padded)
        if batch_grid:
            result["image_grid_thw"] = torch.stack(batch_grid)
        if batch_mm:
            max_mm_len = max(m.shape[0] for m in batch_mm)
            padded_mm = []
            for m in batch_mm:
                if m.shape[0] < max_mm_len:
                    m = torch.cat([m, torch.zeros(max_mm_len - m.shape[0], dtype=m.dtype)])
                padded_mm.append(m[:max_mm_len])
            result["mm_token_type_ids"] = torch.stack(padded_mm)
        return result

    print("Loading processor + model (bf16, eager)...")
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16,
        _attn_implementation="eager", low_cpu_mem_usage=True,
    ).to("cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    lora_config = LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
                             lora_dropout=0.05, target_modules=["q_proj", "v_proj", "k_proj", "o_proj"])
    model = get_peft_model(model, lora_config)
    model.train()

    dataset = Dataset.from_list(examples)
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]
    print(f"Train: {len(train_ds)}, Eval: {len(eval_ds)} (split frozen at seed=42)")

    loader = DataLoader(train_ds, batch_size=1, shuffle=True, collate_fn=collate_batch, num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    total_steps = len(loader) * 2
    scheduler = get_linear_schedule_with_warmup(optimizer, total_steps // 10, total_steps)

    os.makedirs(output_dir, exist_ok=True)
    global_step = 0
    t_start = time.time()
    step_samples = []
    epoch_losses = []

    for epoch in range(2):
        sum_loss = 0.0
        n_steps = 0
        for batch in loader:
            if batch is None:
                continue
            input_ids = batch["input_ids"].to("cuda")
            attention_mask = batch["attention_mask"].to("cuda")
            labels = batch["labels"].to("cuda")
            pixel_values = batch["pixel_values"].to("cuda") if "pixel_values" in batch else None
            image_grid_thw = batch["image_grid_thw"].to("cuda") if "image_grid_thw" in batch else None
            mm_token_type_ids = batch["mm_token_type_ids"].to("cuda") if "mm_token_type_ids" in batch else None

            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                forward_kwargs = dict(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                if pixel_values is not None:
                    forward_kwargs["pixel_values"] = pixel_values
                if image_grid_thw is not None:
                    forward_kwargs["image_grid_thw"] = image_grid_thw
                if mm_token_type_ids is not None:
                    forward_kwargs["mm_token_type_ids"] = mm_token_type_ids
                out = model(**forward_kwargs)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            global_step += 1
            sum_loss += out.loss.item()
            n_steps += 1

            if global_step % 10 == 0:
                elapsed = time.time() - t_start
                step_samples.append({"step": global_step, "loss": out.loss.item(), "elapsed_s": round(elapsed, 1)})
                print(f"  Step {global_step}/{total_steps} | Loss: {out.loss.item():.4f} | {elapsed:.0f}s", flush=True)

        epoch_losses.append(round(sum_loss / max(1, n_steps), 6))
        print(f"Epoch {epoch+1}/2 done | Avg Loss: {epoch_losses[-1]:.4f}", flush=True)

    final_dir = os.path.join(output_dir, "final")
    os.makedirs(final_dir, exist_ok=True)
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    print(f"Saved: {final_dir}", flush=True)

    total_time = time.time() - t_start
    log = {
        "manifest": MANIFEST,
        "model": MODEL_NAME,
        "epochs": 2,
        "lr": 1e-4,
        "effective_batch_size": 1,
        "micro_batch_size": 1,
        "grad_accum": 1,
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "warmup_steps": total_steps // 10,
        "total_steps": total_steps,
        "epoch_losses": epoch_losses,
        "step_samples": step_samples,
        "total_time_seconds": round(total_time, 1),
        "train_size": len(train_ds),
        "eval_size": len(eval_ds),
        "device": torch.cuda.get_device_name(0),
        "timestamp": datetime.now().isoformat(),
    }
    with open(os.path.join(output_dir, "training_log.json"), "w") as f:
        json.dump(log, f, indent=2)
    write_log(output_dir, {"seed": seed, "split_seed": 42, "backbone": "qwen2vl_7b"})
    print(f"Training complete: {total_time:.0f}s", flush=True)


def train_2b(seed: int, output_dir: str):
    """Legacy src/training/lora.py train() with frozen manifest-identical args;
    campaign seed applied via global RNG before the call (split frozen at 42)."""
    from src.training.lora import train as lora_train
    seed_rng(seed)
    lora_train(
        manifest_path=MANIFEST,
        output_dir=output_dir,
        model_name="HuggingFaceTB/SmolVLM2-2.2B-Instruct",
        epochs=2,
        lr=1e-4,
        micro_batch_size=1,
        grad_accum=16,
        max_length=2048,
        warmup_ratio=0.1,
        lora_rank=8,
        lora_alpha=16,
        lora_dropout=0.05,
        seed=42,
        eval_every=100,
    )
    write_log(output_dir, {"seed": seed, "split_seed": 42, "backbone": "smolvlm2_2b"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", choices=["qwen2vl_7b", "smolvlm2_2b"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    tag = [t for t, s in {"A": 101, "B": 202, "C": 303}.items() if s == args.seed]
    tag = tag[0] if tag else "?"

    if args.backbone == "qwen2vl_7b":
        train_7b(args.seed, args.output)
    else:
        train_2b(args.seed, args.output)
    print(f"DONE backbone={args.backbone} seed={args.seed} tag={tag} output={args.output}")


if __name__ == "__main__":
    main()