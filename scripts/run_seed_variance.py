# -*- coding: utf-8 -*-
"""
Multi-seed reruns of the 7B LoRA conditions for training-run variance
estimates (Task 4 of the reviewer-response brief).

IMPORTANT:
  * This script does NOT modify the frozen canonical snapshot. It trains and
    evaluates fresh checkpoints and writes ONLY under
    results/seed_variance/{condition}/{seed}/ (predictions.csv + metrics.json).
  * The training recipe is a faithful mirror of the canonical runs
    (scripts/run_7b_pipeline.py phase2/phase3 and scripts/train_vision_lora.py):
    r=8, alpha=16, dropout=0.05, AdamW lr=1e-4, wd=0.01, linear warmup 10%,
    2 epochs, batch_size=1, bf16 autocast, gradient checkpointing, grad clip
    1.0, eager attention. The ONLY change vs the canonical run is the seed,
    which controls: torch/random/numpy RNGs, the 5% train/validation split,
    and DataLoader shuffle order.
  * The canonical runs were executed on an RTX A6000 (48 GB) with
    transformers 5.14.1 / peft 0.20.0. A preflight check refuses to run on
    machines with < 40 GB VRAM or without the base model available, because
    quantization or other memory tricks would change the recipe and would
    violate the "change only the seed" constraint.

Usage (on the GPU box, one process per condition/seed):
    python scripts/run_seed_variance.py --condition general --seed 101
    python scripts/run_seed_variance.py --condition projector --seed 202
    ...
Conditions: general, targeted, hardneg, projector, vision_proj
Recommended extra seeds: 101, 202 (canonical default seed: 42)
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
from datasets import Dataset, load_dataset
from PIL import Image
from torch.utils.data import DataLoader
from transformers import (AutoProcessor, Qwen2VLForConditionalGeneration,
                          get_linear_schedule_with_warmup)
from peft import LoraConfig, TaskType, get_peft_model

MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"
TRAIN_PROMPT = ('Look at the image carefully.\n\nStatement: "{statement}"\n\n'
                'Is this statement true or false?\n\n'
                'Answer with exactly one word: True or False.')

MANIFESTS = {
    "general": "data/manifests/general_train.jsonl",
    "targeted": "data/manifests/targeted_train.jsonl",
    "hardneg": "data/manifests/hardneg_train.jsonl",
    "projector": "data/manifests/general_train.jsonl",
    "vision_proj": "data/manifests/general_train.jsonl",
}

# LM-only conditions: q/k/v/o on the LLM (matches the committed adapter
# configs checkpoints/*/final/adapter_config.json). Vision-side conditions
# match scripts/train_vision_lora.py build_lora_targets exactly.
def lora_targets(condition):
    if condition in ("general", "targeted", "hardneg"):
        return ["q_proj", "v_proj", "k_proj", "o_proj"]
    if condition == "projector":
        return ["visual.merger.mlp.0", "visual.merger.mlp.2"]
    if condition == "vision_proj":
        mods = ["visual.merger.mlp.0", "visual.merger.mlp.2"]
        for i in range(24, 32):
            mods += [f"visual.blocks.{i}.attn.qkv", f"visual.blocks.{i}.attn.proj",
                     f"visual.blocks.{i}.mlp.fc1", f"visual.blocks.{i}.mlp.fc2"]
        return mods
    raise ValueError(condition)


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def cache_path(url):
    return Path("data/image_cache") / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"


def collate_batch(processor, examples, max_length=2048):
    true_tokens = processor.tokenizer.encode(" True", add_special_tokens=False)
    false_tokens = processor.tokenizer.encode(" False", add_special_tokens=False)
    processor.tokenizer.padding_side = "right"
    if processor.tokenizer.pad_token is None:
        processor.tokenizer.pad_token = processor.tokenizer.eos_token
    processed = []
    for ex in examples:
        img_p = cache_path(ex["image"])
        if not img_p.exists():
            continue
        img = Image.open(img_p).convert("RGB")
        prompt = TRAIN_PROMPT.format(statement=ex["statement"])
        answer = "True" if ex["label"] else "False"
        messages = [{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": prompt}]}]
        prompt_inputs = processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt")
        prompt_ids = prompt_inputs["input_ids"].squeeze(0)
        answer_ids = torch.tensor(true_tokens if ex["label"] else false_tokens,
                                  dtype=prompt_ids.dtype)
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
                          "image_grid_thw": image_grid_thw, "mm_token_type_ids": mm_tt})
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
        batch_ids.append(ids); batch_mask.append(mask); batch_labels.append(labels)
        if p["pixel_values"] is not None:
            batch_pv.append(p["pixel_values"])
        if p["image_grid_thw"] is not None:
            batch_grid.append(p["image_grid_thw"])
        if p.get("mm_token_type_ids") is not None:
            batch_mm.append(p["mm_token_type_ids"].squeeze(0)
                            if p["mm_token_type_ids"].dim() > 1
                            else p["mm_token_type_ids"])
    result = {"input_ids": torch.stack(batch_ids),
              "attention_mask": torch.stack(batch_mask),
              "labels": torch.stack(batch_labels)}
    if batch_pv:
        result["pixel_values"] = torch.stack(batch_pv)
    if batch_grid:
        result["image_grid_thw"] = torch.stack(batch_grid)
    if batch_mm:
        mm_max = max(m.shape[0] for m in batch_mm)
        result["mm_token_type_ids"] = torch.stack(
            [torch.cat([m, torch.zeros(mm_max - m.shape[0], dtype=m.dtype)])
             if m.shape[0] < mm_max else m for m in batch_mm])
    return result


def parse_tf(text):
    t = text.strip().lower()
    if "assistant:" in t:
        t = t.split("assistant:")[-1].strip()
    if t.startswith("true"):
        return True
    if t.startswith("false"):
        return False
    return None


def train(condition, seed, out_dir, max_steps=None):
    with open(MANIFESTS[condition]) as f:
        examples = [json.loads(l) for l in f]
    print(f"[seed {seed}] manifest {MANIFESTS[condition]}: {len(examples)} examples", flush=True)

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    targets = lora_targets(condition)
    lora_config = LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
                             lora_dropout=0.05, target_modules=targets)
    model = get_peft_model(model, lora_config)
    model.train()

    dataset = Dataset.from_list(examples)
    split = dataset.train_test_split(test_size=0.05, seed=seed)  # canonical: seed 42
    train_ds = split["train"]
    print(f"[seed {seed}] train: {len(train_ds)}", flush=True)

    g = torch.Generator()
    g.manual_seed(seed)
    loader = DataLoader(train_ds, batch_size=1, shuffle=True,
                        generator=g,
                        collate_fn=lambda b: collate_batch(processor, b),
                        num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    total_steps = len(loader) * 2  # 2 epochs, canonical
    scheduler = get_linear_schedule_with_warmup(optimizer, total_steps // 10, total_steps)
    print(f"[seed {seed}] total steps: {total_steps}", flush=True)

    t0 = time.time()
    done = 0
    for epoch in range(2):
        for batch in loader:
            if batch is None:
                continue
            fwd = {"input_ids": batch["input_ids"].to("cuda"),
                   "attention_mask": batch["attention_mask"].to("cuda"),
                   "labels": batch["labels"].to("cuda")}
            if "pixel_values" in batch:
                fwd["pixel_values"] = batch["pixel_values"].to("cuda")
            if "image_grid_thw" in batch:
                fwd["image_grid_thw"] = batch["image_grid_thw"].to("cuda")
            if "mm_token_type_ids" in batch:
                fwd["mm_token_type_ids"] = batch["mm_token_type_ids"].to("cuda")
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(**fwd)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            done += 1
            if max_steps is not None and done >= max_steps:
                print(f"[seed {seed}] SMOKE TEST: stopped after {done} steps "
                      f"(--max-steps {max_steps})", flush=True)
                break
        if max_steps is not None and done >= max_steps:
            break
        print(f"[seed {seed}] epoch {epoch+1}/2 done | loss {out.loss.item():.4f} | {time.time()-t0:.0f}s",
              flush=True)

    ckpt = out_dir / "checkpoint"
    ckpt.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(ckpt)
    processor.save_pretrained(ckpt)
    del model
    torch.cuda.empty_cache()
    return ckpt


def evaluate(condition, seed, ckpt, out_dir):
    from peft import PeftModel
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model = PeftModel.from_pretrained(model, ckpt)
    model.eval()

    dataset = load_dataset("cambridgeltl/vsr_random", split="test")
    records = [{"image_url": ex.get("image_link", ""),
                "statement": ex.get("caption", ""),
                "label": bool(ex.get("label", 0)),
                "relation": ex.get("relation", "")} for ex in dataset]

    images = []
    for r in records:
        p = cache_path(r["image_url"])
        images.append(Image.open(p).convert("RGB") if p.exists() else None)

    results = []
    batch_imgs, batch_stmts, batch_recs = [], [], []

    def flush():
        nonlocal batch_imgs, batch_stmts, batch_recs
        if not batch_imgs:
            return
        msgs = [[{"role": "user", "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": TRAIN_PROMPT.format(statement=st)}]}]
            for img, st in zip(batch_imgs, batch_stmts)]
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", padding=True).to("cuda", dtype=torch.bfloat16)
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        texts = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:],
                                       skip_special_tokens=True)
        del inputs, out
        torch.cuda.empty_cache()
        for j, raw in enumerate(texts):
            rec = batch_recs[j]
            pred = parse_tf(raw)
            results.append({"id": len(results), "statement": rec["statement"],
                            "relation": rec["relation"], "ground_truth": rec["label"],
                            "prediction": pred, "correct": pred == rec["label"]
                            if pred is not None else False,
                            "raw_output": raw, "image_url": rec["image_url"]})
        batch_imgs.clear(); batch_stmts.clear(); batch_recs.clear()

    for rec, img in zip(records, images):
        if img is None:
            results.append({"id": len(results), "statement": rec["statement"],
                            "relation": rec["relation"], "ground_truth": rec["label"],
                            "prediction": None, "correct": False,
                            "raw_output": "NO_IMAGE", "image_url": rec["image_url"]})
            continue
        batch_imgs.append(img)
        batch_stmts.append(rec["statement"])
        batch_recs.append(rec)
        if len(batch_imgs) >= 8:
            flush()
    flush()

    with open(out_dir / "predictions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "statement", "relation",
                                          "ground_truth", "prediction", "correct",
                                          "raw_output", "image_url"])
        w.writeheader()
        w.writerows(results)

    correct = sum(1 for r in results if r["correct"])
    total = len(results)
    ori = [r for r in results if r["relation"] in
           {"facing", "facing away from", "parallel to", "perpendicular to"}]
    ori_c = sum(1 for r in ori if r["correct"])
    metrics = {"global": {"accuracy": correct / total, "correct": correct,
                          "total": total},
               "by_family": {"orientation": {"accuracy": ori_c / len(ori),
                                             "correct": ori_c, "total": len(ori)}},
               "config": {"model": MODEL_NAME, "condition": condition,
                          "seed": seed, "lora_r": 8, "lora_alpha": 16,
                          "lora_dropout": 0.05, "lr": 1e-4, "epochs": 2,
                          "manifest": MANIFESTS[condition],
                          "recipe": "canonical (run_7b_pipeline.py / "
                                    "train_vision_lora.py), seed-only change"}}
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[seed {seed}] overall {correct}/{total} = {correct/total:.4f} | "
          f"orientation {ori_c}/{len(ori)} = {ori_c/len(ori):.4f}", flush=True)


def preflight():
    if not torch.cuda.is_available():
        sys.exit("ERROR: no CUDA device. The canonical recipe requires GPU "
                 "bf16 training; refusing to run on CPU.")
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.0f} GB)", flush=True)
    if vram_gb < 40:
        sys.exit(f"ERROR: {vram_gb:.0f} GB VRAM < 40 GB required by the canonical "
                 "recipe (canonical runs used an RTX A6000, 48 GB). Quantizing or "
                 "offloading would change the recipe and violate the "
                 "'change only the seed' constraint. Run this on the GPU box.")
    try:
        from transformers import AutoProcessor
        AutoProcessor.from_pretrained(MODEL_NAME)
    except Exception as e:
        sys.exit(f"ERROR: base model {MODEL_NAME} not available: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True,
                    choices=["general", "targeted", "hardneg", "projector",
                             "vision_proj"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--skip-preflight", action="store_true",
                    help="skip the VRAM/model preflight (use with care)")
    ap.add_argument("--max-steps", type=int, default=None,
                    help="stop training after N optimizer steps (smoke test "
                         "only; canonical behavior is the full 2-epoch run). "
                         "Note: the run still writes metrics.json and is then "
                         "treated as complete, so use a scratch seed for smoke "
                         "tests.")
    args = ap.parse_args()

    seed_everything(args.seed)
    if not args.skip_preflight:
        preflight()

    out_dir = Path("results") / "seed_variance" / args.condition / str(args.seed)
    if (out_dir / "metrics.json").exists():
        sys.exit(f"results/seed_variance/{args.condition}/{args.seed} already "
                 "exists with metrics.json; refusing to overwrite.")
    out_dir.mkdir(parents=True, exist_ok=True)

    ckpt = train(args.condition, args.seed, out_dir, max_steps=args.max_steps)
    if args.max_steps is not None:
        print(f"SMOKE TEST complete: {args.max_steps} steps; skipping full "
              "evaluation. Delete results/seed_variance/{args.condition}/"
              f"{args.seed} before the real run.", flush=True)
        return
    evaluate(args.condition, args.seed, ckpt, out_dir)
    print(f"DONE: results/seed_variance/{args.condition}/{args.seed}/", flush=True)


if __name__ == "__main__":
    main()
