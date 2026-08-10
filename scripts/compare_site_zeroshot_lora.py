"""
Paired comparison: VSR-trained 7B General LoRA vs zero-shot on the frozen
SITE image set (same 2,591 examples, same protocol except adapter).

Subsets: all images, primary (official spatial relationship reasoning),
secondary (orientation heuristic), single-image, multi-image.
Metrics: raw acc, CAA, Wilson 95% CI, exact paired McNemar, fixed/broken.
"""
import os, sys, json, csv, re
os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

from scipy.stats import binomtest
from src.datasets.site import ORIENTATION_KEYWORDS

def load(path):
    rows = {}
    for r in csv.DictReader(open(path)):
        rows[r["id"]] = r
    return rows

zs = load("results/site/zeroshot_7b_predictions.csv")
lr = load("results/site/vsr_lora_predictions.csv")
assert set(zs) == set(lr), "example sets must match"
ids = sorted(zs)
print(f"paired examples: {len(ids)}")

def wilson_ci(k, n, z=1.96):
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    m = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
    return [max(0, c - m), min(1, c + m)]

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
    fixed = sum(1 for a, b in zip(z, l) if a["prediction"] != b["prediction"] and b["correct"] == "1")
    broken = sum(1 for a, b in zip(z, l) if a["prediction"] != b["prediction"] and a["correct"] == "1")
    b_ = sum(1 for a, b in zip(z, l) if a["correct"] == "1" and b["correct"] == "0")
    c_ = sum(1 for a, b in zip(z, l) if a["correct"] == "0" and b["correct"] == "1")
    p = binomtest(min(b_, c_), b_ + c_, 0.5, alternative="two-sided").pvalue if b_ + c_ else 1.0
    print(f"\n== {name} (n={n}) ==")
    print(f"  zero-shot: raw={kz/n:.4f} CI={wilson_ci(kz,n)} CAA={caa(z):.4f}")
    print(f"  LoRA:      raw={kl/n:.4f} CI={wilson_ci(kl,n)} CAA={caa(l):.4f}")
    print(f"  same-pred={same} ({same/n:.1%}) | fixed={fixed} broken={broken} "
          f"| McNemar p={p:.4f} (ctrl-loss {b_}, ctrl-gain {c_})")
    return {"name": name, "n": n,
            "zs": {"raw": kz/n, "ci": wilson_ci(kz, n), "caa": caa(z)},
            "lora": {"raw": kl/n, "ci": wilson_ci(kl, n), "caa": caa(l)},
            "same": same, "fixed": fixed, "broken": broken,
            "mcnemar_p": p, "ctrl_loss": b_, "ctrl_gain": c_}

results = []
all_ids = ids
primary_ids = [i for i in ids if zs[i]["category"] == "spatial relationship reasoning"]
sec_ids = [i for i in ids if any(re.search(rf"\b{kw}", (zs[i]["question"] or "").lower()) for kw in ORIENTATION_KEYWORDS)]
single_ids = [i for i in ids if zs[i]["modality"] == "single-image"]
multi_ids = [i for i in ids if zs[i]["modality"] == "multi-image"]

out = {}
for name, sub in [("All images", all_ids), ("Primary: spatial relationship reasoning", primary_ids),
                  ("Secondary: orientation heuristic", sec_ids),
                  ("single-image", single_ids), ("multi-image", multi_ids)]:
    out[name] = analyze(sub, name)

json.dump(out, open("results/site/vsr_lora_vs_zeroshot.json", "w"), indent=1, default=float)
print("\nSaved results/site/vsr_lora_vs_zeroshot.json")
