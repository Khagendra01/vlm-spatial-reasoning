# CSV schema

## Input sheets

`orientation_137.csv` columns:

`item_id,relation,statement,image_file`

`taxonomy_48.csv` columns:

`item_id,relation,statement,image_file`

The `image_file` path is relative to this folder. Input sheets contain no
ground-truth answer or previous annotation.

## Result sheets

`results_template.csv` stores one row per binary request. `parsed_binary` must
be one of `TRUE`, `FALSE`, or `INVALID`.

`taxonomy_results_template.csv` stores one row per taxonomy request.
`parsed_taxonomy` must be one of the eight identifiers in `prompts.md` or
`INVALID`.

`raw_response` is required even when parsing succeeds. `invalid_reason` is
required for `INVALID` rows and empty otherwise. `run_id` distinguishes model,
provider-setting, and reasoning-sensitivity runs.
