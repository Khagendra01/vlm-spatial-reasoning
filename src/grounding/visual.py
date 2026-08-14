"""Tier-C1 visual counterfactual: horizontal reflection (axis V).

Language is fixed; the image is mirrored horizontally. Per
research/GROUNDING_PROTOCOL_FREEZE.md section 6 and
research/SPATIAL_GROUNDING_LORA_STUDY.md section 10:

- C1 is confirmatory ONLY for relation families with logically guaranteed
  expected behavior. Left/right-style relations are the primary use:
  horizontal reflection flips the left/right axis, so the statement's truth
  MUST flip if the model is causally sensitive to the visual layout.
- NO global label flip: only mirrored-axis relations flip; all other
  relations keep the label, so separate invariant controls are analyzed
  separately (expected-invariant stability never merged with flip rate).
- The exact image transformation (PIL FLIP_LEFT_RIGHT after the uniform
  preprocessing cap) is versioned and recorded in run metadata; the same
  transformed pixels are fed to every compared checkpoint.

Transforms:
- hflip_flip      flip-expected: relations {left of, right of,
                  at the left side of, at the right side of}.
                  expected_transformed_label = NOT original_label.
- hflip_invariant invariant controls: {above, below, in front of, behind}
                  (horizontal mirror preserves vertical and depth ordering).
                  expected_transformed_label = original_label.
"""

import csv
import json

from PIL import Image

from . import config

FLIP_EXPECTED_RELATIONS = {
    "left of", "right of", "at the left side of", "at the right side of",
}

INVARIANT_RELATIONS = {
    "above", "below", "in front of", "behind",
}

TRANSFORMS = ["hflip_flip", "hflip_invariant"]

BEHAVIOR_NAMES = {
    "hflip_flip": "flip_expected",
    "hflip_invariant": "expected_invariant",
}


def flip_image(image: Image.Image) -> Image.Image:
    """Deterministic horizontal reflection; identical for every checkpoint."""
    return image.transpose(Image.FLIP_LEFT_RIGHT)


def eligible_relations(transform: str) -> set:
    if transform == "hflip_flip":
        return FLIP_EXPECTED_RELATIONS
    return INVARIANT_RELATIONS


def build_transform(record: dict, transform: str) -> dict:
    """Transformed input row for one record, or None if not in scope.

    The image itself is not loaded here (the runner loads the cached image,
    applies the uniform preprocessing, then flip_image()). This builder
    carries all expected-behavior metadata.
    """
    relation = record["relation"]
    label = bool(record["label"])
    if relation not in eligible_relations(transform):
        return None
    if transform == "hflip_flip":
        expected = (not label)
        behavior = BEHAVIOR_NAMES["hflip_flip"]
    else:
        expected = label
        behavior = BEHAVIOR_NAMES["hflip_invariant"]
    return {
        "example_id": record["example_id"],
        "statement": record["statement"].strip(),
        "original_statement": record["statement"].strip(),
        "label": label,
        "relation": relation,
        "family": record["family"],
        "subject": record.get("subject", ""),
        "object": record.get("object", ""),
        "expected_transformed_label": expected,
        "expected_prediction_behavior": behavior,
        "transform_name": "hflip",
        "condition": transform,
        "transform_version": config.TRANSFORM_VERSION_TIER_C,
        "transform_metadata": {
            "axis": "visual",
            "transform": "hflip",
            "algorithm": "PIL.Image.FLIP_LEFT_RIGHT applied AFTER uniform "
                         "392px long-side preprocessing",
            "condition": transform,
            "law": behavior,
            "relation_rule": ("mirrored-axis left/right relations flip; "
                              "vertical/depth relations invariant; no global "
                              "label flip"),
        },
    }


def eligible_rows(records: list, transform: str) -> list:
    out = []
    for rec in records:
        row = build_transform(rec, transform)
        if row is not None:
            out.append(row)
    return out


# --------------------------------------------------------------------------
# Freeze artifacts (committed pre-result; never regenerated after results)
# --------------------------------------------------------------------------

def build_validity_rows(records: list) -> list:
    rows = []
    for transform in TRANSFORMS:
        scope = eligible_relations(transform)
        for relation in sorted({r["relation"] for r in records}):
            n_el = sum(1 for r in records if r["relation"] == relation
                       and build_transform(r, transform) is not None)
            n_ex = sum(1 for r in records if r["relation"] == relation
                       and build_transform(r, transform) is None)
            if relation in scope:
                status = "strict_included"
                reason = ("mirror flips the left/right axis"
                          if transform == "hflip_flip"
                          else "horizontal mirror preserves vertical/depth ordering")
            else:
                status = "not_in_scope"
                reason = ("not a mirrored-axis left/right relation"
                          if transform == "hflip_flip"
                          else "not a guaranteed-invariant vertical/depth relation")
            rows.append({
                "transform": transform,
                "relation": relation,
                "status": status,
                "expected_truth_behavior": BEHAVIOR_NAMES[transform],
                "reason": reason,
                "eligible_n": n_el,
                "excluded_n": n_ex,
            })
    return rows


def build_eligible_ids_doc(records: list) -> dict:
    out = {
        "protocol_version": "v0.1",
        "authority": str(config.PROTOCOL_AUTHORITY.relative_to(config.REPO_ROOT)),
        "freeze_note": ("visual transform validity table and eligible IDs are "
                        "committed before any full Tier-C result is inspected"),
        "transform_version": config.TRANSFORM_VERSION_TIER_C,
        "transforms": {},
    }
    for transform in TRANSFORMS:
        entries = {}
        for rec in records:
            row = build_transform(rec, transform)
            if row is None:
                continue
            entries[rec["example_id"]] = {
                "relation": row["relation"],
                "family": row["family"],
                "original_label": bool(row["label"]),
                "expected_transformed_label": bool(row["expected_transformed_label"]),
                "expected_prediction_behavior": row["expected_prediction_behavior"],
            }
        out["transforms"][transform] = {
            "law": BEHAVIOR_NAMES[transform],
            "statements_fixed": True,
            "image_transform": "PIL FLIP_LEFT_RIGHT post-preprocess",
            "n_eligible": len(entries),
            "entries": entries,
        }
    return out


def write_freeze_files(records: list, force: bool = False) -> dict:
    if config.VISUAL_ELIGIBLE_FILE.exists() and not force:
        raise FileExistsError(
            f"{config.VISUAL_ELIGIBLE_FILE} already exists; use --force only "
            "with a decision-log entry"
        )
    rows = build_validity_rows(records)
    config.PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.VISUAL_VALIDITY_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    doc = build_eligible_ids_doc(records)
    with open(config.VISUAL_ELIGIBLE_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    return {
        "validity_file": str(config.VISUAL_VALIDITY_FILE.relative_to(config.REPO_ROOT)),
        "validity_sha256": config.sha256_file(config.VISUAL_VALIDITY_FILE),
        "eligible_file": str(config.VISUAL_ELIGIBLE_FILE.relative_to(config.REPO_ROOT)),
        "eligible_sha256": config.sha256_file(config.VISUAL_ELIGIBLE_FILE),
        "n_eligible": {t: doc["transforms"][t]["n_eligible"] for t in TRANSFORMS},
    }