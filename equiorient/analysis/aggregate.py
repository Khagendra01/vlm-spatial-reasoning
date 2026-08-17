"""Aggregate results across seeds for each arm.

Reads result_*.json files from a run directory and produces per-arm
summary statistics (mean, std, individual seed values).
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import numpy as np


def aggregate(run_dir: Path, arms: list[str] | None = None,
              metric: str = "unseen_accuracy") -> dict:
    """Aggregate dev or test results across seeds.

    Returns: {arm: {mean, std, se, values: [...], per_transform_mean: {...}}}
    """
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(run_dir.glob("result_*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        arm = data.get("arm", "unknown")
        if arms and arm not in arms:
            continue
        by_arm[arm].append(data)

    out = {}
    for arm, runs in by_arm.items():
        evals = [r.get("dev_eval", r.get("test_eval", {})) for r in runs]
        vals = [e.get(metric, float("nan")) for e in evals]
        arr = np.array(vals, dtype=float)
        # per-transform averages
        pt_keys = list(evals[0].get("per_transform", {}).keys()) if evals else []
        pt_means = {}
        for k in pt_keys:
            pt_vals = [e.get("per_transform", {}).get(k, float("nan"))
                       for e in evals]
            pt_means[k] = round(float(np.nanmean(pt_vals)), 4)
        out[arm] = {
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std(ddof=1)), 4) if len(arr) > 1 else 0.0,
            "se": round(float(arr.std(ddof=1) / np.sqrt(len(arr))), 4)
                  if len(arr) > 1 else 0.0,
            "n_seeds": len(arr),
            "values": [round(float(v), 4) for v in arr],
            "per_transform_mean": pt_means,
        }
    return out
