#!/usr/bin/env python3
"""
7B hard-negative orientation LoRA: train + evaluate + analyze + commit.

Control: 7B General LoRA (checkpoints/qwen2vl_7b_general_lora/final).
Treatment: 7B hard-negative LoRA trained on data/manifests/hardneg_train.jsonl
with the exact same config as the control (r=8, alpha=16, dropout=0.05,
q/k/v/o_proj, micro-batch 1, lr=1e-4, 2 epochs, warmup 10%, grad clip 1.0).

Runs in screen 'hn7b'. Logs: /tmp/hn7b_pipeline.log
"""
import os, sys, json, csv, time, hashlib, subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from math import sqrt, erfc
from PIL import Image

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

LOG = "/tmp/hn7b_pipeline.log"
RESULTS_DIR = "results"
CKPT_DIR = "checkpoints"
MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"
CONTROL_LORA = "checkpoints/qwen2vl_7b_general_lora/final"

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def run(cmd):
    log(f"  CMD: {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10800)
    if r.returncode != 0:
        log(f"  STDERR: {r.stderr[-800:]}")
    return r.stdout, r.returncode

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

def parse_tf(text):
    t = text.strip().lower()
    if "assistant:" in t:
        t = t.split("assistant:")[-1].strip()
    if t.startswith("true"):
        return True
    if t.startswith("false"):
        return False
    return None

def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 0.0, 1.0
    stat = (abs(b - c) - 1) ** 2 / n
    p = erfc(sqrt(stat / 2))
    return stat, p

def ci(n_correct, n_total, z=1.96):
    if n_total == 0:
        return 0.0, 0.0
    p = n_correct / n_total
    se = sqrt(p * (1 - p) / n_total)
    return max(0, p - z * se), min(1, p + z * se)

PROMPT_TEMPLATE = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'
TRAIN_PROMPT = PROMPT_TEMPLATE

def load_cached_image(url):
    h = hashlib.md5(url.encode()).hexdigest()
    p = Path("data/image_cache") / f"{h}.jpg"
    return Image.open(p).convert("RGB") if p.exists() else None

# ════════════════════════════════════════════════════════════════
# PHASE 1: Train hard-negative LoRA (same config as control)
# ════════════════════════════════════════════════════════════════
def phase1_train():
    log("=" * 60)
    log("PHASE 1: Train 7B hard-negative LoRA")
    log("=" * 60)

    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, get_linear_schedule_with_warmup
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset
    from torch.utils.data import DataLoader

    with open("data/manifests/hardneg_train.jsonl") as f:
        examples = [json.loads(l) for l in f]
    for e in examples:
        e["id"] = str(e["id"])
        e["is_hard_negative"] = bool(e.get("is_hard_negative", False))
        e["source_id"] = str(e.get("source_id", ""))
    log(f"Hard-negative manifest: {len(examples)} examples")
    hn = sum(1 for e in examples if e.get("is_hard_negative"))
    log(f"  hard negatives: {hn}")
    from collections import Counter
    log(f"  families: {dict(Counter(e['family'] for e in examples))}")

    def collate_batch(processor, batch, max_length=2048):
        true_tokens = processor.tokenizer.encode(" True", add_special_tokens=False)
        false_tokens = processor.tokenizer.encode(" False", add_special_tokens=False)
        processor.tokenizer.padding_side = "right"
        if processor.tokenizer.pad_token is None:
            processor.tokenizer.pad_token = processor.tokenizer.eos_token

        processed = []
        for ex in batch:
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
            if p["mm_token_type_ids"] is not None:
                batch_mm.append(p["mm_token_type_ids"])

        result = {"input_ids": torch.stack(batch_ids),
                  "attention_mask": torch.stack(batch_mask),
                  "labels": torch.stack(batch_labels)}
        if batch_pv:
            if batch_pv[0].dim() == 2:
                max_dim0 = max(pv.shape[0] for pv in batch_pv)
                hidden_dim = batch_pv[0].shape[1]
                padded = [pv if pv.shape[0] == max_dim0 else
                          torch.cat([pv, torch.zeros(max_dim0 - pv.shape[0], hidden_dim, dtype=pv.dtype)], dim=0)
                          for pv in batch_pv]
            else:
                max_patches = max(pv.shape[0] for pv in batch_pv)
                padded = [pv if pv.shape[0] == max_patches else
                          torch.cat([pv, torch.zeros(max_patches - pv.shape[0], *pv.shape[1:], dtype=pv.dtype)], dim=0)
                          for pv in batch_pv]
            result["pixel_values"] = torch.stack(padded)
        if batch_grid:
            result["image_grid_thw"] = torch.stack(batch_grid)
        if batch_mm:
            max_mm_len = max(m.shape[0] for m in batch_mm)
            padded_mm = [m if m.shape[0] == max_mm_len else
                         torch.cat([m, torch.zeros(max_mm_len - m.shape[0], dtype=m.dtype)])
                         for m in batch_mm]
            result["mm_token_type_ids"] = torch.stack(padded_mm)
        return result

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
    log(f"Model + LoRA VRAM: {torch.cuda.memory_allocated()/1e9:.1f}GB")

    dataset = Dataset.from_list(examples)
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split["train"]

    def collate_fn(batch):
        return collate_batch(processor, batch)

    loader = DataLoader(train_ds, batch_size=1, shuffle=True, collate_fn=collate_fn, num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    total_steps = len(loader) * 2
    scheduler = get_linear_schedule_with_warmup(optimizer, total_steps // 10, total_steps)
    log(f"Train: {len(train_ds)}, Steps: {total_steps}")

    output_dir = f"{CKPT_DIR}/qwen2vl_7b_hardneg_lora"
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
            if global_step % 50 == 0:
                elapsed = time.time() - t_start
                log(f"  Step {global_step}/{total_steps} | Loss: {out.loss.item():.4f} | {elapsed:.0f}s")
        log(f"Epoch {epoch+1}/2 done | Loss: {out.loss.item():.4f}")

    final_dir = os.path.join(output_dir, "final")
    os.makedirs(final_dir, exist_ok=True)
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    log(f"Saved: {final_dir}")
    log(f"Training complete: {time.time()-t_start:.0f}s")

    del model
    torch.cuda.empty_cache()
    import gc; gc.collect()
    return final_dir

# ════════════════════════════════════════════════════════════════
# PHASE 2: Evaluate hard-negative LoRA on full test set
# ════════════════════════════════════════════════════════════════
def phase2_eval(lora_path):
    log("=" * 60)
    log("PHASE 2: Evaluate hard-negative LoRA")
    log("=" * 60)

    import torch
    from PIL import Image
    from datasets import load_dataset
    from peft import PeftModel
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16,
        _attn_implementation="eager", low_cpu_mem_usage=True,
    ).to("cuda")
    model = PeftModel.from_pretrained(model, lora_path)
    model.eval()
    log(f"LoRA model loaded: {torch.cuda.memory_allocated()/1e9:.1f}GB")

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

    results = []
    t_start = time.time()
    batch_imgs, batch_stmts, batch_recs = [], [], []

    def flush():
        if not batch_imgs:
            return
        msgs = []
        for img, st in zip(batch_imgs, batch_stmts):
            p = PROMPT_TEMPLATE.format(statement=st)
            msgs.append([{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": p}
            ]}])
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        )
        inputs = {k: (v.to("cuda", dtype=torch.bfloat16) if v.dtype == torch.float32 else v.to("cuda"))
                  for k, v in inputs.items()}
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        texts = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        del inputs, out
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
        batch_imgs.append(img); batch_stmts.append(rec["statement"]); batch_recs.append(rec)
        if len(batch_imgs) >= 8:
            flush()
            if (i + 1) % 200 == 0:
                elapsed = time.time() - t_start
                log(f"  [{i+1}/{len(records)}] {(i+1)/elapsed:.1f} ex/s | {elapsed:.0f}s")
    flush()
    total_time = time.time() - t_start

    correct = sum(1 for r in results if r["correct"])
    acc = correct / len(results)
    family_metrics = {}
    for fam in RELATION_FAMILIES:
        fam_results = [r for r in results if get_family(r["relation"]) == fam]
        if not fam_results:
            continue
        fc = sum(1 for r in fam_results if r["correct"])
        ft = len(fam_results)
        lo, hi = ci(fc, ft)
        family_metrics[fam] = {"accuracy": fc/ft, "correct": fc, "total": ft, "ci_lower": lo, "ci_upper": hi}

    log(f"Accuracy: {acc:.4f} ({correct}/{len(results)}) | {total_time:.0f}s")
    for fam, m in sorted(family_metrics.items(), key=lambda x: -x[1]["accuracy"]):
        log(f"  {fam:25s} {m['accuracy']:.4f} ({m['correct']}/{m['total']})")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = "7B_hardneg_lora"
    metrics_path = f"{RESULTS_DIR}/{label}_metrics_{ts}.json"
    preds_path = f"{RESULTS_DIR}/{label}_predictions_{ts}.csv"
    with open(metrics_path, "w") as f:
        json.dump({"global": {"accuracy": acc, "correct": correct, "total": len(results)},
                    "by_family": family_metrics,
                    "config": {"model": label, "lora_path": lora_path,
                               "num_examples": len(results), "total_time_seconds": total_time}}, f, indent=2)
    with open(preds_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id","statement","relation","ground_truth",
                                           "prediction","correct","raw_output","image_url"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    log(f"Saved: {metrics_path}")
    log(f"Saved: {preds_path}")
    return metrics_path, preds_path

# ════════════════════════════════════════════════════════════════
# PHASE 3: Analysis + report + commit
# ════════════════════════════════════════════════════════════════
def phase3_analysis(metrics_path, preds_path):
    log("=" * 60)
    log("PHASE 3: Analysis vs 7B General LoRA control")
    log("=" * 60)

    import csv as _csv
    with open(preds_path) as f:
        hardneg = list(_csv.DictReader(f))
    with open("results/7B_general_lora_predictions_20260809_094930.csv") as f:
        gen = list(_csv.DictReader(f))
    with open("results/qwen2vl_7b_predictions_20260809_064919.csv") as f:
        z7 = list(_csv.DictReader(f))

    assert len(hardneg) == len(gen) == len(z7) == 2195

    def acc(rows, subset_ids=None):
        rows = rows if subset_ids is None else [r for r in rows if r["id"] in subset_ids]
        if not rows:
            return 0.0, 0, 0
        c = sum(1 for r in rows if r["correct"] == "True")
        return c / len(rows), c, len(rows)

    # Global McNemar: General LoRA (control) vs Hard-negative
    b = sum(1 for r, g, h in zip(z7, gen, hardneg)
            if g["correct"] == "False" and h["correct"] == "True")
    c = sum(1 for r, g, h in zip(z7, gen, hardneg)
            if g["correct"] == "True" and h["correct"] == "False")
    chi2, p = mcnemar(b, c)
    log(f"McNemar GenLoRA vs HardNeg (global): fixed={b}, broken={c}, net={b-c}, chi2={chi2:.2f}, p={p:.6f}")

    weak_ids = set(r["id"] for r in z7 if get_family(r["relation"]) in ("orientation", "depth", "horizontal"))
    b_w = sum(1 for r in z7 if r["id"] in weak_ids
              for g, h in [(gen[int(r['id'])], hardneg[int(r['id'])])]
              if g["correct"] == "False" and h["correct"] == "True")
    c_w = sum(1 for r in z7 if r["id"] in weak_ids
              for g, h in [(gen[int(r['id'])], hardneg[int(r['id'])])]
              if g["correct"] == "True" and h["correct"] == "False")
    chi2w, pw = mcnemar(b_w, c_w)
    log(f"McNemar weak families pooled: fixed={b_w}, broken={c_w}, net={b_w-c_w}, chi2={chi2w:.2f}, p={pw:.6f}")

    # Per-relation orientation table across 4 conditions
    orient_rels = ["facing", "facing away from", "parallel to", "perpendicular to"]
    per_rel = {}
    for rel in orient_rels:
        ids = [r["id"] for r in z7 if r["relation"] == rel]
        per_rel[rel] = {
            "n": len(ids),
            "7B_zero": acc(z7, set(ids))[0],
            "7B_gen_lora": acc(gen, set(ids))[0],
            "7B_hardneg": acc(hardneg, set(ids))[0],
        }
    log("Per-relation orientation:")
    for rel, m in per_rel.items():
        log(f"  {rel:20s} n={m['n']:3d}  7B_zero={m['7B_zero']:.3f}  7B_gen={m['7B_gen_lora']:.3f}  7B_hn={m['7B_hardneg']:.3f}")

    # Per-relation McNemar for orientation relations (Gen vs HN)
    per_rel_mcnemar = {}
    for rel in orient_rels:
        ids = [r["id"] for r in z7 if r["relation"] == rel]
        bb = sum(1 for rid in ids if gen[int(rid)]["correct"] == "False" and hardneg[int(rid)]["correct"] == "True")
        cc = sum(1 for rid in ids if gen[int(rid)]["correct"] == "True" and hardneg[int(rid)]["correct"] == "False")
        chi, pp = mcnemar(bb, cc)
        per_rel_mcnemar[rel] = {"fixed": bb, "broken": cc, "p": pp}
        log(f"  McNemar {rel}: fixed={bb}, broken={cc}, net={bb-cc}, p={pp:.4f}")

    # Persistent orientation failures: wrong in 7B_zero AND gen AND hardneg
    pers = [r for r in z7 if r["relation"] in orient_rels
            and z7[int(r["id"])]["correct"] == "False"
            and gen[int(r["id"])]["correct"] == "False"
            and hardneg[int(r["id"])]["correct"] == "False"]
    pers_prev = [r for r in z7 if r["relation"] in orient_rels
                 and z7[int(r["id"])]["correct"] == "False"
                 and gen[int(r["id"])]["correct"] == "False"]
    log(f"Persistent orientation failures: prev={len(pers_prev)}, still-failing-with-HN={len(pers)}")
    from collections import Counter
    log(f"  still-failing by relation: {dict(Counter(r['relation'] for r in pers))}")

    # Fixes on the 48 annotated set
    with open("results/orientation_persistent_annotations.csv") as f:
        ann = list(_csv.DictReader(f))
    ann_ids = {r["id"] for r in ann}
    fixed_by_hn = [r for r in pers_prev if hardneg[int(r["id"])]["correct"] == "True"]
    ann_fixed = [r for r in fixed_by_hn if r["id"] in ann_ids]
    log(f"Of previous persistent (48 annotated): fixed by HN = {len(ann_fixed)}/{len(pers_prev)}")

    # Family regression check
    log("Family accuracy: control vs hardneg")
    regressions = []
    for fam in RELATION_FAMILIES:
        ids = set(r["id"] for r in z7 if get_family(r["relation"]) == fam)
        a_gen = acc(gen, ids)[0]
        a_hn = acc(hardneg, ids)[0]
        delta = a_hn - a_gen
        flag = "REGRESS" if delta < -0.01 else ""
        if flag:
            regressions.append(fam)
        log(f"  {fam:20s} gen={a_gen:.4f} hn={a_hn:.4f} delta={delta:+.4f} {flag}")

    # ── Write report ──
    with open(metrics_path) as f:
        hn_metrics = json.load(f)
    with open("results/7B_general_lora_metrics_20260809_094930.json") as f:
        gen_metrics = json.load(f)
    with open("results/qwen2vl_7b_metrics_20260809_064919.json") as f:
        z7_metrics = json.load(f)

    report = f"""# Hard-Negative Orientation LoRA: Results

## Experiment
- **Control:** 7B General LoRA (general_train.jsonl, 2000 ex, r=8 α=16 lr=1e-4, 2 epochs)
- **Treatment:** 7B Hard-Negative LoRA (hardneg_train.jsonl, 2000 ex, identical config)
- **Only variable:** orientation block replaced by audited-clean originals + paired hard negatives
  (facing ↔ facing away from, parallel ↔ perpendicular)

## Overall
| Condition | Overall |
|-----------|---------|
| 7B Zero-shot | {z7_metrics['global']['accuracy']*100:.2f}% |
| 7B General LoRA | {gen_metrics['global']['accuracy']*100:.2f}% |
| 7B Hard-Negative LoRA | {hn_metrics['global']['accuracy']*100:.2f}% |

## McNemar: General LoRA vs Hard-Negative
- Global: fixed={b}, broken={c}, net={b-c:+d}, chi2={chi2:.2f}, p={p:.6f}
- Weak families pooled: fixed={b_w}, broken={c_w}, net={b_w-c_w:+d}, chi2={chi2w:.2f}, p={pw:.6f}

## Per-relation orientation accuracy
| Relation | N | 7B Zero | 7B Gen LoRA | 7B HardNeg | McNemar p (Gen vs HN) |
|----------|---|---------|-------------|------------|----------------------|
"""
    for rel in orient_rels:
        m = per_rel[rel]
        mm = per_rel_mcnemar[rel]
        report += f"| {rel} | {m['n']} | {m['7B_zero']*100:.1f}% | {m['7B_gen_lora']*100:.1f}% | {m['7B_hardneg']*100:.1f}% | p={mm['p']:.3f} |\n"

    report += f"""
## Persistent orientation failures
- Previous persistent (7B zero + Gen LoRA both wrong): {len(pers_prev)}
- Still failing with hard-negative LoRA: {len(pers)}
- Fixed by hard-negative LoRA: {len(pers_prev) - len(pers)}
- Of the 48 annotated cases: fixed {len(ann_fixed)}

## Family regression check
| Family | Gen LoRA | HardNeg | Delta |
|--------|----------|---------|-------|
"""
    for fam in RELATION_FAMILIES:
        ids = set(r["id"] for r in z7 if get_family(r["relation"]) == fam)
        a_gen = acc(gen, ids)[0]
        a_hn = acc(hardneg, ids)[0]
        report += f"| {fam} | {a_gen*100:.1f}% | {a_hn*100:.1f}% | {(a_hn-a_gen)*100:+.1f}% |\n"

    report += f"""
## Conclusion
{'Hard-negative LoRA improved orientation relative to General LoRA control.' if (sum(1 for rel in orient_rels if per_rel[rel]['7B_hardneg'] > per_rel[rel]['7B_gen_lora']) >= 2) else 'Hard-negative LoRA did not clearly improve orientation relative to the control.'}

Orientation ceiling evidence: {sum(1 for rel in orient_rels if per_rel[rel]['7B_hardneg'] > per_rel[rel]['7B_zero'])} of 4 relations improved over zero-shot.
"""
    report_path = "results/hardneg_analysis_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    log(f"Saved report: {report_path}")

    # ── Commit ──
    log("COMMITTING TO GITHUB")
    run(f"git add data/manifests/hardneg_train.jsonl results/{os.path.basename(metrics_path)} "
        f"results/{os.path.basename(preds_path)} results/hardneg_analysis_report.md "
        f"results/orientation_train_audit.csv scripts/audit_orientation_train.py "
        f"scripts/audit_orientation_train_model.py scripts/build_hardneg_manifest.py "
        f"scripts/run_7b_hardneg_pipeline.py checkpoints/qwen2vl_7b_hardneg_lora")
    run('git commit -m "Hard-negative orientation LoRA ablation: 7B control vs hard-negative run"')
    out, rc = run("git push origin master")
    log("DONE - committed and pushed")

if __name__ == "__main__":
    log(f"Time: {datetime.now().isoformat()}")
    log("=" * 60)
    log("HARD-NEGATIVE ORIENTATION LoRA PIPELINE")
    log("=" * 60)
    final_dir = phase1_train()
    m_path, p_path = phase2_eval(final_dir)
    phase3_analysis(m_path, p_path)
    log("ALL PHASES COMPLETE")
