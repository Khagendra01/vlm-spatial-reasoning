# Clean-Label Orientation Robustness — HUMAN audit (versioned, additive; rater2 (first human re-audit))

Exclusion masks derived from the HUMAN taxonomy pass (48 cases) and
the HUMAN binary pass (137 cases). The frozen first-annotator (LLM)
table is unchanged: results/tables/orientation_clean_label_table.md.

| Condition | full (137) | -q | clear | strict | human-binary |
|---|---|---|---|---|---|
| 2B zero-shot | 0.628 (n=137) | 0.675 (n=126) | 0.675 (n=126) | 0.766 (n=107) | 0.653 (n=75) |
| 2B structured | 0.533 (n=137) | 0.532 (n=126) | 0.532 (n=126) | 0.514 (n=107) | 0.667 (n=75) |
| 2B General LoRA | 0.620 (n=137) | 0.667 (n=126) | 0.667 (n=126) | 0.748 (n=107) | 0.667 (n=75) |
| 2B Targeted LoRA | 0.642 (n=137) | 0.691 (n=126) | 0.691 (n=126) | 0.776 (n=107) | 0.653 (n=75) |
| 7B zero-shot | 0.635 (n=137) | 0.659 (n=126) | 0.659 (n=126) | 0.748 (n=107) | 0.547 (n=75) |
| 7B General LoRA | 0.657 (n=137) | 0.682 (n=126) | 0.682 (n=126) | 0.729 (n=107) | 0.667 (n=75) |
| 7B Targeted LoRA | 0.642 (n=137) | 0.651 (n=126) | 0.651 (n=126) | 0.692 (n=107) | 0.573 (n=75) |
| 7B Hard-Neg LoRA | 0.664 (n=137) | 0.682 (n=126) | 0.682 (n=126) | 0.729 (n=107) | 0.653 (n=75) |
| 7B Projector LoRA | 0.642 (n=137) | 0.651 (n=126) | 0.651 (n=126) | 0.710 (n=107) | 0.613 (n=75) |
| 7B Vision+Projector LoRA | 0.642 (n=137) | 0.675 (n=126) | 0.675 (n=126) | 0.729 (n=107) | 0.640 (n=75) |
| MiMo-V2.5 zero-shot | 0.657 (n=137) | 0.682 (n=126) | 0.682 (n=126) | 0.720 (n=107) | 0.587 (n=75) |
