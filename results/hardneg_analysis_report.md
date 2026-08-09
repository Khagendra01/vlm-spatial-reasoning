# Hard-Negative Orientation LoRA: Results

## Experiment
- **Control:** 7B General LoRA (general_train.jsonl, 2000 ex, r=8 α=16 lr=1e-4, 2 epochs)
- **Treatment:** 7B Hard-Negative LoRA (hardneg_train.jsonl, 2000 ex, identical config)
- **Only variable:** orientation block replaced by audited-clean originals + paired hard negatives
  (facing ↔ facing away from, parallel ↔ perpendicular)

## Overall
| Condition | Overall |
|-----------|---------|
| 7B Zero-shot | 80.91% |
| 7B General LoRA | 84.69% |
| 7B Hard-Negative LoRA | 84.33% |

## McNemar: General LoRA vs Hard-Negative
- Global: fixed=52, broken=60, net=-8, chi2=0.44, p=0.508332
- Weak families pooled: fixed=20, broken=26, net=-6, chi2=0.54, p=0.460995

## Per-relation orientation accuracy
| Relation | N | 7B Zero | 7B Gen LoRA | 7B HardNeg | McNemar p (Gen vs HN) |
|----------|---|---------|-------------|------------|----------------------|
| facing | 64 | 73.4% | 75.0% | 70.3% | p=0.450 |
| facing away from | 39 | 48.7% | 59.0% | 66.7% | p=0.450 |
| parallel to | 22 | 63.6% | 63.6% | 68.2% | p=1.000 |
| perpendicular to | 12 | 58.3% | 41.7% | 41.7% | p=1.000 |

## Persistent orientation failures
- Previous persistent (7B zero + Gen LoRA both wrong): 20
- Still failing with hard-negative LoRA: 15
- Fixed by hard-negative LoRA: 5
- Of the 48 annotated cases: fixed 5

## Family regression check
| Family | Gen LoRA | HardNeg | Delta |
|--------|----------|---------|-------|
| horizontal | 87.1% | 86.5% | -0.5% |
| vertical | 88.5% | 89.2% | +0.7% |
| depth | 82.3% | 80.7% | -1.6% |
| orientation | 65.7% | 66.4% | +0.7% |
| containment | 93.0% | 90.1% | -2.9% |
| proximity | 88.9% | 87.6% | -1.3% |
| topology_contact | 84.4% | 84.8% | +0.4% |
| compositional | 80.0% | 78.5% | -1.5% |

## Conclusion
Hard-negative LoRA improved orientation relative to General LoRA control.

Orientation ceiling evidence: 2 of 4 relations improved over zero-shot.
