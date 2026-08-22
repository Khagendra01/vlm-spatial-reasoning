# PREREGISTRATION AMENDMENT: ICLR-Push Experiments (E1–E3)

Status: FROZEN 2026-08-22 (before any GPU run of E1/E2/E3).
Branch: `research/equiorient-iclr-push` (off phase-2 tip `e48054b`).
Parent protocol: `equiorient/freezes/phase2_confirmatory.yaml` + Paper-2
grounding protocol (`results/grounding/protocol/`, master `8be6b05`).
Target venue: ICLR 2027 (abstract ~2026-09-19..24, paper ~1 week later).

Motivation (reviewer-facing): the phase-2 canonical result (Eq-Wrong
+0.68pp, p<0.0001, 15/15 seeds; Eq-Aug n.s.) establishes law-sensitivity on
synthetic plan-view scenes with one backbone. The three preregistered
experiments below address the two predictable kill questions: (a) does it
replicate beyond one backbone / the synthetic domain, and (b) does latent
algebra compliance relate to behavior on natural images at all.

---

## E1 — Backbone replication of the 15-seed canonical

- Claim under test: Eq-Wrong > Eq-Aug behavioral advantage replicates on a
  second backbone family.
- Backbone: Qwen2-VL-7B-Instruct (`Qwen/Qwen2-VL-7B-Instruct`) — support
  already merged in phase-2 launchers. SmolVLM2-2.2B is fallback #2 only if
  VRAM makes 7B infeasible on the available GPU.
- Protocol: identical to `run_n128_clean.py` canonical (N=128 clean
  deterministic scenes; matched seeds; determinism fixes from `714c3f5`
  active). 15 matched seeds per arm; arms = equiorient / augmentation /
  wrong_geometry.
- Primary metric: mean behavioral accuracy delta (Eq-Wrong − Aug) across
  15 seeds, paired permutation test + sign count. Success: p<0.01 and ≥12/15
  positive seeds. Failure: n.s. → report honestly as non-replication;
  decision gate below.
- Frozen before run. No architecture/loss/hyperparameter changes permitted.

## E2 — Real-image bridge (latent equivariance vs behavioral flip-law)

- Question: on natural VSR images, does latent horizontal-reflection
  equivariance error predict behavioral hflip flip-law compliance across
  checkpoints?
- Checkpoint set (all existing, zero new training):
  - Qwen2-VL-7B: zero-shot + seedA/B/C General-LoRA (Paper-2 seed campaign)
  - SmolVLM2-2B: zero-shot + seedA/B/C General-LoRA
  - (+ legacy general/targeted checkpoints as secondary points)
- Latent side:
  - Features: vision-tower final hidden states (post-merge patch tokens),
    GLOBAL mean-pool over all tokens (primary; no object boxes — real
    images have no synthetic GT boxes; OWL box-pooled variant is
    exploratory-only and labeled as such).
  - Pairs: z(x) and z(hflip(x)) for each frozen subset image; hflip =
    PIL FLIP_LEFT_RIGHT applied AFTER the same uniform 392px long-side
    preprocessing as the Tier-C transform (exact match to behavioral
    condition; transform_version tier_c_v0.1).
  - Metric: normalized equivariance error E_norm per checkpoint
    (collapse-safe form, generalized to D dims from
    `equiorient/analysis/latent_metrics.py`; rho = reflection matrix with
    x-axis negation in token space is NOT assumed — primary metric is
    ||z(x) − z(flip x)||-based cosine distance and E_norm under identity
    law, because a reflection representation for real-image tokens is not
    identifiable without training; this is stated as a limitation).
    Secondary: mean cosine similarity, latent norm stats, effective rank.
- Behavioral side: per-checkpoint flip-compliance rate computed from the
  committed Tier-C CSVs (`results/grounding/predictions/**/…hflip_flip.csv`,
  columns example_id/correct) — recomputed, not copied.
