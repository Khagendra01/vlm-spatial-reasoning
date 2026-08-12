# Inter-Annotator Agreement (IAA)

Additive reliability evidence for the single-annotator audits. Computed by
`scripts/compute_iaa.py` from the committed rater-1 audit
(`results/orientation_persistent_annotations.csv`) and the blind rater-2
sheets (`results/iaa/rater2_clean_labels.csv`,
`results/iaa/rater2_taxonomy.csv`).

## Clean/ambiguous flag (clean-label sensitivity audit)

- n = 48 (48 persistent-failure cases rated by both annotators)
- Percent agreement: 70.8%
- Cohen's kappa: 0.440 (95% bootstrap CI [0.211, 0.670])
- Chance-expected agreement (p_e): 0.479

Rater-1 binary flag derived from the eight-class taxonomy exactly as in
`scripts/clean_label_orientation.py` (only
`clear_image_model_reasoning_failure` counts as clean).

## Eight-class failure taxonomy

- n = 48
- Percent agreement (exact class match): 85.4%
- Krippendorff's alpha (nominal, two raters): 0.811 (95% bootstrap CI [0.678, 0.919])

## Reading

These are additive results. They do not replace or alter any reported
accuracy number (Table 2 main text / Table 7 supplementary), and the clean-label
analysis remains explicitly a single-annotator exploratory audit if IAA is
not yet available. Per standard conventions (e.g., Landis & Koch 1977 for
kappa), values below 0.41 are commonly read as slight-to-fair agreement and
should be reported as such; at n = 48 the bootstrap CIs are wide.
