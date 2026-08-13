#!/usr/bin/env python3
"""Qwen3-VL-8B post-confirmatory extension (Paper-2 exploratory validation).

STATUS: post-confirmatory modern-backbone external validation, motivated by
reviewer/relevance concerns (2026-08-13, orchestrator guidance). NOT part of
the preregistered confirmatory comparisons (those are Qwen2-VL-7B, HardNeg,
SmolVLM2 on research/spatial-grounding-audit). Do not retrofit as
preregistered.

Purpose: does the primary adaptation decomposition (ΔA accuracy, ΔG
correct-image dependence, visual-response under global reflection) still
appear on a contemporary VLM?

  Qwen3-VL-8B zero-shot -> General VSR LoRA (same recipe as seed-0 7B)
  eval: normal, shuffle (frozen permutation), hflip_flip, hflip_invariant
  optional: relcomp (--with-relcomp)

Contract mirrors the frozen Tier-A/C pipelines:
  * prompt: config.PROMPT_TEMPLATE; greedy, max_new_tokens=5
  * images: md5(url).jpg cache, uniform 392px cap, identical preprocessing
  * shuffle: frozen mapping (results/grounding/protocol/shuffle_mapping.json)
  * hflip:   frozen Tier-C path -- visual.build_transform() rows from
             visual_eligible_ids.json, image = flip_image(preprocess(cached))
  * parser:  src/evaluation/parser.parse_true_false

Deliberate deviations, all documented:
  * model class Qwen3VLForConditionalGeneration (AutoProcessor same API)
  * standalone output layout:
      results/grounding/predictions/q3vl_<tag>/{zero_shot,general_lora}.jsonl
      results/grounding/analysis/q3vl_<tag>_summary.json
  * hflip is GLOBAL horizontal reflection, NOT VisualFLIP's minimal local
    edit protocol. Pair metrics are reported as "collapse-style paired
    answer-update metrics following VisualFLIP (Zhu et al. 2026)", with the
    intervention difference stated explicitly.

Usage:
  python scripts/grounding/run_qwen3vl_extension.py --tag ext_a [--with-relcomp] [--skip-train]
"""

import argparse
import json
import sys
from pathlib import Path

import torch
from PIL import Image

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from src.evaluation.parser import parse_true_false
from src.grounding import config, visual
from src.grounding.eligibility import load_ids_payload
from src.grounding.images import (ensure_cached, load_cached_image,
                                  preprocess_for_vlm)
from src.grounding.shuffle import load_shuffle_mapping

try:
    from transformers import Qwen3VLForConditionalGeneration
    _MODEL_CLS = Qwen3VLForConditionalGeneration
except Exception:
    from transformers import AutoModelForImageTextToText
    _MODEL_CLS = AutoModelForImageTextToText
from transformers import AutoProcessor

MODEL = "Qwen/Qwen3-VL-8B-Instruct"


