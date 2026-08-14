# Tier-A Evidence-Dependence Audit Report

- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash 018b5dd4ce4b...)
- **Run tag:** r1_campaign  |  **Status label:** confirmatory
- **Git commit:** 9b994a2a052f86be9f9d15743c202c4e0c8e0c22  |  branch HEAD
- **Generated:** 2026-08-13T20:03:34+00:00
- **Prediction files:** 24

> Interpretation guardrails (protocol section 16): larger ablation gaps are reported as **visual-evidence dependence** or **evidence consistent with stronger visual dependence**. They are not asserted as proof of internal grounding, geometric reasoning, or memorization.

## Accuracy by checkpoint and condition

| Checkpoint | normal | shuffle | blank | text_only | invalid% |
|---|---:|---:|---:|---:|---:|
| zero_shot | 0.7699 | 0.4633 | 0.4620 | 0.4620 | 0.0000 |
| general_lora | 0.8241 | 0.4720 | 0.4647 | 0.4829 | 0.0000 |
| hardneg_lora | 0.8292 | 0.4683 | 0.4624 | 0.4811 | 0.0000 |
| r1_seedA | 0.8246 | 0.4702 | 0.4642 | 0.4774 | 0.0000 |
| r1_seedB | 0.8155 | 0.4711 | 0.4670 | 0.4916 | 0.0000 |
| r1_seedC | 0.8214 | 0.4683 | 0.4615 | 0.4797 | 0.0000 |

Accuracy `A(m,c)` = correct / total (invalid outputs count as incorrect, matching prior repo convention); invalid rates are always reported separately.

## Visual-evidence dependence gaps

| Checkpoint | G_shuffle | G_blank | G_text |
|---|---:|---:|---:|
| zero_shot | 0.3066 | 0.3080 | 0.3080 |
| general_lora | 0.3522 | 0.3595 | 0.3412 |
| hardneg_lora | 0.3608 | 0.3667 | 0.3481 |
| r1_seedA | 0.3544 | 0.3604 | 0.3472 |
| r1_seedB | 0.3444 | 0.3485 | 0.3239 |
| r1_seedC | 0.3531 | 0.3599 | 0.3417 |

`G_shuffle(m) = A(m,normal) - A(m,shuffle)` is the primary evidence-ablation gap. Blank and text-only gaps are secondary/diagnostic; text-only behavior is exploratory and not the strongest grounding evidence (evidence hierarchy, protocol section 7).

## Transitions (paired, normal condition)

| Transition | DeltaA | DeltaG_shuffle | DeltaG_blank | DeltaG_text |
|---|---:|---:|---:|---:|
| P1 zero_shot -> general_lora | 0.0542 | 0.0456 | 0.0515 | 0.0333 |
| D1 general_lora -> hardneg_lora | 0.0050 | 0.0087 | 0.0073 | 0.0068 |

`DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)`. A positive value is evidence consistent with greater dependence on the correct image; it is not by itself proof of grounding.

## Paired tests and CIs

### P1: zero_shot vs general_lora

- Exact McNemar (normal): b=236 c=117 p=0.0 OR=2.017
- delta_a_ci: mean=0.054214 95% CI [0.037358, 0.071071] (bootstrap n=2195)
- did_ci: mean=0.045558 95% CI [0.02779, 0.063326] (bootstrap n=2195)
- g_shuffle_general_lora_ci: mean=0.352164 95% CI [0.32574, 0.379043] (bootstrap n=2195)
- g_shuffle_zero_shot_ci: mean=0.306606 95% CI [0.283371, 0.330296] (bootstrap n=2195)
- Effect sizes: {'cohens_h_deltaA': 0.1351}

### D1: general_lora vs hardneg_lora

- Exact McNemar (normal): b=58 c=47 p=0.329137 OR=1.234
- delta_a_ci: mean=0.005011 95% CI [-0.0041, 0.014123] (bootstrap n=2195)
- did_ci: mean=0.008656 95% CI [-0.001822, 0.01959] (bootstrap n=2195)
- g_shuffle_general_lora_ci: mean=0.352164 95% CI [0.32574, 0.379043] (bootstrap n=2195)
- g_shuffle_hardneg_lora_ci: mean=0.36082 95% CI [0.333941, 0.387699] (bootstrap n=2195)
- Effect sizes: {'cohens_h_deltaA': 0.0132}

