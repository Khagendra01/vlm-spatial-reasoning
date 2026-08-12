# -*- coding: utf-8 -*-
"""
Bootstrap uncertainty analysis for the family-relative improvement claim.

Headline pattern: scaling (2B -> 7B zero-shot) and adaptation (7B zero-shot ->
7B General LoRA) improve other relation families much more than orientation.

For each example we have the paired correctness of both conditions. For each
family f we compute Delta_f = acc_f(cond2) - acc_f(cond1), then the contrast
  C_f = Delta_f - Delta_orientation
with a paired bootstrap (B resamples over the 2,195 test examples):
point estimate, 95% percentile CI, and P(C_f > 0) (fraction of resamples
where the family's improvement exceeds orientation's improvement).

No headline number is modified; this is an additive uncertainty analysis.

Outputs:
  results/bootstrap_family_contrast.json
  results/bootstrap_family_contrast.md
"""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

FAMILY_MAP = {
    "in front of": "depth", "behind": "depth", "at the back of": "depth",
    "ahead of": "depth",
    "left of": "horizontal", "right of": "horizontal",
    "at the left side of": "horizontal", "at the right side of": "horizontal",
    "next to": "horizontal", "beside": "horizontal",
    "above": "vertical", "below": "vertical", "over": "vertical",
    "under": "vertical", "beneath": "vertical", "on top of": "vertical",
    "facing": "orientation", "facing away from": "orientation",
    "parallel to": "orientation", "perpendicular to": "orientation",
    "in": "containment", "inside": "containment", "contains": "containment",
    "within": "containment",
    "near": "proximity", "far from": "proximity", "far away from": "proximity",
    "close to": "proximity", "away from": "proximity",
    "touching": "topology_contact", "on": "topology_contact",
    "at": "topology_contact", "at the edge of": "topology_contact",
    "off": "topology_contact",
}

FAMILIES = ["orientation", "depth", "horizontal", "containment",
            "topology_contact"]

PAIRS = [
    ("2B zs -> 7B zs (scaling)",
     "results/smolvlm2_baseline_2195_20260808_214536.csv",
     "results/qwen2vl_7b_predictions_20260809_064919.csv"),
    ("7B zs -> 7B General LoRA (adaptation)",
     "results/qwen2vl_7b_predictions_20260809_064919.csv",
     "results/7B_general_lora_predictions_20260809_094930.csv"),
]

B = 10_000
RNG = np.random.default_rng(20260812)


def load(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[int(r["id"])] = r
    return rows


def main():
    out = {}
    for pair_name, f1, f2 in PAIRS:
        a, b = load(ROOT / f1), load(ROOT / f2)
        ids = sorted(a.keys() & b.keys())
        # per-example correctness per family
        fam_of = {}
        corr = {fam: {"a": np.zeros(len(ids), dtype=bool),
                      "b": np.zeros(len(ids), dtype=bool),
                      "mask": np.zeros(len(ids), dtype=bool)}
                for fam in FAMILIES}
        for i, eid in enumerate(ids):
            rel = (a[eid]["relation"] or "").strip()
            fam = FAMILY_MAP.get(rel)
            if fam is None or fam not in corr:
                continue
            corr[fam]["mask"][i] = True
            corr[fam]["a"][i] = a[eid]["correct"] == "True"
            corr[fam]["b"][i] = b[eid]["correct"] == "True"

        # per-family accuracy pair
        acc = {}
        for fam in FAMILIES:
            m = corr[fam]["mask"]
            acc[fam] = (corr[fam]["a"][m].mean(), corr[fam]["b"][m].mean())

        # paired bootstrap over example indices
        n = len(ids)
        delta = {}
        for fam in FAMILIES:
            m = corr[fam]["mask"]
            idx = np.where(m)[0]
            db = np.empty(B)
            for t in range(B):
                s = RNG.choice(idx, size=len(idx), replace=True)
                db[t] = corr[fam]["b"][s].mean() - corr[fam]["a"][s].mean()
            delta[fam] = db

        contrasts = {}
        for fam in FAMILIES:
            if fam == "orientation":
                continue
            c = (delta[fam] - delta["orientation"]) * 100.0  # percentage points
            lo, hi = np.percentile(c, [2.5, 97.5])
            contrasts[fam] = {
                "point_pp": float(c.mean()),
                "ci95_pp": [float(lo), float(hi)],
                "p_positive": float((c > 0).mean()),
                "delta_family_pp": float((acc[fam][1] - acc[fam][0]) * 100),
                "delta_orientation_pp": float(
                    (acc["orientation"][1] - acc["orientation"][0]) * 100),
            }

        out[pair_name] = {
            "n_examples": n,
            "family_accuracy_pair": {fam: [round(acc[fam][0] * 100, 2),
                                           round(acc[fam][1] * 100, 2)]
                                     for fam in FAMILIES},
            "contrasts": contrasts,
        }

    (RESULTS / "bootstrap_family_contrast.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    md = ["# Bootstrap family-relative improvement contrasts",
          "",
          "Paired bootstrap (B=10,000) over the 2,195 shared VSR test examples. "
          "Contrast C_f = Delta_f - Delta_orientation (percentage points).",
          ""]
    for pair_name, d in out.items():
        md.append(f"## {pair_name}")
        md.append("")
        md.append("| family | acc1 % | acc2 % | Delta_f pp | contrast pp | 95% CI | P(contrast>0) |")
        md.append("|---|---|---|---|---|---|---|")
        for fam in FAMILIES:
            a1, a2 = d["family_accuracy_pair"][fam]
            df = a2 - a1
            if fam == "orientation":
                md.append(f"| {fam} | {a1:.1f} | {a2:.1f} | {df:+.1f} | --- | --- | --- |")
            else:
                c = d["contrasts"][fam]
                lo, hi = c["ci95_pp"]
                md.append(f"| {fam} | {a1:.1f} | {a2:.1f} | {df:+.1f} | "
                          f"{c['point_pp']:+.1f} | [{lo:+.1f}, {hi:+.1f}] | "
                          f"{c['p_positive']:.3f} |")
        md.append("")
    (RESULTS / "bootstrap_family_contrast.md").write_text("\n".join(md),
                                                         encoding="utf-8")

    # console summary
    for pair_name, d in out.items():
        print(f"\n=== {pair_name} ===")
        for fam in FAMILIES:
            a1, a2 = d["family_accuracy_pair"][fam]
            df = a2 - a1
            if fam == "orientation":
                print(f"  {fam:<14} {a1:6.1f}% -> {a2:6.1f}%  (Delta {df:+.1f}pp)")
            else:
                c = d["contrasts"][fam]
                print(f"  {fam:<14} {a1:6.1f}% -> {a2:6.1f}%  (Delta {df:+.1f}pp)  "
                      f"contrast {c['point_pp']:+.1f}pp  CI [{c['ci95_pp'][0]:+.1f}, {c['ci95_pp'][1]:+.1f}]  "
                      f"P(>0)={c['p_positive']:.3f}")
    print("\nwrote results/bootstrap_family_contrast.json/.md")


if __name__ == "__main__":
    main()
