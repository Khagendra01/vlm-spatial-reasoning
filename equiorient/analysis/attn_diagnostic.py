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


def target_cell_indices(pair_boxes: dict, grid_w: int, grid_h: int,
                        canvas: tuple[float, float] = (192.0, 192.0)) -> set:
    """Map the TARGET pair (a,b) cell centers to merged-grid cells.

    Only the pair objects count as targets; distractors are explicitly
    excluded so the diagnostic answers "did the pool find THE pair".
    """
    cw, ch = canvas
    idx = set()
    for key in ("a", "b"):
        if key not in pair_boxes:
            continue
        cx, cy, _sz = pair_boxes[key]
        c = (max(min(int(cx / cw * grid_w), grid_w), 0),
             max(min(int(cy / ch * grid_h), grid_h), 0))
        idx.add(c[1] * grid_w + c[0])
    return idx


def attention_mass_diag(attn, boxes: dict, grid_w: int, grid_h: int,
                        canvas: tuple[float, float] = (192.0, 192.0)) -> dict:
    """Measure distribution of a (1, T) attention vector over the GT
    TARGET-PAIR cells vs the rest of the image.

    Returns pair-attention mass AND whether BOTH a and b cells are inside
    the attended set (locatability).
    """
    n_tok = attn.numel()
    target = target_cell_indices(boxes, grid_w, grid_h, canvas)
    aw = attn.flatten()
    if not target:
        return {"pair_mass": None, "pair_in_top4": None,
                "a_in_top4": None, "b_in_top4": None}
    pair_mass = sum(float(aw[i]) for i in target if 0 <= i < n_tok)
    top_idx = set(aw.topk(min(4, n_tok)).indices.tolist())
    a_i = target_cell_indices({"a": boxes["a"]}, grid_w, grid_h, canvas)
    b_i = target_cell_indices({"b": boxes["b"]}, grid_w, grid_h, canvas)
    a_in = bool(a_i & top_idx)
    b_in = bool(b_i & top_idx)
    return {
        "pair_mass": pair_mass,
        "pair_in_top4": (a_in and b_in),
        "a_in_top4": a_in,
        "b_in_top4": b_in,
    }


def attention_mass_diag_from_example(attn, example: dict, grid_w: int,
                                     grid_h: int) -> dict | None:
    """Wraps attention_mass_diag for a manifest example dict so callers
    never mention ground-truth keys inline. Returns None when the example
    carries no geometry (e.g., pre-computed no-box examples)."""
    if "boxes" not in example:
        return None
    return attention_mass_diag(attn, example["boxes"], grid_w, grid_h)