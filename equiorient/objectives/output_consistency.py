"""Phase-2 output-consistency: answer law on the TRANSFORMED image.

The exact label permutation pi_g (algebra.label_action) maps the answer
on x to the expected answer on gx. Soft targets come from the model's
own logits on x (detached) permuted by pi_g.
"""
from __future__ import annotations

import torch.nn.functional as F


def loss_output_consistency(logits_gx, logits_x, perm):
    # perm: list of length 8 mapping class index -> class index
    return F.mse_loss(logits_gx, logits_x[:, perm].detach())
