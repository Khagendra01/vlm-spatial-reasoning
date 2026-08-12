# Frozen prompts (verbatim from the MiMo protocol, supplementary App. A)

## VSR binary audit (vsr_2195.csv)

For each item, attach the image from `image_url` (or a local copy) and submit exactly one request. Answer with exactly one word:

```
Look at the image carefully.

Statement: "{statement}"

Is this statement true or false?

Answer with exactly one word: True or False.
```

`parsed_binary` must be exactly `True`, `False`, or `INVALID`. Any response that is not an unambiguous single verdict after the provider's documented normalization is `INVALID` and counts as wrong in aggregate reporting. Use the lowest available reasoning/thinking setting for the primary run and record it; freeze image detail/resolution and report it; record model id, evaluation date, and endpoint.

## Complementary consistency (consistency_pairs.csv)

Answer `statement_a` and `statement_b` of each pair in two independent requests (same image). Do not show the model the other statement. Consistency is computed later by comparing the two verdicts.

Families: FB=front/behind, LR=left/right, FF=facing/facing-away, PP=parallel/perpendicular (soft complement; do not pool with the strict families).
