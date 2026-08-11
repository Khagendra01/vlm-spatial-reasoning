# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierb_full  |  **Status label:** confirmatory
- **Git commit:** 234579b0a7a86cd16215e5ab94e4da575f0c4b46  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:30:09+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 16): a model can obey a semantic law while being wrong on the scene. C_pair (linked-answer consistency) is therefore ALWAYS reported together with both-correct (obey AND normal-correct), and the transformed-accuracy A_transform is reported separately. Consistency alone is not asserted as proof of grounding, and no internal mechanism is inferred.

## Definitions

- `C_pair(m,t)` = P(pair consistency): the model's TWO answers on the same example obey the linked-answer law — flip-law transforms (relcomp, facingcomp): P(transformed answer != normal answer); stability/paraphrase transforms (sorev, continv): P(transformed answer == normal answer). Invalid outputs count as non-consistent, and the invalid rate is reported separately.
- `A_transform(m,t)` = P(transformed prediction equals the expected transformed label) (transformed-answer accuracy, reported for transparency and diagnostics; previously labeled `C`).
- `both_correct(m,t)` = P(normal prediction correct AND transformed prediction obeys the law).
- `DeltaC_pair(u->v) = C_pair(v) - C_pair(u)` with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the pair-consistency indicator. (The transformed-accuracy analogue `DeltaC` is kept in the metrics JSON under `transitions_transformed_accuracy`.)

> Metric note (decision log 2026-08-11): pair consistency compares the model's two answers on the same example. It is NOT the same as transformed-answer accuracy: e.g. a model answering False on both the original and the flipped statement scores A_transform=1 but C_pair=0 for flip laws.

## Transform definitions (frozen pre-result)

| transform | law | expected behavior |
|---|---|---|
| relcomp | flip_law | expected = NOT original label (strict complement pairs only) |
| sorev | stability_law | expected = original label (symmetric relations, subject/object swap) |
| continv | paraphrase_law | expected = original label (in/inside/within <-> contains) |

Validity table: `results/grounding/protocol/semantic_transform_validity.csv` (all 61 relations classified; strict/soft/unsafe/not_in_scope with reasons). Eligible IDs: `results/grounding/protocol/semantic_eligible_ids.json`.

## Transform: relcomp (law: flip_law, n_eligible=666)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.5060 | 0.6291 | 0.4459 | 0.0000 |
| general_lora | 0.6772 | 0.6712 | 0.5871 | 0.0000 |
| hardneg_lora | 0.6877 | 0.6817 | 0.6081 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1712 | [0.1351, 0.2072] | 0.0 |
| D1 (general_lora->hardneg_lora) | 0.0105 | [-0.0120, 0.0330] | 0.442626 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6507 | 0.0000 |
| horizontal | 245 | 0.6286 | 0.0000 |
| vertical | 129 | 0.5814 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6918 | 0.0000 |
| horizontal | 245 | 0.6490 | 0.0000 |
| vertical | 129 | 0.6667 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7226 | 0.0000 |
| horizontal | 245 | 0.6531 | 0.0000 |
| vertical | 129 | 0.6434 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=603)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8192 | 0.7728 | 0.6799 | 0.0000 |
| general_lora | 0.8375 | 0.8325 | 0.7529 | 0.0000 |
| hardneg_lora | 0.8524 | 0.8474 | 0.7662 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0182 | [-0.0182, 0.0531] | 0.359358 |
| D1 (general_lora->hardneg_lora) | 0.0149 | [-0.0083, 0.0381] | 0.271679 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8095 | 0.0000 |
| other | 25 | 0.7600 | 0.0000 |
| proximity | 153 | 0.7059 | 0.0000 |
| topology_contact | 299 | 0.7926 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8016 | 0.0000 |
| other | 25 | 0.7600 | 0.0000 |
| proximity | 153 | 0.8497 | 0.0000 |
| topology_contact | 299 | 0.8428 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8016 | 0.0000 |
| other | 25 | 0.8000 | 0.0000 |
| proximity | 153 | 0.8824 | 0.0000 |
| topology_contact | 299 | 0.8528 | 0.0000 |

## Transform: continv (law: paraphrase_law, n_eligible=169)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8994 | 0.8580 | 0.8166 | 0.0000 |
| general_lora | 0.9053 | 0.9112 | 0.8521 | 0.0000 |
| hardneg_lora | 0.9053 | 0.9231 | 0.8580 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0059 | [-0.0414, 0.0533] | 1.0 |
| D1 (general_lora->hardneg_lora) | 0.0000 | [-0.0296, 0.0296] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.8580 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.9112 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.9231 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
