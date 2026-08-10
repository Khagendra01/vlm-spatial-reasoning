"""
Paired comparison: VSR-trained 7B General LoRA vs zero-shot on the frozen
SITE image set (same 2,591 examples, same protocol except adapter).

Subset definitions come ONLY from the preregistered frozen protocol
(results/site/site_protocol.json -> frozen_ids), intersected with the
evaluated image prediction IDs. No keyword reconstruction during analysis.

Subsets: all images, primary (official spatial relationship reasoning),
secondary (orientation heuristic), exploratory (movement & navigation),
single-image, multi-image.
Metrics: n, raw acc, Wilson 95% CI, CAA, fixed/broken, exact paired McNemar.

Usage:  python scripts/compare_site_zeroshot_lora.py
Output: results/site/vsr_lora_vs_zeroshot.json
"""
import os
import sys
import csv
import json

from scipy.stats import binomtest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ".")

ZS_CSV = "results/site/zeroshot_7b_predictions.csv"
LR_CSV = "results/site/vsr_lora_predictions.csv"
PROTOCOL = "results/site/site_protocol.json"
OUT = "results/site/vsr_lora_vs_zeroshot.json"


def load(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = r
    return rows


def frozen_ids(subset_key):
    """Authoritative preregistered subset definition (image examples only)."""
    proto = json.load(open(PROTOCOL, encoding="utf-8"))
    ids = proto["frozen_ids"][subset_key]
    return [i for i in ids if str(i).startswith("image_test")]


def wilson_ci(k, n, z=1.96):
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    m = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
    return [max(0.0, c - m), min(1.0, c + m)]


def caa(rows):
    num = sum(int(r["correct"]) - 1 / int(r["n_options"]) for r in rows)
    den = sum(1 - 1 / int(r["n_options"]) for r in rows)
    return num / den if den else 0.0


def analyze(sub_ids, name):
    z = [zs[i] for i in sub_ids]
    l = [lr[i] for i in sub_ids]
    n = len(z)
    kz = sum(int(r["correct"]) for r in z)
    kl = sum(int(r["correct"]) for r in l)
    same = sum(1 for a, b in zip(z, l) if a["prediction"] == b["prediction"])
    fixed = sum(1 for a, b in zip(z, l)
                if a["prediction"] != b["prediction"] and b["correct"] == "1")
    broken = sum(1 for a, b in zip(z, l)
                 if a["prediction"] != b["prediction"] and a["correct"] == "1")
    b_ = sum(1 for a, b in zip(z, l) if a["correct"] == "1" and b["correct"] == "0")
    c_ = sum(1 for a, b in zip(z, l) if a["correct"] == "0" and b["correct"] == "1")
    p = binomtest(min(b_, c_), b_ + c_, 0.5, alternative="two-sided").pvalue if b_ + c_ else 1.0
    print(f"\n== {name} (n={n}) ==")
    print(f"  zero-shot: raw={kz/n:.4f} CI={[round(v, 4) for v in wilson_ci(kz, n)]} CAA={caa(z):.4f}")
    print(f"  LoRA:      raw={kl/n:.4f} CI={[round(v, 4) for v in wilson_ci(kl, n)]} CAA={caa(l):.4f}")
    print(f"  same-pred={same} ({same/n:.1%}) | fixed={fixed} broken={broken} "
          f"| McNemar p={p:.4f} (ctrl-loss {b_}, ctrl-gain {c_})")
    return {"name": name, "n": n,
            "zs": {"raw": kz / n, "ci": wilson_ci(kz, n), "caa": caa(z)},
            "lora": {"raw": kl / n, "ci": wilson_ci(kl, n), "caa": caa(l)},
            "same": same, "fixed": fixed, "broken": broken,
            "mcnemar_p": p, "ctrl_loss": b_, "ctrl_gain": c_}


zs = load(ZS_CSV)
lr = load(LR_CSV)
assert set(zs) == set(lr), "example sets must match"
ids = sorted(zs)
print(f"paired examples: {len(ids)}")

# Subset definitions from the frozen protocol only.
subsets = [
    ("All images", ids),
    ("Primary: spatial relationship reasoning", sorted(set(frozen_ids("primary")) & set(ids))),
    ("Secondary: orientation heuristic", sorted(set(frozen_ids("secondary")) & set(ids))),
    ("Exploratory: movement & navigation", sorted(set(frozen_ids("exploratory")) & set(ids))),
    ("single-image", sorted(i for i in ids if zs[i]["modality"] == "single-image")),
    ("multi-image", sorted(i for i in ids if zs[i]["modality"] == "multi-image")),
]

out = {}
for name, sub in subsets:
    out[name] = analyze(sub, name)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, default=float)
print(f"\nSaved {OUT}")
