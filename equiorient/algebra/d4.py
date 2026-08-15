"""D4 (dihedral) group algebra for EquiOrient Phase 2.

Elements are 2x2 integer matrices acting on math coordinates
(x rightward, y upward). Generators:
    H = [[-1, 0], [0, 1]]   (horizontal reflection)
    R = [[ 0,-1], [1, 0]]   (90deg counter-clockwise rotation)
RH != HR (noncommutative). The group has 8 elements
{I, R, R2, R3, H, RH, R2H, R3H}; the five NON-generator elements
{R2, R3, RH, R2H, R3H} are the unseen/held-out set.
"""

from __future__ import annotations

from dataclasses import dataclass

I = ((1, 0), (0, 1))
H = ((-1, 0), (0, 1))
R = ((0, -1), (1, 0))


def mat_mul(a, b):
    """2x2 integer matrix product."""
    return (
        (a[0][0] * b[0][0] + a[0][1] * b[1][0],
         a[0][0] * b[0][1] + a[0][1] * b[1][1]),
        (a[1][0] * b[0][0] + a[1][1] * b[1][0],
         a[1][0] * b[0][1] + a[1][1] * b[1][1]),
    )


def mat_apply(m, v):
    """Apply 2x2 matrix to a 2-vector (x, y)."""
    return (m[0][0] * v[0] + m[0][1] * v[1],
            m[1][0] * v[0] + m[1][1] * v[1])


def mat_equal(a, b):
    return a == b


@dataclass(frozen=True)
class D4Element:
    """A group element with its canonical name and matrix."""
    name: str
    matrix: tuple  # 2x2 int tuple
    power: int = 0  # R-power (0..3); None for reflections

    def __mul__(self, other: "D4Element") -> "D4Element":
        return COMPOSE[(self.name, other.name)]


# Build all 8 elements explicitly.
R2 = mat_mul(R, R)          # 180deg
R3 = mat_mul(R2, R)         # 270deg
RH = mat_mul(R, H)
R2H = mat_mul(R2, H)
R3H = mat_mul(R3, H)

ELEMENTS: dict[str, D4Element] = {
    "I": D4Element("I", I, 0),
    "R": D4Element("R", R, 1),
    "R2": D4Element("R2", R2, 2),
    "R3": D4Element("R3", R3, 3),
    "H": D4Element("H", H, None),
    "RH": D4Element("RH", RH, None),
    "R2H": D4Element("R2H", R2H, None),
    "R3H": D4Element("R3H", R3H, None),
}

GENERATORS = ("H", "R")
SEEN = ("H", "R")                       # trained generator actions
UNSEEN = ("R2", "R3", "RH", "R2H", "R3H")  # held-out group elements

# Composition table: name -> {other_name -> result element}
COMPOSE: dict[tuple[str, str], D4Element] = {}
for an, a in ELEMENTS.items():
    for bn, b in ELEMENTS.items():
        m = mat_mul(a.matrix, b.matrix)
        COMPOSE[(an, bn)] = next(e for e in ELEMENTS.values()
                                 if mat_equal(e.matrix, m))

# Inverse table.
INVERSE: dict[str, str] = {}
for an, a in ELEMENTS.items():
    for bn, b in ELEMENTS.items():
        if mat_equal(mat_mul(a.matrix, b.matrix), I):
            INVERSE[an] = bn
            break


def group_axiom_checks() -> list[str]:
    """Return a list of all D4 group-law violations (empty = pass)."""
    problems = []
    # closure + associativity
    for a in ELEMENTS.values():
        for b in ELEMENTS.values():
            ab = a * b
            if ab.name not in ELEMENTS:
                problems.append(f"closure {a.name}*{b.name}")
            for c in ELEMENTS.values():
                lhs = (a * b) * c
                rhs = a * (b * c)
                if lhs.name != rhs.name:
                    problems.append(
                        f"assoc {a.name}*{b.name}*{c.name}: "
                        f"{lhs.name} != {rhs.name}")
    # identity
    for a in ELEMENTS.values():
        if (a * ELEMENTS["I"]).name != a.name:
            problems.append(f"right-identity {a.name}")
        if (ELEMENTS["I"] * a).name != a.name:
            problems.append(f"left-identity {a.name}")
    # inverses
    for a in ELEMENTS.values():
        inv = ELEMENTS[INVERSE[a.name]]
        if (a * inv).name != "I" or (inv * a).name != "I":
            problems.append(f"inverse {a.name}")
    # generator relations
    if (ELEMENTS["H"] * ELEMENTS["H"]).name != "I":
        problems.append("H^2 != I")
    if (ELEMENTS["R"] * ELEMENTS["R"] * ELEMENTS["R"] * ELEMENTS["R"]).name != "I":
        problems.append("R^4 != I")
    if (ELEMENTS["R"] * ELEMENTS["H"] * ELEMENTS["R"] * ELEMENTS["H"]).name != "I":
        problems.append("(RH)^2 != I")
    if (ELEMENTS["R"] * ELEMENTS["H"]).name == (ELEMENTS["H"] * ELEMENTS["R"]).name:
        problems.append("RH == HR (group must be noncommutative)")
    return problems
