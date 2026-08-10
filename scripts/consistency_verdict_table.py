"""
Consistency verdict / base-rate table (CPU-only).

For each 7B condition and each strict complement family, report the observed
verdict patterns on complementary statement pairs (from the committed flip
prediction CSVs + the original prediction CSVs):

  n, both True, both False, complementary (opposite verdicts),
  original True rate, flipped True rate

This makes the inconsistency result stand on observed contradiction patterns
without depending on a 50% "chance" null model. The parallel/perp soft
complement is reported separately (both-True contradiction rate).

Outputs: results/consistency_verdict_table.json
         results/consistency_verdict_table.md
"""
import os
import sys
import csv
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ".")

CONDITIONS = {
    "7B_zero_shot": "results/qwen2vl_7b_predictions_20260809_064919.csv",
    "LM_only_LoRA": "results/7B_general_lora_predictions_20260809_094930.csv",
    "hardneg_LoRA": "results/7B_hardneg_lora_predictions_20260809_164619.csv",
    "projector_LoRA": "results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv",
    "vision_proj_LoRA": "results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv",
}
FAMILIES = ["FF", "FB", "LR"]
FAMILY_NAMES = {
    "FF": "facing / facing-away",
    "FB": "in-front-of / behind",
    "LR": "left / right",
}


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    out = {}
    for cond, pred_csv in CONDITIONS.items():
        preds = {r["id"]: r for r in load_csv(pred_csv)}
        flips = load_csv(f"results/consistency_flips_{cond}.csv")
        cond_out = {}
        for fam in FAMILIES + ["PP"]:
            pairs = [r for r in flips if r["family"] == fam]
            if not pairs:
                continue
            n = len(pairs)
            both_true = both_false = complementary = 0
            orig_true = flip_true = 0
            for p in pairs:
                op = preds.get(p["orig_idx"])
                if op is None:
                    raise SystemExit(
                        f"missing orig_idx {p['orig_idx']} in {pred_csv}")
                opred = str(op["prediction"]).strip().lower() == "true"
                fpred = str(p["flip_prediction"]).strip().lower() == "true"
                orig_true += 1 if opred else 0
                flip_true += 1 if fpred else 0
                if opred and fpred:
                    both_true += 1
                elif (not opred) and (not fpred):
                    both_false += 1
                else:
                    complementary += 1
            cond_out[fam] = {
                "n": n,
                "both_true": both_true,
                "both_false": both_false,
                "complementary": complementary,
                "orig_true_rate": orig_true / n,
                "flip_true_rate": flip_true / n,
                "contradiction_rate_strict": both_true / n,  # PP: only both-True is a true contradiction
                # expected under verdict independence given observed base rates
                "exp_both_true": orig_true / n * flip_true / n,
                "exp_both_false": (1 - orig_true / n) * (1 - flip_true / n),
                "exp_complementary": (orig_true / n) * (1 - flip_true / n)
                                     + (1 - orig_true / n) * (flip_true / n),
            }
        out[cond] = cond_out

    with open("results/consistency_verdict_table.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)

    L = []
    L.append("# Consistency Verdict Patterns (CPU-only, from committed CSVs)")
    L.append("")
    L.append("Strict families (exactly one truth value): complementary "
             "verdicts are the consistent outcome. Original and flipped True "
             "rates are the observed answer base rates on each member. "
             "'exp' columns give the verdict rates expected under verdict "
             "independence given the observed base rates (a response-bias "
             "null).")
    L.append("")
    for cond, d in out.items():
        L.append(f"## {cond}")
        L.append("")
        L.append("| Family | n | both True | both False | complementary | "
                 "orig True rate | flip True rate | exp both-False | "
                 "exp comp. |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for fam in FAMILIES:
            x = d[fam]
            L.append(f"| {FAMILY_NAMES[fam]} | {x['n']} | {x['both_true']} "
                     f"({x['both_true']/x['n']:.1%}) | {x['both_false']} "
                     f"({x['both_false']/x['n']:.1%}) | {x['complementary']} "
                     f"({x['complementary']/x['n']:.1%}) | "
                     f"{x['orig_true_rate']:.2f} | {x['flip_true_rate']:.2f} | "
                     f"{x['exp_both_false']:.1%} | {x['exp_complementary']:.1%} |")
        if "PP" in d:
            x = d["PP"]
            L.append(f"| parallel/perpendicular (soft; both-True is the true "
                     f"contradiction) | {x['n']} | {x['both_true']} "
                     f"({x['both_true']/x['n']:.1%}) | {x['both_false']} "
                     f"({x['both_false']/x['n']:.1%}) | --- | "
                     f"{x['orig_true_rate']:.2f} | {x['flip_true_rate']:.2f} | "
                     f"--- | --- |")
        L.append("")
    with open("results/consistency_verdict_table.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[:24]))
    print("\nSaved results/consistency_verdict_table.json/.md")


if __name__ == "__main__":
    main()
