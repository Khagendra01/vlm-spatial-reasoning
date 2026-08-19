"""No-box relation encoder: full-image token pooling + D4-capable latent.

This implements the ``Option B`` design from the no-box experiment plan:
a learned query/attention pooling over **all** visual tokens of the image,
with NO access to ground-truth bounding boxes, object centers, or
pixel-space displacement.

Architecture (identical across every arm; the only difference between
arms is the structural objective):

    Qwen3 deepstack visual tokens  (1, T, feat_dim)  [frozen + LoRA]
      -> learned cross-attention pooling (1 query)
      -> context vector (1, proj_dim)
      -> Linear -> z = [z_x ; z_y] in R^Z_DIM  (z_x, z_y in R^Z_BLOCK)
      -> RelationHead8(z) -> 8-way compass logits

The EquiOrient / wrong-geometry structural losses act on the SAME z
block pair as the boxed PairEncoderV2 (rho(g) = G_g (x) I_Z_BLOCK), so
the causal contrast across arms is preserved while the box shortcut is
eliminated.
"""

from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F

FEAT_DIM = 4096          # Qwen3 deepstack out_hidden_size (8B)
Z_BLOCK = 128
Z_DIM = 2 * Z_BLOCK
N_CLASSES = 8


class FullImagePool(nn.Module):
    """Learned single-query cross-attention over full-image tokens.

    forward(feat) -> (z_x, z_y, attn)
      feat: (1, T, feat_dim) post-merge deepstack tokens (full image).
      attn: (1, T) attention weights over tokens — used as a *localization
            diagnostic* only; it reveals WHERE the model attends, it is
            NOT used to select features and carries no ground truth.
    """

    def __init__(self, feat_dim: int = FEAT_DIM,
                 proj_dim: int = 512):
        super().__init__()
        self.proj_dim = proj_dim
        # single learned query (the "relation readout")
        self.query = nn.Parameter(torch.randn(proj_dim) * 0.02)
        self.k_proj = nn.Linear(feat_dim, proj_dim)
        self.v_proj = nn.Linear(feat_dim, proj_dim)
        self.out = nn.Linear(proj_dim, Z_DIM)
        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.query, std=0.02)
        for m in (self.k_proj, self.v_proj):
            nn.init.xavier_uniform_(m.weight)
            nn.init.zeros_(m.bias)
        nn.init.xavier_uniform_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, feat: torch.Tensor):
        # feat: (1, T, feat_dim) or (T, feat_dim); normalise to 3D
        if feat.dim() == 2:
            feat = feat.unsqueeze(0)
        q = self.query.unsqueeze(0)          # (1, proj_dim)
        k = self.k_proj(feat)                # (1, T, proj_dim)
        v = self.v_proj(feat)                # (1, T, proj_dim)
        logits = torch.einsum("bp,btd->bt", q, k) / (self.proj_dim ** 0.5)  # (1, T)
        attn = F.softmax(logits, dim=-1)     # (1, T)
        ctx = torch.einsum("bt,btd->bd", attn, v)  # (1, proj_dim)
        z = self.out(ctx)                    # (1, Z_DIM)
        return z[..., :Z_BLOCK], z[..., Z_BLOCK:], attn  # (z_x, z_y, attn)


class NoBoxEncoder(nn.Module):
    """Wrapper producing (z_x, z_y) for the RelationHead8 contract."""

    def __init__(self, pool: FullImagePool):
        super().__init__()
        self.pool = pool

    def forward(self, feat: torch.Tensor):
        zx, zy, _ = self.pool(feat)
        return zx, zy


class RelationHead8(nn.Module):
    """Linear(256 -> 8) over the full z. FORCED decoding."""

    def __init__(self):
        super().__init__()
        self.w = nn.Linear(Z_DIM, N_CLASSES)

    def forward(self, zx, zy):
        return self.w(torch.cat([zx, zy], dim=-1))


class FullImageRelation(nn.Module):
    """End-to-end no-box encoder + head (for the tiny gate rig)."""

    def __init__(self, feat_dim: int = FEAT_DIM):
        super().__init__()
        self.enc = NoBoxEncoder(FullImagePool(feat_dim))
        self.head = RelationHead8()

    def forward(self, feat: torch.Tensor):
        zx, zy = self.enc(feat)
        return self.head(zx, zy), (zx, zy)
