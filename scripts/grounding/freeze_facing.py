#!/usr/bin/env python3
"""Freeze the facing/facing-away D1 diagnostic artifacts BEFORE any run.

Writes (committed pre-result, never regenerated after results without a
decision-log entry):

  results/grounding/protocol/facing_transform_validity.csv
    all relations x facingcomp -> strict_included (facing/facing away from)
    or not_in_scope, with the Paper-1 construct note.

  results/grounding/protocol/facing_eligible_ids.json
    eligible example IDs with subject/object, original label, expected
    flipped label, transformed statement; plus the parser audit.

Decision log 2026-08-11 (protocol implementation correction): the Tier-B
relcomp table soft-excludes facing/facing-away, so this dedicated transform
measures the original Paper-1 D1 construct directly. Tier-B artifacts are
not modified.

Usage:
  python scripts/grounding/freeze_facing.py            # refuse overwrite
  python scripts/grounding/freeze_facing.py --force    # only with decision log
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config, semantic
from src.grounding.eligibility import load_ids_payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--spot-check-n", type=int, default=12)
    args = ap.parse_args()

    payload = load_ids_payload()
    records = [r for r in payload["examples"] if r["image_available"]]
    print(f"eligible records: {len(records)}")

    out = semantic.write_facing_freeze_files(records, force=args.force)
    print("wrote:")
    for k, v in out.items():
        print(f"  {k}: {v}")

    rng = random.Random(config.SHUFFLE_SEED)
    eligible = semantic.eligible_rows(records, semantic.FACING_TRANSFORM)
    print(f"\n-- facingcomp ({len(eligible)} eligible) spot checks --")
    for row in rng.sample(eligible, min(args.spot_check_n, len(eligible))):
        print(f"  {row['example_id']} [{row['relation']}]")
        print(f"    orig   : {row['original_statement']}")
        print(f"    trans  : {row['statement']}")
        print(f"    expected: {row['expected_transformed_label']} "
              f"({row['expected_prediction_behavior']})")


if __name__ == "__main__":
    main()