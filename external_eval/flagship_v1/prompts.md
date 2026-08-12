# Frozen prompts

## Binary orientation audit (`orientation_137.csv`)

Use the image and the supplied statement only.

```text
Look at the image carefully. Decide whether the statement is true or false
from the image alone. Answer with exactly one token: TRUE or FALSE.
Do not explain your answer. Do not use outside knowledge.
Statement: {statement}
```

The evaluator must preserve both the raw model response and a parser result:
`TRUE`, `FALSE`, or `INVALID`. Any response that is not an unambiguous exact
binary answer after the provider's documented whitespace/case normalization
is `INVALID` and counts as wrong in aggregate reporting.

## Failure taxonomy (`taxonomy_48.csv`)

Use the image and the supplied statement only. Select exactly one class from
the allowed list below. Return the class identifier exactly and nothing else.

```text
Inspect the image and statement. Choose the single best explanation for why
this example is a difficult or persistent failure case. Return exactly one
allowed class identifier and no explanation.

Statement: {statement}
Allowed classes:
- clear_image_model_reasoning_failure
- camera_viewpoint_ambiguity
- parallel_perpendicular_geometry
- annotation_questionable
- intrinsic_orientation_ambiguous
- front_back_object_ambiguous
- small_occluded_object
- subject_reference_inversion
```

Taxonomy outputs are parsed as `VALID` only when they exactly match one of the
eight identifiers. Otherwise record `INVALID`; never map a near match by
hand.

## Provider settings to freeze

The recommended primary run is the lowest available reasoning/thinking
setting, matching the MiMo run's thinking-disabled protocol as closely as the
provider permits. Record the exact setting. A separate higher-reasoning
sensitivity run may be performed on the 137-item sheet, but it must use a
different `run_id` and must not overwrite the primary results.
