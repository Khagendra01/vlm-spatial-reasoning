# -*- coding: utf-8 -*-
"""
Export BLIND inter-annotator-agreement (IAA) annotation sheets.

Outputs (committed):
  results/iaa/blind_clean_label_sheet.csv    137 orientation test examples
  results/iaa/blind_failure_taxonomy_sheet.csv  48 persistent-failure examples
  results/iaa/README.md                       rating protocol for the second rater

Both sheets are BLIND: they contain only id, relation, statement, and the
image (local path + source URL). They intentionally DO NOT contain ground
truth, model predictions, the first annotator's flags, taxonomy labels,
wrong counts, or notes. The second rater must rate the examples from the
image + statement alone.

Images are downloaded to results/iaa/images/{id}.jpg (gitignored); if a
download fails the sheet still carries the source URL and the annotation
tool (scripts/iaa_tool.py) falls back to it.

Usage:  python scripts/export_iaa_sheets.py
"""
import csv
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
IAA = RESULTS / "iaa"
IMGDIR = IAA / "images"

# Canonical prediction CSV used as the source of ids/statements/images for the
# orientation test set (identical ids/statements across all canonical CSVs).
CANON_PREDS = RESULTS / "smolvlm2_baseline_2195_20260808_214536.csv"
# First-annotator audit file (used ONLY to select the 48 cases; its label and
# annotation columns are never exported to the blind sheets).
RATER1 = RESULTS / "orientation_persistent_annotations.csv"

ORIENT_RELS = {"facing", "facing away from", "parallel to", "perpendicular to"}

# The eight-class taxonomy, exactly as used in the first annotator's audit
# (results/orientation_persistent_annotations.csv) and the supplementary
# (Table: Persistent-failure taxonomy). Order as in the supplementary table.
TAXONOMY_CLASSES = [
    "clear_image_model_reasoning_failure",
    "camera_viewpoint_ambiguity",
    "parallel_perpendicular_geometry",
    "annotation_questionable",
    "intrinsic_orientation_ambiguous",
    "front_back_object_ambiguous",
    "small_occluded_object",
    "subject_reference_inversion",
]

# Binary flag for the clean-label audit, as derived from the first annotator's
# taxonomy in scripts/clean_label_orientation.py: only
# "clear_image_model_reasoning_failure" is kept in all clean subsets, i.e.
# counts as "clean"; every other class counts as "ambiguous".
CLEAN_CLASS = "clear_image_model_reasoning_failure"


