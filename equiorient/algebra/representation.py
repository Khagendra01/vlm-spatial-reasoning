"""Correct geometric representation of D4 on the typed latent.

z = [z_x ; z_y], z_x, z_y in R^128 (z in R^256). The action is
    rho(g) = G_g (x) I_128
where G_g is the 2x2 geometric matrix of g from algebra.d4. The action
is applied to the BLOCK structure: rho(H)[z_x, z_y] = [-z_x, z_y],
rho(R)[z_x, z_y] = [-z_y, z_x]. rho NEVER receives the relation label.
"""

from __future__ import annotations

import torch

from equiorient.algebra.d4 import ELEMENTS

Z_BLOCK = 128          # per-axis block dim
Z_DIM = 2 * Z_BLOCK    # total latent dim


def rho_block(g_name: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return the 2x2 integer block matrix for the element g."""
    return ELEMENTS[g_name].matrix


def apply_rho(g_name: str, z: torch.Tensor) -> torch.Tensor:
    """Apply rho(g) to a latent z of shape (..., 256).

    z is split into [z_x ; z_y] (each 128); the 2x2 geometric matrix is
    applied to the block pair, equivalent to G_g (x) I_128.
    """
    m = rho_block(g_name)
    zx, zy = z[..., :Z_BLOCK], z[..., Z_BLOCK:]
    # (x', y') = G (x, y): x' = m00 x + m01 y ; y' = m10 x + m11 y
    nx = m[0][0] * zx + m[0][1] * zy
    ny = m[1][0] * zx + m[1][1] * zy
    return torch.cat([nx, ny], dim=-1)


def rho_matrices():
    """All 8 rho matrices for the identifiability audit."""
    return {g: rho_block(g) for g in ELEMENTS}