# ---------------------------------------------------------------- training
def train_general_lora(output_dir: str):
    """General VSR LoRA on Qwen3-VL-8B, mirroring the seed-0 7B recipe
    (run_7b_pipeline PHASE 2): manifest general_train.jsonl, split seed=42,
    epochs=2, lr=1e-4, r=8/alpha=16/dropout=0.05, bf16, eager, grad
    checkpointing. Documented deviation: model class swapped for the
    exploratory extension."""
    from transformers import get_linear_schedule_with_warmup
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset
    from torch.utils.data import DataLoader

    MANIFEST = "data/manifests/general_train.jsonl"
    seed = 42
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    import numpy as np; np.random.seed(seed)

    with open(MANIFEST) as f:
        examples = [json.loads(l) for l in f]

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
            prompt = config.PROMPT_TEMPLATE.format(statement=ex["statement"])
            answer = "True" if ex["label"] else "False"
            messages = [{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": prompt}
            ]}]
            pin = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
            prompt_ids = pin["input_ids"].squeeze(0)
            answer_ids = torch.tensor(
                true_tokens if ex["label"] else false_tokens, dtype=prompt_ids.dtype)
            full_ids = torch.cat([prompt_ids, answer_ids])[:max_length]
            labels = torch.full_like(full_ids, -100)
            labels[prompt_ids.shape[0]:full_ids.shape[0]] = \
                full_ids[prompt_ids.shape[0]:full_ids.shape[0]]
            processed.append({
                "input_ids": full_ids,
                "labels": labels,
                "pixel_values": pin.get("pixel_values", None),
                "image_grid_thw": pin.get("image_grid_thw", None),
            })
        if not processed:
            return None
        max_len = max(p["input_ids"].shape[0] for p in processed)
        out = {"input_ids": [], "labels": [], "pixel_values": [],
               "image_grid_thw": []}
        for p in processed:
            ids = p["input_ids"][:max_len]
            labels = p["labels"][:max_len]
            pad = max_len - ids.shape[0]
            if pad:
                ids = torch.cat([ids, torch.zeros(pad, dtype=ids.dtype)])
                labels = torch.cat([labels, torch.full((pad,), -100, dtype=labels.dtype)])
            out["input_ids"].append(ids)
            out["labels"].append(labels)
            if p["pixel_values"] is not None:
                pv = p["pixel_values"]
                pv = pv.squeeze(0) if pv.dim() > 2 else pv
                out["pixel_values"].append(pv)
            if p["image_grid_thw"] is not None:
                out["image_grid_thw"].append(p["image_grid_thw"].squeeze(0))
        batch = {}
        for k, v in out.items():
            if v:
                batch[k] = torch.stack(v)
        return batch or None

    processor = AutoProcessor.from_pretrained(MODEL)
    model = _MODEL_CLS.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    lora = LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
                      lora_dropout=0.05,
                      target_modules=["q_proj", "v_proj", "k_proj", "o_proj"])
    model = get_peft_model(model, lora)
    model.train()

    ds = Dataset.from_list(examples)
    split = ds.train_test_split(test_size=0.05, seed=42)
    loader = DataLoader(split["train"], batch_size=1, shuffle=True,
                        collate_fn=lambda b: collate_batch(processor, b),
                        num_workers=0)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    total = len(loader) * 2
    sched = get_linear_schedule_with_warmup(opt, total // 10, total)
    gstep = 0
    for epoch in range(2):
        for batch in loader:
            if batch is None:
                continue
            batch = {k: v.to("cuda") for k, v in batch.items()}
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(**batch)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            gstep += 1
            if gstep % 100 == 0:
                print(f"  Step {gstep}/{total} | Loss: {out.loss.item():.4f}", flush=True)
    final = Path(output_dir) / "final"
    final.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(final)
    processor.save_pretrained(final)
    log = {"model": MODEL, "epochs": 2, "lr": 1e-4, "lora_rank": 8,
           "lora_alpha": 16, "total_steps": total, "split_seed": 42,
           "device": torch.cuda.get_device_name(0),
           "status": "post-confirmatory exploratory extension"}
    with open(Path(output_dir) / "training_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"Saved: {final}", flush=True)


# ------------------------------------------------------------- evaluation
def predict(model, processor, image, statement):
    if image is None:
        return None
    prompt = config.PROMPT_TEMPLATE.format(statement=statement)
    messages = [{"role": "user", "content": [
        {"type": "image", "image": image}, {"type": "text", "text": prompt}
    ]}]
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True,
        return_dict=True, return_tensors="pt")
    inputs = {k: v.to("cuda") for k, v in inputs.items()}
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.bfloat16):
        ids = model.generate(**inputs, max_new_tokens=config.MAX_NEW_TOKENS,
                             do_sample=config.DO_SAMPLE)
    return processor.decode(ids[0][inputs["input_ids"].shape[1]:],
                            skip_special_tokens=True).strip()


