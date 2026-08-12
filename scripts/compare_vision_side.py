"""
Paired comparison of vision-side LoRA conditions vs the LM-only General LoRA
control. Per-condition metrics (overall / orientation / per-relation) and
exact McNemar tests on paired test examples.
"""
import os, sys, csv, json
from pathlib import Path
from collections import Counter

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scipy.stats import binomtest

ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]

def load_predictions(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def mcnemar_exact(a_correct, b_correct):
    """a, b: binary outcome vectors. Returns (p, b, c)."""
    b_ = sum(1 for x, y in zip(a_correct, b_correct) if x and not y)
    c_ = sum(1 for x, y in zip(a_correct, b_correct) if not x and y)
    n = b_ + c_
    if n == 0:
        return 1.0, b_, c_
    p = binomtest(min(b_, c_), n, 0.5, alternative="two-sided").pvalue
    return float(p), b_, c_

def metrics(rows, subset=None):
    rs = rows if subset is None else [r for r in rows if r["relation"] in subset]
    n = len(rs)
    if n == 0:
        return {"n": 0}
    correct = sum(1 for r in rs if r["correct"] == "True")
    return {"n": n, "acc": correct / n}

def main():
    base = Path("results")
    control = load_predictions(base / "7B_general_lora_predictions_20260809_094930.csv")
    zeroshot = load_predictions(base / "qwen2vl_7b_predictions_20260809_064919.csv")

    conditions = {"7B_zero-shot": zeroshot, "LM_only_LoRA_control": control}
    for name in ["projector", "vision_proj"]:
        matches = sorted(base.glob(f"qwen2vl_7b_{name}_lora_predictions_*.csv"))
        if matches:
            conditions[f"{name}_lora"] = load_predictions(matches[-1])

    groups = {
        "Overall (all 2195)": None,
        "Orientation (4 relations)": ORIENT,
        "facing": ["facing"],
        "facing away from": ["facing away from"],
        "parallel to": ["parallel to"],
        "perpendicular to": ["perpendicular to"],
    }

    names = list(conditions)
    print(f"Conditions: {names}")

    table = {}
    for gname, subset in groups.items():
        table[gname] = {}
        print(f"\n=== {gname} ===")
        for n in names:
            m = metrics(conditions[n], subset)
            table[gname][n] = m["acc"] if m.get("acc") is not None else None
            print(f"  {n:24s} acc={m['acc']:.4f}  (n={m['n']})")

    print("\n=== McNemar (exact binomial) vs LM-only control ===")
    mcn = {}
    for gname, subset in groups.items():
        mcn[gname] = {}
        crows = [r for r in control if subset is None or r["relation"] in subset]
        c_acc = [r["correct"] == "True" for r in crows]
        for n in names:
            if n == "LM_only_LoRA_control":
                continue
            rows = [r for r in conditions[n] if subset is None or r["relation"] in subset]
            acc = [r["correct"] == "True" for r in rows]
            p, b, c = mcnemar_exact(c_acc, acc)
            mcn[gname][n] = {"p": p, "discordant_ctrl": b, "discordant_new": c}
            sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
            print(f"  {gname:28s} {n:20s} p={p:.4f}{sig}  (ctrl-loss {b} / ctrl-gain {c})")

    out = {"conditions": names, "table": table, "mcnemar": mcn}
    (base / "vision_side_comparison.json").write_text(json.dumps(out, indent=2, default=float))
    print("\nSaved: results/vision_side_comparison.json")

if __name__ == "__main__":
    main()
