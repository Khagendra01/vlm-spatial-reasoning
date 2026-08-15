"""Eight-way compass labels and their D4 action (Phase 2).

For a target pair (a, b) the displacement is
    Delta = (x_a - x_b, y_a - y_b)   (a relative to b, y up)
and the label is the compass direction of Delta. Under g in D4 the
displacement transforms by G_g, giving an EXACT known label permutation
pi_g for every group element -- including the unseen ones.
"""

from __future__ import annotations

from equiorient.algebra.d4 import ELEMENTS, mat_apply

# 8 compass labels, ordered so that adjacent labels are 45deg apart.
LABELS = ["right", "upper_right", "above", "upper_left",
          "left", "lower_left", "below", "lower_right"]
# index -> (dx, dy) unit direction (dy positive = up)
DIRECTIONS = [(1, 0), (1, 1), (0, 1), (-1, 1),
              (-1, 0), (-1, -1), (0, -1), (1, -1)]

_MARGIN = 0.10  # margin fraction of the canvas half-extent

_BOUNDARY_SLICE = 0.35  # reject directions inside +-boundary_slice*45deg of axes


def direction_of(dx: float, dy: float):
    """Label of a displacement, or None if too close to an axis boundary."""
    import math
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        return None
    ux, uy = dx / norm, dy / norm
    # unit directions (DIRECTIONS are not unit vectors: normalize here)
    units = [(vx / math.hypot(vx, vy), vy / math.hypot(vx, vy))
             for vx, vy in DIRECTIONS]
    best = max(range(8), key=lambda i: ux * units[i][0] + uy * units[i][1])
    cosang = ux * units[best][0] + uy * units[best][1]
    if cosang < math.cos(math.radians(22.5 * (1.0 - _BOUNDARY_SLICE))):
        return None
    return LABELS[best]


def label_index(label: str) -> int:
    return LABELS.index(label)


def label_permutation(g_name: str) -> list[int]:
    """pi_g: label index -> label index under g (exact, for every g)."""
    G = ELEMENTS[g_name].matrix
    perm = []
    for i, (dx, dy) in enumerate(DIRECTIONS):
        ndx, ndy = mat_apply(G, (dx, dy))
        perm.append(label_index(direction_of(ndx, ndy)))
    return perm


def label_permutation_map():
    """All 8 permutations for tests/audit."""
    return {g: label_permutation(g) for g in ELEMENTS}
