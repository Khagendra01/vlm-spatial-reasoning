# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierc_full  |  **Status label:** confirmatory
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:18:29+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 8/16): reflected-image behavior is about causal sensitivity to the visual layout. Flip rates and expected-invariant stability rates are reported SEPARATELY and never merged. A model can flip coherently and still be wrong on the scene, so C is ALWAYS reported together with both-correct. No internal mechanism is inferred, and consistency alone is not proof of grounding.

## Definitions

- `C(m)` = expected-behavior rate: P(prediction equals the expected transformed label) under the image transform; invalid outputs count as non-obeying, and the invalid rate is reported separately.
- For `hflip_flip` (mirrored left/right relations): C = expected flip rate, `wrong_direction` = P(pred == original label), `change_rate` = any response change, `both_correct` = normal-correct AND obeys the flip.
- For `hflip_invariant` (vertical/depth controls): C = stability rate, `change_rate` = spurious response change, `both_correct` = normal-correct AND stable.
- `DeltaC(u->v) = C(v) - C(u)` with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the obey indicator.

> Naming note: the paper-facing quantity for this visual axis is `DeltaV` (reported below as deltaV). The metrics JSON retains the generic key `delta_C` (same value, no numbers changed); `DeltaC` is reserved for the semantic axis (Tier B).

## Transform definitions (frozen pre-result)

| transform | law | image change | language | expected behavior |
|---|---|---|---|---|
| hflip_flip | flip_expected | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = NOT original label (left/right relations) |
| hflip_invariant | expected_invariant | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = original label (vertical/depth relations) |

Validity table: `results/grounding/protocol/visual_transform_validity.csv` (all 61 relations classified; flip-expected strictly only for mirrored-axis left/right relations; invariant controls kept separate). Eligible IDs: `results/grounding/protocol/visual_eligible_ids.json`. Spot-check image pairs: `results/grounding/protocol/visual_spot/`.

## Transform: hflip_flip (law: flip_expected, n_eligible=245)

| checkpoint | C | both_correct | wrong_dir | change | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.6367 | 0.5388 | 0.3633 | 0.6367 | 0.0000 |
| general_lora | 0.6571 | 0.5959 | 0.3429 | 0.6571 | 0.0000 |
| hardneg_lora | 0.6653 | 0.6204 | 0.3347 | 0.6653 | 0.0000 |

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0204 | [-0.0082, 0.0531] | 0.301758 |
| D1 (general_lora->hardneg_lora) | 0.0082 | [-0.0122, 0.0327] | 0.726562 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6367 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6571 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6653 | 0.0000 |

## Transform: hflip_invariant (law: expected_invariant, n_eligible=421)

| checkpoint | C | both_correct | wrong_dir | change | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.7031 | 0.6556 | 0.7031 | 0.2969 | 0.0000 |
| general_lora | 0.8242 | 0.7696 | 0.8242 | 0.1758 | 0.0000 |
| hardneg_lora | 0.8147 | 0.7720 | 0.8147 | 0.1853 | 0.0000 |

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1211 | [0.0784, 0.1639] | 0.0 |
| D1 (general_lora->hardneg_lora) | -0.0095 | [-0.0356, 0.0166] | 0.584665 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7021 | 0.0000 |
| vertical | 129 | 0.7054 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.8390 | 0.0000 |
| vertical | 129 | 0.7907 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.8253 | 0.0000 |
| vertical | 129 | 0.7907 | 0.0000 |

*Report generated from frozen protocol v0.1; visual transforms frozen in visual_transform_validity.csv before any Tier-C result was inspected.*
