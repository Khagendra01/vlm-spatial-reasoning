"""Qwen3 deepstack feature extraction + object-region pooling (Phase 2).

Identical contract to Phase 1: deepstack features (post-merge, same
layout as image_embeds), mean-pool over the merged-grid cell intersecting
each known object box (synthetic ground truth). Training path keeps
autograd enabled (vision-LoRA gradients flow); evals use no_grad + a
per-arm feature cache.
"""

from __future__ import annotations

import torch


def image_input(self, image_path):
    """Processed pixel input (cached; LoRA-independent)."""
    if image_path not in self._pix_cache:
        if self.tiny:
            pix = torch.randn(1, 3, 2, 2 * 28, 2 * 28, device=self.device)
            grid = torch.tensor([[1, 2, 2]], device=self.device)
        else:
            from PIL import Image
            img = Image.open(self.data_dir / image_path).convert("RGB")
            inp = self.processor(images=img, text="", return_tensors="pt")
            pix = inp["pixel_values"].to(self.device, dtype=torch.bfloat16)
            grid = inp["image_grid_thw"].to(self.device)
        self._pix_cache[image_path] = (pix, grid)
    return self._pix_cache[image_path]


def vision_features(self, image_path, requires_grad):
    if not requires_grad and image_path in self._feat_cache:
        return self._feat_cache[image_path]
    pix, grid = self.image_input(image_path)
    with torch.no_grad() if not requires_grad else torch.enable_grad():
        _, deep = self.model.visual(pix, grid_thw=grid)
    feat = deep[0]
    if not requires_grad:
        self._feat_cache[image_path] = (feat, grid)
    return feat, grid


def pooled(self, feat, grid, boxes, obj_id):
    """Mean-pool the merged-grid cell at an object's PIXEL position.

    Phase-2 boxes are MATH coords (x right, y up, centered at 96): the
    pixel position is px = cx + 96, py = 96 - cy. Mapping math coords
    directly to grid cells picked the WRONG cell (dev-gate catch,
    2026-08-15) — the fix is the explicit pixel conversion.
    """
    h_feat, w_feat = grid[0, 1].item(), grid[0, 2].item()
    mh, mw = h_feat // 2, w_feat // 2
    cx, cy, _ = boxes[obj_id]
    canvas = 192.0
    px = cx + canvas / 2
    py = canvas / 2 - cy
    c = (min(int(px / canvas * mw), mw - 1),
         min(int(py / canvas * mh), mh - 1))
    idx = c[1] * mw + c[0]
    return feat[idx].unsqueeze(0).float()
