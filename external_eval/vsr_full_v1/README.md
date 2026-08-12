# Full VSR blind evaluation package (2,195 items)

Blind, provider-neutral replay of the full VSR random-split test set for external vision models, mirroring the frozen MiMo protocol.

- `vsr_2195.csv`: item_id, relation, statement, image_url (COCO train2017)
- `consistency_pairs.csv`: 696 complementary pairs (FB=314, LR=245, FF=103, PP=34)
- `prompts.md`: frozen prompt verbatim (App. A) + run rules
- `results_template.csv`, `consistency_results_template.csv`: append one row per request
- `REPORT_TEMPLATE.md`: required per-model report format
- `MANIFEST.json`: counts, blindness declaration, prompt hash

Images are NOT committed (COCO URLs provided in the CSVs; cache locally and verify against the SHA-256 map in MANIFEST.json if byte-identity matters). No ground truth, model predictions, or rater labels are included. Run one item per request; preserve raw responses; count invalid outputs as wrong; freeze and report provider settings.
