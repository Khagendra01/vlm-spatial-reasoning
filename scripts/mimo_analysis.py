# -*- coding: utf-8 -*-
"""
Paper-ready analysis of the MiMo-V2.5 zero-shot VSR run.

Reads results/mimo/mimo_v25_zeroshot_predictions.csv (+ the consistency run)
and computes, with the SAME definitions as the canonical pipeline:

  1. Table-1-style row: overall + family accuracies with Wilson 95% CIs
     (family map identical to scripts/run_7b_pipeline.py; Wilson per the
     paper's declared methodology)
  2. Orientation per-relation accuracies (facing / facing away / parallel /
     perpendicular)
  3. Clean-label subsets (full 137 / -questionable 132 / clear 124 /
     strict 107) using the FROZEN first-annotator exclusion masks from
     results/orientation_persistent_annotations.csv
  4. Consistency stats from the complementary-statement run, in the same
     schema as consistency_stats_*.json

Writes:
  results/mimo/mimo_vsr_summary.json
  results/mimo/mimo_vsr_tables.md   (ready to paste into the paper)

Usage:  python scripts/mimo_analysis.py [--predictions results/mimo/mimo_v25_zeroshot_predictions.csv]
"""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MIMO = RESULTS / "mimo"

ORIENT_RELS = {"facing", "facing away from", "parallel to", "perpendicular to"}

RELATION_FAMILIES = {
    "horizontal": ["left of", "right of", "at the left side of", "at the right side of",
                   "at the side of", "beside", "next to", "alongside", "across from"],
    "vertical": ["above", "below", "over", "under", "beneath", "on top of"],
    "depth": ["in front of", "behind", "at the back of", "ahead of"],
    "orientation": ["facing", "facing away from", "parallel to", "perpendicular to"],
    "containment": ["in", "inside", "contains", "within", "enclosed by"],
    "proximity": ["near", "far from", "far away from", "close to", "away from"],
    "topology_contact": ["touching", "on", "at", "at the edge of", "against",
                         "attached to", "connected to", "detached from"],
    "compositional": ["part of", "has as a part", "consists of", "surrounding",
                      "in the middle of", "among"],
}
FAM_OF = {rel: fam for fam, rels in RELATION_FAMILIES.items() for rel in rels}

# frozen first-annotator exclusion masks (exactly as clean_label_orientation.py)
MODES_Q = {"annotation_questionable"}
MODES_CLEAR = MODES_Q | {"camera_viewpoint_ambiguity"}
MODES_STRICT = (MODES_CLEAR | {"intrinsic_orientation_ambiguous",
                               "front_back_object_ambiguous",
                               "small_occluded_object",
                               "subject_reference_inversion",
                               "parallel_perpendicular_geometry"})


def wilson(x, n, z=1.96):
    if n == 0:
        return None, None
    p = x / n
    center = (x + z * z / 2) / (n + z * z)
    half = z * math.sqrt(n) / (n + z * z) * math.sqrt(p * (1 - p) + z * z / (4 * n))
    return center - half, center + half


