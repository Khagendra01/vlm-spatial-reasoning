# Tier-B Semantic-Consistency Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b4958...)
- **Run tag:** facing_pilot200  |  **Status label:** engineering
- **Git commit:** 1fa62a03c28b1a502bc7b7784cd811736e10711a  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-11T02:12:01+00:00
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

## Transform: facingcomp (law: flip_law, n_eligible=103)

| checkpoint | C | both_correct | invalid% |
|---|---:|---:|---:|
| zero_shot | 0.5631 | 0.2621 | 0.0000 |
| general_lora | 0.7087 | 0.5728 | 0.0000 |
| hardneg_lora | 0.7670 | 0.6117 | 0.0000 |

| transition | deltaC | 95% CI | McNemar p |
|---|---:|---:|---:|
| P1 (zero_shot->general_lora) | 0.1456 | [0.0388, 0.2524] | 0.010674 |
| D1 (general_lora->hardneg_lora) | 0.0583 | [0.0000, 0.1262] | 0.145996 |

### Relation-family breakdown (descriptive; relation-level inference is secondary)

**zero_shot**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 103 | 0.5631 | 0.0000 |

**general_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 103 | 0.7087 | 0.0000 |

**hardneg_lora**

| family | n | C | invalid% |
|---|---:|---:|---:|
| orientation | 103 | 0.7670 | 0.0000 |

*Report generated from frozen protocol v0.1; semantic transforms frozen in semantic_transform_validity.csv before any Tier-B result was inspected.*
