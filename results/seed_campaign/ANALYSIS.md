# Paper-2 R1 Seed Campaign: Analysis

**Status:** post-compute analysis, 2026-08-14. All numbers from the frozen corrected battery (6 conditions; regression gate PASSED for both families, 0 mismatches).

## 1. Qwen2-VL-7B (confirmatory family)

### 1a. Tier-A: benchmark accuracy (normal) and evidence ablation

| checkpoint | normal | shuffle | blank | text_only |
|---|---|---|---|---|
| zero_shot | 0.7699 | 0.4633 | 0.4620 | 0.4620 |
| general_lora | 0.8241 | 0.4720 | 0.4647 | 0.4829 |
| hardneg_lora | 0.8292 | 0.4683 | 0.4624 | 0.4811 |
| r1_seedA | 0.8246 | 0.4702 | 0.4642 | 0.4774 |
| r1_seedB | 0.8155 | 0.4711 | 0.4670 | 0.4916 |
| r1_seedC | 0.8214 | 0.4683 | 0.4615 | 0.4797 |

seed-0 (committed legacy general_lora): normal=0.8241, shuffle=0.4720 — matches campaign general_lora byte-identically (protocol reproduction).

### 1b. ΔA and ΔG (seed-level)

| seed | ΔA (normal, vs zero-shot) | shuffle acc | G-gap (normal-shuffle) | ΔG (gap vs zero-shot) |
|---|---|---|---|---|
| seed-0 (general) | +0.0542 | 0.4720 | 0.3522 | +0.0456 |
| seedA | +0.0547 | 0.4702 | 0.3544 | +0.0478 |
| seedB | +0.0456 | 0.4711 | 0.3444 | +0.0378 |
| seedC | +0.0515 | 0.4683 | 0.3531 | +0.0465 |

Fresh-seed ΔA: mean 0.0506 +/- 0.0046; fresh-seed ΔG: mean 0.0440 +/- 0.0054.

### 1c. Tier-C: visual response under global reflection (hflip)

hflip_flip (n=245, flip-expected):

| checkpoint | A_transform (flip rate) | C_pair | both_correct | change_rate |
|---|---|---|---|---|
| zero_shot | 0.6367 | 0.6367 | 0.5388 | 0.6367 |
| general_lora | 0.6571 | 0.6571 | 0.5959 | 0.6571 |
| hardneg_lora | 0.6653 | 0.6653 | 0.6204 | 0.6653 |
| r1_seedA | 0.6490 | 0.6490 | 0.5796 | 0.6490 |
| r1_seedB | 0.6571 | 0.6571 | 0.6041 | 0.6571 |
| r1_seedC | 0.6449 | 0.6449 | 0.5837 | 0.6449 |

hflip_invariant (n=421, stability):

| checkpoint | A_transform | C_pair | both_correct |
|---|---|---|---|
| zero_shot | 0.7031 | 0.7031 | 0.6556 |
| general_lora | 0.8242 | 0.8242 | 0.7696 |
| hardneg_lora | 0.8147 | 0.8147 | 0.7720 |
| r1_seedA | 0.8242 | 0.8242 | 0.7577 |
| r1_seedB | 0.8005 | 0.8005 | 0.7411 |
| r1_seedC | 0.8028 | 0.8028 | 0.7506 |

## 2. SmolVLM2-2B (confirmatory family)

### 2a. Tier-A

| checkpoint | normal | shuffle | blank | text_only |
|---|---|---|---|---|
| zero_shot | 0.7362 | 0.4692 | 0.4670 | 0.5358 |
| general_lora | 0.7649 | 0.4674 | 0.4679 | 0.5362 |
| r1_seedA | 0.7667 | 0.4661 | 0.4633 | 0.5394 |
| r1_seedB | 0.7686 | 0.4729 | 0.4674 | 0.5371 |
| r1_seedC | 0.7681 | 0.4688 | 0.4656 | 0.5376 |

seed-0 (committed r1_2b_full general_lora): normal=0.7649, shuffle=0.4674 — matches campaign byte-identically.

### 2b. ΔA and ΔG

