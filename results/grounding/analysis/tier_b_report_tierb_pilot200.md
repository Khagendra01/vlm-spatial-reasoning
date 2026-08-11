# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierb_pilot200  |  **Status label:** engineering
- **Git commit:** 234579b0a7a86cd16215e5ab94e4da575f0c4b46  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:30:05+00:00
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

## Transform: relcomp (law: flip_law, n_eligible=200)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.5100 | 0.6300 | 0.4300 | 0.0000 |
| general_lora | 0.6950 | 0.6500 | 0.5950 | 0.0000 |
| hardneg_lora | 0.7200 | 0.6700 | 0.6300 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1850 | [0.1250, 0.2500] | 0.0 |
| D1 (general_lora->hardneg_lora) | 0.0250 | [-0.0150, 0.0650] | 0.332306 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.6739 | 0.0000 |
| horizontal | 74 | 0.5811 | 0.0000 |
| vertical | 34 | 0.6176 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.6957 | 0.0000 |
| horizontal | 74 | 0.5946 | 0.0000 |
| vertical | 34 | 0.6471 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.7283 | 0.0000 |
| horizontal | 74 | 0.6081 | 0.0000 |
| vertical | 34 | 0.6471 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=200)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8150 | 0.7900 | 0.6900 | 0.0000 |
| general_lora | 0.8050 | 0.7850 | 0.7150 | 0.0000 |
| hardneg_lora | 0.8350 | 0.8200 | 0.7350 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.0100 | [-0.0650, 0.0450] | 0.86005 |
| D1 (general_lora->hardneg_lora) | 0.0300 | [-0.0100, 0.0700] | 0.237885 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.8000 | 0.0000 |
| other | 12 | 0.7500 | 0.0000 |
| proximity | 46 | 0.7609 | 0.0000 |
| topology_contact | 102 | 0.8039 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.7250 | 0.0000 |
| other | 12 | 0.5833 | 0.0000 |
| proximity | 46 | 0.9130 | 0.0000 |
| topology_contact | 102 | 0.7745 | 0.0000 |

**hardneg_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.7500 | 0.0000 |
| other | 12 | 0.5833 | 0.0000 |
| proximity | 46 | 0.9348 | 0.0000 |
| topology_contact | 102 | 0.8235 | 0.0000 |

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
