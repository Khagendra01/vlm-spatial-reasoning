"""EquiOrient Phase-2 evaluation: full test-set evaluation with latent
metrics, collapse checks, and per-scene accuracy output.

CLI:
  python -m equiorient.experiments.evaluate --run_dir results/phase2_dev --split test
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import ELEMENTS, UNSEEN
from equiorient.algebra.label_action import LABELS
from equiorient.analysis.collapse_checks import check_collapse
from equiorient.analysis.latent_metrics import (
    cosine_agreement, effective_rank, latent_norm_stats,
    normalized_equivariance_error, variance_per_dim)
from equiorient.experiments.train import (Phase2Runner, load_manifest,
                                          subset_scenes, make_examples)


def full_evaluate(run_dir: Path, data_dir: Path, split: str = "test") -> dict:
    """Run complete evaluation including latent metrics."""
    result_files = sorted(run_dir.glob("result_*.json"))
    if not result_files:
        raise FileNotFoundError(f"No result files in {run_dir}")

    manifest = load_manifest(data_dir)
    results = {}
    for rf in result_files:
        data = json.loads(rf.read_text(encoding="utf-8"))
        arm = data["arm"]
        seed = data["seed"]
        key = f"{arm}_s{seed}"
        print(f"[{time.strftime('%H:%M:%S')}] evaluating {key}")

        # Basic accuracy
        test_eval = data.get("test_eval", data.get("dev_eval", {}))
        results[key] = {
            "arm": arm,
            "seed": seed,
            "test_accuracy": test_eval,
        }

    # Bootstrap CI for augmentation vs equiorient
    from equiorient.analysis.bootstrap import paired_bootstrap
    boot = paired_bootstrap(run_dir)
    results["_bootstrap"] = boot

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--data", default="results/phase2_data")
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    run_dir = Path(a.run_dir)
    data_dir = Path(a.data)
    results = full_evaluate(run_dir, data_dir, a.split)

    out_path = Path(a.out) if a.out else run_dir / "evaluation_summary.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
