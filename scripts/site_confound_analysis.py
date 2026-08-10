"""
SITE confound / composition analysis (CPU-only; no inference).

Question: does the orientation-keyword heuristic flag predict lower zero-shot
correctness after controlling for task composition (official category, source
dataset, modality, number of options)?

If the adjusted effect survives -> orientation vocabulary is independently
associated with difficulty. If it disappears -> the low aggregate heuristic
score is largely explained by task composition, and SITE is not treated as
independent confirmation of the VSR orientation construct.

Also computes:
  - within-category and within-source orientation-pos vs orientation-neg
    accuracy comparisons (n >= 30 in both arms)
  - a high-precision POST-HOC/EXPLORATORY subset using only VSR-construct
    terms (facing, facing away, parallel, perpendicular); this does NOT
    replace the preregistered frozen subset

Inputs : results/site/zeroshot_7b_predictions.csv (2,591 rows, unchanged),
         results/site/site_protocol.json (frozen IDs)
Outputs: results/site/orientation_confound_analysis.json
         results/site/orientation_confound_report.md
"""
import os
import re
import sys
import csv
import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ".")

PRED = "results/site/zeroshot_7b_predictions.csv"
PROTO = "results/site/site_protocol.json"
OUT_JSON = "results/site/orientation_confound_analysis.json"
OUT_MD = "results/site/orientation_confound_report.md"

# High-precision post-hoc/exploratory terms: direct VSR construct only.
VSR_TERMS = ["facing", "facing away", "parallel", "perpendicular"]


