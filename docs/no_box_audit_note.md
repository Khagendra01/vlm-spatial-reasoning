# No-Box Experiment — Audit Note

**Branch:** `research/equiorient-no-box`
**Based on:** `e48054b747fd214873dd74bc905382f114998b3d` (submission preflight of Phase-2)
**Date:** 2026-08-18

## 1. The bounding-box shortcut (why this experiment exists)

In the Phase-2 study, the forward path hands the model the exact
ground-truth location of both target objects:

```
pooled(feat, grid, boxes, obj_id):
    cx, cy, _ = boxes[obj_id]          # GT box center (math coords)
    px = cx + canvas/2 ; py = canvas/2 - cy   # -> pixel coords
    cell = (px, py) -> merged-grid index
    return feat[cell]                  # single deepstack token AT the target
```

Then `pair_state` concatenates the two single tokens `(va, vb)` and feeds
them to `PairEncoderV2`. The model is therefore *given*:
- the location of target `a`,
- the location of target `b`,
- hence effectively the displacement `a - b`,

from which the 8-way compass label is essentially recoverable without
any real visual perception. At N>=512 every arm saturates to ~100%;
at N=128 EquiOrient is distinguishable from Wrong Geometry but does not
significantly beat plain Augmentation (Eq-Aug -0.93pp, n.s.).

## 2. The minimal, clean removal (chosen design: Option B)

We replace the box-indexed single-cell feature selection with a
**learned single-query cross-attention pooling over ALL visual tokens**
of the full image:

```
Qwen3 deepstack tokens  (1, T, 4096)
   -> learnable query q (1, 512)
   -> k_proj(feat), v_proj(feat)
   -> attn = softmax(q . k^T / sqrt(d))      # over all T tokens
   -> ctx  = sum_t attn_t * v_t              # (1, 512)
   -> z = Linear(ctx) → [z_x ; z_y] in R^256
   -> RelationHead8(z) -> 8-way logits
```

Why this removes the shortcut:
- NO bounding boxes, NO object centers, NO pixel displacement, NO
  masks, and NO coordinate-derived feature selection enter any part of
  the forward path.
- The model must itself locate the two target objects among the clutter
  and read their compass relation from the full image.
- The attention weights are returned **only as a diagnostic** (where the
  model looks); they carry no ground truth and are not used for feature
  selection.

## 3. Files added (this commit)

| File | Role |
|------|------|
| `equiorient/models/full_image_relation.py` | No-box pool + encoder + head |
| `equiorient/experiments/train_nobox.py` | Six-arm no-box harness (make_examples deliberately excludes boxes/delta) |
| `equiorient/tests/test_nobox_gate.py` | No-box pre-GPU verification gate |
| `equiorient/freezes/no_box_confirmatory.yaml` | (frozen later, before confirmatory runs) |

## 4. Verification (all CPU, precedes any GPU spend)

`python -m equiorient.tests.test_nobox_gate` -> **NOBOX_GATE_PASS (25/25)**
- no GT boxes / displacement / obj_id in executable model code
- `make_examples` example dict keys == {scene_id, transform, png, label_idx}
- D4 laws, wrong-law self-consistency, identifiability intact
- gradient reaches query / k_proj / head; z-ablation changes logits
- attention sums to 1 over the full token set

## 5. Additional protection of the existing study

- The Phase-2 `train.py`, `pair_encoder_v2.py`, `pooled()`, manifests,
  and all `results/phase2_*` / `results/n128_clean` artifacts are
  UNTOUCHED. This experiment is fully namespaced under
  `results/equiorient_no_box/`.

## 6. Dev-phase note

The dev phase will determine whether removing the shortcut produces a
non-saturated task (target 55-90%, preferably 60-85%) using DEV split
only; the confirmatory freeze happens before any test-set look.
