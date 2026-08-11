# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** tierb_smoke10  |  **Status label:** engineering
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:18:22+00:00
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

## Transform: relcomp (law: flip_law, n_eligible=10)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.6000 | 0.6000 | 0.0000 |
| general_lora | 0.7000 | 0.6000 | 0.0000 |
| hardneg_lora | 0.7000 | 0.6000 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1000 | [0.0000, 0.3000] | 1.0 |
| D1 (general_lora->hardneg_lora) | 0.0000 | [0.0000, 0.0000] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 5 | 0.6000 | 0.0000 |
| horizontal | 2 | 1.0000 | 0.0000 |
| vertical | 3 | 0.3333 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 5 | 0.6000 | 0.0000 |
| horizontal | 2 | 1.0000 | 0.0000 |
| vertical | 3 | 0.6667 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| depth | 5 | 0.6000 | 0.0000 |
| horizontal | 2 | 1.0000 | 0.0000 |
| vertical | 3 | 0.6667 | 0.0000 |

## Transform: sorev (law: stability_law, n_eligible=10)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.9000 | 0.8000 | 0.0000 |
| general_lora | 0.9000 | 0.9000 | 0.0000 |
| hardneg_lora | 0.9000 | 0.9000 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.0000 | [-0.3000, 0.3000] | 1.0 |
| D1 (general_lora->hardneg_lora) | 0.0000 | [0.0000, 0.0000] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 4 | 1.0000 | 0.0000 |
| proximity | 1 | 1.0000 | 0.0000 |
| topology_contact | 5 | 0.8000 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 4 | 1.0000 | 0.0000 |
| proximity | 1 | 1.0000 | 0.0000 |
| topology_contact | 5 | 0.8000 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| horizontal | 4 | 1.0000 | 0.0000 |
| proximity | 1 | 1.0000 | 0.0000 |
| topology_contact | 5 | 0.8000 | 0.0000 |

## Transform: continv (law: paraphrase_law, n_eligible=10)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.9000 | 0.7000 | 0.0000 |
| general_lora | 0.8000 | 0.8000 | 0.0000 |
| hardneg_lora | 0.8000 | 0.8000 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | -0.1000 | [-0.3000, 0.0000] | 1.0 |
| D1 (general_lora->hardneg_lora) | 0.0000 | [0.0000, 0.0000] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 10 | 0.9000 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 10 | 0.8000 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| containment | 10 | 0.8000 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
