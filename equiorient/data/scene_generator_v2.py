"""Phase-2 scene generator: independent scenes with one target pair.

Each scene (independent by construction):
  - exactly ONE target pair (a, b) with displacement Delta = (xa-xb, ya-yb)
    sampled away from axis/diagonal boundaries (no label-flip risk);
  - 4-8 distractor objects with unique appearance combinations;
  - symmetric, rotation-safe shapes (circle, square, regular octagon);
  - no text rendered in the image;
  - balanced 8-direction labels across the pack;
  - explicit scene_id; split by scene_id BEFORE any transform.

Coordinates are MATH coords: x rightward, y upward, centered at (0,0)
with half-extent C. Pixel mapping (see renderer): px = x + C, py = C - y.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from equiorient.algebra.label_action import direction_of

HALF = 96.0  # canvas half-extent (math units); render 192x192 px
MIN_DIST = 14.0  # min center distance between objects
TARGET_RANGE = (55.0, 85.0)  # target |Delta| range (px in math units)

SHAPES = ("circle", "square", "octagon")


@dataclass
class Object2:
    obj_id: str
    x: float
    y: float
    shape: str
    size: float  # half-extent / radius
    color: tuple


@dataclass
class Scene2:
    scene_id: str
    target_a: Object2
    target_b: Object2
    distractors: list
    label: str          # 8-way compass label of Delta = a - b
    delta: tuple        # (dx, dy) math coords

    def objects(self):
        return [self.target_a, self.target_b] + list(self.distractors)


_COLORS = [(200, 60, 60), (60, 160, 220), (220, 180, 60), (90, 190, 120),
           (170, 90, 200), (240, 130, 60), (80, 130, 220), (180, 200, 70),
           (220, 100, 160), (110, 200, 190), (140, 90, 70), (90, 90, 200)]


def _gen_appearance(rng: random.Random, used: set) -> tuple:
    for _ in range(200):
        shape = rng.choice(SHAPES)
        color = rng.choice(_COLORS)
        size = round(rng.uniform(8.0, 13.0), 1)
        key = (shape, color, size)
        if key not in used:
            used.add(key)
            return key
    raise RuntimeError("appearance space exhausted")


def make_scene(scene_id: str, rng: random.Random, label: str) -> Scene2:
    """One independent scene with the given compass label for (a,b)."""
    from equiorient.algebra.label_action import DIRECTIONS, LABELS

    used: set = set()
    # target displacement: fixed direction (with margin), random magnitude
    di = LABELS.index(label)
    ux, uy = DIRECTIONS[di]
    mag = rng.uniform(*TARGET_RANGE)
    # center the pair: place b such that both a and b stay within [-HALF, HALF]
    cx = rng.uniform(-20.0, 20.0)
    cy = rng.uniform(-20.0, 20.0)
    # solve: b = c - Delta/2, a = c + Delta/2 with Delta = (ux, uy)*mag
    dx, dy = ux * mag, uy * mag
    bx, by = cx - dx / 2, cy - dy / 2
    ax, ay = cx + dx / 2, cy + dy / 2
    # enforce margins from the canvas edge
    edge = HALF - 16.0
    bx = min(max(bx, -edge), edge); by = min(max(by, -edge), edge)
    ax = min(max(ax, -edge), edge); ay = min(max(ay, -edge), edge)
    # recompute delta AFTER clamping (may shrink slightly; direction kept)
    dx, dy = ax - bx, ay - by
    lab = direction_of(dx, dy)
    if lab is None:  # clamp pushed onto a boundary: resample once
        return make_scene(scene_id, rng, label)
    shape_a, color_a, size_a = _gen_appearance(rng, used)
    shape_b, color_b, size_b = _gen_appearance(rng, used)
    a = Object2("a", ax, ay, shape_a, size_a, color_a)
    b = Object2("b", bx, by, shape_b, size_b, color_b)
    objs = [a, b]
    # distractors: 4-8, unique appearances, min distance from everything
    n_d = rng.randint(4, 8)
    for i in range(n_d):
        for _try in range(300):
            x = rng.uniform(-edge, edge)
            y = rng.uniform(-edge, edge)
            if all(math.hypot(x - o.x, y - o.y) >= MIN_DIST for o in objs):
                sh, co, si = _gen_appearance(rng, used)
                d = Object2(f"d{i}", x, y, sh, si, co)
                objs.append(d)
                break
        else:
            raise RuntimeError("could not place distractor")
    return Scene2(scene_id, a, b, objs[2:], lab, (round(dx, 3), round(dy, 3)))


def generate_pack(num_scenes: int, seed: int,
                  labels: Optional[list] = None,
                  id_offset: int = 0) -> list:
    """Generate `num_scenes` independent scenes with balanced labels.

    id_offset avoids scene-id collisions across split packs.
    """
    rng = random.Random(seed)
    from equiorient.algebra.label_action import LABELS
    if labels is None:
        labels = LABELS
    out = []
    for i in range(num_scenes):
        lab = labels[i % len(labels)]
        out.append(make_scene(f"scene_{i + id_offset:06d}", rng, lab))
    return out
