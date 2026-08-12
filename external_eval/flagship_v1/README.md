# Flagship-model external evaluation package v1

This folder is a **blind, provider-neutral evaluation package** for testing
image-capable flagship models on the same orientation audit used for MiMo and
the independent human raters in this repository.

It contains:

- `orientation_137.csv`: all 137 VSR orientation examples. The model should
  judge whether the image/statement pair is `clean` or `ambiguous`, matching
  the human and MiMo audit protocol.
- `taxonomy_48.csv`: the 48 persistent-failure examples used for the
  eight-class failure taxonomy. The model should select one taxonomy class.
- `images/`: NOT committed (kept out of git to avoid repository bloat).
  The input CSVs reference files like `images/id3.jpg`; obtain them before
  running: fetch each `image_url` listed in
  `results/iaa/blind_clean_label_sheet.csv` / `blind_failure_taxonomy_sheet.csv`
  (COCO train2017) into `results/iaa/images/` (gitignored, kept local), or
  restore the package's own copy from any local checkout of the
  `external-eval/flagship-v1` release before the image purge (commit
  `a06cc49` tree). `MANIFEST.json` records the per-file SHA-256 hashes so a
  regenerated copy can be verified byte-for-byte.
- `prompts.md`: frozen prompts and exact output rules.
- `results_template.csv` and `taxonomy_results_template.csv`: append-only
  result formats for GPT, Gemini, or another vision model.
- `REPORT_TEMPLATE.md`: the report format expected after a model completes
  the two sheets.
- `MANIFEST.json`: item counts, source provenance, hashes, and version.

## Important blind-evaluation rules

Do not use model predictions, VSR ground-truth answers, or previous rater
labels while running the evaluation. The package intentionally exposes only
the image, relation, and statement. Run items one at a time and preserve the
raw response before parsing it. Invalid, empty, or non-conforming responses
must be recorded as invalid; never guess a label.

The 137-item sheet is the primary clean/ambiguous audit. The 48-item sheet is a
separate taxonomy audit of persistent failures. A model's taxonomy output is
not an answer-correctness judgment and must not be used to relabel the
clean/ambiguous sheet. A prior TRUE/FALSE run is a different exploratory task
and is not comparable to the human/MiMo clean-label audit.

## Suggested model run

For each provider/model, record the exact model identifier, API date, endpoint,
reasoning/thinking setting, image-detail setting, temperature or equivalent,
maximum output tokens, system/developer prompt, retry policy, raw response,
parsed response, and invalid-output reason. Use the same frozen prompt for all
items within a run. If a provider cannot provide deterministic decoding,
report that limitation rather than silently presenting the run as greedy.

The package does not contain API keys and should be safe to point at from a
separate GPT/Gemini evaluation script.
