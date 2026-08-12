#!/usr/bin/env python3
"""
Master autonomous script: Full 7B VLM pipeline.
Zero-shot â†’ General LoRA â†’ Targeted LoRA â†’ Evaluate â†’ Compare â†’ Commit.

Runs in screen session 'vlm7b'. Check with: screen -r vlm7b
Logs to: /tmp/vlm7b_pipeline.log
"""

import os, sys, json, csv, time, hashlib, traceback, subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from math import sqrt, erfc

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

LOG = "/tmp/vlm7b_pipeline.log"
RESULTS_DIR = "results"
CKPT_DIR = "checkpoints"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def run(cmd):
    log(f"  CMD: {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        log(f"  STDERR: {r.stderr[-500:]}")
    return r.stdout, r.returncode

# â”€â”€ McNemar test â”€â”€
def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 0.0, 1.0
    stat = (abs(b - c) - 1) ** 2 / n
    p = erfc(sqrt(stat / 2))
    return stat, p

def CI(n_correct, n_total, z=1.96):
    if n_total == 0:
        return 0.0, 0.0
    p = n_correct / n_total
    se = sqrt(p * (1 - p) / n_total)
    return max(0, p - z * se), min(1, p + z * se)

# â”€â”€ Relation families â”€â”€
RELATION_FAMILIES = {
    "horizontal": ["left of", "right of", "at the left side of", "at the right side of",
                    "at the side of", "beside", "next to", "alongside", "across from"],
    "vertical": ["above", "below", "over", "under", "beneath", "on top of"],
    "depth": ["in front of", "behind", "at the back of", "ahead of"],
    "orientation": ["facing", "facing away from", "parallel to", "perpendicular to"],
    "containment": ["in", "inside", "contains", "within", "enclosed by"],
    "proximity": ["near", "far from", "far away from", "close to", "away from"],
    "topology_contact": ["touching", "on", "at", "at the edge of", "against", "attached to",
                          "connected to", "detached from"],
    "compositional": ["part of", "has as a part", "consists of", "surrounding",
                       "in the middle of", "among"],
}

def get_family(relation):
    for fam, rels in RELATION_FAMILIES.items():
        if relation in rels:
            return fam
    return "other"

# â”€â”€ Parse True/False â”€â”€
def parse_tf(text):
    t = text.strip().lower()
    if "assistant:" in t:
        t = t.split("assistant:")[-1].strip()
    if t.startswith("true"):
        return True
    if t.startswith("false"):
        return False
    return None

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PHASE 1: Zero-shot evaluation on 7B model
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def phase1_zeroshot():
    log("=" * 60)
    log("PHASE 1: Qwen2-VL-7B-Instruct ZERO-SHOT evaluation")
    log("=" * 60)

    import torch
    from PIL import Image
    from datasets import load_dataset

    MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

    log("Loading processor...")
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"

    log("Loading model...")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        dtype=torch.bfloat16,
        _attn_implementation="eager",
        low_cpu_mem_usage=True,
    ).to("cuda")
    model.eval()

    vram = torch.cuda.memory_allocated() / 1e9
    log(f"Model loaded: {vram:.1f}GB VRAM")

    # Load test data
    log("Loading VSR test split...")
    dataset = load_dataset("cambridgeltl/vsr_random", split="test")
    records = []
    for ex in dataset:
        records.append({
            "image_url": ex.get("image_link", ""),
            "statement": ex.get("caption", ""),
            "label": bool(ex.get("label", 0)),
            "relation": ex.get("relation", ""),
        })
    log(f"Test examples: {len(records)}")

    # Load cached images
    cache_dir = Path("data/image_cache")
    images = []
    loaded = 0
    for r in records:
        h = hashlib.md5(r["image_url"].encode()).hexdigest()
        p = cache_dir / f"{h}.jpg"
        if p.exists():
            images.append(Image.open(p).convert("RGB"))
            loaded += 1
        else:
            images.append(None)
    log(f"Images loaded from cache: {loaded}/{len(records)}")

    # Evaluate
    prompt_template = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'

    results = []
    t_start = time.time()
    batch_imgs, batch_stmts, batch_recs = [], [], []

    def flush():
        nonlocal batch_imgs, batch_stmts, batch_recs
        if not batch_imgs:
            return
        msgs = []
        for img, st in zip(batch_imgs, batch_stmts):
            p = prompt_template.format(statement=st)
            msgs.append([{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": p}
            ]}])
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        ).to("cuda", dtype=torch.bfloat16)
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        input_len = inputs["input_ids"].shape[1]
        texts = processor.batch_decode(out[:, input_len:], skip_special_tokens=True)
        del inputs, out
        torch.cuda.empty_cache()

        for j, raw in enumerate(texts):
            rec = batch_recs[j]
            pred = parse_tf(raw)
            correct = pred == rec["label"] if pred is not None else False
            results.append({
                "id": len(results), "statement": rec["statement"],
                "relation": rec["relation"], "ground_truth": rec["label"],
                "prediction": pred, "correct": correct,
                "raw_output": raw, "image_url": rec["image_url"],
            })
        batch_imgs.clear()
        batch_stmts.clear()
        batch_recs.clear()

    for i, (rec, img) in enumerate(zip(records, images)):
        if img is None:
            results.append({
                "id": i, "statement": rec["statement"], "relation": rec["relation"],
                "ground_truth": rec["label"], "prediction": None, "correct": False,
                "raw_output": "NO_IMAGE", "image_url": rec["image_url"],
            })
            continue
        batch_imgs.append(img)
        batch_stmts.append(rec["statement"])
        batch_recs.append(rec)
        if len(batch_imgs) >= 8:
            flush()
            if (i + 1) % 200 == 0:
                elapsed = time.time() - t_start
                log(f"  [{i+1}/{len(records)}] {(i+1)/elapsed:.1f} ex/s | {elapsed:.0f}s")

    flush()
    total_time = time.time() - t_start
    log(f"Zero-shot done: {total_time:.0f}s ({total_time/len(records):.2f}s/ex)")

    # Metrics
    correct = sum(1 for r in results if r["correct"])
    total = len(results)
    acc = correct / total

    family_metrics = {}
    for fam in RELATION_FAMILIES:
        fam_results = [r for r in results if get_family(r["relation"]) == fam]
        if not fam_results:
            continue
        fam_correct = sum(1 for r in fam_results if r["correct"])
        fam_total = len(fam_results)
        lo, hi = CI(fam_correct, fam_total)
        family_metrics[fam] = {
            "accuracy": fam_correct / fam_total, "correct": fam_correct,
            "total": fam_total, "ci_lower": lo, "ci_upper": hi,
        }

    log(f"Overall accuracy: {acc:.4f} ({correct}/{total})")
    for fam, m in sorted(family_metrics.items(), key=lambda x: -x[1]["accuracy"]):
        log(f"  {fam:25s} {m['accuracy']:.4f} ({m['correct']}/{m['total']})")

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_path = f"{RESULTS_DIR}/qwen2vl_7b_metrics_{ts}.json"
    preds_path = f"{RESULTS_DIR}/qwen2vl_7b_predictions_{ts}.csv"
    with open(metrics_path, "w") as f:
        json.dump({"global": {"accuracy": acc, "correct": correct, "total": total},
                    "by_family": family_metrics,
                    "config": {"model": MODEL_NAME, "num_examples": total,
                               "total_time_seconds": total_time}}, f, indent=2)
    with open(preds_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id","statement","relation","ground_truth",
                                           "prediction","correct","raw_output","image_url"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    log(f"Saved: {metrics_path}")
    log(f"Saved: {preds_path}")

    # Cleanup
    del model
    torch.cuda.empty_cache()
    import gc; gc.collect()

    return metrics_path, preds_path


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PHASE 2: LoRA training for 7B (general + targeted)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def phase2_lora_training():
    log("=" * 60)
    log("PHASE 2: Qwen2-VL-7B LoRA training (general + targeted)")
    log("=" * 60)

    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, get_linear_schedule_with_warmup
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset
    from torch.utils.data import DataLoader
    from PIL import Image
    import urllib.request
    from io import BytesIO

    MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

    # â”€â”€ Load manifests â”€â”€
    with open("data/manifests/general_train.jsonl") as f:
        general_examples = [json.loads(l) for l in f]
    with open("data/manifests/targeted_train.jsonl") as f:
        targeted_examples = [json.loads(l) for l in f]
    log(f"General manifest: {len(general_examples)} examples")
    log(f"Targeted manifest: {len(targeted_examples)} examples")

    # â”€â”€ Collator â”€â”€
    TRAIN_PROMPT = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'

    def load_cached_image(url):
        h = hashlib.md5(url.encode()).hexdigest()
        p = Path("data/image_cache") / f"{h}.jpg"
        if p.exists():
            return Image.open(p).convert("RGB")
        return None

    def collate_batch(processor, examples, max_length=2048):
        true_tokens = processor.tokenizer.encode(" True", add_special_tokens=False)
        false_tokens = processor.tokenizer.encode(" False", add_special_tokens=False)
        processor.tokenizer.padding_side = "right"
        if processor.tokenizer.pad_token is None:
            processor.tokenizer.pad_token = processor.tokenizer.eos_token

        processed = []
        for ex in examples:
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

            # mm_token_type_ids: extend with zeros for answer tokens
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

        result = {
            "input_ids": torch.stack(batch_ids),
            "attention_mask": torch.stack(batch_mask),
            "labels": torch.stack(batch_labels),
        }
        if batch_pv:
            # Qwen2-VL pixel_values are 2D (total_patches, hidden_dim) - pad along dim 0
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
            # Pad mm_token_type_ids to max_len
            max_mm_len = max(m.shape[0] for m in batch_mm)
            padded_mm = []
            for m in batch_mm:
                if m.shape[0] < max_mm_len:
                    m = torch.cat([m, torch.zeros(max_mm_len - m.shape[0], dtype=m.dtype)])
                padded_mm.append(m[:max_mm_len])
            result["mm_token_type_ids"] = torch.stack(padded_mm)
        return result

    def train_lora(manifest_name, examples, output_dir):
        log(f"\n--- Training {manifest_name} LoRA ---")

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

        vram = torch.cuda.memory_allocated() / 1e9
        log(f"Model loaded + LoRA: {vram:.1f}GB")

        dataset = Dataset.from_list(examples)
        split = dataset.train_test_split(test_size=0.05, seed=42)
        train_ds = split["train"]

        def collate_fn(batch):
            return collate_batch(processor, batch)

        loader = DataLoader(train_ds, batch_size=1, shuffle=True, collate_fn=collate_fn, num_workers=0)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
        total_steps = len(loader) * 2  # 2 epochs
        scheduler = get_linear_schedule_with_warmup(optimizer, total_steps // 10, total_steps)

        log(f"Train: {len(train_ds)}, Steps: {total_steps}")
        os.makedirs(output_dir, exist_ok=True)
        global_step = 0
        t_start = time.time()

        for epoch in range(2):
            for batch_idx, batch in enumerate(loader):
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

                if global_step % 10 == 0:
                    elapsed = time.time() - t_start
                    log(f"  Step {global_step}/{total_steps} | Loss: {out.loss.item():.4f} | {elapsed:.0f}s")

            avg_loss = out.loss.item()
            log(f"Epoch {epoch+1}/2 done | Loss: {avg_loss:.4f}")

        final_dir = os.path.join(output_dir, "final")
        os.makedirs(final_dir, exist_ok=True)
        model.save_pretrained(final_dir)
        processor.save_pretrained(final_dir)
        log(f"Saved: {final_dir}")

        total_time = time.time() - t_start
        log(f"Training complete: {total_time:.0f}s")

        del model
        torch.cuda.empty_cache()
        import gc; gc.collect()

        return final_dir

    # Train general
    gen_dir = train_lora("general", general_examples, f"{CKPT_DIR}/qwen2vl_7b_general_lora")

    # Train targeted
    tgt_dir = train_lora("targeted", targeted_examples, f"{CKPT_DIR}/qwen2vl_7b_targeted_lora")

    return gen_dir, tgt_dir


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PHASE 3: Evaluate LoRA models
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def phase3_evaluate_lora(lora_path, label):
    log("=" * 60)
    log(f"PHASE 3: Evaluate {label}")
    log("=" * 60)

    import torch
    from PIL import Image
    from datasets import load_dataset
    from peft import PeftModel
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16,
        _attn_implementation="eager", low_cpu_mem_usage=True,
    ).to("cuda")
    model = PeftModel.from_pretrained(model, lora_path)
    model.eval()

    vram = torch.cuda.memory_allocated() / 1e9
    log(f"LoRA model loaded: {vram:.1f}GB")

    dataset = load_dataset("cambridgeltl/vsr_random", split="test")
    records = []
    for ex in dataset:
        records.append({
            "image_url": ex.get("image_link", ""),
            "statement": ex.get("caption", ""),
            "label": bool(ex.get("label", 0)),
            "relation": ex.get("relation", ""),
        })

    cache_dir = Path("data/image_cache")
    images = []
    for r in records:
        h = hashlib.md5(r["image_url"].encode()).hexdigest()
        p = cache_dir / f"{h}.jpg"
        images.append(Image.open(p).convert("RGB") if p.exists() else None)

    prompt_template = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'

    results = []
    t_start = time.time()
    batch_imgs, batch_stmts, batch_recs = [], [], []

    def flush():
        nonlocal batch_imgs, batch_stmts, batch_recs
        if not batch_imgs:
            return
        msgs = []
        for img, st in zip(batch_imgs, batch_stmts):
            p = prompt_template.format(statement=st)
            msgs.append([{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": p}
            ]}])
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        ).to("cuda", dtype=torch.bfloat16)
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        texts = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        del inputs, out; torch.cuda.empty_cache()
        for j, raw in enumerate(texts):
            rec = batch_recs[j]
            pred = parse_tf(raw)
            results.append({
                "id": len(results), "statement": rec["statement"],
                "relation": rec["relation"], "ground_truth": rec["label"],
                "prediction": pred, "correct": pred == rec["label"] if pred is not None else False,
                "raw_output": raw, "image_url": rec["image_url"],
            })
        batch_imgs.clear(); batch_stmts.clear(); batch_recs.clear()

    for i, (rec, img) in enumerate(zip(records, images)):
        if img is None:
            results.append({"id": i, "statement": rec["statement"], "relation": rec["relation"],
                           "ground_truth": rec["label"], "prediction": None, "correct": False,
                           "raw_output": "NO_IMAGE", "image_url": rec["image_url"]})
            continue
        batch_imgs.append(img)
        batch_stmts.append(rec["statement"])
        batch_recs.append(rec)
        if len(batch_imgs) >= 8:
            flush()
            if (i + 1) % 200 == 0:
                elapsed = time.time() - t_start
                log(f"  [{i+1}/{len(records)}] {(i+1)/elapsed:.1f} ex/s | {elapsed:.0f}s")

    flush()
    total_time = time.time() - t_start

    correct = sum(1 for r in results if r["correct"])
    total = len(results)
    acc = correct / total

    family_metrics = {}
    for fam in RELATION_FAMILIES:
        fam_results = [r for r in results if get_family(r["relation"]) == fam]
        if not fam_results:
            continue
        fc = sum(1 for r in fam_results if r["correct"])
        ft = len(fam_results)
        lo, hi = CI(fc, ft)
        family_metrics[fam] = {"accuracy": fc/ft, "correct": fc, "total": ft, "ci_lower": lo, "ci_upper": hi}

    log(f"Accuracy: {acc:.4f} ({correct}/{total}) | {total_time:.0f}s")
    for fam, m in sorted(family_metrics.items(), key=lambda x: -x[1]["accuracy"]):
        log(f"  {fam:25s} {m['accuracy']:.4f} ({m['correct']}/{m['total']})")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_path = f"{RESULTS_DIR}/{label}_metrics_{ts}.json"
    preds_path = f"{RESULTS_DIR}/{label}_predictions_{ts}.csv"
    with open(metrics_path, "w") as f:
        json.dump({"global": {"accuracy": acc, "correct": correct, "total": total},
                    "by_family": family_metrics,
                    "config": {"model": label, "lora_path": lora_path,
                               "num_examples": total, "total_time_seconds": total_time}}, f, indent=2)
    with open(preds_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id","statement","relation","ground_truth",
                                           "prediction","correct","raw_output","image_url"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    del model; torch.cuda.empty_cache(); import gc; gc.collect()
    return metrics_path, preds_path


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PHASE 4: Comparison table + McNemar + commit
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def phase4_analysis(metrics_files, preds_files):
    log("=" * 60)
    log("PHASE 4: Analysis + Comparison + Commit")
    log("=" * 60)

    # Load all metrics
    all_metrics = {}
    for name, path in metrics_files.items():
        with open(path) as f:
            all_metrics[name] = json.load(f)

    # Load 2B baseline
    with open("results/smolvlm2_metrics_2195_20260808_214536.json") as f:
        all_metrics["2B_baseline"] = json.load(f)
    with open("results/general_lora_metrics_20260809_054915.json") as f:
        all_metrics["2B_general_lora"] = json.load(f)
    with open("results/targeted_lora_metrics_20260809_061231.json") as f:
        all_metrics["2B_targeted_lora"] = json.load(f)

    # Build comparison table
    conditions = ["2B_baseline", "2B_general_lora", "2B_targeted_lora",
                   "7B_zeroshot", "7B_general_lora", "7B_targeted_lora"]
    display_names = ["2B Zero-shot", "2B General LoRA", "2B Targeted LoRA",
                     "7B Zero-shot", "7B General LoRA", "7B Targeted LoRA"]
    families = ["orientation", "depth", "horizontal", "vertical", "containment",
                "proximity", "topology_contact", "compositional"]

    log("\n" + "=" * 100)
    log("FULL COMPARISON TABLE")
    log("=" * 100)
    header = f"{'Condition':25s} {'Overall':>8s}"
    for fam in families:
        header += f" {fam[:8]:>9s}"
    log(header)
    log("-" * 100)

    for cond, dname in zip(conditions, display_names):
        m = all_metrics.get(cond, {})
        g = m.get("global", {})
        bf = m.get("by_family", {})
        row = f"{dname:25s} {g.get('accuracy', 0):>7.2%}"
        for fam in families:
            fam_acc = bf.get(fam, {}).get("accuracy", 0)
            row += f" {fam_acc:>8.2%}"
        log(row)

    # McNemar tests: 7B baseline vs 7B LoRA
    log("\n" + "=" * 80)
    log("MCNEMAR TESTS: 7B Zero-shot vs 7B LoRA")
    log("=" * 80)

    for label, preds_path in preds_files.items():
        with open(preds_path) as f:
            cond_preds = list(csv.DictReader(f))
        with open(preds_files["7B_zeroshot"]) as f:
            zs_preds = list(csv.DictReader(f))

        # Only compare if not the same file
        if preds_path == preds_files["7B_zeroshot"]:
            continue

        b_fixed = sum(1 for b, c in zip(zs_preds, cond_preds) if b["correct"] != "True" and c["correct"] == "True")
        c_broken = sum(1 for b, c in zip(zs_preds, cond_preds) if b["correct"] == "True" and c["correct"] != "True")
        stat, p = mcnemar(b_fixed, c_broken)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        log(f"\n7B Zero-shot vs {label}:")
        log(f"  Fixed: {b_fixed}, Broken: {c_broken}, Net: {b_fixed-c_broken:+d}")
        log(f"  McNemar chi2: {stat:.2f}, p = {p:.6f} {sig}")

        # Weak families pooled
        weak = set(RELATION_FAMILIES['orientation'] + RELATION_FAMILIES['depth'] + RELATION_FAMILIES['horizontal'])
        weak_b = [(b, c) for b, c in zip(zs_preds, cond_preds) if get_family(b["relation"]) in ("orientation", "depth", "horizontal")]
        wb = sum(1 for b, c in weak_b if b["correct"] != "True" and c["correct"] == "True")
        wc = sum(1 for b, c in weak_b if b["correct"] == "True" and c["correct"] != "True")
        stat2, p2 = mcnemar(wb, wc)
        sig2 = "***" if p2 < 0.001 else "**" if p2 < 0.01 else "*" if p2 < 0.05 else "ns"
        log(f"  Weak families (n={len(weak_b)}): fixed={wb}, broken={wc}, net={wb-wc:+d}, p={p2:.4f} {sig2}")

    # Commit
    log("\n" + "=" * 60)
    log("COMMITTING TO GITHUB")
    log("=" * 60)
    run("git add results/ checkpoints/ data/manifests/ scripts/ src/")
    run('git commit -m "7B VLM experiments: Qwen2-VL-7B zero-shot + general LoRA + targeted LoRA"')
    run("git push origin master")
    log("DONE - all results committed and pushed")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
if __name__ == "__main__":
    try:
        log("STARTING FULL 7B PIPELINE")
        log(f"Time: {datetime.now().isoformat()}")

        # Phase 1
        zs_metrics, zs_preds = phase1_zeroshot()

        # Phase 2
        gen_dir, tgt_dir = phase2_lora_training()

        # Phase 3
        gen_metrics, gen_preds = phase3_evaluate_lora(gen_dir, "7B_general_lora")
        tgt_metrics, tgt_preds = phase3_evaluate_lora(tgt_dir, "7B_targeted_lora")

        # Phase 4
        metrics_files = {
            "7B_zeroshot": zs_metrics,
            "7B_general_lora": gen_metrics,
            "7B_targeted_lora": tgt_metrics,
        }
        preds_files = {
            "7B_zeroshot": zs_preds,
            "7B_general_lora": gen_preds,
            "7B_targeted_lora": tgt_preds,
        }
        phase4_analysis(metrics_files, preds_files)

        log("\n" + "=" * 60)
        log("ALL PHASES COMPLETE")
        log("=" * 60)

    except Exception as e:
        log(f"FATAL ERROR: {e}")
        traceback.print_exc()
        log(traceback.format_exc())
