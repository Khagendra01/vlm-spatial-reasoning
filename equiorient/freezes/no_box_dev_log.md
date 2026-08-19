# EquiOrient NO-BOX dev-phase log
# Every dev configuration is recorded here BEFORE any confirmatory run.
# The dev split is the ONLY split used for design decisions; the test
# split is never touched until a freeze is committed.

| # | date | variant | n_train | epochs | lr | pool | seeds | baseline (Aug dev unseen) | note |
|---|------|---------|---------|--------|----|------|------|---------------------------|------|
| D1 | 2026-08-18 | no-box full-image, v4 data | 128 | 2 | 1e-4 | 1q | 101 | 0.1285 (chance) | not learning; attention pool untrained |
| D2 | 2026-08-18 | same | 128 | 2 | 1e-3 | 1q | 101 | failed (diag idx) | — |
| D3 | 2026-08-18 | same | 128 | 6 | 1e-3 | 1q | 101 | 0.1250 (chance) | constant-class collapse; tgt attn 0.104 |
| D4 | 2026-08-18 | same | 128 | 6 | 3e-4 | 1q | 101 | 0.1250 (chance) | same collapse |
| D5 | 2026-08-18 | multi-query pool | 128 | 10 | 5e-4 | 4q | 101 | 0.1250 (chance) | 4 queries — still collapse |
| D6 | 2026-08-18 | multi-query pool | 128 | 10 | 1e-3 | 4q | 101 | 0.1250 (chance) | 4q hi LR — collapse |
| D7 | 2026-08-18 | multi-query pool | 128 | 15 | 5e-4 | 4q | 101 | 0.1250 (chance) | 4q 15ep — collapse |
| D5b | 2026-08-19 | multi-query pool | 512 | 10 | 5e-4 | 4q | 101 | 0.1250 (chance) | more data — still collapse |
| D5c | 2026-08-19 | multi-query pool | 1024 | 10 | 5e-4 | 4q | 101 | 0.1250 (chance) | 1024 scenes — still collapse |

**KEY FINDING (D1-D7):** targets are statistically indistinguishable from
distractors in v4 data (9/9 appearance combos overlap), so the no-box
label is *unlearnable by construction*. The boxed study was only solvable
because GT boxes identified the pair. => nobox_v1 generator: targets a
(red) / b (blue) visually unique, gray distractors; difficulty tunable.

| D8 | 2026-08-19 | nobox_v1 identifiable targets | 128 | 10 | 5e-4 | 4q | 101 | 0.1824 | targets red/blue, 12-20 gray dist, noise 12, size 3-5 |
| D9 | 2026-08-19 | nobox_v1 easier | 128 | 10 | 5e-4 | 4q | 101 | (rate-limited) | 6-9px, 4-8 dist, noise 6 |
| D10 | 2026-08-19 | nobox_v1 easier2 | 128 | 10 | 5e-4 | 4q | 101 | 0.1250 (chance) | 4-7px, 8-12 dist, noise 8 |
| D11 | 2026-08-19 | nobox_v1 | 512 | 10 | 5e-4 | 4q | 101 | 0.1250 (chance) | same data as D8, more N — paradox |
| D12 | 2026-08-19 | nobox_v1 mid | 256 | 20 | 5e-4 | 4q | 101 | 1.0000 (REPRODUCIBLE) | 4-7px, 6-10 dist, noise 8 — train_acc 0.195 was STALE-CACHE BUG; true train_acc reaches 1.0. Dev 1.0 real. SATURATED |
| D13 | 2026-08-19 | nobox_v1 mid | 128 | 30 | 5e-4 | 4q | 101 | 0.3551 | 4-7px, 6-10 dist, noise 8, eval-mode fix — half the data, still above chance but not saturated |
| D14 | 2026-08-19 | nobox_v1 mid | 256 | 20 | 5e-4 | 4q | 101 | **1.0000** | D12 config + cache fix (140a981). train_acc climbs to 1.0; dev 1.0 all transforms. FIRST LEARNABLE NO-BOX REGIME. SATURATED |
| D15 | 2026-08-19 | nobox_v1 harder | 256 | 20 | 5e-4 | 4q | 101 | 0.1250 (chance) | 3.5-6px, 8-14 dist, noise 10 — cliff below D14 |
| D16 | 2026-08-19 | nobox_v1 mid-hard | 256 | 20 | 5e-4 | 4q | 101 | 0.1250 (chance) | 3.8-6px, 7-11 dist, noise 9 — confirms sharp cliff |
| D17 | 2026-08-19 | nobox_v1 easy | 256 | **10** | 5e-4 | 4q | 101 | 1.0000 | 4-7px, 6-10 dist, noise 8 — easy data saturates even at 10 epochs |
| D18 | 2026-08-19 | nobox_v1 easy | **128** | **40** | 5e-4 | 4q | 101 | **0.8000 ✔ IN WINDOW** | 4-7px, 6-10, noise 8. train_acc kicks in late (ep28+) climbing to 0.88; dev 0.80. Candidate freeze point |
| D19 | 2026-08-19 | nobox_v1 easy | 128 | 60 | 5e-4 | 4q | 101 | (running) | same data — does more epochs overshoot to 1.0? |

