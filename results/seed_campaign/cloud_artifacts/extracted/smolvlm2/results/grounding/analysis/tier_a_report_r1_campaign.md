# Tier-A Evidence-Dependence Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b...)
- **Run tag:** r1_campaign  |  **Status label:** confirmatory
- **Git commit:** 9b994a2a052f86be9f9d15743c202c4e0c8e0c22  |  branch HEAD
- **Generated:** 2026-08-13T22:33:31+00:00
- **Prediction files:** 20

> Interpretation guardrails (protocol section 16): larger ablation gaps are reported as **visual-evidence dependence** or **evidence consistent with stronger visual dependence**. They are not asserted as proof of internal grounding, geometric reasoning, or memorization.

## Accuracy by checkpoint and condition

| Checkpoint | normal | shuffle | blank | text_only | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.7362 | 0.4692 | 0.4670 | 0.5358 | 0.0000 |
| general_lora | 0.7649 | 0.4674 | 0.4679 | 0.5362 | 0.0000 |
| r1_seedA | 0.7667 | 0.4661 | 0.4633 | 0.5394 | 0.0000 |
| r1_seedB | 0.7686 | 0.4729 | 0.4674 | 0.5371 | 0.0000 |
| r1_seedC | 0.7681 | 0.4688 | 0.4656 | 0.5376 | 0.0000 |

Accuracy `A(m,c)` = correct / total (invalid outputs count as incorrect, matching prior repo convention); invalid rates are always reported separately.

## Visual-evidence dependence gaps

| Checkpoint | G_shuffle | G_blank | G_text |
|---|---:|---:|---:|
| zero_shot | 0.2670 | 0.2692 | 0.2005 |
| general_lora | 0.2975 | 0.2970 | 0.2287 |
| r1_seedA | 0.3007 | 0.3034 | 0.2273 |
| r1_seedB | 0.2957 | 0.3011 | 0.2314 |
| r1_seedC | 0.2993 | 0.3025 | 0.2305 |

`G_shuffle(m) = A(m,normal) - A(m,shuffle)` is the primary evidence-ablation gap. Blank and text-only gaps are secondary/diagnostic; text-only behavior is exploratory and not the strongest grounding evidence (evidence hierarchy, protocol section 7).

## Transitions (paired, normal condition)

| Transition | DeltaA | DeltaG_shuffle | DeltaG_blank | DeltaG_text |
|---|---:|---:|---:|---:|
| P1 zero_shot -> general_lora | 0.0287 | 0.0305 | 0.0278 | 0.0282 |

`DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)`. A positive value is evidence consistent with greater dependence on the correct image; it is not by itself proof of grounding.

## Paired tests and CIs

### P1: zero_shot vs general_lora

- Exact McNemar (normal): b=125 c=62 p=5e-06 OR=2.016
- delta_a_ci: mean=0.028702 95% CI [0.016401, 0.041002] (bootstrap n=2195)
- did_ci: mean=0.030524 95% CI [0.016856, 0.044647] (bootstrap n=2195)
- g_shuffle_general_lora_ci: mean=0.297494 95% CI [0.269704, 0.32574] (bootstrap n=2195)
- g_shuffle_zero_shot_ci: mean=0.26697 95% CI [0.238724, 0.295216] (bootstrap n=2195)
- Effect sizes: {'cohens_h_deltaA': 0.0664}

## Relation-family breakdown (descriptive; relation-level inference is secondary)

### normal

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.7846 | 0 |
| containment | 171 | 0.8304 | 0 |
| depth | 322 | 0.6863 | 0 |
| horizontal | 371 | 0.7035 | 0 |
| orientation | 137 | 0.6423 | 0 |
| other | 96 | 0.7292 | 0 |
| proximity | 153 | 0.7843 | 0 |
| topology_contact | 454 | 0.7930 | 0 |
| vertical | 426 | 0.7113 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8308 | 0 |
| containment | 171 | 0.8889 | 0 |
| depth | 322 | 0.7112 | 0 |
| horizontal | 371 | 0.7358 | 0 |
| orientation | 137 | 0.6204 | 0 |
| other | 96 | 0.7500 | 0 |
| proximity | 153 | 0.8497 | 0 |
| topology_contact | 454 | 0.8018 | 0 |
| vertical | 426 | 0.7512 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8308 | 0 |
| containment | 171 | 0.8947 | 0 |
| depth | 322 | 0.7143 | 0 |
| horizontal | 371 | 0.7332 | 0 |
| orientation | 137 | 0.6277 | 0 |
| other | 96 | 0.7604 | 0 |
| proximity | 153 | 0.8562 | 0 |
| topology_contact | 454 | 0.8062 | 0 |
| vertical | 426 | 0.7465 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8308 | 0 |
| containment | 171 | 0.9006 | 0 |
| depth | 322 | 0.7236 | 0 |
| horizontal | 371 | 0.7278 | 0 |
| orientation | 137 | 0.6204 | 0 |
| other | 96 | 0.7604 | 0 |
| proximity | 153 | 0.8497 | 0 |
| topology_contact | 454 | 0.8150 | 0 |
| vertical | 426 | 0.7465 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8308 | 0 |
| containment | 171 | 0.8830 | 0 |
| depth | 322 | 0.7174 | 0 |
| horizontal | 371 | 0.7358 | 0 |
| orientation | 137 | 0.6350 | 0 |
| other | 96 | 0.7708 | 0 |
| proximity | 153 | 0.8562 | 0 |
| topology_contact | 454 | 0.7996 | 0 |
| vertical | 426 | 0.7559 | 0 |


