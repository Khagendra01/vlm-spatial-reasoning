# Paper-2 R1: Canonical Publication Tables (audit-sourced)

All values from numerical_audit.json (Step-1 independent audit, PASS).

## Table 1 — Headline adaptation quantities (per seed)

| family | checkpoint | ΔA | G | ΔG |
|---|---|---|---|---|
| Qwen2-VL-7B | seed-0 | +0.0542 | 0.3522 | +0.0456 |
| Qwen2-VL-7B | seedA | +0.0547 | 0.3544 | +0.0478 |
| Qwen2-VL-7B | seedB | +0.0456 | 0.3444 | +0.0378 |
| Qwen2-VL-7B | seedC | +0.0515 | 0.3531 | +0.0465 |
| SmolVLM2-2B | seed-0 | +0.0287 | 0.2975 | +0.0305 |
| SmolVLM2-2B | seedA | +0.0305 | 0.3007 | +0.0337 |
| SmolVLM2-2B | seedB | +0.0323 | 0.2957 | +0.0287 |
| SmolVLM2-2B | seedC | +0.0319 | 0.2993 | +0.0323 |
| Qwen3-VL-8B | tuned | +0.0323 | 0.3827 | +0.0355 |

## Table 2 — Tier-C transformation behavior, hflip_flip (n=245)

| family | checkpoint | A_transform | C_pair | both_correct |
|---|---|---|---|---|
| Qwen2-VL-7B | zero_shot | 0.6367 | 0.6163 | 0.5388 |
| Qwen2-VL-7B | general_lora | 0.6571 | 0.6857 | 0.5959 |
| Qwen2-VL-7B | r1_seedA | 0.6490 | 0.6490 | 0.5796 |
| Qwen2-VL-7B | r1_seedB | 0.6571 | 0.6898 | 0.6041 |
| Qwen2-VL-7B | r1_seedC | 0.6449 | 0.6653 | 0.5837 |
| SmolVLM2-2B | zero_shot | 0.4980 | 0.3184 | 0.2531 |
| SmolVLM2-2B | general_lora | 0.5224 | 0.3469 | 0.2980 |
| SmolVLM2-2B | r1_seedA | 0.5469 | 0.3429 | 0.3061 |
| SmolVLM2-2B | r1_seedB | 0.5469 | 0.3633 | 0.3143 |
| SmolVLM2-2B | r1_seedC | 0.5469 | 0.3714 | 0.3224 |

## Table 3 — Fresh-seed summary statistics

| family | ΔA mean ± SD | ΔG mean ± SD |
|---|---|---|
| Qwen2-VL-7B | +0.0506 ± 0.0046 | +0.0440 ± 0.0054 |
| SmolVLM2-2B | +0.0316 ± 0.0009 | +0.0316 ± 0.0026 |

## Table 4 — Qwen3-VL-8B post-confirmatory extension

| metric | zero-shot | tuned | Δ |
|---|---|---|---|
| normal accuracy | 0.8141 | 0.8465 | +0.0323 |
| shuffle accuracy | 0.4670 | 0.4638 | -0.0032 |
| hflip_flip A_transform | 0.6571 | 0.7020 | +0.0449 |

C_pair not computed for the extension; no response-law claim.

## Table 5 — Canonical subset sizes (frozen)

| condition | n | source |
|---|---|---|
| normal / shuffle / blank / text_only | 2195 | vsr_test_ids.json |
| relcomp | 666 | semantic_eligible_ids.json |
| facingcomp | 103 | facing_eligible_ids.json |
| hflip_flip | 245 | visual_eligible_ids.json |
| hflip_invariant | 421 | visual_eligible_ids.json |