def load_preds(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_masks():
    ann = {}
    with open(RESULTS / "orientation_persistent_annotations.csv",
              newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ann[int(r["id"])] = r["annotation"]
    return {
        "full": set(),
        "minus_questionable": {i for i, a in ann.items() if a in MODES_Q},
        "clear": {i for i, a in ann.items() if a in MODES_CLEAR},
        "strict": {i for i, a in ann.items() if a in MODES_STRICT},
    }


def acc(rows):
    n = len(rows)
    if n == 0:
        return None, 0, 0
    c = sum(1 for r in rows if r["correct"] == "True")
    return c, c / n, n


def pct(x, n):
    return 100.0 * x / n if n else float("nan")


def analyze_consistency(orig_csv, flip_csv):
    orig = {}
    with open(orig_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["prediction"] in ("True", "False"):
                orig[int(row["id"])] = (row["prediction"] == "True")
    fam_stats = defaultdict(lambda: {"n": 0, "orig_acc": 0, "flip_acc": 0,
                                     "consistent": 0, "contradiction": 0,
                                     "both_correct": 0, "both_wrong": 0,
                                     "flip_na": 0, "orig_na": 0})
    with open(flip_csv, newline="", encoding="utf-8") as f:
        for fl in csv.DictReader(f):
            st = fam_stats[fl["family"]]
            st["n"] += 1
            o = orig.get(int(fl["orig_idx"]))
            fp = fl["prediction"]
            if fp in ("True", "False"):
                fp = fp == "True"
            else:
                fp = None
            flip_label = fl["ground_truth"] == "True"
            if o is None:
                st["orig_na"] += 1
            if fp is None:
                st["flip_na"] += 1
            if o is not None and fp is not None:
                if o == (fl["ground_truth"] == "True"):
                    st["orig_acc"] += 1
                if fp == flip_label:
                    st["flip_acc"] += 1
                if fp == (not o):
                    st["consistent"] += 1
                if fp == o:
                    st["contradiction"] += 1
                if o == flip_label and fp == flip_label:
                    st["both_correct"] += 1
                if o != flip_label and fp != flip_label:
                    st["both_wrong"] += 1
    return {k: dict(v) for k, v in fam_stats.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions",
                    default=str(MIMO / "mimo_v25_zeroshot_predictions.csv"))
    ap.add_argument("--consistency-flips",
                    default=str(MIMO / "consistency_flips_mimo.csv"))
    args = ap.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        print(f"no predictions yet at {pred_path} — nothing to analyze "
              "(no fabricated numbers).")
        return
    rows = load_preds(pred_path)
    masks = read_masks()
    by_id = {int(r["id"]): r for r in rows}

    # ---- 1. Table-1-style row + family table ----
    fam_rows = {}
    for fam in ["horizontal", "vertical", "depth", "orientation", "containment",
                "proximity", "topology_contact", "compositional"]:
        sub = [r for r in rows if FAM_OF.get(r["relation"]) == fam]
        c, a, n = acc(sub)
        lo, hi = wilson(c, n)
        fam_rows[fam] = {"n": n, "correct": c,
                         "accuracy": round(a, 4) if a is not None else None,
                         "wilson95": [round(lo, 4), round(hi, 4)] if lo else None}
    c, a, n = acc(rows)
    lo, hi = wilson(c, n)
    overall = {"n": n, "correct": c, "accuracy": round(a, 4),
               "wilson95": [round(lo, 4), round(hi, 4)]}

    # ---- 2. orientation per-relation ----
    per_rel = {}
    for rel in ["facing", "facing away from", "parallel to", "perpendicular to"]:
        sub = [r for r in rows if r["relation"] == rel]
        c, a, n = acc(sub)
        lo, hi = wilson(c, n)
        per_rel[rel] = {"n": n, "correct": c,
                        "accuracy": round(a, 4) if a is not None else None,
                        "wilson95": [round(lo, 4), round(hi, 4)] if lo else None}

    # ---- 3. clean-label subsets (frozen masks) ----
    clean = {}
    for k, ex in masks.items():
        sub = [by_id[i] for i in sorted(by_id) if i not in ex
               and by_id[i]["relation"] in ORIENT_RELS]
        c, a, n = acc(sub)
        clean[k] = {"n": n, "accuracy": round(a, 4) if a is not None else None,
                    "correct": c}

    # ---- 4. consistency ----
    cons = None
    flip_path = Path(args.consistency_flips)
    if flip_path.exists() and pred_path.exists():
        cons = analyze_consistency(pred_path, flip_path)

    summary = {
        "model": "XiaomiMiMo/MiMo-V2.5 (zero-shot)",
        "prompt": "frozen VSR prompt (supplementary App. A)",
        "overall": overall,
        "by_family": fam_rows,
        "orientation_by_relation": per_rel,
        "clean_label_subsets": clean,
        "consistency": cons,
        "note": "additive evidence; canonical tables untouched. Wilson 95% CIs; "
                "perpendicular (n=12) and other small subsets are descriptive.",
    }
    (MIMO / "mimo_vsr_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    # ---- markdown tables for the paper ----
    lines = ["# MiMo-V2.5 zero-shot VSR (additive evidence)", ""]
    hdr = ["Condition", "Overall", "Orientation", "Depth", "Horizontal",
           "Containment", "Topology/contact"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    row = ["MiMo-V2.5 zero-shot",
           f"{pct(overall['correct'], overall['n']):.1f}",
           f"{pct(fam_rows['orientation']['correct'], fam_rows['orientation']['n']):.1f}",
           f"{pct(fam_rows['depth']['correct'], fam_rows['depth']['n']):.1f}",
           f"{pct(fam_rows['horizontal']['correct'], fam_rows['horizontal']['n']):.1f}",
           f"{pct(fam_rows['containment']['correct'], fam_rows['containment']['n']):.1f}",
           f"{pct(fam_rows['topology_contact']['correct'], fam_rows['topology_contact']['n']):.1f}"]
    lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("Orientation family: n="
                 f"{fam_rows['orientation']['n']} | "
                 "Wilson 95% CI "
                 f"[{100*fam_rows['orientation']['wilson95'][0]:.1f}, "
                 f"{100*fam_rows['orientation']['wilson95'][1]:.1f}]")
    lines.append("")
    lines.append("## Orientation per relation")
    lines.append("| relation | n | acc % | Wilson 95% |")
    lines.append("|---|---|---|---|")
    for rel, m in per_rel.items():
        ci = (f"[{100*m['wilson95'][0]:.1f}, {100*m['wilson95'][1]:.1f}]"
              if m["wilson95"] else "-")
        lines.append(f"| {rel} | {m['n']} | {100*m['accuracy']:.1f} | {ci} |")
    lines.append("")
    lines.append("## Clean-label subsets (frozen first-annotator masks)")
    lines.append("| subset | n | acc % |")
    lines.append("|---|---|---|")
    for k in ["full", "minus_questionable", "clear", "strict"]:
        lines.append(f"| {k} | {clean[k]['n']} | {100*clean[k]['accuracy']:.1f} |")
    lines.append("")
    if cons:
        lines.append("## Consistency (complementary statements)")
        lines.append("| family | n | orig acc % | flip acc % | consistent % | contradiction % |")
        lines.append("|---|---|---|---|---|---|")
        for fam in ["LR", "FB", "FF", "PP"]:
            s = cons.get(fam)
            if not s or s["n"] == 0:
                continue
            lines.append(
                f"| {fam} | {s['n']} | {100*s['orig_acc']/s['n']:.1f} | "
                f"{100*s['flip_acc']/s['n']:.1f} | "
                f"{100*s['consistent']/s['n']:.1f} | "
                f"{100*s['contradiction']/s['n']:.1f} |")
    (MIMO / "mimo_vsr_tables.md").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")

    print(f"overall   {pct(overall['correct'], overall['n']):.1f}% "
          f"({overall['correct']}/{overall['n']})")
    print(f"orient    {pct(fam_rows['orientation']['correct'], fam_rows['orientation']['n']):.1f}% "
          f"CI [{100*fam_rows['orientation']['wilson95'][0]:.1f}, "
          f"{100*fam_rows['orientation']['wilson95'][1]:.1f}]")
    for rel, m in per_rel.items():
        print(f"  {rel:18s} {100*m['accuracy']:.1f}% (n={m['n']})")
    print(f"clean     full={100*clean['full']['accuracy']:.1f}  "
          f"-q={100*clean['minus_questionable']['accuracy']:.1f}  "
          f"clear={100*clean['clear']['accuracy']:.1f}  "
          f"strict={100*clean['strict']['accuracy']:.1f}")
    print("wrote results/mimo/mimo_vsr_summary.json + mimo_vsr_tables.md")


if __name__ == "__main__":
    main()