def load_predictions(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def frozen_secondary_ids():
    proto = json.load(open(PROTO, encoding="utf-8"))
    return set(proto["frozen_ids"]["secondary"])


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    m = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
    return [max(0.0, c - m), min(1.0, c + m)]


def caa(rows):
    num = sum(int(r["correct"]) - 1 / int(r["n_options"]) for r in rows)
    den = sum(1 - 1 / int(r["n_options"]) for r in rows)
    return num / den if den else 0.0


def main():
    rows = load_predictions(PRED)
    sec_ids = frozen_secondary_ids()

    df = pd.DataFrame([
        {
            "id": r["id"],
            "correct": int(r["correct"]),
            "orient": 1 if r["id"] in sec_ids else 0,      # frozen-ID heuristic flag
            "category": r["category"],
            "source": r["source_dataset"],
            "modality": r["modality"],
            "n_options": int(r["n_options"]),
            "question": r["question"],
            "options": r["options"],
        }
        for r in rows
    ])
    assert len(df) == 2591

    out = {"n": len(df)}

    # ---- Model 1: full controls ----
    m1 = smf.logit(
        "correct ~ orient + C(category) + C(source) + C(modality) + n_options",
        data=df,
    ).fit(disp=False)
    c1 = m1.conf_int().loc["orient"]
    out["model_full"] = {
        "orient_coef": float(m1.params["orient"]),
        "orient_odds_ratio": float(np.exp(m1.params["orient"])),
        "orient_ci_95": [float(np.exp(c1[0])), float(np.exp(c1[1]))],
        "orient_p": float(m1.pvalues["orient"]),
        "nobs": int(m1.nobs),
        "pseudo_r2": float(m1.prsquared),
    }

    # ---- Model 2: category controls only (composition sensitivity) ----
    m2 = smf.logit("correct ~ orient + C(category)", data=df).fit(disp=False)
    c2 = m2.conf_int().loc["orient"]
    out["model_category_only"] = {
        "orient_coef": float(m2.params["orient"]),
        "orient_odds_ratio": float(np.exp(m2.params["orient"])),
        "orient_ci_95": [float(np.exp(c2[0])), float(np.exp(c2[1]))],
        "orient_p": float(m2.pvalues["orient"]),
    }

    # ---- Model 3: unadjusted ----
    m3 = smf.logit("correct ~ orient", data=df).fit(disp=False)
    c3 = m3.conf_int().loc["orient"]
    out["model_unadjusted"] = {
        "orient_coef": float(m3.params["orient"]),
        "orient_odds_ratio": float(np.exp(m3.params["orient"])),
        "orient_ci_95": [float(np.exp(c3[0])), float(np.exp(c3[1]))],
        "orient_p": float(m3.pvalues["orient"]),
    }

    # ---- Within-category ----
    cat_rows = []
    for cat, g in df.groupby("category"):
        pos = g[g["orient"] == 1]
        neg = g[g["orient"] == 0]
        if len(pos) >= 30 and len(neg) >= 30:
            kp, np_ = pos["correct"].sum(), len(pos)
            kn, nn_ = neg["correct"].sum(), len(neg)
            cat_rows.append({
                "category": cat,
                "orient_pos_n": np_, "orient_pos_acc": float(kp / np_),
                "orient_neg_n": nn_, "orient_neg_acc": float(kn / nn_),
                "delta_pp": float((kp / np_ - kn / nn_) * 100),
            })
    out["within_category"] = cat_rows

    # ---- Within-source ----
    src_rows = []
    src_arms = []
    for src, g in df.groupby("source"):
        pos = g[g["orient"] == 1]
        neg = g[g["orient"] == 0]
        src_arms.append((src, int(len(pos)), int(len(neg))))
        if len(pos) >= 30 and len(neg) >= 30:
            kp, np_ = pos["correct"].sum(), len(pos)
            kn, nn_ = neg["correct"].sum(), len(neg)
            src_rows.append({
                "source": src,
                "orient_pos_n": np_, "orient_pos_acc": float(kp / np_),
                "orient_neg_n": nn_, "orient_neg_acc": float(kn / nn_),
                "delta_pp": float((kp / np_ - kn / nn_) * 100),
            })
    out["within_source"] = src_rows
    out["within_source_concentration_note"] = (
        "No source dataset has n>=30 in both orientation arms: the heuristic "
        "is heavily concentrated within sources (orientation-heavy corpora are "
        "almost entirely flagged, others almost never). Source indicators "
        "therefore absorb most of the orientation variance in the full model. "
        "Arms: " + str(src_arms))

    # ---- High-precision post-hoc/exploratory subset (VSR construct terms) ----
    pat = re.compile(
        r"\b(" + "|".join(VSR_TERMS) + r")\b", re.IGNORECASE)
    hp_ids = [
        r["id"] for r in rows
        if pat.search((r["question"] or ""))
        or pat.search((r["options"] or "").replace("<image>", ""))
    ]
    hp = df[df["id"].isin(hp_ids)]
    k = int(hp["correct"].sum())
    hp_rows = [r for r in rows if r["id"] in set(hp_ids)]
    out["high_precision_exploratory"] = {
        "n": int(len(hp)),
        "raw": float(k / len(hp)),
        "ci_95": wilson_ci(k, len(hp)),
        "caa": caa(hp_rows),
        "by_category": hp.groupby("category").size().to_dict(),
        "note": ("POST-HOC exploratory subset, VSR-construct terms only "
                 "(facing/facing away/parallel/perpendicular); does NOT "
                 "replace the preregistered frozen subset"),
    }
    # overlap with frozen secondary
    out["high_precision_exploratory"]["overlap_with_frozen_secondary"] = int(
        len(set(hp_ids) & sec_ids))
    out["high_precision_exploratory"]["not_in_frozen_secondary"] = int(
        len(set(hp_ids) - sec_ids))

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)

    # ---- Report ----
    L = []
    L.append("# SITE Orientation-Heuristic Confound Analysis (CPU-only)")
    L.append("")
    L.append(f"Data: `{PRED}` (2,591 zero-shot image predictions, unchanged). "
             "Orientation flag = frozen-ID secondary membership "
             "(`site_protocol.json -> frozen_ids.secondary`).")
    L.append("")
    L.append("## Logistic regressions: correct ~ orient + controls")
    L.append("")
    L.append("| Model | OR (orient) | 95% CI | p |")
    L.append("|---|---|---|---|")
    for name, key in [("Unadjusted", "model_unadjusted"),
                      ("+ official category", "model_category_only"),
                      ("+ category + source + modality + n_options",
                       "model_full")]:
        d = out[key]
        L.append(f"| {name} | {d['orient_odds_ratio']:.3f} | "
                 f"[{d['orient_ci_95'][0]:.3f}, {d['orient_ci_95'][1]:.3f}] | "
                 f"{d['orient_p']:.4g} |")
    L.append("")
    L.append("## Within-category (orient-pos vs orient-neg, both n>=30)")
    L.append("")
    L.append("| Category | pos n | pos acc | neg n | neg acc | delta (pp) |")
    L.append("|---|---|---|---|---|---|")
    for d in sorted(cat_rows, key=lambda x: -abs(x["delta_pp"])):
        L.append(f"| {d['category']} | {d['orient_pos_n']} | "
                 f"{d['orient_pos_acc']*100:.1f} | {d['orient_neg_n']} | "
                 f"{d['orient_neg_acc']*100:.1f} | {d['delta_pp']:+.1f} |")
    L.append("")
    L.append("## Within-source (orient-pos vs orient-neg, both n>=30)")
    L.append("")
    if src_rows:
        L.append("| Source | pos n | pos acc | neg n | neg acc | delta (pp) |")
        L.append("|---|---|---|---|---|---|")
        for d in sorted(src_rows, key=lambda x: -abs(x["delta_pp"])):
            L.append(f"| {d['source']} | {d['orient_pos_n']} | "
                     f"{d['orient_pos_acc']*100:.1f} | {d['orient_neg_n']} | "
                     f"{d['orient_neg_acc']*100:.1f} | {d['delta_pp']:+.1f} |")
    else:
        L.append("No source dataset has n>=30 in both arms: the heuristic is "
                 "heavily concentrated within sources (orientation-heavy "
                 "corpora are almost entirely flagged, others almost never), "
                 "so source indicators absorb most of the orientation "
                 "variance in the full model.")
    L.append("")
    hp_d = out["high_precision_exploratory"]
    L.append("## High-precision post-hoc/exploratory subset (VSR-construct terms)")
    L.append("")
    L.append(f"- Terms: `{', '.join(VSR_TERMS)}` (word-boundary, question + "
             "option text; POST-HOC, does not replace the preregistered subset).")
    L.append(f"- n = {hp_d['n']} (overlap with frozen secondary: "
             f"{hp_d['overlap_with_frozen_secondary']}, outside: "
             f"{hp_d['not_in_frozen_secondary']})")
    L.append(f"- raw acc = {hp_d['raw']*100:.1f}% "
             f"CI={[round(v*100, 1) for v in hp_d['ci_95']]}, "
             f"CAA = {hp_d['caa']*100:.1f}%")
    L.append(f"- by official category: {hp_d['by_category']}")
    L.append("")
    L.append("## Reading")
    L.append("")
    L.append("- If the adjusted OR remains clearly < 1 with p < 0.05: "
             "orientation vocabulary is independently associated with "
             "difficulty beyond task composition.")
    L.append("- If it collapses toward 1: the aggregate heuristic score is "
             "largely explained by task composition; SITE is then reported "
             "as cross-dataset transfer evidence only, with the heuristic "
             "slice as exploratory.")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print("\n".join(L[:22]))
    print(f"\nSaved {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
