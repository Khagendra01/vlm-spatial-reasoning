"""EquiOrient — transformation algebra, Gate 1 (2026-08-14).

Executable version of the mutated protocol target (PROTOCOL_FREEZE.md
Amendment A). Defines the typed spatial state, the predeclared
geometry-derived actions rho(T), and the algebra checks:

    identity:      rho(I) = I
    inverse:       rho(T^-1) rho(T) = I
    composition:   rho(V o H) = rho(V) rho(H)

rho is derived from geometry ONLY: a horizontal reflection acts on the
horizontal state component and leaves provably-orthogonal components
invariant. rho NEVER receives the ground-truth relation label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Typed spatial state components
# ---------------------------------------------------------------------------


class StateComponent(str, Enum):
    """Typed components of the object-pair spatial state z(a,b)."""

    H = "z_h"          # horizontal axis (left/right)
    V = "z_v"          # vertical axis (above/below)
    D = "z_d"          # depth axis (in front of / behind)
    POSE = "z_pose"    # intrinsic orientation (facing etc.) — Phase 2 only
    ORIENT = "z_orient"  # parallel / perpendicular (invariance-controlled)


# ---------------------------------------------------------------------------
# Transforms (geometry only)
# ---------------------------------------------------------------------------


class Transform(str, Enum):
    """Input-image transforms. Phase 1: H and V seen, V o H held out."""

    I = "identity"
    H = "hflip"          # horizontal reflection (left <-> right)
    V = "vflip"          # vertical reflection (above <-> below)
    VH = "v_after_h"     # composition V o H  (HELD OUT in Phase 1)
    H2 = "hflip_hflip"   # H o H (for inverse testing)


# rho(T): predeclared action on typed state components.
# Values: +1 = keep, -1 = flip (negate the component).
# Derived from geometry: H flips the horizontal axis, V flips the vertical
# axis; depth and orientation are orthogonal to both reflections in a
# plan-view (camera-orthogonal) rendering model.
RHO_ACTION: Dict[Transform, Dict[StateComponent, int]] = {
    Transform.I: {c: +1 for c in StateComponent},
    Transform.H: {
        StateComponent.H: -1,
        StateComponent.V: +1,
        StateComponent.D: +1,
        StateComponent.POSE: -1,  # mirror flips intrinsic facing direction
        StateComponent.ORIENT: +1,  # parallel/perpendicular preserved
    },
    Transform.V: {
        StateComponent.H: +1,
        StateComponent.V: -1,
        StateComponent.D: +1,
        StateComponent.POSE: +1,
        StateComponent.ORIENT: +1,
    },
    Transform.VH: {  # V o H: product of the two actions
        StateComponent.H: -1,
        StateComponent.V: -1,
        StateComponent.D: +1,
        StateComponent.POSE: -1,
        StateComponent.ORIENT: +1,
    },
    Transform.H2: {c: +1 for c in StateComponent},  # H o H = identity
}


@dataclass(frozen=True)
class TransformDef:
    """Machine-readable transform row (protocol section 5/6, Amendment A)."""

    transform: Transform
    transform_class: str
    is_confirmatory: bool
    is_safe: bool
    reason: str


TRANSFORM_TABLE: List[TransformDef] = [
    TransformDef(Transform.I, "identity", True, True,
                 "identity transform for algebra checks"),
    TransformDef(Transform.H, "relation_permutation", True, True,
                 "horizontal reflection: flips left/right, leaves "
                 "above/below + depth invariant in plan-view model"),
    TransformDef(Transform.V, "relation_permutation", True, True,
                 "vertical reflection: flips above/below, leaves "
                 "left/right + depth invariant"),
    TransformDef(Transform.VH, "relation_permutation_composition", False, True,
                 "V o H composition; HELD OUT from Phase-1 training"),
    TransformDef(Transform.H2, "composition_identity", True, True,
                 "H o H must equal identity"),
]


# ---------------------------------------------------------------------------
# Relation algebra: expected relation BEFORE/AFTER each transform
# ---------------------------------------------------------------------------


class Relation(str, Enum):
    """Phase-1 relation set (facing EXCLUDED, per Amendment A3)."""

    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    ABOVE = "above"
    BELOW = "below"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    IN_FRONT = "in_front_of"
    BEHIND = "behind"


# flip pairings under the respective reflection axes (relation -> its pair)
_H_PAIRS = {Relation.LEFT_OF: Relation.RIGHT_OF,
            Relation.RIGHT_OF: Relation.LEFT_OF}
_V_PAIRS = {Relation.ABOVE: Relation.BELOW,
            Relation.BELOW: Relation.ABOVE}
# which axis component each relation lives on (paired flip axis)
_PAIR_FOR = {
    Relation.LEFT_OF: (StateComponent.H, _H_PAIRS),
    Relation.RIGHT_OF: (StateComponent.H, _H_PAIRS),
    Relation.ABOVE: (StateComponent.V, _V_PAIRS),
    Relation.BELOW: (StateComponent.V, _V_PAIRS),
}


def expected_after(relation: Relation, transform: Transform) -> Relation:
    """Expected relation label after applying ``transform``.

    Geometry-derived: a transform flips a relation iff it flips the typed
    state component that carries the relation; otherwise the relation is
    invariant (including depth + orientation, which no Phase-1 reflection
    touches). Predeclared and deterministic.
    """
    if transform == Transform.I:
        return relation
    if transform == Transform.H2:
        # H o H = identity, verified against the state action below
        return relation
    # composition V o H: apply H first, then V (flip products on components)
    if transform == Transform.VH:
        after_h = expected_after(relation, Transform.H)
        return expected_after(after_h, Transform.V)
    # single reflections: flip iff the relation's component is flipped
    if relation in _PAIR_FOR:
        comp, pairs = _PAIR_FOR[relation]
        if RHO_ACTION[transform][comp] == -1:
            return pairs[relation]
        return relation  # orthogonal axis: invariant
    # depth / orientation relations: invariant under both reflections
    return relation


# Full machine-readable algebra table (relation x transform -> expected_after)
ALGEBRA_TABLE: Dict[str, Dict[str, str]] = {
    r.value: {t.value: expected_after(r, t).value for t in Transform}
    for r in Relation
}


def relation_state_component(relation: Relation) -> StateComponent:
    """Which typed component carries a relation's truth (for rho checks)."""
    if relation in (Relation.LEFT_OF, Relation.RIGHT_OF):
        return StateComponent.H
    if relation in (Relation.ABOVE, Relation.BELOW):
        return StateComponent.V
    if relation in (Relation.IN_FRONT, Relation.BEHIND):
        return StateComponent.D
    return StateComponent.ORIENT