- Subset: preregistered as 500 examples sampled once with numpy
  default_rng(42) from `results/grounding/protocol/vsr_test_ids.json`,
  restricted to `hflip_flip`-eligible IDs. DEVIATION LOGGED BEFORE ANY GPU
  RUN (2026-08-22): the eligible pool contains only 245 IDs (the Tier-C
  hflip_flip condition has 245 rows), so the frozen subset is the full pool,
  n=245 — no sampling occurred; `e2_subset_ids.json` + `e2_image_ids.json`
  are committed and frozen. Any future enlargement (e.g., adding
  hflip_invariant rows or re-running Tier-C on more examples) must be
  logged here before extraction.
- Analysis: Spearman correlation between E_norm and compliance across the
  ~14 checkpoints (per backbone separately AND pooled); bootstrap 95% CI
  over checkpoints (10k resamples); per-seed paired deltas (zero-shot → LoRA)
  as secondary unit of analysis. Both outcomes pre-declared as informative
  (positive correlation OR clean null both advance the claim; only
  inconclusive power (CI spanning >0.6 width) forces "uninformative").
- Compute: inference-only; no LoRA training.

## E3 — Wrong-law specificity sweep (synthetic)

- Extend wrong_geometry from {axis-swap} to {axis-swap, rot90, translation}
  on the N=128 canonical setup, 15 matched seeds, equiorient arm only vs
  each wrong law's own rho.
- Claim under test: trained latents obey ANY self-consistent wrong algebra,
  not merely axis-swap.
- Success: per-transform correct-law rho error < each wrong-law's own-law
  error pattern replicates across laws (descriptive; no single p-value gate).

---

## AMENDMENT STATUS — HONEST PROVENANCE (rewritten 2026-08-22)

Correction of an earlier overstated framing: this is NOT a clean-slate
preregistration. All phase-2 GPU results (including the Qwen3-VL canonical
outcome) were known before these decisions were made. This section is a
COMPUTE-CONSTRAINED AMENDMENT designed with full knowledge of prior results.
It governs the not-yet-run E1/E2/E3 experiments only.

## PLANNED DEVIATIONS (compute-driven, declared before E1/E2/E3 runs)

1. **E1-SmolVLM numerics:** the frozen protocol specifies bf16. Turing-era
   free-tier cards (T4/P100) cannot execute bf16. Preference order:
   a) **fp32 preferred** — SmolVLM2-2B (~9 GB weights fp32 + LoRA +
      gradient checkpointing) plausibly fits 16 GB; verified by smoke test
      before committing.
   b) fp16 ONLY if fp32 does not fit, AND only together with a numerics
      control: at least 3 seeds executed in BOTH formats, fp32-vs-fp16
      deltas reported, and an explicit limitations paragraph stating that
      sub-1pp effects (the paper's regime) are sensitive to
      gradient-underflow/loss-scaling differences between float formats.
   Rationale: the measured effects are +0.68pp-scale; float-format-induced
   changes to gradient dynamics are a genuine confound at this scale and
   must be bounded, not waved off ("not quantization" is NOT sufficient).
2. **E1 backbone scope:** formal replication (15 seeds × 3 arms) carried
   by SmolVLM2-2B (different family, smaller scale); Qwen2-VL-7B demoted
   to a pilot (up to 2 seeds × 3 arms) on the pooled premium hours.
   Declared risk, stated openly: gates below were calibrated on Qwen3-VL
   behavior; there is no guarantee effect sizes transfer across a 4× scale
   drop and a family change. A gate failure on SmolVLM will be reported as
   non-replication, NOT re-gated or explained away.
3. **Gates:** retained numerically (p<0.01, >=12/15 positive seeds) but
   with the above caveat stated: identical thresholds on a different
   backbone/floating-point path constitute a *choice*, and a miss will be
   interpreted as possible true non-replication rather than attributed to
   hardware.

## Decision gates

| Outcome | Action |
|---|---|
| E1 replicate + E2 any informative result | Submit ICLR 2027 |
| E1 replicate + E2 uninformative-power | Prefer TMLR; ICLR only if timeline allows strengthening |
| E1 non-replication | Stop ICLR push; TMLR with honest scope |

## What stays frozen

- No changes to phase-2 harness, losses, or scene generator.
- No new seeds beyond declared counts; no post-hoc subset swaps; every
  deviation logged here with timestamp before results are seen.
