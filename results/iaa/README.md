# Blind IAA Rating Protocol (second, independent human rater)

You are rating 137 VSR test examples for a reliability study. You must
rate **independently**: do not discuss these examples with, or look at the
labels/annotations of, the first annotator (files
`results/orientation_persistent_annotations.csv`,
`results/failure_annotations.csv`), and do not look at any model predictions.
The sheets contain only the example id, relation, statement, and image; the
ground truth and model outputs are withheld on purpose.

## Sheet 1: `blind_clean_label_sheet.csv` (n=137)

For each example decide whether the image + statement is **unambiguous** for a
human judge:

- `clean`      � a human can confidently decide whether the statement is true
                 or false from the image alone (even if the answer is hard).
- `ambiguous`  � the statement cannot be confidently judged from the image:
                 annotation seems wrong, camera viewpoint hides the relevant
                 geometry, the objects have no meaningful orientation, the
                 reference object is not clearly visible, etc.

Fill the `rating_clean` column with exactly one of these two strings.
`notes` is optional free text.

## Sheet 2: `blind_failure_taxonomy_sheet.csv` (n=48)

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

## Recommended workflow: the auto-saving web server

Instead of editing the CSVs by hand, use the annotation server — every
rating click and note edit is saved instantly, and you can close the tab /
reboot and resume where you left off:

    python scripts/iaa_tool.py --port 5000
    # open http://127.0.0.1:5000

- Sheet 1 (`/sheet/clean`): 137 examples, binary clean/ambiguous flag.
- Sheet 2 (`/sheet/taxonomy`): 48 examples, eight-class taxonomy.
- Shortcuts: `1..N` select option, `n` next, `p` prev, `r` jump to next
  unrated. Notes autosave ~0.8 s after you stop typing.
- Outputs are written exactly where `scripts/compute_iaa.py` expects them
  (`results/iaa/rater2_clean_labels.csv`,
  `results/iaa/rater2_taxonomy.csv`), so when you are done simply run:
  `python scripts/compute_iaa.py`
