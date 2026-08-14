# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** r1_2b_full  |  **Status label:** confirmatory
- **Git commit:** 5cc3a4f64f0d09e02b3a49ba7234826aa61d42c9  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T05:27:36+00:00
- **Normal-condition baseline:** tag r1_2b_full

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
| zero_shot | 0.3184 | 0.4980 | 0.2531 | 0.0000 |
| general_lora | 0.3469 | 0.5224 | 0.2980 | 0.0000 |

`response_flip` (per checkpoint, = C_pair by definition): zero_shot 0.3184, general_lora 0.3469

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0286 | [-0.0245, 0.0816] | 0.360378 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.4980 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 245 | 0.5224 | 0.0000 |

## Transform: hflip_invariant (law: expected_invariant, n_eligible=421)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8836 | 0.7031 | 0.6485 | 0.0000 |
| general_lora | 0.8907 | 0.7245 | 0.6770 | 0.0000 |

`response_stability` (per checkpoint, = C_pair by definition): zero_shot 0.8836, general_lora 0.8907

| transition | deltaV | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0071 | [-0.0285, 0.0428] | 0.791366 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7158 | 0.0000 |
| vertical | 129 | 0.6744 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7295 | 0.0000 |
| vertical | 129 | 0.7132 | 0.0000 |

*Report generated from frozen protocol v0.1; visual transforms frozen in visual_transform_validity.csv before any Tier-C result was inspected.*
