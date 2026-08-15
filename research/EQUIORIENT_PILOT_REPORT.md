# EquiOrient Phase-1 Pilot Report — Run #2 (valid)

**Date:** 2026-08-15 · **Backbone:** Qwen/Qwen3-VL-8B-Instruct @ `0c351dd0` (bf16/sdpa) ·
**Freeze commit:** `91185d7` · **Harness:** `cdc80b7` (post-void-run correction) ·
**Wall time:** 65 min (3908 s) on 1×A6000 · **GPU unlock:** explicit (orchestrator tokens)

Run #1 (62 min) was declared VOID in the decision log: five implementation
deviations (V∘H leak into train/val, equiorient arm lost its loss,
wrong-geometry not wrong, no common-init LoRA restore, single-arm holdout).
Run #2 below is the first valid execution.

---

## 1. Result matrix (selected-λ arms; all λ=0.1 after val selection)

| arm | val acc | holdout V∘H | z-corrupted | ablation Δ |
|---|---|---|---|---|
| ordinary_sft_lora | 0.7014 | — | — | — |
| augmentation_only | 0.9861 | **1.0000** | 0.5000 | +0.5000 |
| output_consistency | 0.9861 | **1.0000** | 0.5000 | +0.5000 |
| latent_invariance | 0.9861 | **1.0000** | 0.5000 | +0.5000 |
| **equiorient** | 0.9861 | **1.0000** | 0.5000 | +0.5000 |
| wrong_geometry | 0.9861 | **1.0000** | 0.5000 | +0.5000 |

Grid arms (3 λ each) all 0.9861 on validation; selection rule (best val, tie
→ smallest λ) → 0.1 everywhere. Per-arm raw logs: `pilot_run/run.log`.

## 2. Stop-condition assessment (frozen YAML)

1. **EquiOrient does NOT beat augmentation_only AND output_consistency on
   held-out V∘H → TRIGGERED** (1.0 = 1.0 = 1.0). No behavioral advantage.
2. **Latent equivariance error drop on held-out V∘H — NOT MEASURABLE**:
   the harness never computed `latent_equivariance_error_VoH` (frozen primary
   metric missing from the implementation — harness gap, not a protocol
   change; must be added before any further run).
3. **Causal ablation (z corruption → accuracy collapse): PASS** — 1.0 → 0.5
   (chance) in every arm: the forced-from-z answer path is real, not
   LM-side leakage.
4. **correct_rho == wrong_rho on held-out V∘H → TRIGGERED** (1.0 == 1.0):
   geometry appears irrelevant at the behavioral level — but see §3.

## 3. Verdict: MUTATE the held-out test (ceiling, not falsification of EquiOrient)

The held-out V∘H composition is **at ceiling (1.0) for every arm including
the controls and the wrong-geometry control**. The H/V relation algebra is
closed at the answer level: a model that saw left/right + above/below under
H and V can trivially compose to V∘H without any latent structure. The pilot
therefore has **no discriminative power** — this falsifies the *test design*,
not the method. EquiOrient may still shape z in a way no behavioral
ceiling test can see; the frozen primary metrics that would reveal it
(`latent_equivariance_error_VoH`, `paired_both_correct_VoH`,
`correct_rho_vs_wrong_rho_contrast`) were only partially implemented.

**Gate-4 decision (per execution guide): MUTATE before scaling.** Options
under consideration (decision log, 2026-08-15):

- A. **Held-out relation family**: hold out depth relations (in_front/behind);
  extend head to 6 classes; EquiOrient's rho keeps z_d invariant (geometry-
  derived), so the question becomes: does z_d acquire depth structure that
  transfers to an unseen relation family (augmentation-only has no depth
  supervision at all)? Changes frozen head spec → requires Amendment C.
- B. **Latent-first re-run (cheapest, no design change)**: implement the two
  missing frozen primary metrics and re-run the SAME design — the behavioral
  ceiling stays, but `latent_equivariance_error_VoH` + `both_correct_VoH`
  may still discriminate EquiOrient vs controls at the representation level.
- C. **Unseen transform class** (e.g., 90° rotation): requires extending Gate-1
  algebra (currently frozen "do not reopen") → heaviest amendment.

Recommended order: **B first** (completes the frozen measurement suite, ~1 h
GPU, zero protocol change), then **A** if B does not discriminate.

## 4. Sanity notes

- Causal path verified: z→head is the only answer route (ablation Δ=0.5).
- Init-equivalence honored: common-init LoRA snapshot restored per arm
  (Amendment B3); enc/head re-inited per arm.
- Held-out discipline honored: V∘H absent from train/val (360 pairs/arm).
- Backbone/revision/architecture/losses/data/seeds unchanged vs freeze.

## 5. Open gaps (harness, not protocol)

- `latent_equivariance_error_VoH`, `paired_both_correct_VoH` not computed.
- Per-arm checkpoints not archived (run dirs hold logs only) — fine for a
  pilot, must be fixed for Gate-6 main runs (guide §9 save list).
