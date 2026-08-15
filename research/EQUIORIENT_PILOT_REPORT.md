# EquiOrient Phase-1 Pilot — FINAL VERDICT (run #5, complete metric suite)

**Date:** 2026-08-15 · **Backbone:** Qwen/Qwen3-VL-8B-Instruct @ `0c351dd0`
(bf16/sdpa) · **Freeze:** `91185d7` · **Harness:** `8cea717` (Amendment C +
latent metrics) · **GPU:** 1×A6000, 69 min, run #5 of 5 · **Compute: CLOSED**
(account budget exhausted after this run; instance deleted, snapshot
`xv1GpVkwBL7ZTMZ9Ne72` retained)

Run #1 void (implementation deviations, decision log). Run #2 valid but
behavioral-ceiling (MUTATE verdict). Runs #3/#4 aborted operationally (no
scientific loss). Run #5 = complete frozen metric matrix incl. Amendment C
depth probe. This is the final Phase-1 falsification evidence.

## 1. Result matrix (selected-λ; λ: oc=1.0, li=1.0, eq=10.0)

| arm | val | holdout V∘H | z-corr | both_correct | latent_err | depth probe |
|---|---|---|---|---|---|---|
| ordinary_sft_lora | 0.7014 | — | — | — | — | — |
| augmentation_only | 0.9722 | 1.0000 | 0.5000 | 0.9444 | 10.370 | 0.6111 |
| output_consistency | 0.9722 | 1.0000 | 0.5000 | 0.9722 | 10.384 | 0.6111 |
| latent_invariance | 0.9722 | 1.0000 | 0.5000 | 0.9722 | 10.392 | 0.6111 |
| **equiorient** | 0.9722 | 1.0000 | 0.5000 | 0.9722 | **10.309** | **0.6111** |
| wrong_geometry | 0.9722 | 1.0000 | 0.5000 | 0.9722 | 10.359 | 0.6111 |

(Chance = 0.5; depth probe chance is 0.5 with n≈36 holdout depth pairs.)

## 2. Stop conditions (frozen YAML)

1. **EquiOrient does NOT beat augmentation_only AND output_consistency on
   held-out V∘H → TRIGGERED** (1.0 = 1.0 = 1.0).
2. **Latent equivariance error does NOT drop on held-out V∘H →
   TRIGGERED** (10.309 vs 10.370/10.384 — a 0.06–0.07 difference on a
   scale where the loss enforces ~0; no meaningful rho structure learned).
3. Causal ablation: **PASS** (1.0 → 0.5 under z corruption in every arm —
   the forced-from-z answer path is real; no LM-side leakage).
4. **correct_rho == wrong_rho on held-out V∘H → TRIGGERED** (1.0 = 1.0;
   also depth probe identical 0.6111 = 0.6111).

## 3. Amendment C (depth probe) — does NOT discriminate

Every arm scores 0.6111 on the held-out depth-family probe — including
augmentation_only (no rho shaping) and wrong_geometry (explicitly wrong
rho). The above-chance 0.6111 common to ALL arms indicates generic depth
signal carried by the answer-path training itself, with **zero additional
contribution from EquiOrient's equivariance loss**. No evidence that
rho-shaped z_d transfers to the unseen relation family.

## 4. VERDICT: Phase-1 pilot FAILS to support EquiOrient — KILL as designed

- All four frozen decision criteria that can fire, fired (1, 2, 4); the
  only pass (3) is a sanity check, not support.
- The method provides no measurable advantage over matched controls in
  this regime (closed H/V algebra, simple plan-view synthetic scenes,
  one seed, 2 epochs, λ grid {0.1,1,10}).
- Per the execution guide Gate 4: **stop, do NOT scale to Gate 6
  (multi-seed)** on this design. Account compute budget exhausted; any
  continuation requires fresh budget + explicit orchestrator unlock.

## 5. Honest framing for any future write-up

The pilot is a clean negative within its declared Phase-1 scope: on a
task where the answer-level algebra is closed, behavioral composition
generalizes from augmentation alone, and the latent equivariance loss
neither improves nor harms any measured quantity (behavior, latent error,
transfer probe). Consistent with the guide's allowed story: "equivariance
training does not improve downstream behavior on algebra-closed tasks" or
"answer consistency does not imply representation equivariance" — with the
caveat that a harder regime (richer scenes, longer training, non-closed
held-out structure) was NOT tested and remains open.

## 6. Compute ledger (this session)

| run | outcome | GPU min |
|---|---|---|
| #1 | VOID (5 implementation deviations) | 62 |
| #2 | valid, ceiling → MUTATE | 65 |
| #3 | aborted (superseded) | ~25 |
| #4 | aborted (stale provisioner, no sklearn) | ~10 |
| #5 | final valid matrix | 69 |
| total | — | ~3.9 GPU-h ≈ $1.35 |

Box `65c57arp` deleted 06:10 UTC; snapshot `xv1GpVkwBL7ZTMZ9Ne72`
(equiorient-pilot-provisioned-run5) retained.
