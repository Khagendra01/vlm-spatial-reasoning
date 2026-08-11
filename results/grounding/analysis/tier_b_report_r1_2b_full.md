# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** r1_2b_full  |  **Status label:** confirmatory
- **Git commit:** 5cc3a4f64f0d09e02b3a49ba7234826aa61d42c9  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T05:27:33+00:00
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
| facingcomp | flip_law (antonym) | expected = NOT original label (facing <-> facing away from; facing-antonym flip-law compliance, Paper-1 antonym construct; NOT a universal strict logical complement, decision log 2026-08-11) |

Validity table: `results/grounding/protocol/facing_transform_validity.csv`. Eligible IDs: `results/grounding/protocol/facing_eligible_ids.json`. Dedicated D1 diagnostic; the Tier-B relcomp table soft-excludes facing/facing-away (oblique orientations) and is unchanged.

## Transform: facingcomp (law: flip_law, n_eligible=103)

| checkpoint | C_pair | A_transform | both_correct | invalid% |
|---|---:|---:|---:|---:|
| zero_shot | 0.6214 | 0.5340 | 0.3981 | 0.0000 |
| general_lora | 0.5534 | 0.5049 | 0.3398 | 0.0000 |

| transition | deltaC_pair | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.0680 | [-0.1553, 0.0097] | 0.167068 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| orientation | 103 | 0.5340 | 0.0000 |

**general_lora**

| family | n | A_transform | invalid% |
|---|---:|---:|---:|
| orientation | 103 | 0.5049 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
