"""Phase-2 scene generator: independent scenes with one target pair.

ESCALATION v4 (2026-08-16): extreme difficulty.
  - Canvas 192x192, targets 2-4px (tiny dots)
  - 12-20 distractors of similar size/color  
  - ALL objects use the same 3 muted colors (near-indistinguishable)
  - Heavy per-pixel noise (amp=12)
  - Objects packed tightly (MIN_DIST=6, no separation from targets)
  - Background contrast further reduced

The VLM must distinguish the target pair from homogeneous clutter.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from equiorient.algebra.label_action import direction_of

HALF = 96.0
MIN_DIST = 6.0
TARGET_RANGE = (50.0, 80.0)
SHAPES = ("circle", "square", "octagon")

# v4: only 3 nearly-identical colors — targets and distractors look the same
_PALETTE = [
    (145, 140, 135),  # warm gray
    (140, 145, 150),  # cool gray
    (150, 145, 140),  # brownish gray
]


@dataclass
class Object2:
    obj_id: str
    x: float
    y: float
    shape: str
    size: float
    color: tuple


@dataclass
class Scene2:
    scene_id: str
    target_a: Object2
    target_b: Object2
    distractors: list
    label: str
    delta: tuple

    def objects(self):
        return [self.target_a, self.target_b] + list(self.distractors)


def _gen_appearance(rng: random.Random) -> tuple:
    shape = rng.choice(SHAPES)
    color = rng.choice(_PALETTE)
    size = round(rng.uniform(2.0, 4.0), 1)
    return (shape, color, size)


def make_scene(scene_id: str, rng: random.Random, label: str) -> Scene2:
    from equiorient.algebra.label_action import DIRECTIONS, LABELS

    di = LABELS.index(label)
    ux, uy = DIRECTIONS[di]
    mag = rng.uniform(*TARGET_RANGE)
    cx = rng.uniform(-20.0, 20.0)
    cy = rng.uniform(-20.0, 20.0)
    dx, dy = ux * mag, uy * mag
    bx, by = cx - dx / 2, cy - dy / 2
    ax, ay = cx + dx / 2, cy + dy / 2
    edge = HALF - 8.0
    bx = min(max(bx, -edge), edge); by = min(max(by, -edge), edge)
    ax = min(max(ax, -edge), edge); ay = min(max(ay, -edge), edge)
    dx, dy = ax - bx, ay - by
    lab = direction_of(dx, dy)
    if lab is None:
        return make_scene(scene_id, rng, label)

    sa, ca, sza = _gen_appearance(rng)
    sb, cb, szb = _gen_appearance(rng)
    a = Object2("a", ax, ay, sa, sza, ca)
    b = Object2("b", bx, by, sb, szb, cb)
    objs = [a, b]

    # 12-20 distractors: dense homogeneous clutter
    n_d = rng.randint(12, 20)
    for i in range(n_d):
        for _try in range(600):
            x = rng.uniform(-edge, edge)
            y = rng.uniform(-edge, edge)
            # tight packing: no separation requirement from targets
            if all(math.hypot(x - o.x, y - o.y) >= MIN_DIST
                   for o in objs):
                sh, co, si = _gen_appearance(rng)
                d = Object2(f"d{i}", x, y, sh, si, co)
                objs.append(d)
                break
    return Scene2(scene_id, a, b, objs[2:], lab, (round(dx, 3), round(dy, 3)))


def generate_pack(num_scenes: int, seed: int,
                  labels: Optional[list] = None,
                  id_offset: int = 0) -> list:
    rng = random.Random(seed)
    from equiorient.algebra.label_action import LABELS
    if labels is None:
        labels = LABELS
    out = []
    for i in range(num_scenes):
        lab = labels[i % len(labels)]
        out.append(make_scene(f"scene_{i + id_offset:06d}", rng, lab))
    return out
