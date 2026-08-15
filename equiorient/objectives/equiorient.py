"""Phase-2 EquiOrient objective: z(gx) ~= rho(g) z(x) with the CORRECT
geometric action. z is a (z_x, z_y) block pair.

rho_vec encodes the 2x2 matrix G_g = ((sxx, sxy), (syx, syy)) so that
    rho(g)[zx, zy] = [sxx*zx + sxy*zy, syx*zx + syy*zy]
which is exactly G_g (x) I_128.
"""
from __future__ import annotations


def rho_vec_of(g_name: str):
    """Flatten the 2x2 geometric matrix into the (sxx, sxy, syx, syy) tuple."""
    from equiorient.algebra.d4 import ELEMENTS
    m = ELEMENTS[g_name].matrix
    return (m[0][0], m[0][1], m[1][0], m[1][1])


def wrong_rho_vec_of(g_name: str):
    from equiorient.algebra.wrong_representation import _WRONG_MATRICES
    m = _WRONG_MATRICES[g_name]
    return (m[0][0], m[0][1], m[1][0], m[1][1])


def loss_equiorient(zx, zgx, rho_vec):
    zx0, zx1 = zx
    gx0, gx1 = zgx
    sxx, sxy, syx, syy = rho_vec
    pred0 = sxx * zx0 + sxy * zx1
    pred1 = syx * zx0 + syy * zx1
    return ((pred0 - gx0) ** 2).mean() + ((pred1 - gx1) ** 2).mean()
