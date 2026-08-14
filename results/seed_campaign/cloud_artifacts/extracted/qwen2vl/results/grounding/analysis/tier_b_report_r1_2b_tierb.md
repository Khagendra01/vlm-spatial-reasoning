# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** r1_2b_full  |  **Status label:** confirmatory
- **Git commit:** b2c4bcf56962788e103845b20c72a3d6dc80ec5f  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T05:33:08+00:00
- **Normal-condition baseline:** tag r1_2b_full

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
| zero_shot | 0.4685 | 0.5195 | 0.3453 | 0.0000 |
| general_lora | 0.5015 | 0.5721 | 0.4039 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0330 | [0.0015, 0.0646] | 0.048725 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6096 | 0.0000 |
| horizontal | 245 | 0.4816 | 0.0000 |
| vertical | 129 | 0.3876 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6507 | 0.0000 |
| horizontal | 245 | 0.5388 | 0.0000 |
| vertical | 129 | 0.4574 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=603)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.8192 | 0.7645 | 0.6915 | 0.0000 |
| general_lora | 0.8010 | 0.7745 | 0.6949 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.0182 | [-0.0464, 0.0100] | 0.241645 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.7381 | 0.0000 |
| other | 25 | 0.9200 | 0.0000 |
| proximity | 153 | 0.6863 | 0.0000 |
| topology_contact | 299 | 0.8027 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.7619 | 0.0000 |
| other | 25 | 0.8400 | 0.0000 |
| proximity | 153 | 0.6993 | 0.0000 |
| topology_contact | 299 | 0.8127 | 0.0000 |

## Transform: continv (law: paraphrase_law, n_eligible=169)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.9172 | 0.8166 | 0.7811 | 0.0000 |
| general_lora | 0.8580 | 0.8402 | 0.7929 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.0592 | [-0.1124, -0.0059] | 0.041389 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.8166 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.8402 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
