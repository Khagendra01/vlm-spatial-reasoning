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
| D5 | 2026-08-18 | multi-query pool | 128 | 10 | 5e-4 | 4q | 101 | (fill) | 4 queries |
| D6 | 2026-08-18 | multi-query pool | 128 | 10 | 1e-3 | 4q | 101 | (fill) | 4 queries, hi LR |
| D7 | 2026-08-18 | multi-query pool | 128 | 15 | 5e-4 | 4q | 101 | (fill) | 4 queries, more epochs |
