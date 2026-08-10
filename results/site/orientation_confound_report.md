# SITE Orientation-Heuristic Confound Analysis (CPU-only)

Data: `results/site/zeroshot_7b_predictions.csv` (2,591 zero-shot image predictions, unchanged). Orientation flag = frozen-ID secondary membership (`site_protocol.json -> frozen_ids.secondary`).

## Logistic regressions: correct ~ orient + controls

| Model | OR (orient) | 95% CI | p |
|---|---|---|---|
| Unadjusted | 0.307 | [0.249, 0.378] | 2.364e-28 |
| + official category | 0.741 | [0.572, 0.959] | 0.02282 |
| + category + source + modality + n_options | 0.837 | [0.602, 1.164] | 0.2903 |

## Within-category (orient-pos vs orient-neg, both n>=30)

| Category | pos n | pos acc | neg n | neg acc | delta (pp) |
|---|---|---|---|---|---|
| spatial relationship reasoning | 488 | 71.3 | 505 | 78.8 | -7.5 |
| movement prediction & navigation | 186 | 49.5 | 62 | 46.8 | +2.7 |

## Within-source (orient-pos vs orient-neg, both n>=30)

| Source | pos n | pos acc | neg n | neg acc | delta (pp) |
|---|---|---|---|---|---|
| ThreeDSRBench | 95 | 61.1 | 46 | 67.4 | -6.3 |
| SPEC | 102 | 50.0 | 31 | 54.8 | -4.8 |

## High-precision post-hoc/exploratory subset (VSR-construct terms)

- Terms: `facing, facing away, parallel, perpendicular` (word-boundary, question + option text; POST-HOC, does not replace the preregistered subset).
- n = 177 (overlap with frozen secondary: 177, outside: 0)
- raw acc = 44.1% CI=[37.0, 51.4], CAA = -2.3%
- by official category: {'multi-view & cross-image reasoning': 99, 'object localization & positioning': 1, 'spatial relationship reasoning': 77}

## Reading

- If the adjusted OR remains clearly < 1 with p < 0.05: orientation vocabulary is independently associated with difficulty beyond task composition.
- If it collapses toward 1: the aggregate heuristic score is largely explained by task composition; SITE is then reported as cross-dataset transfer evidence only, with the heuristic slice as exploratory.
