"""Frozen E2 subset selection + behavioral compliance recomputation.

Deterministic, preregistered (research/EQUIORIENT_ICLR_PUSH_PREREGISTRATION.md):
subset = 500 example_ids sampled once with default_rng(42) from the frozen
vsr_test_ids protocol manifest, intersected with IDs eligible in the
committed Tier-C hflip_flip CSVs. Compliance is RECOMPUTED from raw
prediction rows, never copied from reports.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

E2_N = 500
E2_SEED = 42


def select_subset(vsr_test_ids_path: str | Path,
                  eligible_ids: set[str],
                  n: int = E2_N,
                  seed: int = E2_SEED) -> list[str]:
    ids = json.load(open(vsr_test_ids_path))
    if isinstance(ids, dict):
        ids = ids.get("test_ids", ids.get("ids"))
        if ids is None and "examples" in json.load(open(vsr_test_ids_path)):
            ids = [e["example_id"]
                   for e in json.load(open(vsr_test_ids_path))["examples"]]
    pool = sorted(set(ids) & set(eligible_ids))
    rng = np.random.default_rng(seed)
    k = min(n, len(pool))
    idx = np.sort(rng.choice(len(pool), size=k, replace=False))
    return [pool[i] for i in idx]


def load_hflip_rows(csv_path: str | Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def flip_compliance(rows: list[dict], subset_ids: set[str] | None = None) -> dict:
    """Flip-compliance rate: prediction == expected_transformed_label."""
    kept = total = correct = 0
    per_example: dict[str, bool] = {}
    for r in rows:
        eid = r["example_id"]
        if subset_ids is not None and eid not in subset_ids:
            continue
        exp = r["expected_transformed_label"].strip().lower()
        pred = r["prediction"].strip().lower()
        ok = pred == exp and pred in ("true", "false")
        total += 1; correct += bool(ok)
        per_example[eid] = ok
        kept += 1
    return {"n": kept,
            "compliance_rate": round(correct / total, 6) if total else None,
            "per_example": per_example}


def image_id_index(rows: list[dict]) -> dict[str, str]:
    """example_id -> source image URL for the latent extractor."""
    out = {}
    for r in rows:
        iid = r.get("source_image_id") or r.get("image_id")
        if iid:
            out[r["example_id"]] = iid
    return out


def checkpoint_compliance(csv_path: str | Path,
                          subset_ids: set[str]) -> tuple[float, dict[str, bool]]:
    res = flip_compliance(load_hflip_rows(csv_path), subset_ids)
    assert res["n"] > 0, f"no subset overlap in {csv_path}"
    return res["compliance_rate"], res["per_example"]
