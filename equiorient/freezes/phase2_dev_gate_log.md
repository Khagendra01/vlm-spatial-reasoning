# Phase-2 development-gate log

## 2026-08-15 — DEV GATE: FAIL on non-ceiling (task still too easy)

Dev run (Modal L40S, seed 101, N=512, lambda=1.0, epochs=2; repo commit
a0da544; dataset manifest sha 5e33f47f after the label fix):

| arm | I | R | R2 | R3 | H | RH | R2H | R3H | unseen |
|---|---|---|---|---|---|---|---|---|---|
| augmentation | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0000 |
| equiorient | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0000 |

Gate requirement: "augmentation unseen accuracy < 0.95 at N=512" -> NOT MET.
Predeclared consequence: do NOT launch the confirmatory run; increase task
difficulty first.

Bugs caught by the dev gate before this (all fixed, gate 45/45):
1. pooled() mapped math coords to grid cells without the pixel conversion
   (px = cx+96, py = 96-cy) — transformed views pooled the wrong cell.
2. transform_scene copied the ORIGINAL label onto every view — answer
   targets for transformed views were geometrically wrong.
3. Modal data volume served the stale dataset (persisted across runs) —
   scaffold now always rebuilds in-sandbox.

Analysis: with one target pair, clean margin-separated shapes, and ground-
truth boxes, the 8-way label is directly readable from ANY single view;
neither arm needs to compose anything. The compositional test only binds
when per-view readout is hard (or exposure is tiny), so augmentation can
cheat by reading each view directly.

## Difficulty escalation (next, per gate)

- distractors 4-8 -> 6-10 (validate_dataset bound updated)
- target object size smaller (8-13 -> 6-9 half-extent)
- mild overlap allowed between distractors and near the target pair
- background texture noise (weak per-pixel jitter)
- margin from directional boundaries unchanged (labels stay exact)

Then re-run: augmentation dev at N=512 must be < 0.95 before any
confirmatory launch; also check N=128 per the predeclared order.
