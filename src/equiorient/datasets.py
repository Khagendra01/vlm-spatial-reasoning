"""EquiOrient — CPU-side synthetic paired-scene generator (Gate 2).

Builds synthetic scenes of simple primitives with known ground-truth
relations, renders them, applies the Phase-1 transforms (H, V, V o H), and
recomputes relations on the TRANSFORMED geometry. The Gate-2 contract:

    recomputed_relation_after(transform) == expected_after(relation, transform)

for EVERY object pair and EVERY relation — i.e. the renderer's transform
changes only what the algebra claims (no accidental relation changes from
renderer semantics, tie-breaking, or margin issues).

Object model (plan-view, camera-orthogonal):
  - each object has (cx, cy) in pixel space, depth z, shape, size, color;
  - line segments additionally have a direction (dx, dy) for
    parallel/perpendicular (invariance-controlled);
  - relations: left_of / right_of (x), above / below (y), in_front_of /
    behind (z), parallel / perpendicular (direction vectors).

Facing/facing-away intentionally NOT modeled (Amendment A3: excluded from
Phase 1).

All geometry is float; relations use a declared margin to avoid ties, and
rendering uses the same coordinates, so the algebra law is testable at both
the geometry level and the rendered-pixel level (inverse/composition/determinism).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from src.equiorient.transforms import Relation, Transform, expected_after

# margins: fractions of the canvas used to guarantee strict inequalities
_X_MARGIN = 0.08
_Y_MARGIN = 0.08


@dataclass
class ObjectSpec:
    """A single primitive in a synthetic scene (canonical: center coords)."""

    obj_id: str
    cx: float
    cy: float
    depth: float = 0.0
    shape: str = "rect"  # rect | circle | line
    size: float = 24.0   # half-extent in px (rect/circle); line length / 2
    color: Tuple[int, int, int] = (80, 80, 200)
    direction: Optional[Tuple[float, float]] = None  # (dx, dy) for lines


@dataclass
class Scene:
    """A synthetic scene: canvas + objects + derived relations."""

    width: int
    height: int
    objects: List[ObjectSpec]
    scene_id: str = ""

    def relation(self, a: ObjectSpec, b: ObjectSpec,
                 relation: Relation) -> bool:
        """Ground-truth truth value of `relation` between a and b."""
        m = _X_MARGIN * self.width
        my = _Y_MARGIN * self.height
        if relation == Relation.LEFT_OF:
            return a.cx < b.cx - m
        if relation == Relation.RIGHT_OF:
            return a.cx > b.cx + m
        if relation == Relation.ABOVE:      # smaller y = higher on canvas
            return a.cy < b.cy - my
        if relation == Relation.BELOW:
            return a.cy > b.cy + my
        if relation == Relation.IN_FRONT:   # smaller depth = nearer
            return a.depth < b.depth
        if relation == Relation.BEHIND:
            return a.depth > b.depth
        if relation == Relation.PARALLEL:
            return _parallel(a, b)
        if relation == Relation.PERPENDICULAR:
            return _perpendicular(a, b)
        raise ValueError(f"relation {relation} not modeled in Phase 1")

    def relation_vector(self) -> Dict[str, Dict[str, bool]]:
        """All relations for all ordered object pairs (a, b)."""
        out: Dict[str, Dict[str, bool]] = {}
        for a in self.objects:
            for b in self.objects:
                if a is b:
                    continue
                out[f"{a.obj_id}>{b.obj_id}"] = {
                    r.value: self.relation(a, b, r) for r in Relation
                }
        return out

    def transformed(self, transform: Transform) -> "Scene":
        """New scene with geometry transformed by `transform` (geometry only)."""
        objs = [self._transform_object(o, transform) for o in self.objects]
        return Scene(self.width, self.height, objs, self.scene_id)

    def _transform_object(self, o: ObjectSpec, t: Transform) -> ObjectSpec:
        cx, cy = o.cx, o.cy
        if t == Transform.H:
            cx = self.width - o.cx
        elif t == Transform.V:
            cy = self.height - o.cy
        elif t == Transform.VH:
            cx = self.width - o.cx
            cy = self.height - o.cy
        elif t == Transform.I:
            pass
        else:
            raise ValueError(f"unsupported transform {t} for rendering")
        direction = o.direction
        if direction is not None and t in (Transform.H, Transform.VH):
            direction = (-direction[0], direction[1])
        if direction is not None and t in (Transform.V, Transform.VH):
            direction = (direction[0], -direction[1])
        return ObjectSpec(o.obj_id, cx, cy, o.depth, o.shape, o.size,
                          o.color, direction)

    # ------------------------------------------------------------------ #
    # rendering
    # ------------------------------------------------------------------ #
    def render(self) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (250, 250, 250))
        d = ImageDraw.Draw(img)
        # draw in depth order (farthest first)
        for o in sorted(self.objects, key=lambda o: -o.depth):
            s = o.size
            if o.shape == "circle":
                d.ellipse([o.cx - s, o.cy - s, o.cx + s, o.cy + s],
                          fill=o.color, outline=(40, 40, 40), width=2)
            elif o.shape == "line":
                (dx, dy) = o.direction or (1.0, 0.0)
                n = math.hypot(dx, dy) or 1.0
                ux, uy = dx / n, dy / n
                p1 = (o.cx - ux * s, o.cy - uy * s)
                p2 = (o.cx + ux * s, o.cy + uy * s)
                d.line([p1, p2], fill=o.color, width=6)
                # endpoint dot marks direction for human inspection
                r = max(3.0, s * 0.22)
                d.ellipse([p2[0] - r, p2[1] - r, p2[0] + r, p2[1] + r],
                          fill=(200, 60, 60))
            else:  # rect
                d.rectangle([o.cx - s, o.cy - s, o.cx + s, o.cy + s],
                            fill=o.color, outline=(40, 40, 40), width=2)
        return img

    def annotate(self, img: Image.Image) -> Image.Image:
        """Add object id labels for the human-inspection pack."""
        d = ImageDraw.Draw(img)
        for o in self.objects:
            d.text((o.cx - 8, o.cy - o.size - 14), o.obj_id, fill=(20, 20, 20))
        return img


# --------------------------------------------------------------------- #
# scene generation
# --------------------------------------------------------------------- #

def _parallel(a: ObjectSpec, b: ObjectSpec) -> bool:
    if a.direction is None or b.direction is None:
        return False
    (ax, ay), (bx, by) = a.direction, b.direction
    return abs(ax * by - ay * bx) < 1e-6


def _perpendicular(a: ObjectSpec, b: ObjectSpec) -> bool:
    if a.direction is None or b.direction is None:
        return False
    (ax, ay), (bx, by) = a.direction, b.direction
    return abs(ax * bx + ay * by) < 1e-6


def make_scene(scene_id: str, rng: random.Random, width: int = 320,
               height: int = 320) -> Scene:
    """Generate one scene with 3 objects and clean, unambiguous relations.

    Guarantees: distinct x/y/depth for all objects (no ties, margins
    respected after any Phase-1 transform), and each pair carries at least
    one axis relation so the algebra law is exercised.
    """
    m = _X_MARGIN * width
    my = _Y_MARGIN * height
    objs: List[ObjectSpec] = []
    used_x: List[float] = []
    used_y: List[float] = []
    used_z: List[float] = []

    def free_x() -> float:
        for _ in range(200):
            v = rng.uniform(40, width - 40)
            if all(abs(v - u) >= m for u in used_x):
                return v
        raise RuntimeError("could not place object (x)")

    def free_y() -> float:
        for _ in range(200):
            v = rng.uniform(40, height - 40)
            if all(abs(v - u) >= my for u in used_y):
                return v
        raise RuntimeError("could not place object (y)")

    # object 0, 1: axis-pair carriers (rectangles)
    for i in range(2):
        cx, cy = free_x(), free_y()
        used_x.append(cx)
        used_y.append(cy)
        objs.append(ObjectSpec(f"o{i}", cx, cy, depth=float(i),
                               shape="rect",
                               color=(60 + i * 60, 120, 200 - i * 40)))

    # object 2: line segment (orientation carrier), placed freely
    cx, cy = free_x(), free_y()
    used_x.append(cx)
    used_y.append(cy)
    used_z.append(0.5)
    ang = rng.uniform(0, math.pi)
    objs.append(ObjectSpec("o2", cx, cy, depth=0.5, shape="line",
                           color=(60, 180, 90),
                           direction=(math.cos(ang), math.sin(ang))))

    # parallel/perpendicular pair: add object 3 as a second line, either
    # parallel or perpendicular to o2
    cx, cy = free_x(), free_y()
    used_x.append(cx)
    used_y.append(cy)
    used_z.append(1.5)
    kind = rng.choice(["parallel", "perpendicular"])
    (dx2, dy2) = objs[2].direction or (1.0, 0.0)
    if kind == "parallel":
        d3 = (dx2, dy2)
    else:
        d3 = (-dy2, dx2)
    objs.append(ObjectSpec("o3", cx, cy, depth=1.5, shape="line",
                           color=(200, 120, 60), direction=d3))

    # o0,o1,o2,o3 distinct depths
    objs[1].depth = 2.0
    objs[0].depth = 0.0
    objs[2].depth = 1.0
    objs[3].depth = 3.0
    return Scene(width, height, objs, scene_id)


def generate_pack(num_scenes: int, seed: int = 20260814) -> List[Scene]:
    rng = random.Random(seed)
    return [make_scene(f"scene_{i:04d}", rng) for i in range(num_scenes)]


# --------------------------------------------------------------------- #
# Amendment D (2026-08-15): harder visual regime — scene recipe v2
# --------------------------------------------------------------------- #

def make_scene_v2(scene_id: str, rng: random.Random, width: int = 320,
                  height: int = 320) -> Scene:
    """Amendment D recipe: 5 objects (3 rectangles + 2 orientation lines)
    with size variance.

    Same guarantees as v1: distinct x/y/depth for all objects (margins
    respected after any Phase-1 transform), every pair carries at least one
    axis relation, depths strictly distinct (depth probe signal). Harder
    pooling disambiguation than v1's 4 objects: 20 ordered pairs/image vs
    12. D2 (longer training) deliberately deferred — budget-constrained,
    and D1 isolates the difficulty variable.
    """
    m = _X_MARGIN * width
    my = _Y_MARGIN * height
    objs: List[ObjectSpec] = []
    used_x: List[float] = []
    used_y: List[float] = []
    used_z: List[float] = []

    def free_x() -> float:
        for _ in range(400):
            v = rng.uniform(40, width - 40)
            if all(abs(v - u) >= m for u in used_x):
                return v
        raise RuntimeError("could not place object (x)")

    def free_y() -> float:
        for _ in range(400):
            v = rng.uniform(40, height - 40)
            if all(abs(v - u) >= my for u in used_y):
                return v
        raise RuntimeError("could not place object (y)")

    # 3 rectangles: axis carriers, varied sizes/colors
    for i in range(3):
        cx, cy = free_x(), free_y()
        used_x.append(cx)
        used_y.append(cy)
        objs.append(ObjectSpec(f"o{i}", cx, cy, depth=0.0, shape="rect",
                               size=rng.uniform(16, 30),
                               color=(60 + (i % 3) * 70, 90 + (i % 2) * 90,
                                      200 - i * 40)))

    # 2 lines: orientation carriers (parallel/perpendicular pair)
    ang = rng.uniform(0, math.pi)
    cx, cy = free_x(), free_y()
    used_x.append(cx)
    used_y.append(cy)
    objs.append(ObjectSpec("o3", cx, cy, depth=0.0, shape="line",
                           size=rng.uniform(16, 28), color=(60, 180, 90),
                           direction=(math.cos(ang), math.sin(ang))))
    cx, cy = free_x(), free_y()
    used_x.append(cx)
    used_y.append(cy)
    kind = rng.choice(["parallel", "perpendicular"])
    (dx2, dy2) = objs[3].direction or (1.0, 0.0)
    d4 = (dx2, dy2) if kind == "parallel" else (-dy2, dx2)
    objs.append(ObjectSpec("o4", cx, cy, depth=0.0, shape="line",
                           size=rng.uniform(16, 28), color=(200, 120, 60),
                           direction=d4))

    # distinct depths 0..4 (shuffled)
    depths = list(range(5))
    rng.shuffle(depths)
    for o, z in zip(objs, depths):
        o.depth = float(z)
    return Scene(width, height, objs, scene_id)


def generate_pack_v2(num_scenes: int, seed: int = 20260815) -> List[Scene]:
    """Amendment D pack: 17 scenes (10 train / 4 val / 3 holdout ids
    unchanged), harder recipe, new deterministic seed."""
    rng = random.Random(seed)
    return [make_scene_v2(f"scene_{i:04d}", rng) for i in range(num_scenes)]
