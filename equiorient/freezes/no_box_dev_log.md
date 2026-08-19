# EquiOrient NO-BOX dev-phase log
# Every dev configuration is recorded here BEFORE any confirmatory run.
# The dev split is the ONLY split used for design decisions; the test
# split is never touched until a freeze is committed.

| # | date | variant | n_train | epochs | lr | seeds | baseline (Aug dev unseen) | note |
|---|------|---------|---------|--------|----|------|---------------------------|------|
| D1 | 2026-08-18 | no-box full-image, v4 data | 128 | 2 | 1e-4 | 101 | 0.1285 (chance) | not learning; attention pool untrained |
| D2 | 2026-08-18 | same | 128 | 2 | 1e-3 | 101 | (fill) | higher LR |
| D3 | 2026-08-18 | same | 128 | 6 | 1e-3 | 101 | (fill) | higher LR + epochs |
| D4 | 2026-08-18 | same | 128 | 6 | 3e-4 | 101 | (fill) | mid LR + epochs |
