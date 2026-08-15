"""Phase-2 pair encoder + 8-way relation head.

z = [z_x ; z_y], each 128-dim (z in R^256). The head consumes ALL of z
and outputs the 8 compass classes. Same matched-architecture discipline
as Phase 1: identical in every arm.
"""

from __future__ import annotations

import torch
from torch import nn

FEAT_DIM = 4096          # Qwen3 deepstack out_hidden_size (8B)
Z_BLOCK = 128
Z_DIM = 2 * Z_BLOCK
N_CLASSES = 8


class PairEncoderV2(nn.Module):
    """Linear(2*4096 -> 512) -> GELU -> Linear(512 -> 256); split [zx; zy]."""

    def __init__(self, feat_dim: int = FEAT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2 * feat_dim, 512), nn.GELU(),
            nn.Linear(512, Z_DIM))

    def forward(self, va, vb):
        z = self.net(torch.cat([va, vb], dim=-1))
        return z[..., :Z_BLOCK], z[..., Z_BLOCK:]  # (z_x, z_y)


class RelationHead8(nn.Module):
    """Linear(256 -> 8) over the full z. FORCED decoding."""

    def __init__(self):
        super().__init__()
        self.w = nn.Linear(Z_DIM, N_CLASSES)

    def forward(self, zx, zy):
        return self.w(torch.cat([zx, zy], dim=-1))
