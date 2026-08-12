# External model report: `GPT-5.6 Sol`

- `run_id`: `gpt-5.6-sol-interactive-vision-20260812`
- provider: OpenAI
- model identifier / version: GPT-5.6 Sol
- evaluation date (UTC): 2026-08-12T18:57:18Z
- endpoint / SDK version: ChatGPT interactive conversation (not an API/SDK run)
- reasoning or thinking setting: interactive reasoning model; not a frozen low/no-reasoning setting
- image detail / resolution setting: native uploaded JPGs; reviewed in visual batches with individual zoom rechecks for ambiguous cases
- temperature / decoding setting: not exposed in ChatGPT
- maximum output tokens: not applicable to per-item interactive review
- total requests and retries: not comparable to provider API requests
- total cost: unavailable

> **Protocol note:** This is a blind exploratory vision audit: no ground truth, prior model predictions, or prior rater labels were consulted. However, the repo's strict benchmark protocol says items should be run one at a time. This interactive pass used contact-sheet batches for efficiency and therefore should **not** be treated as a protocol-valid apples-to-apples provider benchmark.

## 1. Binary audit (137 items)

| quantity | value |
|---|---:|
| total items | 137 |
| valid TRUE/FALSE | 137 |
| invalid | 0 |
| TRUE | 77 |
| FALSE | 60 |
| parser-valid rate | 100% |

These are output counts only, **not accuracy**, because no ground-truth comparison was performed.

## 2. Binary results by relation

| relation | n | TRUE | FALSE | INVALID |
|---|---:|---:|---:|---:|
| facing | 64 | 40 | 24 | 0 |
| facing away from | 39 | 19 | 20 | 0 |
| parallel to | 22 | 13 | 9 | 0 |
| perpendicular to | 12 | 5 | 7 | 0 |

## 3. Failure taxonomy (48 items)

| taxonomy class | count |
|---|---:|
| clear_image_model_reasoning_failure | 7 |
| camera_viewpoint_ambiguity | 3 |
| parallel_perpendicular_geometry | 13 |
| annotation_questionable | 5 |
| intrinsic_orientation_ambiguous | 3 |
| front_back_object_ambiguous | 6 |
| small_occluded_object | 6 |
| subject_reference_inversion | 5 |
| INVALID | 0 |

## 4. Per-item artifacts

- Binary CSV: `gpt56sol_orientation_137_results.csv`
  - SHA-256: `c87e20cd1499281f5e6b74b3e8491a0df7204bf577c592fbdcc0c8e315ba02e9`
- Taxonomy CSV: `gpt56sol_taxonomy_48_results.csv`
  - SHA-256: `e1fa16c708db2674e8831ef26eee84a66ba20e757888b8dcdc45e015fa15fc53`

## 5. Interpretation guardrails

- This is a model-generated audit, not independent human agreement.
- Taxonomy labels are not ground truth.
- No accuracy claim is made without a separately documented ground-truth comparison.
- For a publishable model comparison, rerun all 137 items independently with the repo's frozen prompt and fixed provider settings, one image per request.
