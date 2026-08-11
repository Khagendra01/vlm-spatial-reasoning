# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** facing_smoke10  |  **Status label:** engineering
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:08:13+00:00
- **Normal-condition baseline:** tag full

> Interpretation guardrails (protocol section 16): a model can obey a semantic law while being wrong on the scene. C (obeying the expected linked-answer law) is therefore ALWAYS reported together with both-correct (obey AND normal-correct). Consistency alone is not asserted as proof of grounding, and no internal mechanism is inferred.

## Definitions

- `C_t(m)` = P(model prediction equals the expected transformed label under transform `t` for checkpoint `m`); invalid outputs count as non-obeying, and the invalid rate is reported separately.
- `both_correct(m,t)` = P(normal prediction correct AND transformed prediction obeys the law).
- `DeltaC(u->v) = C_t(v) - C_t(u)` with paired bootstrap CI (n=10000, seed 20260810) and exact McNemar on the obey indicator.

## Transform definitions (frozen pre-result)

| transform | law | expected behavior |
|---|---|---|
| facingcomp | flip_law | expected = NOT original label (facing <-> facing away from; dedicated Paper-1 D1 construct, decision log 2026-08-11) |

Validity table: `results/grounding/protocol/facing_transform_validity.csv`. Eligible IDs: `results/grounding/protocol/facing_eligible_ids.json`. Dedicated D1 diagnostic; the Tier-B relcomp table soft-excludes facing/facing-away (oblique orientations) and is unchanged.

## Transform: facingcomp (law: flip_law, n_eligible=10)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.5000 | 0.0000 | 0.0000 |
| general_lora | 0.9000 | 0.8000 | 0.0000 |
| hardneg_lora | 1.0000 | 0.9000 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.4000 | [0.0000, 0.8000] | 0.21875 |
| D1 (general_lora->hardneg_lora) | 0.1000 | [0.0000, 0.3000] | 1.0 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 10 | 0.5000 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 10 | 0.9000 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 10 | 1.0000 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
