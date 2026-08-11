# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierb_full  |  **Status label:** confirmatory
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:18:15+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 16): a model can obey a semantic law while being wrong on the scene. C (obeying the expected linked-answer law) is therefore ALWAYS reported together with both-correct (obey AND normal-correct). Consistency alone is not asserted as proof of grounding, and no internal mechanism is inferred.

## Definitions

- `C_t(m)` = P(model prediction equals the expected transformed label under transform `t` for checkpoint `m`); invalid outputs count as non-obeying, and the invalid rate is reported separately.
- `both_correct(m,t)` = P(normal prediction correct AND transformed prediction obeys the law).
- `DeltaC(u->v) = C_t(v) - C_t(u)` with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the obey indicator.

## Transform definitions (frozen pre-result)

| transform | law | expected behavior |
|---|---|---|
| relcomp | flip_law | expected = NOT original label (strict complement pairs only) |
| sorev | stability_law | expected = original label (symmetric relations, subject/object swap) |
| continv | paraphrase_law | expected = original label (in/inside/within <-> contains) |

Validity table: `results/grounding/protocol/semantic_transform_validity.csv` (all 61 relations classified; strict/soft/unsafe/not_in_scope with reasons). Eligible IDs: `results/grounding/protocol/semantic_eligible_ids.json`.

## Transform: relcomp (law: flip_law, n_eligible=666)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.6291 | 0.4459 | 0.0000 |
| general_lora | 0.6712 | 0.5871 | 0.0000 |
| hardneg_lora | 0.6817 | 0.6081 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0420 | [0.0195, 0.0661] | 0.000617 |
| D1 (general_lora->hardneg_lora) | 0.0105 | [-0.0045, 0.0255] | 0.229523 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6507 | 0.0000 |
| horizontal | 245 | 0.6286 | 0.0000 |
| vertical | 129 | 0.5814 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.6918 | 0.0000 |
| horizontal | 245 | 0.6490 | 0.0000 |
| vertical | 129 | 0.6667 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 292 | 0.7226 | 0.0000 |
| horizontal | 245 | 0.6531 | 0.0000 |
| vertical | 129 | 0.6434 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=603)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.7728 | 0.6799 | 0.0000 |
| general_lora | 0.8325 | 0.7529 | 0.0000 |
| hardneg_lora | 0.8474 | 0.7662 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0597 | [0.0282, 0.0912] | 0.000355 |
| D1 (general_lora->hardneg_lora) | 0.0149 | [-0.0033, 0.0332] | 0.162756 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8095 | 0.0000 |
| other | 25 | 0.7600 | 0.0000 |
| proximity | 153 | 0.7059 | 0.0000 |
| topology_contact | 299 | 0.7926 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8016 | 0.0000 |
| other | 25 | 0.7600 | 0.0000 |
| proximity | 153 | 0.8497 | 0.0000 |
| topology_contact | 299 | 0.8428 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 126 | 0.8016 | 0.0000 |
| other | 25 | 0.8000 | 0.0000 |
| proximity | 153 | 0.8824 | 0.0000 |
| topology_contact | 299 | 0.8528 | 0.0000 |

## Transform: continv (law: paraphrase_law, n_eligible=169)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.8580 | 0.8166 | 0.0000 |
| general_lora | 0.9112 | 0.8521 | 0.0000 |
| hardneg_lora | 0.9231 | 0.8580 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0533 | [0.0059, 0.1065] | 0.063568 |
| D1 (general_lora->hardneg_lora) | 0.0118 | [-0.0118, 0.0355] | 0.625 |

> Note: P1: positive point estimate with CONFLICTING inferential evidence (bootstrap CI excludes 0, McNemar p=0.0636); NOT labeled significant.

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.8580 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.9112 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 169 | 0.9231 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
