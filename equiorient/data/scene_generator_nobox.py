"""NO-BOX scene generator: visually identifiable target pair.

DEV-CALIBRATION (2026-08-19) — WHY THIS EXISTS
-----------------------------------------------
The Phase-2 v4 generator (scene_generator_v2.py) samples target and
distractor appearances from the SAME palette/shapes/sizes. Under the
boxed harness this was fine: ground-truth boxes identified which two
dots were the target pair, and the shortcut carried the rest.

Under the NO-BOX harness the same data is *unlearnable by construction*:
the label is defined by the (a,b) displacement, but with targets visually
identical to 12-20 distractors the image cannot identify which pair the
label refers to. Empirically all 9 target appearance combos overlap
distractor combos, and dev accuracy collapses to exactly chance (0.1250)
at every N and training budget.

The no-box task therefore needs targets that are *identifiable from the
pixels alone*:

  * target a: unique color, always "a" (the label is direction b -> a,
    so the ordered pair matters)
  * target b: unique color, always "b"
  * distractors: draw from a disjoint muted palette, same shapes/sizes

The relation label is STILL a pure geometric property of the scene
(direction of b -> a in math coords), so the D4 structural hypothesis
(EquiOrient vs Augmentation vs WrongGeometry on held-out group
elements) is preserved. Difficulty knobs (target size, distractor
count/color distance, noise, background contrast) let the DEV phase
tune accuracy into 55-90% (prefer 60-85%) BEFORE any confirmatory
freeze.

This module does NOT touch scene_generator_v2.py (frozen for the boxed
Phase-2 study).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

from equiorient.algebra.label_action import direction_of

HALF = 96.0
MIN_DIST = 6.0
TARGET_RANGE = (50.0, 80.0)
SHAPES = ("circle", "square", "octagon")

# target identity colors (well separated from each other and from
# distractor grays) — a and b are ORDERED: label = direction b -> a
TARGET_A_COLOR = (222, 60, 52)    # red
TARGET_B_COLOR = (48, 98, 214)    # blue

# ------------------------------------------------------------------ #
# Variants (DEV investigation 2026-08-19)
# ------------------------------------------------------------------ #
# nobox_v1             : a is ALWAYS red, b is ALWAYS blue. We then
#   discovered a global shortcut: the model can read "red-mass centroid
#   vs blue-mass centroid" from pooled tokens and recover label without
#   ever localizing the pair (attention never concentrates on the pair
#   cells). Probes: linear 0.10 / MLP 0.11 cell-pair recall; attention
#   pair_in_top4_pct 0.0-2.0.
#
# nobox_v2_colorflip   : removes the red-vs-blue mass/centroid shortcut.
#   Identity moves from color to SHAPE (a = circle ALWAYS, b = square
#   ALWAYS) and the a/b color assignment is randomized per scene: half
#   the scenes are (a=red, b=blue), half are (a=blue, b=red), sampled
#   independently of geometry. Then:
#     * red-vs-blue mass centroid direction is UNcorrelated with the
#       label across the dataset (red is "a" only 50% of scenes) -> the
#       color centroid shortcut is unlearnable by construction;
#     * the image still uniquely determines the label (the one red
#       object is the circle in some scenes and the square in others;
#       shape disambiguates a vs b) so the task stays well-posed and
#       gate tests still pass;
#     * solving now REQUIRES localizing the two colored blobs and
#       reading shape-fused identity — the behavior we want to probe.
#   Warning (disclosed, not hidden): "red circle centroid vs blue
#   square centroid" is still a global statistic; it is harder to pool
#   than pure color (needs shape classification per mass token) but
#   EXISTS. The dev runs below measure whether the baseline stays
#   non-saturated after convergence WITH these residual leakages.
VARIANT_V1 = "nobox_v1"
VARIANT_V2 = "nobox_v2_colorflip"

# distractor palette: muted grays, disjoint from target colors
DISTRACTOR_PALETTE = [
    (145, 140, 135),  # warm gray
    (140, 145, 150),  # cool gray
    (150, 145, 140),  # brownish gray
]


@dataclass
class ObjectNB:
    obj_id: str
    x: float
    y: float
    shape: str
    size: float
    color: tuple


@dataclass
class SceneNB:
    scene_id: str
    target_a: ObjectNB
    target_b: ObjectNB
    distractors: list
    label: str
    delta: tuple

    def objects(self):
        return [self.target_a, self.target_b] + list(self.distractors)


def _gen_distractor_appearance(rng: random.Random,
                               n_colors: int = 3) -> tuple:
    shape = rng.choice(SHAPES)
    color = rng.choice(DISTRACTOR_PALETTE[:n_colors])
    size = round(rng.uniform(2.0, 4.0), 1)
    return (shape, color, size)


def make_scene(scene_id: str, rng: random.Random, label: str,
               target_size: tuple = (3.0, 5.0),
               n_distractor_range: tuple = (12, 20),
               variant: str = VARIANT_V1) -> SceneNB:
    """Scene with visually identifiable target pair.

    Geometry matches the boxed v2/v4 generator: a and b sit opposite
    around a random center at the label direction; 12-20 gray
    distractors clutter the canvas. Label = direction of b -> a.

    variant selects the identity encoding (see VARIANT_V1/VARIANT_V2
    docs at the top of this module).
    """
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
        return make_scene(scene_id, rng, label, target_size,
                          n_distractor_range, variant)

    if variant == VARIANT_V2:
        # Identity by SHAPE: a is always the circle, b is always the
        # square. Color is decoupled from identity: 50/50 per scene
        # whether (a=red, b=blue) or (a=blue, b=red). Draws the rng
        # state in the same order that v1 would have used for shapes,
        # so the geometry RNG stream is shared across variants.
        flip = rng.choice((False, True))
        if flip:
            a_color, b_color = TARGET_B_COLOR, TARGET_A_COLOR
        else:
            a_color, b_color = TARGET_A_COLOR, TARGET_B_COLOR
        a = ObjectNB("a", ax, ay, "circle",
                     round(rng.uniform(*target_size), 1), a_color)
        b = ObjectNB("b", bx, by, "square",
                     round(rng.uniform(*target_size), 1), b_color)
    else:
        a = ObjectNB("a", ax, ay, rng.choice(SHAPES),
                     round(rng.uniform(*target_size), 1), TARGET_A_COLOR)
        b = ObjectNB("b", bx, by, rng.choice(SHAPES),
                     round(rng.uniform(*target_size), 1), TARGET_B_COLOR)
    objs = [a, b]

    lo, hi = n_distractor_range
    n_d = rng.randint(lo, hi)
    for i in range(n_d):
        for _try in range(600):
            x = rng.uniform(-edge, edge)
            y = rng.uniform(-edge, edge)
            if all(math.hypot(x - o.x, y - o.y) >= MIN_DIST
                   for o in objs):
                sh, co, si = _gen_distractor_appearance(rng)
                d = ObjectNB(f"d{i}", x, y, sh, si, co)
                objs.append(d)
                break
    return SceneNB(scene_id, a, b, objs[2:], lab,
                   (round(dx, 3), round(dy, 3)))


def generate_pack(num_scenes: int, seed: int,
                  labels: Optional[list] = None,
                  id_offset: int = 0,
                  target_size: tuple = (3.0, 5.0),
                  n_distractor_range: tuple = (12, 20),
                  variant: str = VARIANT_V1) -> list:
    rng = random.Random(seed)
    from equiorient.algebra.label_action import LABELS
    if labels is None:
        labels = LABELS
    out = []
    for i in range(num_scenes):
        lab = labels[i % len(labels)]
        out.append(make_scene(f"scene_{i + id_offset:06d}", rng, lab,
                              target_size, n_distractor_range, variant))
    return out