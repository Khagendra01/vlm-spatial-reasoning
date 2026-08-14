"""Prediction row schema and CSV IO for the grounding audit.

Schema follows SPATIAL_GROUNDING_LORA_STUDY.md section 19. Tier-A rows keep
the full provenance columns; raw model output is preserved verbatim so any
future parser change can be replayed (preserve raw outputs requirement).
"""

import csv
import json

from . import config
from .hashing import git_commit

PREDICTION_FIELDS = [
    "example_id",
    "paired_parent_id",
    "split",
    "condition",
    "intervention_axis",
    "statement",
    "original_statement",
    "relation",
    "relation_family",
    "subject",
    "object",
    "ground_truth",
    "expected_transformed_label",
    "expected_prediction_behavior",
    "prediction",
    "correct",
    "raw_output",
    "model_id",
    "model_revision",
    "model_condition",
    "adapter_path",
    "adapter_hash",
    "training_seed",
    "prompt_version",
    "parser_version",
    "image_id",
    "source_image_id",
    "replacement_image_id",
    "transformed_image_id",
    "transform_name",
    "transform_version",
    "transform_metadata",
    "shuffle_seed",
    "generation_settings",
    "run_id",
    "git_commit",
    "protocol_version",
]


def build_prediction_row(record: dict, input_row: dict, parsed, raw_output: str,
                         checkpoint: dict, run_id: str,
                         prompt_version: str, parser_version: str,
                         adapter_hash: str) -> dict:
    """Assemble one full schema row."""
    label = input_row["label"]
    correct = parsed is not None and bool(parsed) == bool(label)
    transform_name = input_row["transform_name"]
    return {
        "example_id": input_row["example_id"],
        "paired_parent_id": input_row["example_id"],
        "split": config.DATASET_SPLIT,
        "condition": config.TRANSFORM_TO_CONDITION.get(transform_name, transform_name),
        "intervention_axis": "evidence",
        "statement": input_row["statement"],
        "original_statement": input_row["statement"],
        "relation": input_row["relation"],
        "relation_family": input_row["family"],
        "subject": record.get("subject", "") if record else "",
        "object": record.get("object", "") if record else "",
        "ground_truth": bool(label),
        "expected_transformed_label": None,
        "expected_prediction_behavior": None,
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
        "image_id": input_row["image_link"],
        "source_image_id": input_row["source_image_id"],
        "replacement_image_id": input_row["replacement_image_id"],
        "transformed_image_id": input_row["transformed_image_id"],
        "transform_name": transform_name,
        "transform_version": input_row["transform_version"],
        "transform_metadata": json.dumps(input_row["transform_metadata"], sort_keys=True),
        "shuffle_seed": config.SHUFFLE_SEED if transform_name == "shuffle_image" else None,
        "generation_settings": json.dumps({
            "do_sample": config.DO_SAMPLE,
            "max_new_tokens": config.MAX_NEW_TOKENS,
        }, sort_keys=True),
        "run_id": run_id,
        "git_commit": git_commit(),
        "protocol_version": "v0.1",
    }


def write_predictions(path, rows: list) -> str:
    """Write rows to CSV; returns file sha256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PREDICTION_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return config.sha256_file(path)


def _to_bool_or_none(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if value in ("True", "true", "1"):
        return True
    if value in ("False", "false", "0"):
        return False
    return None


def read_predictions(path) -> list:
    """Read a predictions CSV with light type recovery."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = list(csv.DictReader(f))
    for row in raw:
        row["ground_truth"] = _to_bool_or_none(row.get("ground_truth"))
        row["prediction"] = _to_bool_or_none(row.get("prediction"))
        row["correct"] = _to_bool_or_none(row.get("correct"))
        row["expected_transformed_label"] = _to_bool_or_none(
            row.get("expected_transformed_label"))
        if "label" in row:
            row["label"] = _to_bool_or_none(row.get("label"))
    return raw


def verify_paired_ids(files: dict) -> None:
    """Assert exact example-ID equality across all prediction files.

    `files` maps label -> path. Raises RuntimeError on any drift.
    """
    sets = {}
    for label, path in files.items():
        rows = read_predictions(path)
        sets[label] = {r["example_id"] for r in rows}
    reference = None
    for label, ids in sets.items():
        if reference is None:
            reference = ids
        elif ids != reference:
            missing = sorted(reference - ids)[:5]
            extra = sorted(ids - reference)[:5]
            raise RuntimeError(
                f"example-ID mismatch in {label}: missing={missing} extra={extra}"
            )
