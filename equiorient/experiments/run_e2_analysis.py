"""E2 analysis: correlate latent equivariance error with behavioral
flip-law compliance across checkpoints. CPU-only; runs on committed
Tier-C CSVs + extracted latent .npz files (GPU extraction deferred).

Usage:
  python -m equiorient.experiments.run_e2_analysis \
      --latents results/e2/z_*.npz \
      --csv results/grounding/predictions/tierc_full/zero_shot_hflip_flip.csv \
      --subset research/equiorient_iclr_push/e2_subset_ids.json \
      --protocol-ids results/grounding/protocol/vsr_test_ids.json \
      --out results/e2/e2_analysis.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

from ..analysis.bridge_metrics import (cosine_agreement, effective_rank,
                                       latent_norm_stats,
                                       normalized_equivariance_error,
                                       spearman_bootstrap)
from ..data.e2_behavior import checkpoint_compliance, select_subset


def analyze_npz(npz_path: str) -> dict:
    d = np.load(npz_path, allow_pickle=False)
    zx, ztx = d["zx"], d["ztx"]
    return {
        "path": npz_path,
        "backbone": str(d["backbone"]),
        "adapter": str(d["adapter"]),
        "n": int(zx.shape[0]),
        "dim": int(zx.shape[1]),
        "e_norm": normalized_equivariance_error(zx, ztx),
        "cosine": cosine_agreement(zx, ztx),
        **latent_norm_stats(zx),
        "effective_rank": effective_rank(zx),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--latents", nargs="+", required=True)
    ap.add_argument("--csv", action="append", required=True,
                    help="hflip_flip CSV per checkpoint; repeatable")
    ap.add_argument("--labels", nargs="*", default=[],
                    help="optional labels matching --csv order")
    ap.add_argument("--protocol-ids", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    csv_paths = []
    for pattern in a.csv:
        csv_paths.extend(sorted(glob.glob(pattern)))

    eligible: set[str] = set()
    for p in csv_paths:
        from ..data.e2_behavior import load_hflip_rows
        eligible |= {r["example_id"] for r in load_hflip_rows(p)}
    subset = select_subset(a.protocol_ids, eligible)
    subset_set = set(subset)

    latent_stats = [analyze_npz(p) for p in a.latents]
    compliance = {}
    for i, p in enumerate(csv_paths):
        label = a.labels[i] if i < len(a.labels) else Path(p).stem
        rate, _ = checkpoint_compliance(p, subset_set)
        compliance[label] = {"csv": p, "compliance_rate": rate}

    result = {"subset_n": len(subset),
              "subset_seed": 42,
              "latent_checkpoints": latent_stats,
              "behavioral_compliance": compliance,
              "correlations": {}}

    # Preregistered correlation requires one label per checkpoint (the
    # checkpoint is the unit of analysis); unlabeled invocations report
    # both sides without joining.
    if a.labels and len(a.labels) == len(csv_paths):
        xs = [analyze_npz(p)["e_norm"] for p in a.latents]
        ys = [checkpoint_compliance(c, subset_set)[0] for c in csv_paths]
        pairs = [(x, y) for x, y in zip(xs, ys) if y is not None]
        result["correlations"]["pooled"] = spearman_bootstrap(
            [p[0] for p in pairs], [p[1] for p in pairs])
        for backbone in {s["backbone"] for s in latent_stats}:
            idxs = [i for i, s in enumerate(latent_stats)
                    if s["backbone"] == backbone]
            result["correlations"][backbone] = spearman_bootstrap(
                [xs[i] for i in idxs], [ys[i] for i in idxs])

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(a.out, "w"), indent=2)
    print(json.dumps({k: v for k, v in result.items()
                      if k != "latent_checkpoints"}, indent=2))


if __name__ == "__main__":
    main()
