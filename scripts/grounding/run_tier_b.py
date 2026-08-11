#!/usr/bin/env python3
"""Tier-B runner: semantic-transform predictions for checkpoint x transform
(semantic axis S; pixels fixed, language changes).

Usage:
  python scripts/grounding/run_tier_b.py --tag tierb_smoke10 --limit 10
  python scripts/grounding/run_tier_b.py --tag tierb_pilot200 --limit 200
  python scripts/grounding/run_tier_b.py --tag tierb_full

Options:
  --checkpoints zero_shot,general_lora,hardneg_lora  (default: all three)
  --transforms relcomp,sorev,continv                 (default: all three)
  --limit N        first N ELIGIBLE examples per transform (frozen order)

The images are identical to the Tier-A normal condition; only the statement
changes. Eligibility per transform is the frozen semantic_eligible_ids.json
artifact; the runner refuses to start if that freeze file is missing.

Prediction rows carry expected_transformed_label + expected_prediction_behavior
(study plan section 19 schema) and are suitable for paired example-level
statistics identical to Tier A.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.parser import parse_true_false
from src.grounding import config, semantic
from src.grounding.eligibility import load_ids_payload
from src.grounding.hashing import (adapter_hashes, env_snapshot, git_branch,
                                   git_commit, record_private_hashes,
                                   utc_now_iso, write_json)
from src.grounding.images import ensure_cached, load_cached_image, preprocess_for_vlm
from src.grounding.predictions import PREDICTION_FIELDS, write_predictions
from src.grounding.qwen2vl import Qwen2VLClassifier


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default="tierb_run")
    p.add_argument("--checkpoints", default=",".join(config.CHECKPOINTS))
    p.add_argument("--transforms", default=",".join(semantic.TRANSFORMS))
    p.add_argument("--batch-size", type=int, default=config.DEFAULT_BATCH_SIZE)
    p.add_argument("--attn", choices=["eager", "sdpa"], default="eager")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def build_semantic_row(transform_row: dict, record: dict, parsed, raw_output: str,
                       checkpoint: dict, run_id: str, prompt_version: str,
                       parser_version: str, adapter_hash: str) -> dict:
    tr = transform_row
    correct = parsed is not None and bool(parsed) == bool(tr["expected_transformed_label"])
    return {
        "example_id": tr["example_id"],
        "paired_parent_id": tr["example_id"],
        "split": config.DATASET_SPLIT,
        "condition": tr["transform_name"],
        "intervention_axis": "semantic",
        "statement": tr["statement"],
        "original_statement": tr["original_statement"],
        "relation": tr["relation"],
        "relation_family": tr["family"],
        "subject": tr["subject"],
        "object": tr["object"],
        "ground_truth": bool(tr["label"]),
        "expected_transformed_label": bool(tr["expected_transformed_label"]),
        "expected_prediction_behavior": tr["expected_prediction_behavior"],
        "prediction": parsed,
        "correct": correct,
        "raw_output": raw_output,
        "model_id": checkpoint["model_id"],
        "model_revision": None,
        "model_condition": checkpoint["label"],
        "adapter_path": str(checkpoint["adapter_path"]) if checkpoint["adapter_path"] else "",
        "adapter_hash": adapter_hash,
        "training_seed": None,
        "prompt_version": prompt_version,
        "parser_version": parser_version,
        "image_id": record["image_link"],
        "source_image_id": record["image_link"],
        "replacement_image_id": None,
        "transformed_image_id": record["image_link"],
        "transform_name": tr["transform_name"],
        "transform_version": tr["transform_version"],
        "transform_metadata": json.dumps(tr["transform_metadata"], sort_keys=True),
        "shuffle_seed": None,
        "generation_settings": json.dumps({
            "do_sample": config.DO_SAMPLE,
            "max_new_tokens": config.MAX_NEW_TOKENS,
        }, sort_keys=True),
        "run_id": run_id,
        "git_commit": git_commit(),
        "protocol_version": "v0.1",
    }


def run_transform(classifier, rows, records_by_id, args, run_id, parser_version,
                  adapter_hash, checkpoint, out_csv, resume):
    if resume and out_csv.exists():
        print(f"  {rows[0]['transform_name']}: exists (resume skip)")
        return
    statements = [r["statement"] for r in rows]
    images = [preprocess_for_vlm(load_cached_image(records_by_id[r["example_id"]]["image_link"]))
              for r in rows]
    t0 = time.time()
    done = 0
    out = []
    for start in range(0, len(rows), args.batch_size):
        end = min(start + args.batch_size, len(rows))
        try:
            raw_texts = classifier.predict_batch_oom_safe(
                images[start:end], statements[start:end]
            )
        except torch.cuda.OutOfMemoryError:
            raw_texts = [classifier.predict_batch_oom_safe([i], [s])[0]
                         for i, s in zip(images[start:end], statements[start:end])]
        for j, raw in enumerate(raw_texts):
            idx = start + j
            parsed = parse_true_false(raw)
            rec = records_by_id[rows[idx]["example_id"]]
            out.append(build_semantic_row(
                transform_row=rows[idx], record=rec, parsed=parsed,
                raw_output=raw, checkpoint=checkpoint, run_id=run_id,
                prompt_version=config.prompt_hash(),
                parser_version=parser_version, adapter_hash=adapter_hash,
            ))
        done = end
        if done % (args.batch_size * 25) == 0 or done == len(rows):
            elapsed = time.time() - t0
            print(f"    [{done}/{len(rows)}] {done/elapsed:.2f} ex/s | {elapsed:.0f}s",
                  flush=True)
    sha = write_predictions(out_csv, out)
    print(f"    wrote {out_csv.relative_to(config.REPO_ROOT)} "
          f"({len(out)} rows, sha256={sha[:12]}...)")


def main():
    args = parse_args()
    run_id = f"tier_b_{args.tag}"
    out_dir = config.PREDICTIONS_DIR / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print(f"TIER-B RUN  id={run_id}")
    print(f"git: {git_branch()} @ {git_commit()}  protocol hash: {config.protocol_hash()}")
    print("=" * 70)

    # frozen Tier-B artifacts must exist
    if not config.SEMANTIC_ELIGIBLE_FILE.exists():
        raise SystemExit(
            f"missing frozen artifact {config.SEMANTIC_ELIGIBLE_FILE}; "
            "run scripts/grounding/freeze_tier_b.py first (pre-result)"
        )
    eligible_doc = json.load(open(config.SEMANTIC_ELIGIBLE_FILE, encoding="utf-8"))
    print(f"validity file: {config.SEMANTIC_VALIDITY_FILE} "
          f"(sha256 {config.sha256_file(config.SEMANTIC_VALIDITY_FILE)[:12]}...)")
    print(f"eligible file: {config.SEMANTIC_ELIGIBLE_FILE} "
          f"(sha256 {config.sha256_file(config.SEMANTIC_ELIGIBLE_FILE)[:12]}...)")

    payload = load_ids_payload()
    records = [r for r in payload["examples"] if r["image_available"]]
    records_by_id = {r["example_id"]: r for r in records}

    checkpoints = [c.strip() for c in args.checkpoints.split(",") if c.strip()]
    transforms = [t.strip() for t in args.transforms.split(",") if t.strip()]
    for c in checkpoints:
        if c not in config.CHECKPOINTS:
            raise SystemExit(f"unknown checkpoint {c!r}")
    for t in transforms:
        if t not in semantic.TRANSFORMS:
            raise SystemExit(f"unknown transform {t!r}")

    # per-transform eligible rows (frozen artifact is the ONLY source)
    semantic.audit_parser(records)
    rows_by_transform = {}
    for t in transforms:
        doc_rows = eligible_doc["transforms"][t]["entries"]
        rows = []
        for rec in records:
            if rec["example_id"] not in doc_rows:
                continue
            row = semantic.build_transform(rec, t)
            if row is not None:
                rows.append(row)
        if args.limit:
            rows = rows[: args.limit]
        rows_by_transform[t] = rows
        print(f"transform {t}: {len(rows)} rows"
              + (f" (limit {args.limit})" if args.limit else ""))

    # image guard: normal-condition images (identical to Tier A)
    needed = {rec["image_link"] for rec in records}
    ensure_cached(sorted(needed))
    print(f"image cache verified: {len(needed)} unique images present")

    for ckpt_name in checkpoints:
        ckpt = config.CHECKPOINTS[ckpt_name]
        print(f"\n## checkpoint: {ckpt_name} ({ckpt['label']}) "
              f"adapter={ckpt['adapter_path']}")
        private = record_private_hashes(f"{run_id}_{ckpt_name}", ckpt)
        adapter_hash = json.dumps(private["adapter_hashes"], sort_keys=True) \
            if private["adapter_hashes"] else ""
        classifier = Qwen2VLClassifier(
            model_id=ckpt["model_id"],
            adapter_path=ckpt["adapter_path"],
            attn_implementation=args.attn,
        )
        for t in transforms:
            rows = rows_by_transform[t]
            if not rows:
                print(f"  {t}: no eligible rows, skipping")
                continue
            out_csv = out_dir / f"{ckpt_name}_{t}.csv"
            print(f"  transform: {t}", flush=True)
            run_transform(classifier, rows, records_by_id, args, run_id,
                          config.parser_hash(), adapter_hash, ckpt, out_csv,
                          args.resume)
        del classifier

    meta = {
        "run_id": run_id,
        "tag": args.tag,
        "tier": "B",
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "protocol_hash": config.protocol_hash(),
        "prompt_hash": config.prompt_hash(),
        "parser_hash": config.parser_hash(),
        "ids_file": str(config.IDS_FILE.relative_to(config.REPO_ROOT)),
        "ids_file_sha256": payload.get("file_sha256"),
        "semantic_validity_file": str(config.SEMANTIC_VALIDITY_FILE.relative_to(config.REPO_ROOT)),
        "semantic_validity_sha256": config.sha256_file(config.SEMANTIC_VALIDITY_FILE),
        "semantic_eligible_file": str(config.SEMANTIC_ELIGIBLE_FILE.relative_to(config.REPO_ROOT)),
        "semantic_eligible_sha256": config.sha256_file(config.SEMANTIC_ELIGIBLE_FILE),
        "checkpoints": args.checkpoints,
        "transforms": args.transforms,
        "limit": args.limit,
        "batch_size": args.batch_size,
        "attn": args.attn,
        "generation": {"do_sample": config.DO_SAMPLE,
                       "max_new_tokens": config.MAX_NEW_TOKENS},
        "preprocessing": {"cap_long_side_px": config.MAX_LONG_SIDE,
                          "note": "identical to Tier-A normal condition"},
        "env": env_snapshot(),
        "started_at": utc_now_iso(),
    }
    meta_path = write_json(out_dir / "run_metadata.json", meta)
    print(f"\nmetadata: {meta_path}")
    print("DONE")


if __name__ == "__main__":
    main()