# Clean-Label Orientation Robustness — HUMAN audit (versioned, additive; rater3 (second human re-audit))

Exclusion masks derived from the HUMAN taxonomy pass (48 cases) and
the HUMAN binary pass (137 cases). The frozen first-annotator (LLM)
table is unchanged: results/tables/orientation_clean_label_table.md.

| Condition | full (137) | -q | clear | strict | human-binary |
|---|---|---|---|---|---|
| 2B zero-shot | 0.628 (n=137) | 0.664 (n=128) | 0.672 (n=125) | 0.779 (n=104) | 0.623 (n=77) |
| 2B structured | 0.533 (n=137) | 0.531 (n=128) | 0.528 (n=125) | 0.510 (n=104) | 0.597 (n=77) |
| 2B General LoRA | 0.620 (n=137) | 0.656 (n=128) | 0.664 (n=125) | 0.750 (n=104) | 0.636 (n=77) |
| 2B Targeted LoRA | 0.642 (n=137) | 0.688 (n=128) | 0.688 (n=125) | 0.788 (n=104) | 0.636 (n=77) |
| 7B zero-shot | 0.635 (n=137) | 0.656 (n=128) | 0.664 (n=125) | 0.760 (n=104) | 0.584 (n=77) |
| 7B General LoRA | 0.657 (n=137) | 0.680 (n=128) | 0.688 (n=125) | 0.740 (n=104) | 0.623 (n=77) |
| 7B Targeted LoRA | 0.642 (n=137) | 0.656 (n=128) | 0.664 (n=125) | 0.712 (n=104) | 0.610 (n=77) |
| 7B Hard-Neg LoRA | 0.664 (n=137) | 0.680 (n=128) | 0.696 (n=125) | 0.740 (n=104) | 0.610 (n=77) |
| 7B Projector LoRA | 0.642 (n=137) | 0.656 (n=128) | 0.648 (n=125) | 0.721 (n=104) | 0.662 (n=77) |
| 7B Vision+Projector LoRA | 0.642 (n=137) | 0.672 (n=128) | 0.680 (n=125) | 0.740 (n=104) | 0.636 (n=77) |
| MiMo-V2.5 zero-shot | 0.657 (n=137) | 0.680 (n=128) | 0.672 (n=125) | 0.731 (n=104) | 0.623 (n=77) |
