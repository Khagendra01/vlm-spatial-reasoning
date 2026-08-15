"""Phase-2 answer objective: cross-entropy on the forced 8-way head."""
from __future__ import annotations

import torch.nn.functional as F


def loss_answer(logits, y):
    return F.cross_entropy(logits, y)
