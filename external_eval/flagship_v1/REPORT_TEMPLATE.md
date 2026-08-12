# External model report: `{model_id}`

- `run_id`:
- provider:
- model identifier / version:
- evaluation date (UTC):
- endpoint / SDK version:
- reasoning or thinking setting:
- image detail / resolution setting:
- temperature / decoding setting:
- maximum output tokens:
- total requests and retries:
- total cost, if available:

## 1. Clean/ambiguous audit (137 items)

| quantity | value |
|---|---:|
| total items | 137 |
| valid CLEAN/AMBIGUOUS | |
| invalid | |
| CLEAN | |
| AMBIGUOUS | |
| parser-valid rate | |

Report the clean/ambiguous output distribution and invalid-output policy. This
is an audit-label distribution, not statement accuracy.

## 2. Clean/ambiguous results by relation

| relation | n | CLEAN | AMBIGUOUS | INVALID |
|---|---:|---:|---:|---:|
| facing | | | | |
| facing away from | | | | |
| parallel to | | | | |
| perpendicular to | | | | |

## 3. Failure taxonomy (48 items)

| taxonomy class | count |
|---|---:|
| clear_image_model_reasoning_failure | |
| camera_viewpoint_ambiguity | |
| parallel_perpendicular_geometry | |
| annotation_questionable | |
| intrinsic_orientation_ambiguous | |
| front_back_object_ambiguous | |
| small_occluded_object | |
| subject_reference_inversion | |
| INVALID | |

Report the full class distribution, not only the modal class. A collapsed
distribution is a result and must be disclosed.

## 4. Per-item artifacts

Include the completed CSVs, raw responses, parser version, and a SHA-256 hash
of each result file. Preserve provider errors and retries separately from
model outputs.

## 5. Interpretation guardrails

- This is a model-generated audit of examples previously selected as an audit
  set; it is not independent human agreement.
- Do not convert the model's taxonomy labels into ground truth.
- Compare models using identical item IDs, prompts, parser rules, and output
  accounting.
- State whether the result was primary low/no reasoning or a sensitivity run.
