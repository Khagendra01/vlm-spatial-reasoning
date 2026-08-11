# Seed Campaign Battery — Justification (frozen before training, 2026-08-11)

## Why a battery at all

The seed-0 runs were each evaluated with a single VSR accuracy number plus,
for the 2B, the grounding tier analyses. A single number cannot detect
whether a re-run with a fresh seed produces *systematically* different
behavior: it could match on overall accuracy while drifting on specific
conditions (e.g., flipping hflip/hflip_inv behavior, cheap-image tricks via
numerical-identity jitter, or relation-comp family bias). The battery
exists to make seed-variance visible along the same axes the Paper-2
evaluation contract already defines.

## Battery composition (7 runs per checkpoint)

| Run   | Purpose |
|-------|---------|
| normal | Reference condition; the contract's baseline accuracy at 392px |
| with_sample | 2px numerical-identity jitter: a re-sized copy of the same image must give the same answer (identity robustness) |
| with_shuffle | Row-order permutation with constant sampling without replacement: answer stability under order change |
| relcomp | Relation-comparison rows (semantic distance < 0.3): checks that discrimination is driven by the relation, not by paired-row artifacts |
| facing | Orientation-facing subset: the known-weak family (orientation) gets its own readout per seed |
| hflip / hflip_inv | Horizontal-flip variants: mirror-symmetry robustness and the label-inversion contract |

## Contract constants (frozen)

- Image contract: uniform 392px long-side cap for ALL conditions including
  normal (docs/TECHNIQUES.md ss4; src/grounding/config.py MAX_LONG_SIDE=392).
  Rationale: enforces the 28x28 patch-grid budget as a constant protocol
  parameter across all subsets; the seed-0 metrics were produced under the
  same contract.
- with_sample tolerance: 2px (PIL resize of the 392px image by 2px on the
  capped long side).
- relcomp threshold: normalized semantic distance < 0.3, using the legacy
  hardneg manifest builder's relation semantics.
- Sampling: constant, without replacement, deterministic row order per
  condition. The battery MUST NOT sample randomly; each run is fully
  reproducible from the frozen builders.
- Inference: greedy; same prompt as training; one-word True/False.

## Why the 392px contract is not applied at training time

Training pipelines (both backbones) feed raw cached images to the model's
own processor without a manual cap (verified verbatim from the seed-0 code:
scripts/run_7b_pipeline.py PHASE 2 collate_fn, src/training/collator.py).
That is part of the frozen TRAINING manifest and is retained exactly.
The 392px cap is an EVALUATION contract and is applied only by the battery
drivers. Changing training preprocessing would alter the manifest, which
the campaign explicitly forbids.

## Implementation status note

At freeze time, no battery implementation existed in the repo (verified by
searching master and all remote branches for with_sample/with_shuffle/
relcomp terms; only the spec in aftertrain.md and the partial building
blocks scripts/build_hardneg_manifest.py, scripts/grounding/freeze_facing.py,
src/grounding/images.py, src/datasets/vsr.py were found). The battery is
implemented as part of this campaign and every driver is pre-registered to
reproduce the table above exactly.

## Outcomes this battery is designed to detect

1. Seed variance in overall accuracy (normal) — expected to be small;
2. Seed variance in condition-level accuracy (any condition);
3. Systematic per-seed differences in hflip/hflip_inv asymmetry;
4. Per-family drift (orientation/depth/horizontal weak families);
5. Cheap-image / jitter-sensitivity changes (with_sample);
6. Order sensitivity (with_shuffle).