# Amendment D — Harder-regime re-test (draft for orchestrator approval)

**Date:** 2026-08-15 · **Status:** DRAFT — needs orchestrator sign-off before freeze
**GPU:** Modal L40S (~50 min, ≈ $1.60, within the $30/mo credit)

---

## 1. Why (evidence from run #5)

Run #5 (final valid Phase-1 pilot) triggered every fireable stop condition:

- Held-out V∘H = 1.0000 for **all five causal arms** (behavioral ceiling —
  the H/V answer algebra is closed, augmentation alone composes it);
- depth probe = 0.6111 for **all arms incl. wrong_geometry** (no
  discrimination; the common above-chance value is generic depth signal
  from answer-path training, zero EquiOrient contribution);
- latent equivariance error ≈ 10.3–10.4 for **all arms** (no rho structure
  learned by anyone — and, tellingly, the equivariance loss neither helped
  nor hurt).

Two readings: (a) EquiOrient doesn't work; (b) the regime is too easy /
too short for any arm to differentiate — the test cannot discriminate.
Amendment D is the minimal experiment that decides between them: make the
visual task genuinely harder and give training more budget, then re-run
the IDENTICAL six-arm comparison.

## 2. Design (all changes pre-result, logged)

### D1 — Richer scenes (visual difficulty up)
- Objects per scene: 4 → **6** (4 rectangles + 2 orientation lines),
  sizes/colors varied, margins tightened (still no ties post-transform —
  same algebra guarantees, re-verified by the hostile law tests).
- Same canvas 320×320, same relation-labeling rule, same transform set
  (I/H/V seen, V∘H held out), same 17 scenes / 10-4-3 scene split.
- New data seed `20260815` (reproducible; new committed artifact
  `results/equiorient/pilot_data_v2`).
- Expected effect: more objects → more pairs per image (~30 vs 12), harder
  pooling disambiguation → augmentation_only should drop below ceiling.

### D2 — Longer training budget (method gets its best shot)
- epochs 2 → **6** (frozen YAML `optimization.epochs`).
- Everything else unchanged: AdamW lr 1e-4, batch 8, bf16, grad
  checkpointing, λ grid {0.1, 1.0, 10.0} on scene_0010–13, stop
  conditions, seeds (20260814 arm seed kept).

### D3 — Unchanged (frozen, not reopened)
- Backbone/revision, PairEncoder/z/head specs, losses (pure functions),
  arms (six matched), wrong-geometry definition (Amendment C probe stays),
  selection rule, primary/secondary metrics, causal ablation, V∘H
  holdout discipline, depth probe protocol.

## 3. Decision rules (predeclared)

| Outcome | Verdict |
|---|---|
| EquiOrient beats augmentation_only AND output_consistency on held-out V∘H, AND/OR depth probe discriminates (≥ +0.15 over controls) | **PROCEED** → Gate 6 multi-seed confirmatory (3 seeds, Modal parallel, ~$5) |
| EquiOrient == controls on every metric again (esp. probe flat at control level) | **KILL** — definitive Phase-1 negative with a harder regime; write-up path (negative-result paper per guide §12) |
| augmentation_only still at ceiling (task still too easy) | regime insufficient; either escalate again (with orchestrator) or KILL |

## 4. Implementation checklist (zero GPU)

1. `src/equiorient/datasets.py`: scene recipe v2 (6 objects, margin/size
   variance params) + `generate_pack_v2(num_scenes, seed=20260815)` —
   algebra guarantees re-verified by the existing hostile law tests
   (re-run `tests/test_equiorient_synthetic.py` + law check on v2 pack).
2. `scripts/equiorient/build_pilot_data.py`: v2 manifest into
   `results/equiorient/pilot_data_v2` (same schema — harness untouched).
3. YAML: `configs/equiorient_pilot_freeze_v2.yaml` — D1/D2 amendments,
   same structure, freeze marker + decision-log reference.
4. Harness: unchanged (reads YAML; --data pilot_data_v2).
5. Local gates: py_compile + `--tiny` PASS on v2 data.
6. Modal: CPU tiny gate → L40S pilot (scaffold's `--data` points at v2
   volume mount — the modal app gains a `data_v2` arg).
7. Collect → commit → verdict per §3.

## 5. Cost & compute budget

- Pilot: ~50 min L40S ≈ **$1.60** (optimized harness).
- Gate 6 (if PROCEED): 3 seeds × ~50 min in parallel ≈ **$4.90**.
- Total this amendment ≈ **$6.50** — well inside the $30 monthly credit.
