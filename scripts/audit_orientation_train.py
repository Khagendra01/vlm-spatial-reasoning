"""
Audit orientation training examples before hard-negative construction.

Two-stage flagging:
  1. Heuristic: subject/object nouns with intrinsically ambiguous orientation
     (curated from the 48-case annotation notes).
  2. Model consensus: 7B General LoRA prediction disagrees with the label.

Output: results/orientation_train_audit.csv with flag reasons for manual review.
"""
import os, sys, json, csv, time, hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]

# Nouns whose intrinsic orientation is debatable (from annotation notes)
AMBIG_NOUNS = {
    "toilet", "laptop", "hair drier", "hairdryer", "teddy bear", "bed", "tv",
    "television", "banana", "bench", "chair", "couch", "sofa", "book", "cake",
    "backpack", "suitcase", "keyboard", "sink", "table", "desk", "plate",
    "bowl", "vase", "bottle", "cup", "glass", "umbrella", "clock",
    "cell phone", "phone", "mirror", "painting", "picture", "flag",
    "bench", "stool", "lamp", "ceiling fan", "kite", "snowboard",
}

def extract_subject_object(statement: str):
    low = statement.lower().rstrip(".")
    parts = low.split(" is ")
    if len(parts) < 2:
        return "", ""
    subj = parts[0]
    if subj.startswith("the "):
        subj = subj[4:]
    obj_part = parts[1]
    for rel in sorted(ORIENT, key=lambda r: -len(r)):
        idx = obj_part.find(rel)
        if idx >= 0:
            obj = obj_part[idx + len(rel):].strip()
            break
    else:
        obj = obj_part
    if obj.startswith("the "):
        obj = obj[4:]
    return subj.strip(), obj.strip()

def heuristic_flag(subj: str, obj: str):
    reasons = []
    for noun in AMBIG_NOUNS:
        if noun in subj or noun in obj:
            reasons.append(f"ambiguous_noun:{noun}")
    return reasons

def main():
    from datasets import load_dataset

    ds = load_dataset("cambridgeltl/vsr_random", split="train")
    records = []
    for idx, r in enumerate(ds):
        if r["relation"] not in ORIENT:
            continue
        subj, obj = extract_subject_object(r["caption"])
        reasons = heuristic_flag(subj, obj)
        records.append({
            "id": idx, "statement": r["caption"], "label": bool(r["label"]),
            "relation": r["relation"], "subject": subj, "object": obj,
            "image": r["image_link"], "heuristic_reasons": ";".join(reasons),
        })
    print(f"Orientation train pool: {len(records)}")
    print("Heuristic flags:", sum(1 for r in records if r["heuristic_reasons"]))

    # Save base audit (before model pass)
    base_path = "results/orientation_train_audit_base.csv"
    with open(base_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "statement", "relation", "label",
                                          "subject", "object", "image",
                                          "heuristic_reasons", "model_pred",
                                          "model_disagree", "final_status"])
        w.writeheader()
        for r in records:
            w.writerow({**r, "model_pred": "", "model_disagree": "",
                        "final_status": ""})
    print(f"Saved base audit: {base_path}")

if __name__ == "__main__":
    main()
