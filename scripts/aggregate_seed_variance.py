# -*- coding: utf-8 -*-
"""
Aggregate multi-seed reruns into results/seed_variance/summary.json.

Reads every results/seed_variance/{condition}/{seed}/metrics.json produced by
scripts/run_seed_variance.py and reports, per condition:
  - overall accuracy  mean +/- std across seeds (n_seeds)
  - orientation accuracy mean +/- std across seeds
  - per-seed values
plus a comparison of the between-condition deltas in the frozen canonical
results against the observed seed-to-seed standard deviation, so that any
"X outperforms Y" language in the paper can be calibrated (or softened) on
the basis of measured training-run variance.

The frozen canonical snapshot is NOT touched. If no seed runs exist yet, the
script reports that and writes nothing.

Usage:  python scripts/aggregate_seed_variance.py
"""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SV = ROOT / "results" / "seed_variance"

# Canonical (frozen, single-seed) orientation accuracies per condition, from
# results/tables/vsr_conditions_table.md / the audit output (paper/fig/
# audit_output.txt). Used ONLY for the delta-vs-variance comparison.
CANONICAL_ORIENT = {
    "general": 65.7,
    "targeted": 64.2,
    "hardneg": 66.4,
    "projector": 64.2,
    "vision_proj": 64.2,
}
CANONICAL_OVERALL = {
    "general": 84.7,
    "targeted": 83.9,
    "hardneg": 84.3,
    "projector": 82.9,
    "vision_proj": 83.1,
}
CONDITIONS = ["general", "targeted", "hardneg", "projector", "vision_proj"]


def main():
    if not SV.exists():
        print("results/seed_variance/ does not exist: no seed runs yet. "
              "Nothing written (no fabricated numbers).")
        return

    per_condition = {}
    for cond in CONDITIONS:
        cdir = SV / cond
        if not cdir.exists():
            continue
        seeds = sorted(p.name for p in cdir.iterdir()
                       if (p / "metrics.json").exists())
        if not seeds:
            continue
        overall, orient = [], []
        for s in seeds:
            with open(cdir / s / "metrics.json", encoding="utf-8") as f:
                m = json.load(f)
            overall.append(100.0 * m["global"]["accuracy"])
            orient.append(100.0 * m["by_family"]["orientation"]["accuracy"])
        per_condition[cond] = {
            "n_seeds": len(seeds),
            "seeds": seeds,
            "overall": {"values": [round(v, 2) for v in overall],
                        "mean": round(statistics.mean(overall), 2) if len(overall) > 1
                                else None,
                        "std": round(statistics.stdev(overall), 2) if len(overall) > 1
                               else None},
            "orientation": {"values": [round(v, 2) for v in orient],
                            "mean": round(statistics.mean(orient), 2) if len(orient) > 1
                                    else None,
                            "std": round(statistics.stdev(orient), 2) if len(orient) > 1
                                   else None},
        }

    if not per_condition:
        print("results/seed_variance/ is empty: no seed runs yet. "
              "Nothing written (no fabricated numbers).")
        return

    # ---- delta-vs-variance comparison (orientation accuracy, % points) ----
    deltas = {}
    max_std = max(c["orientation"]["std"] or 0.0 for c in per_condition.values())
    pairs = [("general", "hardneg"), ("general", "targeted"),
             ("general", "projector"), ("general", "vision_proj"),
             ("targeted", "hardneg"), ("hardneg", "projector"),
             ("hardneg", "vision_proj"), ("targeted", "vision_proj")]
    for a, b in pairs:
        if a not in per_condition or b not in per_condition:
            continue
        delta = CANONICAL_ORIENT[a] - CANONICAL_ORIENT[b]
        std_a = per_condition[a]["orientation"]["std"]
        std_b = per_condition[b]["orientation"]["std"]
        pooled = None
        if std_a is not None and std_b is not None:
            pooled = round(((std_a ** 2 + std_b ** 2) / 2) ** 0.5, 2)
        deltas[f"{a}_vs_{b}"] = {
            "canonical_delta_pp": round(delta, 1),
            "inside_seed_variance": (pooled is not None and abs(delta) <= pooled),
            "pooled_seed_std_pp": pooled,
        }

    summary = {
        "note": ("Additive seed-variance evidence. Does not alter the frozen "
                 "canonical snapshot (results/* committed files). std is only "
                 "reported with n_seeds >= 2."),
        "per_condition": per_condition,
        "orientation_delta_vs_seed_variance": deltas,
        "interpretation": (
            "A canonical between-condition delta whose absolute value is "
            "smaller than the pooled seed-to-seed std is within observed "
            "training-run variance: 'X outperforms Y' language for that pair "
            "should be softened (e.g., 'nominally higher, within seed "
            "variance')."),
    }
    out = SV / "summary.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 70)
    print("Seed-variance summary")
    print("=" * 70)
    for cond, c in per_condition.items():
        ov = f"{c['overall']['mean']:.2f}±{c['overall']['std']:.2f}" if c["overall"]["std"] else "n/a"
        ori = f"{c['orientation']['mean']:.2f}±{c['orientation']['std']:.2f}" if c["orientation"]["std"] else "n/a"
        print(f"{cond:12s} seeds={c['n_seeds']}  overall {ov}%  orientation {ori}%")
    print()
    print("canonical orientation deltas (pp) vs pooled seed std:")
    for pair, d in deltas.items():
        inside = "INSIDE" if d["inside_seed_variance"] else "outside"
        print(f"  {pair:28s} delta={d['canonical_delta_pp']:+.1f}  "
              f"pooled_std={d['pooled_seed_std_pp']}  -> {inside} seed variance")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
