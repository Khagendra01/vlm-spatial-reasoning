# External VSR report: `{model_id}`

- run_id, model id/version, provider, eval date (UTC), endpoint
- reasoning/thinking setting, image-detail setting, temperature, max output tokens, retries, cost

## 1. VSR 2,195

- overall accuracy (with 95% Wilson CI) **after** scoring against the VSR ground truth on the validator's side; report invalid outputs separately and count them wrong
- per relation family: orientation, depth, horizontal, containment, topology/contact
- per orientation relation: facing (n=64), facing away from (n=39), parallel to (n=22), perpendicular to (n=12)

## 2. Consistency (verdicts only; no scoring against ground truth)

- facing/facing-away (FF): consistency %, both-True %, both-False % (n=103)
- front/behind (FB, n=314) and left/right (LR, n=245): consistency %
- parallel/perpendicular (PP, n=34): report separately, soft complement

## 3. Guardrails
- identical prompt/parser/accounting as MiMo (App. A); different provider settings must be disclosed, not silently equalized
- no ground truth, predictions, or rater labels were included in the input sheets
