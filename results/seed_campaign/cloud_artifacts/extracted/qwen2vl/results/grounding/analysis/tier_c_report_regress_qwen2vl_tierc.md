# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** regress_qwen2vl_tierc  |  **Status label:** confirmatory
- **Git commit:** 9b994a2a052f86be9f9d15743c202c4e0c8e0c22  |  branch HEAD
- **Generated:** 2026-08-13T17:17:54+00:00
- **Normal-condition baseline:** tag regress_qwen2vl

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

## Transform: hflip_flip (law: flip_expected, n_eligible=245)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.6163 | 0.6367 | 0.5388 | 0.0000 |
| general_lora | 0.6857 | 0.6571 | 0.5959 | 0.0000 |
| hardneg_lora | 0.6980 | 0.6653 | 0.6204 | 0.0000 |

`response_flip` (per checkpoint, = C_pair by definition): zero_shot 0.6163, general_lora 0.6857, hardneg_lora 0.6980

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0694 | [0.0204, 0.1184] | 0.009475 |
| D1 (general_lora->hardneg_lora) | 0.0122 | [-0.0163, 0.0449] | 0.607239 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6367 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6571 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.6653 | 0.0000 |

## Transform: hflip_invariant (law: expected_invariant, n_eligible=421)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8907 | 0.7031 | 0.6556 | 0.0000 |
| general_lora | 0.9026 | 0.8242 | 0.7696 | 0.0000 |
| hardneg_lora | 0.9002 | 0.8147 | 0.7720 | 0.0000 |

`response_stability` (per checkpoint, = C_pair by definition): zero_shot 0.8907, general_lora 0.9026, hardneg_lora 0.9002

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0119 | [-0.0261, 0.0475] | 0.620145 |
| D1 (general_lora->hardneg_lora) | -0.0024 | [-0.0309, 0.0261] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7021 | 0.0000 |
| vertical | 129 | 0.7054 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.8390 | 0.0000 |
| vertical | 129 | 0.7907 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.8253 | 0.0000 |
| vertical | 129 | 0.7907 | 0.0000 |

*Report generated from frozen protocol v0.1; visual transforms frozen in visual_transform_validity.csv before any Tier-C result was inspected.*
