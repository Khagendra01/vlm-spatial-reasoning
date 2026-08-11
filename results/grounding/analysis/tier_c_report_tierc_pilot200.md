# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierc_pilot200  |  **Status label:** engineering
- **Git commit:** 38ad6fbc3e13cd785730b656c19512866d0845fd  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T01:20:24+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 8/16): reflected-image behavior is about causal sensitivity to the visual layout. Flip rates and expected-invariant stability rates are reported SEPARATELY and never merged. A model can flip coherently and still be wrong on the scene, so C is ALWAYS reported together with both-correct. No internal mechanism is inferred, and consistency alone is not proof of grounding.

## Definitions

- `C(m)` = expected-behavior rate: P(prediction equals the expected transformed label) under the image transform; invalid outputs count as non-obeying, and the invalid rate is reported separately.
- For `hflip_flip` (mirrored left/right relations): C = expected flip rate, `wrong_direction` = P(pred == original label), `change_rate` = any response change, `both_correct` = normal-correct AND obeys the flip.
- For `hflip_invariant` (vertical/depth controls): C = stability rate, `change_rate` = spurious response change, `both_correct` = normal-correct AND stable.
- `DeltaC(u->v)` = C(v) - C(u) with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the obey indicator.

## Transform definitions (frozen pre-result)

| transform | law | image change | language | expected behavior |
|---|---|---|---|---|
| hflip_flip | flip_expected | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = NOT original label (left/right relations) |
| hflip_invariant | expected_invariant | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = original label (vertical/depth relations) |

Validity table: `results/grounding/protocol/visual_transform_validity.csv` (all 61 relations classified; flip-expected strictly only for mirrored-axis left/right relations; invariant controls kept separate). Eligible IDs: `results/grounding/protocol/visual_eligible_ids.json`. Spot-check image pairs: `results/grounding/protocol/visual_spot/`.

## Transform: hflip_flip (law: flip_expected, n_eligible=200)

| checkpoint | C | both_correct | wrong_dir | change | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.6200 | 0.5200 | 0.3800 | 0.6200 | 0.0000 |
| general_lora | 0.6500 | 0.5850 | 0.3500 | 0.6500 | 0.0000 |
| hardneg_lora | 0.6600 | 0.6100 | 0.3400 | 0.6600 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0300 | [-0.0050, 0.0650] | 0.179565 |
| D1 (general_lora->hardneg_lora) | 0.0100 | [-0.0150, 0.0400] | 0.726562 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6200 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6500 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6600 | 0.0000 |

## Transform: hflip_invariant (law: expected_invariant, n_eligible=200)

| checkpoint | C | both_correct | wrong_dir | change | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.7250 | 0.6800 | 0.7250 | 0.2750 | 0.0000 |
| general_lora | 0.8750 | 0.8200 | 0.8750 | 0.1250 | 0.0000 |
| hardneg_lora | 0.8550 | 0.8250 | 0.8550 | 0.1450 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1500 | [0.0900, 0.2150] | 5e-06 |
| D1 (general_lora->hardneg_lora) | -0.0200 | [-0.0600, 0.0200] | 0.454498 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.7133 | 0.0000 |
| vertical | 57 | 0.7544 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.8601 | 0.0000 |
| vertical | 57 | 0.9123 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.8322 | 0.0000 |
| vertical | 57 | 0.9123 | 0.0000 |

*Report generated from frozen protocol v0.1; visual transforms frozen in visual_transform_validity.csv before any Tier-C result was inspected.*
