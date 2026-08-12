"""
Clean-label robustness: orientation accuracy (all VSR conditions) on the
full test set vs clean subsets (annotation-questionable removed).

Exclusion sets (from the 48-annotation audit):
  questionable: annotation_questionable (5 ids)
  clear:        + camera_viewpoint_ambiguity (13 total)
  strict:       + intrinsic_orientation_ambiguous, front_back_object_ambiguous,
                 small_occluded_object, subject_reference_inversion,
                 parallel_perpendicular_geometry (30 total from the 137-example
                 orientation test set; resulting strict subset n=107)
"""
import os, sys, csv
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODES_Q = {"annotation_questionable"}
MODES_CLEAR = MODES_Q | {"camera_viewpoint_ambiguity"}
MODES_STRICT = (MODES_CLEAR | {"intrinsic_orientation_ambiguous",
                               "front_back_object_ambiguous",
                               "small_occluded_object",
                               "subject_reference_inversion",
                               "parallel_perpendicular_geometry"})

ann = {}
with open("results/orientation_persistent_annotations.csv") as f:
    for r in csv.DictReader(f):
        ann[int(r["id"])] = r["annotation"]

excl = {
    "full": set(),
    "minus_questionable": {i for i, a in ann.items() if a in MODES_Q},
    "clear": {i for i, a in ann.items() if a in MODES_CLEAR},
    "strict": {i for i, a in ann.items() if a in MODES_STRICT},
}

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
ORIENT = {"facing", "facing away from", "parallel to", "perpendicular to"}

print(f"{'condition':<26} {'full(137)':>10} {'-q(132)':>9} {'clear(124)':>11} {'strict(107)':>12}")
lines = ["# Clean-Label Orientation Robustness (VSR test)", "",
         "Full test (137) vs subsets with annotation-questionable / ambiguous examples removed.",
         "Exclusion sets from the 48-example manual audit (results/orientation_persistent_annotations.csv).",
         "", "| Condition | full (137) | âˆ’questionable (132) | clear (124) | strict (107) |", "|---|---|---|---|---|"]
for name, path in CONDS:
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows[int(r["id"])] = r
    cells = {}
    for k, ex in excl.items():
        sub = [rows[i] for i in rows if i not in ex and rows[i]["relation"] in ORIENT]
        n = len(sub)
        acc = sum(1 for r in sub if r["correct"] == "True") / n
        cells[k] = f"{acc:.3f} (n={n})"
        if k == "full":
            cells["full_n"] = n
    print(f"{name:<26} {cells['full']:>10} {cells['minus_questionable']:>9} {cells['clear']:>11} {cells['strict']:>12}")
    lines.append(f"| {name} | {cells['full']} | {cells['minus_questionable']} | {cells['clear']} | {cells['strict']} |")
open("results/tables/orientation_clean_label_table.md", "w").write("\n".join(lines) + "\n")
print("\nSaved results/tables/orientation_clean_label_table.md")
