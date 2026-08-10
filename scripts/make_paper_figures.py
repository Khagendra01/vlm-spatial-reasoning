# -*- coding: utf-8 -*-
"""
Generate paper figures and the numerical-audit table directly from raw
result artifacts (prediction CSVs + metrics JSONs).

Usage:  python scripts/make_paper_figures.py
Outputs: paper/fig/*.pdf|.png  (and prints the audit table + appendix tables)
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGDIR = os.path.join(ROOT, "paper", "fig")
os.makedirs(FIGDIR, exist_ok=True)

ORIENT_RELS = ["facing", "facing away from", "parallel to", "perpendicular to"]

CONDITIONS = {
    "2B zero-shot": "smolvlm2_baseline_2195_20260808_214536.csv",
    "2B General LoRA": "general_lora_predictions_20260809_054915.csv",
    "2B Targeted LoRA": "targeted_lora_predictions_20260809_061231.csv",
    "7B zero-shot": "qwen2vl_7b_predictions_20260809_064919.csv",
    "7B General LoRA": "7B_general_lora_predictions_20260809_094930.csv",
    "7B HardNeg LoRA": "7B_hardneg_lora_predictions_20260809_164619.csv",
    "7B Projector LoRA": "qwen2vl_7b_projector_lora_predictions_20260809_221720.csv",
    "7B Vision+Proj LoRA": "qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv",
}


def load_preds(fname):
    with open(os.path.join(RESULTS, fname), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def acc_correct(rows, rel=None):
    rs = [r for r in rows if rel is None or (r.get("relation") or "").strip() == rel]
    if not rs:
        return None, 0
    n = sum(1 for r in rs if str(r.get("correct")).strip() == "True")
    return n, len(rs)


def pct(n, d):
    return 100.0 * n / d if d else float("nan")


def main():
    print("=" * 88)
    print("AUDIT TABLE: orientation family + per-relation accuracy per condition")
    print("(computed from raw prediction CSVs; 'correct' == True)")
    print("=" * 88)
    hdr = "{:22s} {:>8s} {:>8s} | {:>7s} {:>7s} {:>7s} {:>7s} {:>12s}".format(
        "condition", "overall", "orient", "facing", "away", "paral", "perp", "orient n")
    print(hdr)
    print("-" * len(hdr))

    per_rel = {}
    family = {}
    overall = {}
    for name, fname in CONDITIONS.items():
        rows = load_preds(fname)
        c, t = acc_correct(rows)
        overall[name] = (c, t)
        fam_n, fam_t = 0, 0
        pr = {}
        for rel in ORIENT_RELS:
            rc, rt = acc_correct(rows, rel)
            fam_n += rc
            fam_t += rt
            pr[rel] = (rc, rt)
        per_rel[name] = pr
        family[name] = (fam_n, fam_t)
        print("{:22s} {:7.1f}% {:7.1f}% | {:6.1f}% {:6.1f}% {:6.1f}% {:6.1f}% {:>6d}/{:d}".format(
            name, pct(*overall[name]), pct(*family[name]),
            pct(*pr["facing"]), pct(*pr["facing away from"]),
            pct(*pr["parallel to"]), pct(*pr["perpendicular to"]),
            fam_n, fam_t))

    # ---- cross-check against metrics JSONs ----
    print()
    print("Cross-check vs metrics JSONs:")
    checks = [
        ("2B zero-shot overall", "smolvlm2_metrics_2195_20260808_214536.json", "global.accuracy"),
        ("7B zero-shot overall", "qwen2vl_7b_metrics_20260809_064919.json", "global.accuracy"),
        ("7B General overall", "7B_general_lora_metrics_20260809_094930.json", "global.accuracy"),
        ("7B HardNeg overall", "7B_hardneg_lora_metrics_20260809_164619.json", "global.accuracy"),
        ("7B General orient", "7B_general_lora_metrics_20260809_094930.json", "by_family.orientation.accuracy"),
        ("7B HardNeg orient", "7B_hardneg_lora_metrics_20260809_164619.json", "by_family.orientation.accuracy"),
    ]
    for label, fname, path in checks:
        with open(os.path.join(RESULTS, fname), encoding="utf-8") as f:
            js = json.load(f)
        v = js
        for k in path.split("."):
            v = v[k]
        print("  {:24s} json={:.4f}".format(label, v))

    # =====================================================================
    # FIGURE 1: per-relation orientation accuracy, 4 headline conditions
    # =====================================================================
    conds = ["2B zero-shot", "7B zero-shot", "7B General LoRA", "7B HardNeg LoRA"]
    rels_short = ["facing", "facing away", "parallel", "perpendicular"]
    x = np.arange(len(rels_short))
    width = 0.2
    fig, ax = plt.subplots(figsize=(6.6, 2.6), dpi=300)
    colors = ["#8ca5d9", "#4c6bb4", "#1f3d7a", "#0f2547"]
    for i, cond in enumerate(conds):
        vals = [pct(*per_rel[cond][r]) for r in ORIENT_RELS]
        ns = ["n=%d" % per_rel[cond][r][1] for r in ORIENT_RELS]
        bars = ax.bar(x + (i - 1.5) * width, vals, width, label=cond, color=colors[i])
        for b, nn in zip(bars, ns):
            ax.annotate(nn, (b.get_x() + b.get_width() / 2, b.get_height() + 1),
                        ha="center", fontsize=5.2, color="#444444")
    ax.set_xticks(x)
    ax.set_xticklabels(rels_short, fontsize=8)
    ax.set_ylabel("accuracy (%)", fontsize=8)
    ax.set_ylim(0, 100)
    ax.axhline(50, color="#999999", ls="--", lw=0.7)
    ax.text(3.42, 51, "chance", fontsize=6, color="#777777", ha="right")
    ax.legend(fontsize=6.5, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.14))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "orientation_per_relation.pdf"))
    fig.savefig(os.path.join(FIGDIR, "orientation_per_relation.png"), dpi=300)
    plt.close(fig)
    print()
    print("wrote paper/fig/orientation_per_relation.pdf/.png")

    # =====================================================================
    # FIGURE 2: facing-family self-consistency across conditions
    # =====================================================================
    with open(os.path.join(RESULTS, "consistency_stats_all.json"), encoding="utf-8") as f:
        cstats = json.load(f)["stats"]
    ff = {k: v["FF"] for k, v in cstats.items()}
    order = ["7B_zero_shot", "LM_only_LoRA", "hardneg_LoRA", "projector_LoRA", "vision_proj_LoRA"]
    labels = ["7B zero-shot", "LM-only LoRA", "HardNeg LoRA", "Projector LoRA", "Vision+Proj LoRA"]
    cons = [100.0 * ff[k]["cons"] / ff[k]["n"] for k in order]
    contra = [100.0 * ff[k]["contra"] / ff[k]["n"] for k in order]
    x2 = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(4.6, 2.6), dpi=300)
    b1 = ax.bar(x2, cons, 0.55, label="consistent", color="#2e6f40")
    b2 = ax.bar(x2, contra, 0.55, bottom=cons, label="self-contradictory", color="#b23a3a")
    for b, cval in zip(b1, cons):
        ax.annotate("%.0f%%" % cval, (b.get_x() + b.get_width() / 2, cval / 2),
                    ha="center", fontsize=7, color="white", weight="bold")
    ax.set_xticks(x2)
    ax.set_xticklabels(labels, fontsize=6.5, rotation=14, ha="right")
    ax.set_ylabel("facing-pair verdicts (%)", fontsize=7)
    ax.set_ylim(0, 100)
    ax.axhline(50, color="#999999", ls="--", lw=0.7)
    ax.text(4.3, 51, "chance", fontsize=6, color="#777777", ha="right")
    ax.legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.1), ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "consistency_facing.pdf"))
    fig.savefig(os.path.join(FIGDIR, "consistency_facing.png"), dpi=300)
    plt.close(fig)
    print("wrote paper/fig/consistency_facing.pdf/.png")

    # =====================================================================
    # FIGURE 3 + appendix tables: SITE (from zeroshot predictions CSV)
    # =====================================================================
    site_csv = os.path.join(RESULTS, "site", "zeroshot_7b_predictions.csv")
    with open(site_csv, newline="", encoding="utf-8") as f:
        srows = list(csv.DictReader(f))

    def site_acc(rows):
        n = len(rows)
        c = sum(1 for r in rows if str(r.get("correct")).strip() == "1")
        num = sum((1 if str(r.get("correct")).strip() == "1" else 0)
                  - 1.0 / float(r["n_options"]) for r in rows)
        denom = sum(1.0 - 1.0 / float(r["n_options"]) for r in rows)
        caa = 100.0 * num / denom if denom else float("nan")
        return c, n, caa

    def subset_rows(tag):
        return [r for r in srows if tag in (r.get("subset") or "").split(",")]

    subsets = {}
    for r in srows:
        subsets.setdefault(r["subset"], []).append(r)
    print()
    print("SITE audit (computed from zeroshot_7b_predictions.csv; canonical vs frozen protocol):")
    for name in ["primary", "secondary", "exploratory"]:
        rows = subset_rows(name)
        c, n, caa = site_acc(rows)
        print("  {:10s} n={:5d} raw={:6.1f}%  CAA={:6.1f}%".format(name, n, pct(c, n), caa))
    allrows = srows
    c, n, caa = site_acc(allrows)
    print("  {:10s} n={:5d} raw={:6.1f}%  CAA={:6.1f}%".format("all", n, pct(c, n), caa))

    # by modality
    mods = {}
    for r in srows:
        mods.setdefault(r["modality"], []).append(r)
    for m, rows in sorted(mods.items()):
        c, n, caa = site_acc(rows)
        print("  {:12s} n={:5d} raw={:6.1f}%  CAA={:6.1f}%".format("mod:" + m, n, pct(c, n), caa))

    # by source (n>=30) and by category (secondary subset)
    srcs = {}
    for r in srows:
        srcs.setdefault(r["source_dataset"], []).append(r)
    print()
    print("  by source (n>=30):")
    src_rows = []
    for s, rows in srcs.items():
        if len(rows) >= 30:
            c, n, caa = site_acc(rows)
            src_rows.append((s, n, pct(c, n), caa))
    src_rows.sort(key=lambda t: -t[2])
    for s, n, raw, caa in src_rows:
        print("    {:22s} n={:4d} raw={:6.1f}% CAA={:6.1f}%".format(s, n, raw, caa))

    print()
    print("  secondary subset (n=%d) by official category:" % len(subset_rows("secondary")))
    cats = {}
    for r in subset_rows("secondary"):
        cats.setdefault(r["category"], []).append(r)
    for cat, rows in sorted(cats.items(), key=lambda kv: -len(kv[1])):
        c, n, caa = site_acc(rows)
        print("    {:42s} n={:4d} raw={:6.1f}% CAA={:6.1f}%".format(cat, n, pct(c, n), caa))

    print()
    print("  secondary subset (n=%d) top source datasets:" % len(subset_rows("secondary")))
    sec_srcs = {}
    for r in subset_rows("secondary"):
        sec_srcs.setdefault(r["source_dataset"], []).append(r)
    for s, rows in sorted(sec_srcs.items(), key=lambda kv: -len(kv[1]))[:20]:
        c, n, caa = site_acc(rows)
        print("    {:24s} n={:4d} raw={:6.1f}% CAA={:6.1f}%".format(s, n, pct(c, n), caa))

    # ---- SITE figure ----
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3), dpi=300)
    ax = axes[0]
    labels3 = ["all images", "primary\n(spatial rel.)", "secondary\n(orientation kw)"]
    rawv = []
    caav = []
    for tag in ["all", "primary", "secondary"]:
        rows = srows if tag == "all" else subset_rows(tag)
        c, n, caa = site_acc(rows)
        rawv.append(pct(c, n))
        caav.append(caa)
    x3 = np.arange(3)
    ax.bar(x3 - 0.2, rawv, 0.4, label="raw accuracy", color="#4c6bb4")
    ax.bar(x3 + 0.2, caav, 0.4, label="CAA", color="#e0a63c")
    for i in range(3):
        ax.annotate("n=%d" % (len(srows) if i == 0 else len(subset_rows(["", "primary", "secondary"][i]))),
                    (x3[i], max(rawv[i], caav[i]) + 2), ha="center", fontsize=6.5, color="#444444")
    ax.set_xticks(x3)
    ax.set_xticklabels(labels3, fontsize=6.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("accuracy (%)", fontsize=7)
    ax.axhline(50, color="#999999", ls="--", lw=0.7)
    ax.legend(fontsize=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.set_title("(a) subset results", fontsize=8)

    ax = axes[1]
    srt = sorted(src_rows, key=lambda t: t[3])
    names = [t[0] for t in srt]
    vals = [t[3] for t in srt]
    ax.barh(np.arange(len(names)), vals, 0.7, color="#2e6f40")
    ax.axvline(0, color="#999999", lw=0.7)
    ax.set_yticks(np.arange(len(names)))
    ax.set_yticklabels(names, fontsize=5.6)
    ax.set_xlabel("CAA (%)", fontsize=7)
    ax.set_xlim(-15, 100)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.set_title("(b) by source dataset (CAA)", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "site_validation.pdf"))
    fig.savefig(os.path.join(FIGDIR, "site_validation.png"), dpi=300)
    plt.close(fig)
    print("wrote paper/fig/site_validation.pdf/.png")

    # =====================================================================
    # Failure-grid figure: crop top rows of representative_failures.png
    # =====================================================================
    from PIL import Image
    src = os.path.join(ROOT, "figures", "representative_failures.png")
    im = Image.open(src)
    # separators detected at y ~ 0,472,1008,1528,2056,2584 -> rows: 0-472, 472-1008, ...
    # take first 3 rows (2 cols? grid is 3 cols x 5 rows); crop rows 0..1528 full width
    crop = im.crop((0, 0, im.width, 1528))
    crop.save(os.path.join(FIGDIR, "representative_failures.png"), optimize=True)
    print("wrote paper/fig/representative_failures.png (rows 1-3 of the annotated grid)")


if __name__ == "__main__":
    main()