def main():
    IAA.mkdir(parents=True, exist_ok=True)
    IMGDIR.mkdir(parents=True, exist_ok=True)

    # ---- load the 137 orientation examples from the canonical CSV ----
    rows = {}
    with open(CANON_PREDS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("relation") or "").strip() in ORIENT_RELS:
                rows[int(r["id"])] = r
    assert len(rows) == 137, f"expected 137 orientation examples, got {len(rows)}"

    # ---- select the 48 audited cases from the first annotator's file ----
    audited_ids = set()
    with open(RATER1, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            audited_ids.add(int(r["id"]))
    assert len(audited_ids) == 48, f"expected 48 audited cases, got {len(audited_ids)}"
    missing = audited_ids - set(rows)
    if missing:
        sys.exit(f"ERROR: audited ids missing from canonical CSV: {sorted(missing)}")

    # ---- download images (local copy; remote URL retained as fallback) ----
    def fetch_image(rid, url):
        p = IMGDIR / f"id{rid}.jpg"
        if p.exists() and p.stat().st_size > 0:
            return str(p.relative_to(ROOT))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(p, "wb") as f:
                f.write(resp.read())
            return str(p.relative_to(ROOT))
        except Exception as e:
            print(f"  WARN: image download failed id={rid} {url}: {e}")
            return ""

    print(f"Downloading images for {len(rows)} orientation examples ...")
    for rid in sorted(rows):
        rows[rid]["_img_local"] = fetch_image(rid, rows[rid]["image_url"])
    ok = sum(1 for r in rows.values() if r["_img_local"])
    print(f"  {ok}/{len(rows)} images available locally")

    # ---- sheet 1: blind clean-label sheet (137 examples) ----
    sheet1 = IAA / "blind_clean_label_sheet.csv"
    with open(sheet1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "relation", "statement", "image_path", "image_url",
                    "rating_clean", "notes"])
        for rid in sorted(rows):
            r = rows[rid]
            w.writerow([r["id"], r["relation"], r["statement"],
                        r["_img_local"], r["image_url"], "", ""])
    print(f"wrote {sheet1.relative_to(ROOT)}  ({len(rows)} rows)")

    # ---- sheet 2: blind failure-taxonomy sheet (48 examples) ----
    sheet2 = IAA / "blind_failure_taxonomy_sheet.csv"
    with open(sheet2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "relation", "statement", "image_path", "image_url",
                    "class", "notes"])
        for rid in sorted(audited_ids):
            r = rows[rid]
            w.writerow([r["id"], r["relation"], r["statement"],
                        r["_img_local"], r["image_url"], "", ""])
    print(f"wrote {sheet2.relative_to(ROOT)}  ({len(audited_ids)} rows)")

    # ---- rating protocol readme (for the second, independent human rater) ----
    readme = IAA / "README.md"
    readme.write_text(f"""# Blind IAA Rating Protocol (second, independent human rater)

You are rating {len(rows)} VSR test examples for a reliability study. You must
rate **independently**: do not discuss these examples with, or look at the
labels/annotations of, the first annotator (files
`results/orientation_persistent_annotations.csv`,
`results/failure_annotations.csv`), and do not look at any model predictions.
The sheets contain only the example id, relation, statement, and image; the
ground truth and model outputs are withheld on purpose.

## Sheet 1: `blind_clean_label_sheet.csv` (n={len(rows)})

For each example decide whether the image + statement is **unambiguous** for a
human judge:

- `clean`      — a human can confidently decide whether the statement is true
                 or false from the image alone (even if the answer is hard).
- `ambiguous`  — the statement cannot be confidently judged from the image:
                 annotation seems wrong, camera viewpoint hides the relevant
                 geometry, the objects have no meaningful orientation, the
                 reference object is not clearly visible, etc.

Fill the `rating_clean` column with exactly one of these two strings.
`notes` is optional free text.

## Sheet 2: `blind_failure_taxonomy_sheet.csv` (n={len(audited_ids)})

For each example, choose exactly one class from the eight below (fill the
`class` column with the exact string):

| class | meaning |
|---|---|
| `clear_image_model_reasoning_failure` | image is visually clear and the statement is judgeable; a failure to answer correctly is a reasoning failure, not an image/annotation problem |
| `camera_viewpoint_ambiguity` | camera angle/depth separation makes the relation hard or impossible to judge |
| `parallel_perpendicular_geometry` | requires geometric assessment of alignment between objects |
| `annotation_questionable` | the claimed truth value of the statement seems wrong or undecidable given the image |
| `intrinsic_orientation_ambiguous` | the subject object has no meaningful intrinsic orientation (furniture, produce, etc.) |
| `front_back_object_ambiguous` | the reference object is barely visible / its position must be inferred |
| `small_occluded_object` | the relevant object is small or partially occluded |
| `subject_reference_inversion` | the statement's subject/reference roles are easy to confuse |

## Instructions for everyone involved

- Rate ALL examples in both sheets (no skipping).
- Do not edit the `id`, `relation`, `statement`, `image_path`, `image_url`
  columns.
- When done, save a copy of each sheet as
  `results/iaa/rater2_clean_labels.csv` and
  `results/iaa/rater2_taxonomy.csv` (same columns; your ratings in the
  `rating_clean` / `class` columns), then run:
  `python scripts/compute_iaa.py`
  to obtain Cohen's kappa (clean/ambiguous) and Krippendorff's alpha
  (taxonomy) with bootstrap 95% CIs.
""")
    print(f"wrote {readme.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