## Relation-family breakdown (descriptive; relation-level inference is secondary)

### normal

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.7692 | 0 |
| containment | 171 | 0.8772 | 0 |
| depth | 322 | 0.6894 | 0 |
| horizontal | 371 | 0.8113 | 0 |
| orientation | 137 | 0.5985 | 0 |
| other | 96 | 0.8125 | 0 |
| proximity | 153 | 0.6993 | 0 |
| topology_contact | 454 | 0.7819 | 0 |
| vertical | 426 | 0.8099 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8000 | 0 |
| containment | 171 | 0.8889 | 0 |
| depth | 322 | 0.8075 | 0 |
| horizontal | 371 | 0.8356 | 0 |
| orientation | 137 | 0.6715 | 0 |
| other | 96 | 0.7500 | 0 |
| proximity | 153 | 0.8497 | 0 |
| topology_contact | 454 | 0.8326 | 0 |
| vertical | 426 | 0.8521 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.7692 | 0 |
| containment | 171 | 0.8889 | 0 |
| depth | 322 | 0.8168 | 0 |
| horizontal | 371 | 0.8571 | 0 |
| orientation | 137 | 0.6569 | 0 |
| other | 96 | 0.7604 | 0 |
| proximity | 153 | 0.8497 | 0 |
| topology_contact | 454 | 0.8304 | 0 |
| vertical | 426 | 0.8615 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.7692 | 0 |
| containment | 171 | 0.8947 | 0 |
| depth | 322 | 0.7764 | 0 |
| horizontal | 371 | 0.8625 | 0 |
| orientation | 137 | 0.6277 | 0 |
| other | 96 | 0.7812 | 0 |
| proximity | 153 | 0.8693 | 0 |
| topology_contact | 454 | 0.8216 | 0 |
| vertical | 426 | 0.8685 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8000 | 0 |
| containment | 171 | 0.8830 | 0 |
| depth | 322 | 0.7702 | 0 |
| horizontal | 371 | 0.8464 | 0 |
| orientation | 137 | 0.6496 | 0 |
| other | 96 | 0.7708 | 0 |
| proximity | 153 | 0.8497 | 0 |
| topology_contact | 454 | 0.8084 | 0 |
| vertical | 426 | 0.8568 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.8000 | 0 |
| containment | 171 | 0.8889 | 0 |
| depth | 322 | 0.7950 | 0 |
| horizontal | 371 | 0.8437 | 0 |
| orientation | 137 | 0.6569 | 0 |
| other | 96 | 0.8125 | 0 |
| proximity | 153 | 0.8105 | 0 |
| topology_contact | 454 | 0.8348 | 0 |
| vertical | 426 | 0.8427 | 0 |


### shuffle

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5322 | 0 |
| depth | 322 | 0.4224 | 0 |
| horizontal | 371 | 0.4447 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4688 | 0 |
| proximity | 153 | 0.4118 | 0 |
| topology_contact | 454 | 0.5022 | 0 |
| vertical | 426 | 0.4343 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5846 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4379 | 0 |
| horizontal | 371 | 0.4474 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4896 | 0 |
| proximity | 153 | 0.4575 | 0 |
| topology_contact | 454 | 0.5044 | 0 |
| vertical | 426 | 0.4390 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5846 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4503 | 0 |
| horizontal | 371 | 0.4420 | 0 |
| orientation | 137 | 0.4818 | 0 |
| other | 96 | 0.4375 | 0 |
| proximity | 153 | 0.4575 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4366 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5692 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4410 | 0 |
| horizontal | 371 | 0.4501 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4792 | 0 |
| proximity | 153 | 0.4379 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4413 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5846 | 0 |
| containment | 171 | 0.5322 | 0 |
| depth | 322 | 0.4410 | 0 |
| horizontal | 371 | 0.4501 | 0 |
| orientation | 137 | 0.4891 | 0 |
| other | 96 | 0.4792 | 0 |
| proximity | 153 | 0.4314 | 0 |
| topology_contact | 454 | 0.5066 | 0 |
| vertical | 426 | 0.4390 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5846 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4410 | 0 |
| horizontal | 371 | 0.4447 | 0 |
| orientation | 137 | 0.4891 | 0 |
| other | 96 | 0.4792 | 0 |
| proximity | 153 | 0.4248 | 0 |
| topology_contact | 454 | 0.5000 | 0 |
| vertical | 426 | 0.4413 | 0 |


