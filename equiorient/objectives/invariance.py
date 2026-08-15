"""Phase-2 latent invariance: z(gx) ~= z(x)."""
from __future__ import annotations


def loss_invariance(zx, zgx):
    return sum(((a - b) ** 2).mean() for a, b in zip(zx, zgx))
