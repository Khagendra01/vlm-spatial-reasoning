# Follow-up correction prompt

Please rerun **only the 137-item orientation audit**. Your previous 48-item
taxonomy output was correctly formatted and should be retained unchanged.

The previous 137-item run answered whether each statement was TRUE/FALSE. That
is a different task from the human and MiMo audit. The required output for the
137-item audit is whether the image/statement pair is **CLEAN** or
**AMBIGUOUS**.

Use `orientation_137.csv` and the corresponding image in its `image_file`
column. Process exactly one image/question per request; do not use contact
sheets or batch multiple examples together. Do not consult ground truth,
previous model predictions, or human labels.

For each item, return exactly one token:

```text
CLEAN
```

or

```text
AMBIGUOUS
```

Use `AMBIGUOUS` when a human cannot confidently judge the statement from the
image alone, including hidden viewpoint/depth, an unclear or occluded object,
an object without meaningful intrinsic orientation, or a questionable
annotation. A statement may be false and still be `CLEAN` if its truth value
is visually judgeable.

Preserve the raw response and write a new CSV with these columns:

```text
run_id,model_id,provider,eval_date_utc,item_id,relation,raw_response,parsed_clean,invalid_reason,latency_ms
```

`parsed_clean` must be exactly `CLEAN`, `AMBIGUOUS`, or `INVALID`. Do not
overwrite the previous TRUE/FALSE CSV; save the corrected run under a new
filename such as:

- `gpt56sol_clean_ambiguity_137_results.csv`
- `gemini_clean_ambiguity_137_results.csv`

The existing 48-item taxonomy CSVs are already valid. No taxonomy rerun is
needed unless you want a separate one-item-per-request reproducibility pass.
