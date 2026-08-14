# Paper-2 R1 Seed Campaign: Independent Numerical Audit

**Verdict: PASS**

Method: standalone reimplementation (scripts/audit_paper2_numbers_independent.py) of the frozen metric formulas directly from raw prediction CSVs/JSONL and frozen protocol manifests. No analyzer module imported; committed analysis JSONs loaded only as comparison targets. Hard-fail rule: any deterministic-proportion discrepancy > 1e-6, any row-count/ID mismatch, any terminology mismatch => FAIL.

## Claim-level audit

- **dA_positive_all_fresh_seeds_both_backbones**: PASS
- **dG_positive_all_fresh_seeds_both_backbones**: PASS
- **fresh_2b_cpair_exceed_2b_zero_shot**: PASS
- **fresh_seed_cpair_close_to_legacy_general**: PASS
- **q3vl_only_supported_quantities**: PASS

## qwen2vl

### Committed-target check (general_lora, tier-a)

| condition | committed | recomputed | abs diff | pass |
|---|---|---|---|---|
| general_lora_normal | 0.82414579 | 0.82414579 | 0.00e+00 | True |
| general_lora_shuffle | 0.47198178 | 0.47198178 | 0.00e+00 | True |

### Headline quantities

- seed-0: dA +0.0542, dG +0.0456, G 0.3522
- r1_seedA: dA +0.0547, dG +0.0478, G 0.3544
- r1_seedB: dA +0.0456, dG +0.0378, G 0.3444
- r1_seedC: dA +0.0515, dG +0.0465, G 0.3531
- fresh-seed dA: mean 0.0506 +/- 0.0046; dG: mean 0.0440 +/- 0.0054

### Tier-C hflip_flip (n=245)

| checkpoint | A_transform | C_pair | both_correct |
|---|---|---|---|
| zero_shot | 0.6367 | 0.6163 | 0.5388 |
| general_lora | 0.6571 | 0.6857 | 0.5959 |
| r1_seedA | 0.6490 | 0.6490 | 0.5796 |
| r1_seedB | 0.6571 | 0.6898 | 0.6041 |
| r1_seedC | 0.6449 | 0.6653 | 0.5837 |

## smolvlm2

### Committed-target check (general_lora, tier-a)

| condition | committed | recomputed | abs diff | pass |
|---|---|---|---|---|
| general_lora_normal | 0.76492027 | 0.76492027 | 0.00e+00 | True |
| general_lora_shuffle | 0.46742597 | 0.46742597 | 0.00e+00 | True |

### Headline quantities

- seed-0: dA +0.0287, dG +0.0305, G 0.2975
- r1_seedA: dA +0.0305, dG +0.0337, G 0.3007
- r1_seedB: dA +0.0323, dG +0.0287, G 0.2957
- r1_seedC: dA +0.0319, dG +0.0323, G 0.2993
- fresh-seed dA: mean 0.0316 +/- 0.0009; dG: mean 0.0316 +/- 0.0026

### Tier-C hflip_flip (n=245)

| checkpoint | A_transform | C_pair | both_correct |
|---|---|---|---|
| zero_shot | 0.4980 | 0.3184 | 0.2531 |
| general_lora | 0.5224 | 0.3469 | 0.2980 |
| r1_seedA | 0.5469 | 0.3429 | 0.3061 |
| r1_seedB | 0.5469 | 0.3633 | 0.3143 |
| r1_seedC | 0.5469 | 0.3714 | 0.3224 |

## Qwen3-VL-8B (extension; only computed quantities)

| checkpoint | normal | shuffle | hflip_flip A_transform | hflip_invariant A_transform |
|---|---|---|---|---|
| zero_shot | 0.8141 | 0.4670 | 0.6571 | 0.7838 |
| general_lora | 0.8465 | 0.4638 | 0.7020 | 0.8124 |

Q3VL deltas: dA +0.0323, dG +0.0355, hflip_flip A_transform +0.0449 (transformed-accuracy gain only; C_pair NOT computed for the extension).

## Terminology audit

- A_transform = P(transformed prediction == expected transformed label): transformed-answer accuracy. Used consistently in tables above (never "flip rate").
- C_pair = P(pair consistency): linked-answer law compliance (hflip_flip/relcomp/facing: P(transformed != normal); hflip_invariant: P(transformed == normal)). Recomputed by joining normal and transformed predictions on example_id.
- both_correct = P(normal-correct AND transformed obeys the law): joint correctness, never consistency.
- Seeds are independent draws: fresh-seed statements report means/SDs and ranges, never "monotonic".
