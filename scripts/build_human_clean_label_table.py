# -*- coding: utf-8 -*-
"""
VERSIONED clean-label orientation table derived from the HUMAN audit
(taxonomy pass on the 48 persistent failures, binary pass on all 137),
built with the SAME exclusion-mask methodology as the frozen first-annotator
table (scripts/clean_label_orientation.py).

The frozen LLM-derived table (results/tables/orientation_clean_label_table.md)
is NOT modified; this is a new, separately named artifact (guardrail: new
versioned file + logged change).

Masks:
  full           137
  human-Q         137 minus annotation_questionable        (from taxonomy pass)
  human-clear     ... minus + camera_viewpoint_ambiguity
  human-strict    ... minus + intrinsic/front_back/small_occluded/
                           subject_reference_inversion/parallel_perpendicular
  human-binary    137 minus the human's binary "ambiguous" flags

Usage:  python scripts/build_human_clean_label_table.py [--rater rater2|rater3]
Outputs (rater2, default; file names preserved for backward compatibility):
  results/tables/orientation_clean_label_table_human.md
  results/tables/orientation_clean_label_table_human.json
Outputs (rater3):
  results/tables/orientation_clean_label_table_human2.md
  results/tables/orientation_clean_label_table_human2.json
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

ORIENT = {"facing", "facing away from", "parallel to", "perpendicular to"}

MODES_Q = {"annotation_questionable"}
MODES_CLEAR = MODES_Q | {"camera_viewpoint_ambiguity"}
MODES_STRICT = (MODES_CLEAR | {"intrinsic_orientation_ambiguous",
                               "front_back_object_ambiguous",
                               "small_occluded_object",
                               "subject_reference_inversion",
                               "parallel_perpendicular_geometry"})

CONDS = [
    ("2B zero-shot", "results/smolvlm2_baseline_2195_20260808_214536.csv"),
    ("2B structured", "results/smolvlm2_structured_2195_20260808_225009.csv"),
    ("2B General LoRA", "results/general_lora_predictions_20260809_054915.csv"),
    ("2B Targeted LoRA", "results/targeted_lora_predictions_20260809_061231.csv"),
    ("7B zero-shot", "results/qwen2vl_7b_predictions_20260809_064919.csv"),
    ("7B General LoRA", "results/7B_general_lora_predictions_20260809_094930.csv"),
    ("7B Targeted LoRA", "results/7B_targeted_lora_predictions_20260809_095926.csv"),
    ("7B Hard-Neg LoRA", "results/7B_hardneg_lora_predictions_20260809_164619.csv"),
    ("7B Projector LoRA", "results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv"),
    ("7B Vision+Projector LoRA", "results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv"),
    ("MiMo-V2.5 zero-shot", "results/mimo/mimo_v25_zeroshot_predictions.csv"),
]


def load_csv_col(path, col):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["id"])] = r[col].strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater", choices=["rater2", "rater3"], default="rater2",
                    help="which blind human re-audit to use (default: rater2, "
                         "the first human re-audit; outputs keep the original "
                         "file names). rater3 writes *_human2.* files.")
    args = ap.parse_args()
    second = args.rater == "rater3"

    # human taxonomy pass (48) + human binary pass (137)
    taxo = load_csv_col(RESULTS / "iaa" / (args.rater + "_taxonomy.csv"), "class")
    binary = load_csv_col(RESULTS / "iaa" / (args.rater + "_clean_labels.csv"),
                          "rating_clean")

    excl = {
        "full": set(),
        "human_minus_q": {i for i, c in taxo.items() if c in MODES_Q},
        "human_clear": {i for i, c in taxo.items() if c in MODES_CLEAR},
        "human_strict": {i for i, c in taxo.items() if c in MODES_STRICT},
        "human_binary": {i for i, v in binary.items() if v == "ambiguous"},
    }

    table = {}
    for name, path in CONDS:
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        cells = {}
        for key, ex in excl.items():
            sub = [r for r in rows if r["relation"] in ORIENT
                   and int(r["id"]) not in ex]
            n = len(sub)
            c = sum(1 for r in sub if r["correct"] == "True")
            cells[key] = {"n": n, "accuracy": round(c / n, 4)}
        table[name] = cells

    suffix = "2" if second else ""
    tag = "rater3 (second human re-audit)" if second else "rater2 (first human re-audit)"

    lines = [
        f"# Clean-Label Orientation Robustness — HUMAN audit (versioned, additive; {tag})",
        "",
        "Exclusion masks derived from the HUMAN taxonomy pass (48 cases) and",
        "the HUMAN binary pass (137 cases). The frozen first-annotator (LLM)",
        "table is unchanged: results/tables/orientation_clean_label_table.md.",
        "",
        "| Condition | full (137) | -q | clear | strict | human-binary |",
        "|---|---|---|---|---|---|",
    ]
    for name, cells in table.items():
        lines.append(
            f"| {name} | {cells['full']['accuracy']:.3f} (n={cells['full']['n']}) | "
            f"{cells['human_minus_q']['accuracy']:.3f} (n={cells['human_minus_q']['n']}) | "
            f"{cells['human_clear']['accuracy']:.3f} (n={cells['human_clear']['n']}) | "
            f"{cells['human_strict']['accuracy']:.3f} (n={cells['human_strict']['n']}) | "
            f"{cells['human_binary']['accuracy']:.3f} (n={cells['human_binary']['n']}) |")

    out_md = RESULTS / "tables" / f"orientation_clean_label_table_human{suffix}.md"
    out_json = RESULTS / "tables" / f"orientation_clean_label_table_human{suffix}.json"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps({"note": "human-audit versioned table: " + tag,
                                    "exclusion_masks": {
                                        k: sorted(v) for k, v in excl.items()},
                                    "table": table}, indent=2), encoding="utf-8")
    print(f"wrote {out_md}")
    print(f"wrote {out_json}")
    print(f"{'condition':<24} {'full':>7} {'-q':>7} {'clear':>7} {'strict':>7} {'bin(75)':>8}")
    for name, cells in table.items():
        print(f"{name:<24} "
              f"{100*cells['full']['accuracy']:6.1f} "
              f"{100*cells['human_minus_q']['accuracy']:6.1f} "
              f"{100*cells['human_clear']['accuracy']:6.1f} "
              f"{100*cells['human_strict']['accuracy']:6.1f} "
              f"{100*cells['human_binary']['accuracy']:7.1f}")


if __name__ == "__main__":
    main()
