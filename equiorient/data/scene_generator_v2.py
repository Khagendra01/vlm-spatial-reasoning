"""Phase-2 scene generator: independent scenes with one target pair.

Each scene (independent by construction):
  - exactly ONE target pair (a, b) with displacement Delta = (xa-xb, ya-yb)
    sampled away from axis/diagonal boundaries (no label-flip risk);
  - 8-16 distractor objects with similar visual properties to targets;
  - shapes (circle, square, regular octagon);
  - no text rendered in the image;
  - balanced 8-direction labels across the pack;
  - explicit scene_id; split by scene_id BEFORE any transform.

Coordinates are MATH coords: x rightward, y upward, centered at (0,0)
with half-extent C. Pixel mapping (see renderer): px = x + C, py = C - y.

ESCALATION v3 (2026-08-16): targets are tiny (3-5), all objects share a
muted color palette so targets blend into clutter, distractors outnumber
targets 8-16:1, heavy per-pixel noise, overlap allowed. The VLM must
actually *find* the target pair among dense homogeneous clutter — simple
position-based readout from pooled grid cells is no longer reliable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from equiorient.algebra.label_action import direction_of

HALF = 96.0  # canvas half-extent (math units); render 192x192 px
MIN_DIST = 10.0  # min center distance between any two objects
TARGET_RANGE = (50.0, 80.0)  # target |Delta| range (px in math units)

SHAPES = ("circle", "square", "octagon")

# Muted palette: all objects share similar tones so targets don't stand out.
# Grouped into families; each family has 3-4 near-identical shades.
_MUTED_PALETTE = [
    # warm grays / browns
    (160, 150, 140), (155, 145, 135), (165, 155, 145), (150, 140, 130),
    # cool grays / blues
    (130, 140, 155), (125, 135, 150), (135, 145, 160), (120, 130, 145),
    # olive / dark green
    (140, 150, 120), (135, 145, 115), (145, 155, 125), (130, 140, 110),
    # muted purple / slate
    (145, 135, 155), (140, 130, 150), (150, 140, 160), (135, 125, 145),
    # dark earth tones
    (120, 110, 100), (125, 115, 105), (115, 105, 95), (130, 120, 110),
]


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


def _gen_appearance(rng: random.Random, used: set,
                    size_lo: float = 3.0, size_hi: float = 5.0) -> tuple:
    """Generate a muted appearance (shape + color + small size)."""
    for _ in range(300):
        shape = rng.choice(SHAPES)
        color = rng.choice(_MUTED_PALETTE)
        size = round(rng.uniform(size_lo, size_hi), 1)
        key = (shape, color, size)
        if key not in used:
            used.add(key)
            return key
    # Fallback: relax uniqueness (dense clutter, reuse is OK)
    shape = rng.choice(SHAPES)
    color = rng.choice(_MUTED_PALETTE)
    size = round(rng.uniform(size_lo, size_hi), 1)
    return (shape, color, size)


def make_scene(scene_id: str, rng: random.Random, label: str) -> Scene2:
    """One independent scene with the given compass label for (a,b)."""
    from equiorient.algebra.label_action import DIRECTIONS, LABELS

    used: set = set()
    # target displacement: fixed direction (with margin), random magnitude
    di = LABELS.index(label)
    ux, uy = DIRECTIONS[di]
    mag = rng.uniform(*TARGET_RANGE)
    # center the pair: place b such that both a and b stay within [-HALF, HALF]
    cx = rng.uniform(-25.0, 25.0)
    cy = rng.uniform(-25.0, 25.0)
    # solve: b = c - Delta/2, a = c + Delta/2 with Delta = (ux, uy)*mag
    dx, dy = ux * mag, uy * mag
    bx, by = cx - dx / 2, cy - dy / 2
    ax, ay = cx + dx / 2, cy + dy / 2
    # enforce margins from the canvas edge
    edge = HALF - 10.0
    bx = min(max(bx, -edge), edge); by = min(max(by, -edge), edge)
    ax = min(max(ax, -edge), edge); ay = min(max(ay, -edge), edge)
    # recompute delta AFTER clamping (may shrink slightly; direction kept)
    dx, dy = ax - bx, ay - by
    lab = direction_of(dx, dy)
    if lab is None:  # clamp pushed onto a boundary: resample once
        return make_scene(scene_id, rng, label)
    # targets: tiny (3-5), muted colors — they blend into clutter
    shape_a, color_a, size_a = _gen_appearance(rng, used, 3.0, 5.0)
    shape_b, color_b, size_b = _gen_appearance(rng, used, 3.0, 5.0)
    a = Object2("a", ax, ay, shape_a, size_a, color_a)
    b = Object2("b", bx, by, shape_b, size_b, color_b)
    objs = [a, b]
    # distractors: 8-16 (dense homogeneous clutter), same size range as targets
    n_d = rng.randint(8, 16)
    placed = 0
    for i in range(n_d):
        for _try in range(500):
            x = rng.uniform(-edge, edge)
            y = rng.uniform(-edge, edge)
            # minimum separation from ALL existing objects (tight packing)
            if all(math.hypot(x - o.x, y - o.y) >= MIN_DIST * 0.4
                   for o in objs):
                sh, co, si = _gen_appearance(rng, used, 3.0, 6.0)
                d = Object2(f"d{i}", x, y, sh, si, co)
                objs.append(d)
                placed += 1
                break
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
