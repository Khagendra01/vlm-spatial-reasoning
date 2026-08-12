# -*- coding: utf-8 -*-
"""
Annotator-dependence of the clean-label sensitivity analysis (additive IAA
evidence, clearly NOT a replacement for the frozen first-annotator table).

After the second blind annotator completed the 137-example clean/ambiguous
rating, this script recomputes orientation accuracy under three exclusion
masks in addition to the frozen one:

  r1-strict (107)  frozen first-annotator exclusion sets
                   (scripts/clean_label_orientation.py, MODES_STRICT)
  r2-ambiguous (75) second annotator's own ambiguous flags
  consensus (62)   union of both annotators' exclusions

Outputs:
  results/iaa/consensus_subsets.json
  results/iaa/consensus_subsets.md

Usage:  python scripts/iaa_consensus_subsets.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
IAA = RESULTS / "iaa"

ORIENT = {"facing", "facing away from", "parallel to", "perpendicular to"}

MODES_STRICT = {"annotation_questionable", "camera_viewpoint_ambiguity",
                "intrinsic_orientation_ambiguous", "front_back_object_ambiguous",
                "small_occluded_object", "subject_reference_inversion",
                "parallel_perpendicular_geometry"}

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
]


def load_ann(path, col):
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[int(r["id"])] = r[col].strip()
    return out


def main():
    r1 = load_ann(RESULTS / "orientation_persistent_annotations.csv", "annotation")
    r2 = load_ann(IAA / "rater2_clean_labels.csv", "rating_clean")

    m_r1 = {i for i, a in r1.items() if a in MODES_STRICT}
    m_r2 = {i for i, v in r2.items() if v == "ambiguous"}
    masks = {"full": set(), "r1_strict": m_r1, "r2_ambiguous": m_r2,
             "consensus": m_r1 | m_r2}

    table = {}
    for name, path in CONDS:
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        row = {}
        for key, ex in masks.items():
            sub = [r for r in rows if r["relation"] in ORIENT
                   and int(r["id"]) not in ex]
            n = len(sub)
            c = sum(1 for r in sub if r["correct"] == "True")
            row[key] = {"n": n, "accuracy": round(c / n, 4)}
        table[name] = row

    out = {"note": ("Additive annotator-dependence analysis; the frozen "
                    "first-annotator table (results/tables/"
                    "orientation_clean_label_table.md) is NOT modified."),
           "mask_sizes": {k: 137 - len(v) for k, v in masks.items()},
           "conditions": table}
    (IAA / "consensus_subsets.json").write_text(json.dumps(out, indent=2),
                                                encoding="utf-8")

    lines = ["# Clean-label sensitivity: annotator dependence (additive)",
             "",
             "Frozen first-annotator table is retained unchanged. The second",
             "blind annotator flagged more examples ambiguous; accuracies under",
             "each mask are shown below.",
             "",
             "| condition | full (137) | r1-strict (107) | r2-ambiguous (75) | "
             "consensus (62) |",
             "|---|---|---|---|---|"]
    for name, row in table.items():
        lines.append(
            f"| {name} | {100*row['full']['accuracy']:.1f} | "
            f"{100*row['r1_strict']['accuracy']:.1f} | "
            f"{100*row['r2_ambiguous']['accuracy']:.1f} | "
            f"{100*row['consensus']['accuracy']:.1f} |")
    (IAA / "consensus_subsets.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    print("wrote results/iaa/consensus_subsets.json + consensus_subsets.md")
    for name, row in table.items():
        print(f"  {name:<24} full={100*row['full']['accuracy']:.1f}  "
              f"r1={100*row['r1_strict']['accuracy']:.1f}  "
              f"r2={100*row['r2_ambiguous']['accuracy']:.1f}  "
              f"cons={100*row['consensus']['accuracy']:.1f}")


if __name__ == "__main__":
    main()