def run_rows(model, processor, rows, out_path):
    """rows: list of dicts with id, statement, label, image(PIL), condition,
    expected_label (for hflip) / behavior."""
    results = []
    for r in rows:
        raw = predict(model, processor, r["image"], r["statement"])
        parsed = parse_true_false(raw) if raw else None
        correct = (parsed is not None) and (bool(parsed) == bool(r["label"]))
        results.append({
            "example_id": r["id"],
            "condition": r["condition"],
            "statement": r["statement"],
            "ground_truth": bool(r["label"]),
            "expected_transformed_label": r.get("expected_label"),
            "expected_prediction_behavior": r.get("behavior"),
            "prediction": parsed,
            "correct": correct,
            "raw_output": raw,
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for x in results:
            f.write(json.dumps(x) + "\n")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="ext_a")
    ap.add_argument("--with-relcomp", action="store_true")
    ap.add_argument("--skip-train", action="store_true",
                    help="use existing adapter checkpoints/q3vl_general_lora")
    args = ap.parse_args()

    adapter = REPO / "checkpoints" / "q3vl_general_lora"
    if not args.skip_train:
        train_general_lora(str(adapter))

    processor = AutoProcessor.from_pretrained(MODEL)

    # ---- build condition rows -------------------------------------------
    payload = load_ids_payload()
    records = [r for r in payload["examples"] if r["image_available"]]
    records_by_id = {r["example_id"]: r for r in records}
    needed = {r["image_link"] for r in records}
    ensure_cached(sorted(needed))
    shuffle_doc = load_shuffle_mapping()
    mapping = shuffle_doc.get("mapping", {})
    link_lookup = {r["example_id"]: r["image_link"] for r in records}

    rows = []
    for rec in records:
        eid = rec["example_id"]
        img = load_cached_image(rec["image_link"])
        img = preprocess_for_vlm(img) if img is not None else None
        # normal
        rows.append({"id": eid, "statement": rec["statement"],
                     "label": rec["label"], "image": img, "condition": "normal"})
        # shuffle (frozen derangement)
        if eid in mapping:
            repl = link_lookup.get(mapping[eid])
            s_img = load_cached_image(repl) if repl else None
            s_img = preprocess_for_vlm(s_img) if s_img is not None else None
            rows.append({"id": eid, "statement": rec["statement"],
                         "label": rec["label"], "image": s_img,
                         "condition": "shuffle"})

    # hflip (frozen Tier-C rows + reflection)
    if not config.VISUAL_ELIGIBLE_FILE.exists():
        raise SystemExit(f"missing frozen artifact {config.VISUAL_ELIGIBLE_FILE}")
    eligible_doc = json.load(open(config.VISUAL_ELIGIBLE_FILE, encoding="utf-8"))
    for t in visual.TRANSFORMS:
        doc_rows = eligible_doc["transforms"][t]["entries"]
        for rec in records:
            eid = rec["example_id"]
            if eid not in doc_rows:
                continue
            tr = visual.build_transform(rec, t)
            if tr is None:
                continue
            img = load_cached_image(rec["image_link"])
            img = visual.flip_image(preprocess_for_vlm(img)) if img is not None else None
            rows.append({"id": eid, "statement": tr["statement"],
                         "label": tr["expected_transformed_label"],
                         "expected_label": tr["expected_transformed_label"],
                         "behavior": tr["expected_prediction_behavior"],
                         "image": img, "condition": t})

    # optional relcomp (frozen Tier-B semantic condition: language changes)
    if args.with_relcomp:
        if not config.SEMANTIC_ELIGIBLE_FILE.exists():
            raise SystemExit(f"missing frozen artifact {config.SEMANTIC_ELIGIBLE_FILE}")
        from src.grounding.semantic import audit_parser, build_transform as sem_build
        from src.grounding import semantic
        audit = audit_parser(records)
        recs = [{**r, **audit.get(r["example_id"], {})} for r in records]
        n_comp = 0
        for rec in recs:
            row = sem_build(rec, "relcomp")
            if row is None:
                continue
            img = load_cached_image(rec["image_link"])
            img = preprocess_for_vlm(img) if img is not None else None
            rows.append({"id": rec["example_id"], "statement": row["statement"],
                         "label": row["expected_transformed_label"],
                         "expected_label": row["expected_transformed_label"],
                         "behavior": row["expected_prediction_behavior"],
                         "image": img, "condition": "relcomp"})
            n_comp += 1
        print(f"relcomp rows: {n_comp}")

    print(f"total eval rows: {len(rows)}")

    out_dir = REPO / "results" / "grounding" / "predictions" / f"q3vl_{args.tag}"

    # ---- zero-shot ------------------------------------------------------
    model = _MODEL_CLS.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.eval()
    print("zero-shot predictions...", flush=True)
    run_rows(model, processor, rows, out_dir / "zero_shot.jsonl")
    del model; torch.cuda.empty_cache()

    # ---- tuned -----------------------------------------------------------
    from peft import PeftModel
    model = _MODEL_CLS.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model = PeftModel.from_pretrained(model, adapter / "final")
    model.eval()
    print("general_lora predictions...", flush=True)
    run_rows(model, processor, rows, out_dir / "general_lora.jsonl")

    # ---- summary (local aggregator: per-condition accuracy + pair metrics)
    from collections import defaultdict
    summary = {"tag": args.tag, "model": MODEL, "conditions": {}}
    for ckpt_file in ("zero_shot", "general_lora"):
        path = out_dir / f"{ckpt_file}.jsonl"
        by_cond = defaultdict(list)
        with open(path) as f:
            for line in f:
                x = json.loads(line)
                by_cond[x["condition"]].append(x)
        cond_stats = {}
        for cond, items in by_cond.items():
            n = len(items)
            acc = sum(1 for it in items if it["correct"]) / n if n else 0.0
            cond_stats[cond] = {"n": n, "accuracy": round(acc, 4)}
        # hflip pair metrics (collapse-style, following VisualFLIP naming)
        for pair_cond, law in (("hflip_flip", "flip_expected"),
                               ("hflip_invariant", "expected_invariant")):
            items = by_cond.get(pair_cond, [])
            if items:
                both = sum(1 for it in items if it["correct"])
                flip_rate = both / len(items) if items else 0.0
                cond_stats[pair_cond]["both_correct_rate"] = round(flip_rate, 4)
        summary["conditions"][ckpt_file] = cond_stats
        summary["conditions"][ckpt_file]["n_rows"] = len(rows)
    # ΔG (shuffle gap), ΔA, and hflip flip-rate deltas
    zs, gl = summary["conditions"]["zero_shot"], summary["conditions"]["general_lora"]
    summary["deltas"] = {
        "dA_normal": round(gl["normal"]["accuracy"] - zs["normal"]["accuracy"], 4),
        "dG_shuffle_gap": round(
            (gl["normal"]["accuracy"] - gl["shuffle"]["accuracy"])
            - (zs["normal"]["accuracy"] - zs["shuffle"]["accuracy"]), 4),
        "dhflip_flip_both_correct": round(
            gl["hflip_flip"].get("both_correct_rate", 0)
            - zs["hflip_flip"].get("both_correct_rate", 0), 4),
    }
    ana_dir = REPO / "results" / "grounding" / "analysis"
    ana_dir.mkdir(parents=True, exist_ok=True)
    with open(ana_dir / f"q3vl_{args.tag}_summary.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Done: {out_dir}")


if __name__ == "__main__":
    main()
