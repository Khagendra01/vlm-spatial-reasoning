# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierb_pilot200  |  **Status label:** engineering
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:18:19+00:00
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

## Transform: relcomp (law: flip_law, n_eligible=200)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.6300 | 0.4300 | 0.0000 |
| general_lora | 0.6500 | 0.5950 | 0.0000 |
| hardneg_lora | 0.6700 | 0.6300 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0200 | [-0.0150, 0.0550] | 0.42395 |
| D1 (general_lora->hardneg_lora) | 0.0200 | [-0.0100, 0.0500] | 0.34375 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.6739 | 0.0000 |
| horizontal | 74 | 0.5811 | 0.0000 |
| vertical | 34 | 0.6176 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.6957 | 0.0000 |
| horizontal | 74 | 0.5946 | 0.0000 |
| vertical | 34 | 0.6471 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 92 | 0.7283 | 0.0000 |
| horizontal | 74 | 0.6081 | 0.0000 |
| vertical | 34 | 0.6471 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=200)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.7900 | 0.6900 | 0.0000 |
| general_lora | 0.7850 | 0.7150 | 0.0000 |
| hardneg_lora | 0.8200 | 0.7350 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.0050 | [-0.0600, 0.0500] | 1.0 |
| D1 (general_lora->hardneg_lora) | 0.0350 | [0.0050, 0.0700] | 0.06543 |

> Note: D1: positive point estimate with CONFLICTING inferential evidence (bootstrap CI excludes 0, McNemar p=0.0654); NOT labeled significant.

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.8000 | 0.0000 |
| other | 12 | 0.7500 | 0.0000 |
| proximity | 46 | 0.7609 | 0.0000 |
| topology_contact | 102 | 0.8039 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.7250 | 0.0000 |
| other | 12 | 0.5833 | 0.0000 |
| proximity | 46 | 0.9130 | 0.0000 |
| topology_contact | 102 | 0.7745 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 40 | 0.7500 | 0.0000 |
| other | 12 | 0.5833 | 0.0000 |
| proximity | 46 | 0.9348 | 0.0000 |
| topology_contact | 102 | 0.8235 | 0.0000 |

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
