# R1 Replication (2B) vs 7B: Qualitative Pattern Comparison

**Date:** 2026-08-11 | **Branch:** research/spatial-grounding-audit
**Contract:** frozen Paper-2 contract (prompt `prompt_hash`, parser, 392px cap, batch 8;
decisions 2026-08-11: `sdpa` attention backend for the 2B family, eager/sdpa output
identity verified 0/32 examples differ; CHECKPOINTS_2B registry; `--model-family smolvlm2`).
**Checkpoints:** `HuggingFaceTB/SmolVLM2-2.2B-Instruct` zero-shot (2B_zero_shot) vs
pre-existing 2B General LoRA at `checkpoints/general_lora/final` (PEFT LoRA r=8).
**Rows per cell:** Tier A 2195; relcomp 666; sorev 603; continv 169; facingcomp 103;
hflip_flip 245; hflip_invariant 421. All cells valid-parse 2195/2195, 0 invalid.
**Outputs:** predictions `results/grounding/predictions/r1_2b_full/`; metrics/reports
`tier_a_report_r1_2b_full.md`, `tier_b_report_r1_2b_tierb.md`,
`tier_b_report_r1_2b_facing.md`, `tier_c_report_r1_2b_full.md`.
Harness prelock commit `c0c9afe`; results commit `b2c4bcf`.

## 1. Benchmark accuracy (ΔA, normal condition, n=2195)

| backbone | zero | general | ΔA | Cohen's h |
|---|---|---|---|---|
| 7B (eager) | 0.7699 | 0.8241 | +5.42pp | 0.129 |
| 2B (sdpa) | 0.7362 | 0.7649 | +2.87pp | 0.066 |

Directional replication: both backbones improve under General LoRA; the 2B gain is
smaller. 2B zero-shot normal (0.7362, 392px contract) vs the master native-image
2B baseline (0.7399): the 392px cap effect is small on the 2B backbone (≈0.4pp).

## 2. Visual-evidence dependence (ΔG, Tier A, n=2195)

| backbone | normal | shuffle | blank | text_only | P1 ΔG (DiD) [95% CI] |
|---|---|---|---|---|---|
| 7B | 0.7699 / 0.8241 | 0.4485 / 0.4560 | 0.4592 / 0.4624 | 0.5412 / 0.5421 | +4.56pp [+2.8, +6.3] |
| 2B | 0.7362 / 0.7649 | 0.4692 / 0.4674 | 0.4670 / 0.4679 | 0.5358 / 0.5362 | +3.05pp [+1.7, +4.5] |

**Replicates.** Both backbones: shuffle/blank → chance level; text_only slightly above
chance (≈0.54); General LoRA increases normal-vs-shuffle gap; the 2B ΔG CI excludes 0
(3.05pp), qualitatively the same direction and magnitude class as the 7B result
(4.56pp). Bootstrapped per-checkpoint G values: 2B zero 0.2670, 2B general 0.2975.
This is the key confirmatory axis: evidence consistent with **stronger visual
evidence dependence after General LoRA in both backbones** (guardrail wording;
both-correct reported separately; not proof of grounding).

## 3. Semantic consistency (Tier B)

| transform (law) | 7B ΔC [95% CI], p | 2B ΔC [95% CI], p | replicates? |
|---|---|---|---|
| relcomp (flip) | +4.2pp [+2.0, +6.6] | **+3.30pp [+0.15, +6.46], p=.049** | directional yes (2B weaker/borderline) |
| sorev (stability) | null | −1.82pp [−4.6, +1.0], p=.24 | yes (null in both) |
| continv (paraphrase) | null | **−5.92pp [−11.2, −0.6], p=.041** | NO — 2B point estimate negative, CI excludes 0 |

relcomp: the flip-law consistency gain under General LoRA is directionally replicated
in 2B (same sign, smaller, borderline significance; report per protocol §17 wording).

continv: divergence. In the 2B backbone the paraphrase-law consistency point estimate
is negative with the bootstrap CI excluding 0 (n=169; McNemar p=.041). Do NOT call
this significant "improvement"; describe as: "negative point estimate with CI
excluding 0 on the 2B backbone, opposite in direction to the 7B null result."

## 4. Facing-antonym diagnostic (facingcomp, n=103)

| backbone | zero | general | ΔC [95% CI], p |
|---|---|---|---|
| 7B | 0.563 | 0.709 | +14.6pp [+3.9, +25.2], p=.011 |
| 2B | 0.6214 | 0.5534 | **−6.80pp [−15.5, +1.0], p=.167** |

**Does NOT replicate.** The strong 7B improvement in facing-antonym flip-law
compliance is absent in the 2B backbone; point estimates move in opposite directions
(2B directionally negative, not statistically significant at n=103). Per the locked
wording rule: "facing-antonym flip-law compliance"; never "strict logical complement
accuracy"; never claim HardNeg/General "significantly improves" anything here.

## 5. Visual reflection (Tier C, hflip)

| transform | 7B ΔV [95% CI], p | 2B ΔV [95% CI], p | replicates? |
|---|---|---|---|
| hflip_flip (flip-expected) | +2.0pp NS | +2.86pp [−2.5, +8.2], p=.36 | yes (null in both) |
| hflip_invariant (stability) | **+12.1pp [+7.8, +16.4], p<.001** | +0.71pp [−2.9, +4.3], p=.79 | NO — 7B's strong invariance gain absent in 2B |

The flagship 7B finding on this axis (large invariance-consistency gain under
General LoRA) does not generalize to the 2B backbone: point estimate ≈ 0. This is
the most notable replication failure on the visual axis.

## 6. Qualitative summary (the three-way decomposition on the 2B backbone)

- **ΔA (accuracy):** replicates directionally, smaller magnitude.
- **ΔG (visual-evidence dependence):** replicates; CI excludes 0 in both backbones.
- **ΔC (semantic flip-law consistency, relcomp):** replicates directionally (borderline in 2B);
  sorev null in both; continv diverges (2B negative).
- **Facing-antonym compliance:** replicates only in the sense of an unchanged-null-or-worse
  state on the 2B backbone; the 7B positive effect does NOT transfer.
- **Visual reflection (hflip invariance):** the 7B effect does NOT transfer; 2B ≈ null.

**Reading:** the evidence-dependence benefit of General LoRA is backbone-general
(Tier A ΔG replicates); the consistency/reflection gains observed in the 7B backbone
(facing-antonym +14.6pp; hflip invariance +12.1pp) are NOT present in the 2B backbone
under the same contract. The 2B General LoRA improves accuracy and visual-evidence
dependence without the relation-consistency improvements of the 7B variant — i.e., the
7B adaptation decomposition does not transfer wholesale to the smaller backbone;
report as a qualitative replication failure of the secondary axes.

**Engineering notes:** 2B throughput ~1.7 ex/s (eager) → ~2.8 ex/s (sdpa) on the A6000;
SmolVLM2 upsamples every image to 1536px and tiles into 13×384px frames (≈1053 image
tokens), which dominates wall time; batch >8 measured slower (padding); the run's
per-run metadata records `attn: sdpa` and the eager/sdpa identity check (0/32).