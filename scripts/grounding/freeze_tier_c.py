#!/usr/bin/env python3
"""Freeze Tier-C1 visual artifacts BEFORE any Tier-C prediction run.

Writes (committed pre-result, never regenerated after results without a
decision-log entry):

  results/grounding/protocol/visual_transform_validity.csv
    relation x transform -> status (strict_included / not_in_scope),
    expected-truth behavior (flip_expected / expected_invariant),
    reason, eligible/excluded counts.

  results/grounding/protocol/visual_eligible_ids.json
    eligible example IDs per transform with relation, original label,
    expected transformed label, and expected prediction behavior.

  results/grounding/protocol/visual_spot/
    manual spot-check images: original + horizontally reflected pairs for a
    sample of eligible examples (reviewed by the researcher pre-result).

Per the freeze protocol section 6: Tier-C1 is confirmatory only for
mirrored-axis left/right relations (flip_expected) plus separated
guaranteed-invariant vertical/depth relations (expected_invariant, reported
separately, never merged with the flip rate).

Usage:
  python scripts/grounding/freeze_tier_c.py            # refuse overwrite
  python scripts/grounding/freeze_tier_c.py --force    # only with decision log
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config, visual
from src.grounding.eligibility import load_ids_payload
from src.grounding.images import load_cached_image, preprocess_for_vlm


def write_spot_checks(records: list, n: int = 3) -> list:
    rng = random.Random(config.SHUFFLE_SEED)
    records_by_id = {r["example_id"]: r for r in records}
    config.VISUAL_SPOT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for transform in visual.TRANSFORMS:
        rows = visual.eligible_rows(records, transform)
        for row in rng.sample(rows, min(n, len(rows))):
            img = preprocess_for_vlm(
                load_cached_image(records_by_id[row["example_id"]]["image_link"]))
            flip = visual.flip_image(img)
            img.save(config.VISUAL_SPOT_DIR / f"{row['example_id']}_orig.png")
            flip.save(config.VISUAL_SPOT_DIR / f"{row['example_id']}_flip.png")
            written.append(row["example_id"])
    return sorted(set(written))


def print_spot_checks(records: list, n: int = 12) -> None:
    rng = random.Random(config.SHUFFLE_SEED)
    for transform in visual.TRANSFORMS:
        rows = visual.eligible_rows(records, transform)
        print(f"\n-- {transform} ({len(rows)} eligible) statement spot checks --")
        for row in rng.sample(rows, min(n, len(rows))):
            print(f"  {row['example_id']} [{row['relation']}] "
                  f"label={int(row['label'])}")
            print(f"    statement : {row['statement']}")
            print(f"    expected  : {int(row['expected_transformed_label'])} "
                  f"({row['expected_prediction_behavior']}), image hflipped")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--spot-check-n", type=int, default=12)
    args = ap.parse_args()

    payload = load_ids_payload()
    records = [r for r in payload["examples"] if r["image_available"]]
    print(f"eligible records: {len(records)}")

    out = visual.write_freeze_files(records, force=args.force)
    print("wrote:")
    for k, v in out.items():
        print(f"  {k}: {v}")

    spot_ids = write_spot_checks(records, 3)
    print(f"spot-check images: {len(spot_ids)} pairs -> "
          f"{config.VISUAL_SPOT_DIR.relative_to(config.REPO_ROOT)}/")
    print_spot_checks(records, args.spot_check_n)


if __name__ == "__main__":
    main()