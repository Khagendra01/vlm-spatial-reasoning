"""Identifiability audit: does the evaluation separate correct from wrong?

Phase 1's composition test failed to separate the correct law from the
axis-swapped wrong law. Phase 2 audits EVERY group element BEFORE any GPU
run: for each element g (especially the unseen set), compare
rho_correct(g) with rho_wrong(g) as 2x2 matrices; emit a collision
matrix; assert the unseen set distinguishes the two laws.
"""

from __future__ import annotations

from equiorient.algebra.d4 import ELEMENTS, UNSEEN
from equiorient.algebra.representation import rho_matrices
from equiorient.algebra.wrong_representation import _WRONG_MATRICES


def collision_matrix() -> dict[str, dict[str, bool]]:
    """element -> {correct==wrong?} over all 8 elements."""
    correct = rho_matrices()
    out = {}
    for g in ELEMENTS:
        out[g] = {"collides": correct[g] == _WRONG_MATRICES[g]}
    return out


def audit() -> dict:
    """Full identifiability audit result."""
    cm = collision_matrix()
    unseen_collisions = [g for g in UNSEEN if cm[g]["collides"]]
    seen_collisions = [g for g in ("H", "R", "I") if cm[g]["collides"]]
    # Design intent: H collides (wrong H == correct H by design); R must
    # NOT collide; and the ENTIRE unseen set must distinguish the laws.
    ok = (len(unseen_collisions) == 0
          and not cm["R"]["collides"]
          and cm["H"]["collides"])  # H shared by design
    return {
        "collision_matrix": cm,
        "unseen_collisions": unseen_collisions,
        "seen_collisions": seen_collisions,
        "passes": ok,
    }


if __name__ == "__main__":
    import json
    a = audit()
    print(json.dumps(a, indent=1))
    print("UNSEEN SET:", UNSEEN)
    print("correct rho(R2) =", rho_matrices()["R2"],
          " wrong rho(R2) =", _WRONG_MATRICES["R2"])
    print("correct rho(R)  =", rho_matrices()["R"],
          " wrong rho(R)  =", _WRONG_MATRICES["R"])