## PROBES (frozen deepstack features, held-out scenes — no training)
| config | linear top2 recall | mlp top2 recall | verdict |
|--------|-------------------|-----------------|---------|
| 3-5px, 12-20 dist, noise 12 | 0.10 | 0.11 | weak; ~200-400x chance but unreliable |
| 6-9px, 4-8 dist, noise 6 | 0.19 | — | stronger |
| 10-14px, 2-4 dist, noise 3 | 0.12 | — | non-monotonic (probe variance) |

interpretation: cell-level target signal in frozen deepstack tokens is *weak but
present* (~0.1-0.2 top2 recall vs chance ~0.0005). The pool CAN in principle
learn to localize, but needs capacity + budget; attention diag shows it currently
doesn't (pair_in_top4_pct=0.0 across runs).

PROBE-FREEZE CANDIDATE: N=128, epochs=40, lr=5e-4, difficulty (4-7px, 6-10 dist, noise8)
=> dev 0.80. Waiting on D19 (60ep) to confirm 40ep is the non-saturated point.

REVISED (post-D14): the weak cell-level signal is NOT the bottleneck. With
identifiable targets at 4-7px/6-10 dist/noise8 and N=256×20ep, the full-image
pool achieves dev 1.0 WITHOUT cell-level localization (attention essentially
uniform, pair_in_top4 0.0) — it reads a GLOBAL statistical signature of the pair
(e.g. red-mass vs blue-mass centroid) from the pooled context, which is enough
under equiorient noise. So no-box learning works when the pixels carry
identifiable color statistics; it failed before only because (a) v4 data made
targets visually identical to distractors, and (b) the stale feature cache hid
real training progress.

## Diagnostic Runs (2026-08-19)

### Task 1: Latent Collapse Diagnosis (EquiOrient, v1 D18, seed 101)
- File: equiorient/freezes/diag_eq_s101_latent.json
- FINDING: Trivial latent collapse. z norm collapses 1.41 -> 0.09 (ep1->27).
  Effective rank 11.66 -> 1.97. cos(zx,zgx) ~1.000 throughout (z invariant to g).
  z_ablation_acc = 0.125 at all epochs (z carries no information).
  Root cause: MSE loss ||G*g*z - z_gx|| has trivial minimum at z=0.
  Fix: add norm regularizer lambda*||z||^2 to prevent collapse.

### Task 2: v2 Feature Probes
- BLOCKED: Modal workspace spend limit exceeded.
- Code ready in equiorient/experiments/probe_nobox_v2.py.

### Task 3: Easier v2 Conditions
- Condition A (6-10px/4-6 dist/n4): 0.125 chance at 60ep. UNLEARNABLE.
- Condition B (5-8px/5-8 dist/n6): BLOCKED (spend limit).
- Condition C (4-7px/4-6 dist/n4): BLOCKED (spend limit).

### Budget Status
- Modal workspace spend limit EXCEEDED. No further GPU runs possible.
