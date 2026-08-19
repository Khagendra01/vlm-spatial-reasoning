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
| D12 | 2026-08-19 | nobox_v1 mid | 256 | 20 | 5e-4 | 4q | 101 | (fill) | 4-7px, 6-10 dist, noise 8, eval-mode fix |
| D13 | 2026-08-19 | nobox_v1 mid | 128 | 30 | 5e-4 | 4q | 101 | (fill) | 4-7px, 6-10 dist, noise 8, eval-mode fix |

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
