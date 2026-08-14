#!/usr/bin/env python3
"""Tier-A runner: predictions for checkpoint x condition (frozen protocol).

Usage:
  # smoke (10 examples, engineering):
  python scripts/grounding/run_tier_a.py --tag smoke10 --limit 10

  # pilot (~200 examples, engineering):
  python scripts/grounding/run_tier_a.py --tag pilot200 --limit 200

  # full confirmatory grid (2,195 examples):
  python scripts/grounding/run_tier_a.py --tag full

Options:
  --checkpoints zero_shot,general_lora,hardneg_lora   (default: all three)
  --conditions normal,shuffle,blank,text_only         (default: all four)
  --batch-size 8        (single-image safe batch; A6000 measured)
  --attn eager|sdpa     (default eager: matches all prior 7B runs)
  --quantize 4bit       (LOCAL ENGINEERING ONLY; documented in metadata)
  --limit N             (first N eligible IDs in frozen order)
  --tag NAME            (output subdir + run id)
  --resume              (skip already-completed run_id rows)

Frozen-artifact checks: IDs file, shuffle mapping, blank spec are loaded and
their hashes verified; any mismatch aborts the run. Private model/checkpoint
hashes are recorded under results/grounding/private/ (gitignored).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.parser import parse_true_false
from src.grounding import config
from src.grounding.eligibility import load_ids_payload, subset_records
from src.grounding.hashing import (adapter_hashes, env_snapshot, git_branch,
                                   git_commit, record_private_hashes,
                                   utc_now_iso, write_json)
from src.grounding.interventions import build_condition_inputs
from src.grounding.predictions import (PREDICTION_FIELDS, build_prediction_row,
                                       write_predictions)
from src.grounding.qwen2vl import Qwen2VLClassifier
from src.grounding.smolvlm2 import SmolVLM2Classifier

MODEL_FAMILY_CLASSIFIERS = {
    "qwen2vl": Qwen2VLClassifier,
    "smolvlm2": SmolVLM2Classifier,
}
from src.grounding.shuffle import load_shuffle_mapping


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default="run", help="run label (smoke10/pilot200/full)")
    p.add_argument("--checkpoints", default=",".join(config.CHECKPOINTS))
    p.add_argument("--conditions", default=",".join(config.CONDITIONS))
    p.add_argument("--model-family", choices=list(config.MODEL_FAMILIES),
                   default="qwen2vl")
    p.add_argument("--batch-size", type=int, default=config.DEFAULT_BATCH_SIZE)
    p.add_argument("--attn", choices=["eager", "sdpa"], default="eager")
    p.add_argument("--quantize", choices=["none", "4bit"], default="none")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def run_condition(classifier, records, condition, shuffle_doc, args,
                  run_id, parser_version, adapter_hash, checkpoint, link_lookup):
    inputs = build_condition_inputs(records, condition, shuffle_doc, link_lookup)
    rows = []
    images = [i["image"] for i in inputs]
    statements = [i["statement"] for i in inputs]

    t0 = time.time()
    done = 0
    for start in range(0, len(inputs), args.batch_size):
        end = min(start + args.batch_size, len(inputs))
        batch_inputs = inputs[start:end]
        batch_records = records[start:end]
        try:
            raw_texts = classifier.predict_batch_oom_safe(
                images[start:end], statements[start:end]
            )
        except torch.cuda.OutOfMemoryError:
            # last-resort: fall back to one-at-a-time (unlikely with ladder)
            raw_texts = [classifier.predict_batch_oom_safe([i["image"]], [i["statement"]])[0]
                         for i in batch_inputs]
        for j, raw in enumerate(raw_texts):
            row_in = batch_inputs[j]
            parsed = parse_true_false(raw)
            rows.append(build_prediction_row(
                record=batch_records[j], input_row=row_in, parsed=parsed,
                raw_output=raw, checkpoint=checkpoint, run_id=run_id,
                prompt_version=config.prompt_hash(),
                parser_version=parser_version,
                adapter_hash=adapter_hash,
            ))
        done = end
        if done % (args.batch_size * 25) == 0 or done == len(inputs):
            elapsed = time.time() - t0
            print(f"    [{done}/{len(inputs)}] {done/elapsed:.2f} ex/s | {elapsed:.0f}s",
                  flush=True)
    return rows


def main():
    args = parse_args()
    run_id = f"tier_a_{args.tag}"
    out_dir = config.PREDICTIONS_DIR / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print(f"TIER-A RUN  id={run_id}")
    print(f"git: {git_branch()} @ {git_commit()}  protocol hash: {config.protocol_hash()}")
    print("=" * 70)

    # frozen artifacts
    ids_payload = load_ids_payload()
    shuffle_doc = load_shuffle_mapping()
    print(f"eligible IDs: {ids_payload['count_total']} total, "
          f"{sum(1 for r in ids_payload['examples'] if r['image_available'])} eligible")

    checkpoints = [c.strip() for c in args.checkpoints.split(",") if c.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    registry = config.family_registry(args.model_family)
    for c in checkpoints:
        if c not in registry:
            raise SystemExit(f"unknown checkpoint {c!r}")
    for c in conditions:
        if c not in config.CONDITIONS:
            raise SystemExit(f"unknown condition {c!r}")

    records = subset_records(ids_payload, args.limit) if args.limit else \
        [r for r in ids_payload["examples"] if r["image_available"]]
    link_lookup = {r["example_id"]: r["image_link"]
                   for r in ids_payload["examples"] if r["image_available"]}
    print(f"evaluating {len(records)} examples per cell")

    # Hard guard: every required image must be in the cache BEFORE inference.
    # A missing image must never silently degrade to a text-only row.
    from src.grounding.images import ensure_cached
    mapping = shuffle_doc["mapping"]
    needed = {r["image_link"] for r in records}
    if "shuffle" in conditions:
        needed |= {link_lookup[mapping[r["example_id"]]] for r in records}
    ensure_cached(sorted(needed))
    print(f"image cache verified: {len(needed)} unique images present")

    for ckpt_name in checkpoints:
        ckpt = registry[ckpt_name]
        print(f"\n## checkpoint: {ckpt_name} ({ckpt['label']}) "
              f"adapter={ckpt['adapter_path']}")
        # private hashes (model/checkpoint/config) recorded once per checkpoint
        private = record_private_hashes(f"{run_id}_{ckpt_name}", ckpt)
        adapter_hash = json.dumps(private["adapter_hashes"], sort_keys=True) \
            if private["adapter_hashes"] else ""

        classifier = MODEL_FAMILY_CLASSIFIERS[args.model_family](
            model_id=ckpt["model_id"],
            adapter_path=ckpt["adapter_path"],
            attn_implementation=args.attn,
            quantize=None if args.quantize == "none" else args.quantize,
        )
        for condition in conditions:
            out_csv = out_dir / f"{ckpt_name}_{condition}.csv"
            if args.resume and out_csv.exists():
                print(f"  {condition}: exists (resume skip) -> {out_csv}")
                continue
            print(f"  condition: {condition}", flush=True)
            rows = run_condition(classifier, records, condition, shuffle_doc,
                                 args, run_id, config.parser_hash(),
                                 adapter_hash, ckpt, link_lookup)
            sha = write_predictions(out_csv, rows)
            print(f"    wrote {out_csv.relative_to(config.REPO_ROOT)} "
                  f"({len(rows)} rows, sha256={sha[:12]}...)")
        del classifier

    # run metadata
    meta = {
        "run_id": run_id,
        "tag": args.tag,
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "protocol_hash": config.protocol_hash(),
        "prompt_hash": config.prompt_hash(),
        "parser_hash": config.parser_hash(),
        "ids_file": str(config.IDS_FILE.relative_to(config.REPO_ROOT)),
        "ids_file_sha256": ids_payload.get("file_sha256"),
        "shuffle_mapping_sha256": shuffle_doc.get("file_sha256"),
        "checkpoints": args.checkpoints,
        "conditions": args.conditions,
        "model_family": args.model_family,
        "model_ids": {c: registry[c]["model_id"] for c in checkpoints},
        "limit": args.limit,
        "batch_size": args.batch_size,
        "attn": args.attn,
        "quantize": args.quantize,
        "generation": {"do_sample": config.DO_SAMPLE,
                       "max_new_tokens": config.MAX_NEW_TOKENS},
        "preprocessing": {"cap_long_side_px": config.MAX_LONG_SIDE,
                          "note": "uniform across conditions (TECHNIQUES.md §4)"},
        "env": env_snapshot(),
        "started_at": utc_now_iso(),
    }
    meta_path = write_json(out_dir / "run_metadata.json", meta)
    print(f"\nmetadata: {meta_path}")
    print("DONE")


if __name__ == "__main__":
    main()
