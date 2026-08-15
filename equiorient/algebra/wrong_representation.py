"""WRONG geometric representation of D4 (Phase-2 causal control).

    rho_wrong(R) = R180 = -I
    rho_wrong(H) = H   (same as correct)

This is an algebraically SELF-CONSISTENT homomorphism of D4
(rho_wrong(R)^4 = I, rho_wrong(H)^2 = I, (rho_wrong(RH))^2 = I) but it
is geometrically wrong. Crucially:
    rho_wrong(R^2) = I        while  rho_correct(R^2) = -I
    rho_wrong(R^3) = -I       while  rho_correct(R^3) != -I
so the wrong law CANNOT accidentally look correct on the unseen set
(the Phase-1 symmetry collision is eliminated).
"""

from __future__ import annotations

import torch

from equiorient.algebra.representation import Z_BLOCK, Z_DIM

# 2x2 integer matrices of the wrong representation, per group element name.
_WRONG_MATRICES = {
    "I": ((1, 0), (0, 1)),
    "R": ((-1, 0), (0, -1)),    # R180 = -I
    "R2": ((1, 0), (0, 1)),     # (-I)^2 = I
    "R3": ((-1, 0), (0, -1)),   # (-I)^3 = -I
    "H": ((-1, 0), (0, 1)),     # same as correct H
    "RH": ((1, 0), (0, -1)),    # (-I) H
    "R2H": ((-1, 0), (0, 1)),   # I H
    "R3H": ((1, 0), (0, -1)),   # (-I) H
}


def wrong_rho_block(g_name: str):
    return _WRONG_MATRICES[g_name]


def apply_wrong_rho(g_name: str, z: torch.Tensor) -> torch.Tensor:
    m = _WRONG_MATRICES[g_name]
    zx, zy = z[..., :Z_BLOCK], z[..., Z_BLOCK:]
    nx = m[0][0] * zx + m[0][1] * zy
    ny = m[1][0] * zx + m[1][1] * zy
    return torch.cat([nx, ny], dim=-1)


def wrong_self_consistency_checks() -> list[str]:
    """Verify the wrong map is a homomorphism (self-consistent)."""
    from equiorient.algebra.d4 import COMPOSE, ELEMENTS
    problems = []
    for an, a in ELEMENTS.items():
        for bn, b in ELEMENTS.items():
            ab = COMPOSE[(an, bn)].name
            lhs = _WRONG_MATRICES[an]
            rhs = _WRONG_MATRICES[bn]
            prod = (
                (lhs[0][0] * rhs[0][0] + lhs[0][1] * rhs[1][0],
                 lhs[0][0] * rhs[0][1] + lhs[0][1] * rhs[1][1]),
                (lhs[1][0] * rhs[0][0] + lhs[1][1] * rhs[1][0],
                 lhs[1][0] * rhs[0][1] + lhs[1][1] * rhs[1][1]),
            )
            if prod != _WRONG_MATRICES[ab]:
                problems.append(f"wrong rep not homomorphic on {an}*{bn}")
    return problems
