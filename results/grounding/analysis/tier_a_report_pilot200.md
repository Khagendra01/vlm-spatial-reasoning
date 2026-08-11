# Tier-A Evidence-Dependence Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b...)
- **Run tag:** pilot200  |  **Status label:** engineering
- **Git commit:** 2f047945e4a22ea8774c8172826991930be36ad0  |  branch research/spatial-grounding-audit
- **Generated:** 2026-08-10T21:54:27+00:00
- **Prediction files:** 12

> Interpretation guardrails (protocol section 16): larger ablation gaps are reported as **visual-evidence dependence** or **evidence consistent with stronger visual dependence**. They are not asserted as proof of internal grounding, geometric reasoning, or memorization.

## Accuracy by checkpoint and condition

| Checkpoint | normal | shuffle | blank | text_only | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.7350 | 0.4400 | 0.4350 | 0.4350 | 0.0000 |
| general_lora | 0.8300 | 0.4500 | 0.4500 | 0.4250 | 0.0000 |
| hardneg_lora | 0.8250 | 0.4400 | 0.4400 | 0.4400 | 0.0000 |

Accuracy `A(m,c)` = correct / total (invalid outputs count as incorrect, matching prior repo convention); invalid rates are always reported separately.

## Visual-evidence dependence gaps

| Checkpoint | G_shuffle | G_blank | G_text |
|---|---:|---:|---:|
| zero_shot | 0.2950 | 0.3000 | 0.3000 |
| general_lora | 0.3800 | 0.3800 | 0.4050 |
| hardneg_lora | 0.3850 | 0.3850 | 0.3850 |

`G_shuffle(m) = A(m,normal) - A(m,shuffle)` is the primary evidence-ablation gap. Blank and text-only gaps are secondary/diagnostic; text-only behavior is exploratory and not the strongest grounding evidence (evidence hierarchy, protocol section 7).

## Transitions (paired, normal condition)

| Transition | DeltaA | DeltaG_shuffle | DeltaG_blank | DeltaG_text |
|---|---:|---:|---:|---:|
| P1 zero_shot -> general_lora | 0.0950 | 0.0850 | 0.0800 | 0.1050 |
| D1 general_lora -> hardneg_lora | -0.0050 | 0.0050 | 0.0050 | -0.0200 |

`DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)`. A positive value is evidence consistent with greater dependence on the correct image; it is not by itself proof of grounding.

## Paired tests and CIs

### P1: zero_shot vs general_lora

- Exact McNemar (normal): b=28 c=9 p=0.002563 OR=3.111
- delta_a_ci: mean=0.095 95% CI [0.035, 0.155] (bootstrap n=200)
- did_ci: mean=0.085 95% CI [0.025, 0.145] (bootstrap n=200)
- g_shuffle_general_lora_ci: mean=0.38 95% CI [0.295, 0.465] (bootstrap n=200)
- g_shuffle_zero_shot_ci: mean=0.295 95% CI [0.22, 0.375] (bootstrap n=200)
- Effect sizes: {'cohens_h_deltaA': 0.2315}

### D1: general_lora vs hardneg_lora

- Exact McNemar (normal): b=3 c=4 p=1.0 OR=0.75
- delta_a_ci: mean=-0.005 95% CI [-0.03, 0.02] (bootstrap n=200)
- did_ci: mean=0.005 95% CI [-0.03, 0.035] (bootstrap n=200)
- g_shuffle_general_lora_ci: mean=0.38 95% CI [0.295, 0.465] (bootstrap n=200)
- g_shuffle_hardneg_lora_ci: mean=0.385 95% CI [0.295, 0.475] (bootstrap n=200)
- Effect sizes: {'cohens_h_deltaA': -0.0132}

## Relation-family breakdown (descriptive; relation-level inference is secondary)

### normal

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.6000 | 0 |
| containment | 24 | 0.8333 | 0 |
| depth | 25 | 0.7200 | 0 |
| horizontal | 35 | 0.7714 | 0 |
| orientation | 13 | 0.5385 | 0 |
| other | 4 | 1.0000 | 0 |
| proximity | 14 | 0.7143 | 0 |
| topology_contact | 42 | 0.6905 | 0 |
| vertical | 38 | 0.7632 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.6000 | 0 |
| containment | 24 | 0.8750 | 0 |
| depth | 25 | 0.8000 | 0 |
| horizontal | 35 | 0.8857 | 0 |
| orientation | 13 | 0.7692 | 0 |
| other | 4 | 0.7500 | 0 |
| proximity | 14 | 0.9286 | 0 |
| topology_contact | 42 | 0.7619 | 0 |
| vertical | 38 | 0.8684 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.6000 | 0 |
| containment | 24 | 0.8750 | 0 |
| depth | 25 | 0.8800 | 0 |
| horizontal | 35 | 0.8857 | 0 |
| orientation | 13 | 0.7692 | 0 |
| other | 4 | 0.5000 | 0 |
| proximity | 14 | 0.9286 | 0 |
| topology_contact | 42 | 0.7381 | 0 |
| vertical | 38 | 0.8421 | 0 |


### shuffle

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3600 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.4615 | 0 |
| other | 4 | 0.7500 | 0 |
| proximity | 14 | 0.5000 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.4000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3600 | 0 |
| horizontal | 35 | 0.3143 | 0 |
| orientation | 13 | 0.5385 | 0 |
| other | 4 | 0.7500 | 0 |
| proximity | 14 | 0.5714 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.4000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3600 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.4615 | 0 |
| other | 4 | 0.5000 | 0 |
| proximity | 14 | 0.5000 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5000 | 0 |


### blank

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3200 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.4615 | 0 |
| other | 4 | 0.7500 | 0 |
| proximity | 14 | 0.5000 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3200 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.4615 | 0 |
| other | 4 | 0.5000 | 0 |
| proximity | 14 | 0.7143 | 0 |
| topology_contact | 42 | 0.4762 | 0 |
| vertical | 38 | 0.5526 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.2800 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.3846 | 0 |
| other | 4 | 0.2500 | 0 |
| proximity | 14 | 0.7857 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5263 | 0 |


### text_only

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.4167 | 0 |
| depth | 25 | 0.3200 | 0 |
| horizontal | 35 | 0.3429 | 0 |
| orientation | 13 | 0.4615 | 0 |
| other | 4 | 0.7500 | 0 |
| proximity | 14 | 0.5000 | 0 |
| topology_contact | 42 | 0.5000 | 0 |
| vertical | 38 | 0.5000 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.3750 | 0 |
| depth | 25 | 0.2400 | 0 |
| horizontal | 35 | 0.5429 | 0 |
| orientation | 13 | 0.3077 | 0 |
| other | 4 | 0.0000 | 0 |
| proximity | 14 | 0.5714 | 0 |
| topology_contact | 42 | 0.4524 | 0 |
| vertical | 38 | 0.5000 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 5 | 0.2000 | 0 |
| containment | 24 | 0.2500 | 0 |
| depth | 25 | 0.3200 | 0 |
| horizontal | 35 | 0.5143 | 0 |
| orientation | 13 | 0.3846 | 0 |
| other | 4 | 0.2500 | 0 |
| proximity | 14 | 0.6429 | 0 |
| topology_contact | 42 | 0.4286 | 0 |
| vertical | 38 | 0.5789 | 0 |



*Report generated from frozen protocol v0.1; predictions: 12 files.*