### shuffle

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4286 | 0 |
| horizontal | 371 | 0.4447 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4688 | 0 |
| proximity | 153 | 0.5229 | 0 |
| topology_contact | 454 | 0.4978 | 0 |
| vertical | 426 | 0.4272 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.5205 | 0 |
| depth | 322 | 0.4161 | 0 |
| horizontal | 371 | 0.4340 | 0 |
| orientation | 137 | 0.5328 | 0 |
| other | 96 | 0.5000 | 0 |
| proximity | 153 | 0.4837 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4343 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5205 | 0 |
| depth | 322 | 0.4161 | 0 |
| horizontal | 371 | 0.4313 | 0 |
| orientation | 137 | 0.5328 | 0 |
| other | 96 | 0.5000 | 0 |
| proximity | 153 | 0.4641 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4343 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.5205 | 0 |
| depth | 322 | 0.4317 | 0 |
| horizontal | 371 | 0.4340 | 0 |
| orientation | 137 | 0.5474 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.4902 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4366 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.5205 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4340 | 0 |
| orientation | 137 | 0.5328 | 0 |
| other | 96 | 0.5000 | 0 |
| proximity | 153 | 0.4837 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4343 | 0 |


### blank

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.4795 | 0 |
| depth | 322 | 0.4224 | 0 |
| horizontal | 371 | 0.4582 | 0 |
| orientation | 137 | 0.4818 | 0 |
| other | 96 | 0.5625 | 0 |
| proximity | 153 | 0.5098 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4178 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.4854 | 0 |
| depth | 322 | 0.4224 | 0 |
| horizontal | 371 | 0.4555 | 0 |
| orientation | 137 | 0.4745 | 0 |
| other | 96 | 0.5625 | 0 |
| proximity | 153 | 0.4902 | 0 |
| topology_contact | 454 | 0.4978 | 0 |
| vertical | 426 | 0.4272 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.4737 | 0 |
| depth | 322 | 0.4224 | 0 |
| horizontal | 371 | 0.4474 | 0 |
| orientation | 137 | 0.4818 | 0 |
| other | 96 | 0.5312 | 0 |
| proximity | 153 | 0.4837 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4272 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.4912 | 0 |
| depth | 322 | 0.4224 | 0 |
| horizontal | 371 | 0.4501 | 0 |
| orientation | 137 | 0.4891 | 0 |
| other | 96 | 0.5208 | 0 |
| proximity | 153 | 0.5163 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4272 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.4912 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4447 | 0 |
| orientation | 137 | 0.5036 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.5033 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4296 | 0 |


### text_only

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5385 | 0 |
| containment | 171 | 0.5088 | 0 |
| depth | 322 | 0.5342 | 0 |
| horizontal | 371 | 0.5768 | 0 |
| orientation | 137 | 0.5255 | 0 |
| other | 96 | 0.5521 | 0 |
| proximity | 153 | 0.5752 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.5352 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5029 | 0 |
| depth | 322 | 0.5559 | 0 |
| horizontal | 371 | 0.5418 | 0 |
| orientation | 137 | 0.5109 | 0 |
| other | 96 | 0.5521 | 0 |
| proximity | 153 | 0.5817 | 0 |
| topology_contact | 454 | 0.5132 | 0 |
| vertical | 426 | 0.5399 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5029 | 0 |
| depth | 322 | 0.5590 | 0 |
| horizontal | 371 | 0.5606 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.5729 | 0 |
| proximity | 153 | 0.5817 | 0 |
| topology_contact | 454 | 0.5088 | 0 |
| vertical | 426 | 0.5423 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.4912 | 0 |
| depth | 322 | 0.5621 | 0 |
| horizontal | 371 | 0.5526 | 0 |
| orientation | 137 | 0.5109 | 0 |
| other | 96 | 0.5729 | 0 |
| proximity | 153 | 0.5817 | 0 |
| topology_contact | 454 | 0.5066 | 0 |
| vertical | 426 | 0.5376 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.4971 | 0 |
| depth | 322 | 0.5559 | 0 |
| horizontal | 371 | 0.5499 | 0 |
| orientation | 137 | 0.5109 | 0 |
| other | 96 | 0.5833 | 0 |
| proximity | 153 | 0.5817 | 0 |
| topology_contact | 454 | 0.5044 | 0 |
| vertical | 426 | 0.5446 | 0 |



*Report generated from frozen protocol v0.1; predictions: 20 files.*