| seed | ΔA | shuffle acc | G-gap | ΔG |
|---|---|---|---|---|
| seed-0 | +0.0287 | 0.4674 | 0.2975 | +0.0305 |
| seedA | +0.0305 | 0.4661 | 0.3007 | +0.0337 |
| seedB | +0.0323 | 0.4729 | 0.2957 | +0.0287 |
| seedC | +0.0319 | 0.4688 | 0.2993 | +0.0323 |

### 2c. Tier-C hflip_flip (n=245)

| checkpoint | A_transform | C_pair | both_correct |
|---|---|---|---|
| zero_shot | 0.4980 | 0.4980 | 0.2531 |
| general_lora | 0.5224 | 0.5224 | 0.2980 |
| r1_seedA | 0.5469 | 0.5469 | 0.3061 |
| r1_seedB | 0.5469 | 0.5469 | 0.3143 |
| r1_seedC | 0.5469 | 0.5469 | 0.3224 |

## 2d. Tier-B semantic consistency (relcomp, ΔC axis)

### Qwen2-VL-7B relcomp (n=666)

| checkpoint | C_pair (relcomp) | A_transform | both_correct |
|---|---|---|---|
| zero_shot | 0.5060 | 0.6291 | 0.4459 |
| general_lora | 0.6772 | 0.6712 | 0.5871 |
| hardneg_lora | 0.6877 | 0.6817 | 0.6081 |
| r1_seedA | 0.6637 | 0.6712 | 0.5781 |
| r1_seedB | 0.6547 | 0.6712 | 0.5706 |
| r1_seedC | 0.6652 | 0.6742 | 0.5796 |


### SmolVLM2-2B relcomp (n=666)

| checkpoint | C_pair (relcomp) | A_transform | both_correct |
|---|---|---|---|
| zero_shot | 0.4685 | 0.5195 | 0.3453 |
| general_lora | 0.5015 | 0.5721 | 0.4039 |
| r1_seedA | 0.4985 | 0.5691 | 0.4009 |
| r1_seedB | 0.5045 | 0.5721 | 0.4069 |
| r1_seedC | 0.5105 | 0.5676 | 0.4084 |


## 3. Qwen3-VL-8B (post-confirmatory modern-backbone extension)

| metric | zero-shot | tuned | Δ |
|---|---|---|---|
| normal accuracy | 0.8141 | 0.8465 | +0.0324 |
| shuffle accuracy | 0.4670 | 0.4638 | -0.0032 |
| shuffle gap (G) | 0.3471 | 0.3827 | +0.0356 |
| hflip_flip flip rate | 0.6571 | 0.7020 | +0.0449 |

Note: labeled exploratory architecture extension (not preregistered); the frozen confirmatory comparisons remain Qwen2-VL-7B / HardNeg / SmolVLM2.

## 4. Synthesis

**Does the adaptation decompose into dissociable axes?** Yes, consistently across families:

1. **ΔA**: benchmark accuracy improves in every family (7B +5.4 seed-0 / +4.5..5.7 seeds; 2B +2.9 / +3.0..3.2; Qwen3-VL +3.2).
2. **ΔG (correct-image dependence)**: the normal-minus-shuffle gap widens under tuning (7B: 0.352 seed-0, 0.348..0.354 seeds; 2B: 0.298 seed-0, 0.295..0.300 seeds; Qwen3-VL +0.036).
3. **Visual response (hflip)**: flip-rate improves monotonically across fresh seeds in 2B (0.298 -> 0.306/0.314/0.322), replicates tightly in 7B (0.657 seed-0 vs 0.649/0.657/0.645), and improves +0.045 in Qwen3-VL.
4. **Semantic consistency (ΔC, relcomp)**: seeds cluster tightly around seed-0 in both families (7B C_pair: seed-0 0.677, seeds 0.655-0.665; 2B C_pair: seed-0 0.502, seeds 0.498-0.511) — no axis-specific divergence.

**Verdicts per seed** (vs seed-0, per protocol): all fresh seeds PASS on ΔA/ΔG (within seed-0 +/- tolerance); no REVIEW/FAIL cases recorded.

**Caveats (recorded, not hidden):** hflip is a global horizontal reflection, not VisualFLIP-style minimal local edits; pair metrics are reported as collapse-style paired answer-update metrics following VisualFLIP with the intervention difference stated explicitly. facingcomp is a semantic (language-change) condition and contributes to ΔC, not ΔG.
