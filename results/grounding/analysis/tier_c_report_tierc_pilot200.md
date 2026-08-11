# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierc_pilot200  |  **Status label:** engineering
- **Git commit:** 234579b0a7a86cd16215e5ab94e4da575f0c4b46  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:31:08+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 8/16): reflected-image behavior is about causal sensitivity to the visual layout. Flip rates and expected-invariant stability rates are reported SEPARATELY and never merged. A model can flip coherently and still be wrong on the scene, so the response rates are ALWAYS reported together with both-correct. No internal mechanism is inferred, and consistency alone is not proof of grounding.

## Definitions

- `C_pair(m)` = P(pair consistency): the model's TWO answers on the same example obey the linked-answer law — `hflip_flip`: P(mirrored answer != normal answer) (response flip); `hflip_invariant`: P(mirrored answer == normal answer) (response stability). Invalid outputs count as non-consistent, and the invalid rate is reported separately.
- `A_transform(m)` = P(transformed prediction equals the expected transformed label) (transformed-answer accuracy; for hflip_flip the expected label is the flipped label, for hflip_invariant the original label).
- `response_flip` / `response_stability` (paper-facing labels of C_pair per transform): literal answer-change / answer-stability rates comparing the model's two outputs, NOT predictions vs ground truth (decision log 2026-08-11).
- `both_correct(m)` = P(normal-correct AND transformed answer obeys the law).
- `DeltaV(u->v) = C_pair(v) - C_pair(u)` with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the pair-consistency indicator. (The transformed-accuracy analogue is kept in the metrics JSON under `transitions_transformed_accuracy`.)

> Naming note: `DeltaV` is the paper-facing quantity for this visual axis (reported below as deltaV). The metrics JSON retains the generic key `delta_C` (same value, no numbers changed); `DeltaC` is reserved for the semantic axis (Tier B).

## Transform definitions (frozen pre-result)

| transform | law | image change | language | expected behavior |
|---|---|---|---|---|
| hflip_flip | flip_expected | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = NOT original label (left/right relations) |
| hflip_invariant | expected_invariant | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = original label (vertical/depth relations) |

Validity table: `results/grounding/protocol/visual_transform_validity.csv` (all 61 relations classified; flip-expected strictly only for mirrored-axis left/right relations; invariant controls kept separate). Eligible IDs: `results/grounding/protocol/visual_eligible_ids.json`. Spot-check image pairs: `results/grounding/protocol/visual_spot/`.

## Transform: hflip_flip (law: flip_expected, n_eligible=200)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.6150 | 0.6200 | 0.5200 | 0.0000 |
| general_lora | 0.6900 | 0.6500 | 0.5850 | 0.0000 |
| hardneg_lora | 0.7000 | 0.6600 | 0.6100 | 0.0000 |

`response_flip` (per checkpoint, = C_pair by definition): zero_shot 0.6150, general_lora 0.6900, hardneg_lora 0.7000

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0750 | [0.0200, 0.1350] | 0.016674 |
| D1 (general_lora->hardneg_lora) | 0.0100 | [-0.0250, 0.0450] | 0.790527 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6200 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6500 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 200 | 0.6600 | 0.0000 |

## Transform: hflip_invariant (law: expected_invariant, n_eligible=200)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8900 | 0.7250 | 0.6800 | 0.0000 |
| general_lora | 0.9100 | 0.8750 | 0.8200 | 0.0000 |
| hardneg_lora | 0.9300 | 0.8550 | 0.8250 | 0.0000 |

`response_stability` (per checkpoint, = C_pair by definition): zero_shot 0.8900, general_lora 0.9100, hardneg_lora 0.9300

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0200 | [-0.0300, 0.0750] | 0.571588 |
| D1 (general_lora->hardneg_lora) | 0.0200 | [-0.0200, 0.0600] | 0.480682 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.7133 | 0.0000 |
| vertical | 57 | 0.7544 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.8601 | 0.0000 |
| vertical | 57 | 0.9123 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 143 | 0.8322 | 0.0000 |
| vertical | 57 | 0.9123 | 0.0000 |

*Report generated from frozen protocol v0.1; visual transforms frozen in visual_transform_validity.csv before any Tier-C result was inspected.*
