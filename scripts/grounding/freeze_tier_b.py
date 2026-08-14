#!/usr/bin/env python3
"""Freeze Tier-B semantic artifacts BEFORE any Tier-B prediction run.

Writes (committed pre-result, never regenerated after results without a
decision-log entry):

  results/grounding/protocol/semantic_transform_validity.csv
    relation x transform -> status (strict_included / soft_excluded /
    unsafe_excluded / not_in_scope), expected-truth behavior, reason,
    eligible/excluded counts.

  results/grounding/protocol/semantic_eligible_ids.json
    eligible example IDs per transform with subject/object, original label,
    expected transformed label, expected law, and the transformed statement;
    plus the full parser-audit statistics (study plan section 18).

Also prints a manual spot-check sample of transformed statements for review.

Usage:
  python scripts/grounding/freeze_tier_b.py            # refuse overwrite
  python scripts/grounding/freeze_tier_b.py --force    # only with decision log
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config, semantic
from src.grounding.eligibility import load_ids_payload


def print_parser_audit(stats: dict) -> None:
    print("Parser audit (study plan section 18):")
    for k, v in stats.items():
        print(f"  {k}: {v}")


def print_spot_checks(records: list, n: int = 12) -> None:
    rng = random.Random(config.SHUFFLE_SEED)
    for transform in semantic.TRANSFORMS:
        eligible = semantic.eligible_rows(records, transform)
        print(f"\n-- {transform} ({len(eligible)} eligible) spot checks --")
        for row in rng.sample(eligible, min(n, len(eligible))):
            print(f"  {row['example_id']} [{row['relation']}]")
            print(f"    orig   : {row['original_statement']}")
            print(f"    trans  : {row['statement']}")
            print(f"    expected: {row['expected_transformed_label']} "
                  f"({row['expected_prediction_behavior']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--spot-check-n", type=int, default=12)
    args = ap.parse_args()

    payload = load_ids_payload()
    records = [r for r in payload["examples"] if r["image_available"]]
    print(f"eligible records: {len(records)}")

    out = semantic.write_freeze_files(records, force=args.force)
    print("wrote:")
    for k, v in out.items():
        print(f"  {k}: {v}")

    print_parser_audit(semantic.audit_parser(records))
    print_spot_checks(records, args.spot_check_n)


if __name__ == "__main__":
    main()