### blank

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5322 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4420 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4896 | 0 |
| proximity | 153 | 0.4183 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4319 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5385 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4420 | 0 |
| orientation | 137 | 0.4891 | 0 |
| other | 96 | 0.5000 | 0 |
| proximity | 153 | 0.4706 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4319 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5231 | 0 |
| containment | 171 | 0.5263 | 0 |
| depth | 322 | 0.4255 | 0 |
| horizontal | 371 | 0.4367 | 0 |
| orientation | 137 | 0.5036 | 0 |
| other | 96 | 0.4688 | 0 |
| proximity | 153 | 0.4706 | 0 |
| topology_contact | 454 | 0.4890 | 0 |
| vertical | 426 | 0.4319 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5385 | 0 |
| containment | 171 | 0.5146 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4394 | 0 |
| orientation | 137 | 0.4599 | 0 |
| other | 96 | 0.5208 | 0 |
| proximity | 153 | 0.4837 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4390 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5380 | 0 |
| depth | 322 | 0.4068 | 0 |
| horizontal | 371 | 0.4367 | 0 |
| orientation | 137 | 0.5036 | 0 |
| other | 96 | 0.5312 | 0 |
| proximity | 153 | 0.4575 | 0 |
| topology_contact | 454 | 0.4978 | 0 |
| vertical | 426 | 0.4413 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5231 | 0 |
| containment | 171 | 0.4795 | 0 |
| depth | 322 | 0.4255 | 0 |
| horizontal | 371 | 0.4394 | 0 |
| orientation | 137 | 0.4818 | 0 |
| other | 96 | 0.5000 | 0 |
| proximity | 153 | 0.4641 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4413 | 0 |


### text_only

**zero_shot**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5538 | 0 |
| containment | 171 | 0.5322 | 0 |
| depth | 322 | 0.4193 | 0 |
| horizontal | 371 | 0.4420 | 0 |
| orientation | 137 | 0.4964 | 0 |
| other | 96 | 0.4896 | 0 |
| proximity | 153 | 0.4183 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4319 | 0 |

**general_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5077 | 0 |
| containment | 171 | 0.4620 | 0 |
| depth | 322 | 0.4472 | 0 |
| horizontal | 371 | 0.4852 | 0 |
| orientation | 137 | 0.5474 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.5425 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4531 | 0 |

**hardneg_lora**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5231 | 0 |
| containment | 171 | 0.4678 | 0 |
| depth | 322 | 0.4379 | 0 |
| horizontal | 371 | 0.4717 | 0 |
| orientation | 137 | 0.5328 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.5229 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4695 | 0 |

**r1_seedA**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5385 | 0 |
| containment | 171 | 0.4620 | 0 |
| depth | 322 | 0.4410 | 0 |
| horizontal | 371 | 0.4690 | 0 |
| orientation | 137 | 0.5255 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.5033 | 0 |
| topology_contact | 454 | 0.4956 | 0 |
| vertical | 426 | 0.4577 | 0 |

**r1_seedB**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5385 | 0 |
| containment | 171 | 0.4678 | 0 |
| depth | 322 | 0.4472 | 0 |
| horizontal | 371 | 0.4852 | 0 |
| orientation | 137 | 0.5182 | 0 |
| other | 96 | 0.4688 | 0 |
| proximity | 153 | 0.5425 | 0 |
| topology_contact | 454 | 0.5044 | 0 |
| vertical | 426 | 0.4977 | 0 |

**r1_seedC**

| Family | n | accuracy | invalid |
|---|---:|---:|---:|
| compositional | 65 | 0.5077 | 0 |
| containment | 171 | 0.4386 | 0 |
| depth | 322 | 0.4317 | 0 |
| horizontal | 371 | 0.5094 | 0 |
| orientation | 137 | 0.5109 | 0 |
| other | 96 | 0.5104 | 0 |
| proximity | 153 | 0.4902 | 0 |
| topology_contact | 454 | 0.4934 | 0 |
| vertical | 426 | 0.4671 | 0 |



*Report generated from frozen protocol v0.1; predictions: 24 files.*