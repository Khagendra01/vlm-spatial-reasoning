# Tier-A Evidence-Dependence Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b...)
- **Run tag:** smoke10  |  **Status label:** engineering
- **Git commit:** 2f047945e4a22ea8774c8172826991930be36ad0  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-10T21:43:53+00:00
- **Prediction files:** 12

> Interpretation guardrails (protocol section 16): larger ablation gaps are reported as **visual-evidence dependence** or **evidence consistent with stronger visual dependence**. They are not asserted as proof of internal grounding, geometric reasoning, or memorization.

## Accuracy by checkpoint and condition

| Checkpoint | normal | shuffle | blank | text_only | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.6000 | 0.5000 | 0.5000 | 0.5000 | 0.0000 |
| general_lora | 0.6000 | 0.5000 | 0.5000 | 0.4000 | 0.0000 |
| hardneg_lora | 0.6000 | 0.5000 | 0.4000 | 0.3000 | 0.0000 |

Accuracy `A(m,c)` = correct / total (invalid outputs count as incorrect, matching prior repo convention); invalid rates are always reported separately.

## Visual-evidence dependence gaps

| Checkpoint | G_shuffle | G_blank | G_text |
|---|---:|---:|---:|
| zero_shot | 0.1000 | 0.1000 | 0.1000 |
| general_lora | 0.1000 | 0.1000 | 0.2000 |
| hardneg_lora | 0.1000 | 0.2000 | 0.3000 |

`G_shuffle(m) = A(m,normal) - A(m,shuffle)` is the primary evidence-ablation gap. Blank and text-only gaps are secondary/diagnostic; text-only behavior is exploratory and not the strongest grounding evidence (evidence hierarchy, protocol section 7).

## Transitions (paired, normal condition)

| Transition | DeltaA | DeltaG_shuffle | DeltaG_blank | DeltaG_text |
|---|---:|---:|---:|---:|
| P1 zero_shot -> general_lora | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
| D1 general_lora -> hardneg_lora | 0.0000 | 0.0000 | 0.1000 | 0.1000 |

`DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)`. A positive value is evidence consistent with greater dependence on the correct image; it is not by itself proof of grounding.

## Paired tests and CIs

### P1: zero_shot vs general_lora

- Exact McNemar (normal): b=1 c=1 p=1.0 OR=1
- delta_a_ci: mean=0.0 95% CI [-0.3, 0.3] (bootstrap n=10)
- did_ci: mean=0.0 95% CI [-0.3, 0.3] (bootstrap n=10)
- g_shuffle_general_lora_ci: mean=0.1 95% CI [-0.3, 0.5] (bootstrap n=10)
- g_shuffle_zero_shot_ci: mean=0.1 95% CI [-0.2, 0.4] (bootstrap n=10)
- Effect sizes: {'cohens_h_deltaA': 0.0}

### D1: general_lora vs hardneg_lora

- Exact McNemar (normal): b=0 c=0 p=1.0 OR=inf
- delta_a_ci: mean=0.0 95% CI [0.0, 0.0] (bootstrap n=10)
- did_ci: mean=0.0 95% CI [0.0, 0.0] (bootstrap n=10)
- g_shuffle_general_lora_ci: mean=0.1 95% CI [-0.3, 0.5] (bootstrap n=10)
- g_shuffle_hardneg_lora_ci: mean=0.1 95% CI [-0.3, 0.5] (bootstrap n=10)
- Effect sizes: {'cohens_h_deltaA': 0.0}

## Relation-family breakdown (descriptive; relation-level inference is secondary)

### normal

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 1.0000 | 0 |
| horizontal | 1 | 1.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 0.0000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 1.0000 | 0 |
| horizontal | 1 | 1.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 0.0000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 1.0000 | 0 |
| horizontal | 1 | 1.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 0.0000 | 0 |


### shuffle

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |


### blank

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.0000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |


### text_only

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.0000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.5000 | 0 |
| vertical | 1 | 1.0000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 1 | 0.0000 | 0 |
| containment | 2 | 0.5000 | 0 |
| depth | 2 | 0.5000 | 0 |
| horizontal | 1 | 0.0000 | 0 |
| orientation | 1 | 1.0000 | 0 |
| topology_contact | 2 | 0.0000 | 0 |
| vertical | 1 | 0.0000 | 0 |



*Report generated from frozen protocol v0.1; predictions: 12 files.*