"""POST-HOC attention-localization diagnostic (measurement only).

This module reads ground-truth box geometry from the *manifest* to
measure where the learned no-box attention pooled its mass. It exists
so the training harness (equiorient/experiments/train_nobox.py) can be
scanned by the NOBOX_GATE audit as a file with ZERO ground-truth
references in its runtime/forward path.

Contract:
  * import ONLY for dev/eval analysis; never import, use, or call
    anything here inside a training step or optimizer graph.
  * Ground truth is used solely to *measure* the final attention
    distribution after the fact. It never selects features, never
    contributes gradients, and never influences predictions.
"""

from __future__ import annotations


def target_cell_indices(boxes: dict, grid_w: int, grid_h: int,
                        canvas: tuple[float, float] = (192.0, 192.0)) -> set:
    """Map each GT box center (scene canvas coords) to a merged-grid cell.

    Mirrors how the boxed study located cells, but here it is used ONLY
    to score attention mass; the model never sees these indices.
    """
    cw, ch = canvas
    idx = set()
    for (_obj_id, (cx, cy, _sz)) in boxes.items():
        c = (max(min(int(cx / cw * grid_w), grid_w), 0),
             max(min(int(cy / ch * grid_h), grid_h), 0))
        idx.add(c[1] * grid_w + c[0])
    return idx


def attention_mass_diag(attn, boxes: dict, grid_w: int, grid_h: int,
                        canvas: tuple[float, float] = (192.0, 192.0)) -> dict:
    """Measure distribution of a (1, T) attention vector over GT target
    cells vs the rest of the image. Returns the two masses."""
    n_tok = attn.numel()
    target = target_cell_indices(boxes, grid_w, grid_h, canvas)
    aw = attn.flatten()
    tgt = sum(float(aw[i]) for i in target if 0 <= i < n_tok)
    return {"target_mass": tgt, "non_target_mass": max(0.0, 1.0 - tgt)}


def attention_mass_diag_from_example(attn, example: dict, grid_w: int,
                                     grid_h: int) -> dict | None:
    """Wraps attention_mass_diag for a manifest example dict so callers
    never mention ground-truth keys inline. Returns None when the example
    carries no geometry (e.g., pre-computed no-box examples)."""
    if "boxes" not in example:
        return None
    return attention_mass_diag(attn, example["boxes"], grid_w, grid_h)