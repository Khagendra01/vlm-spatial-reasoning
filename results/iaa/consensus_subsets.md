# Clean-label sensitivity: annotator dependence (additive)

Frozen first-annotator table is retained unchanged. The second
blind annotator flagged more examples ambiguous; accuracies under
each mask are shown below.

| condition | full (137) | r1-strict (107) | r2-ambiguous (75) | consensus (62) |
|---|---|---|---|---|
| 2B zero-shot | 62.8 | 75.7 | 65.3 | 72.6 |
| 2B structured | 53.3 | 53.3 | 66.7 | 69.3 |
| 2B General LoRA | 62.0 | 72.9 | 66.7 | 71.0 |
| 2B Targeted LoRA | 64.2 | 76.6 | 65.3 | 71.0 |
| 7B zero-shot | 63.5 | 72.0 | 54.7 | 58.1 |
| 7B General LoRA | 65.7 | 78.5 | 66.7 | 77.4 |
| 7B Targeted LoRA | 64.2 | 72.0 | 57.3 | 64.5 |
| 7B Hard-Neg LoRA | 66.4 | 76.6 | 65.3 | 74.2 |
| 7B Projector LoRA | 64.2 | 73.8 | 61.3 | 67.7 |
| 7B Vision+Projector LoRA | 64.2 | 73.8 | 64.0 | 69.3 |
