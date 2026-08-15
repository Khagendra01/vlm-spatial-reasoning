"""Phase-2 geometry transforms in math coordinates + pixel mapping.

Math coords: x rightward, y upward, centered at (0,0), half-extent HALF.
Pixel mapping: px = round(x + HALF), py = round(HALF - y).
Group action: g : (x, y) -> G_g (x, y) with G from algebra.d4.

Pixel-level consequences (used by the renderer tests):
  H  : (px, py) -> (2*HALF - px, py)            mirror about vertical axis
  R  : (px, py) -> (py, 2*HALF - px)            rotate CW 90 deg in pixels
  R2 : (px, py) -> (2*HALF - px, 2*HALF - py)   180 deg
  R3 : (px, py) -> (2*HALF - py, px)            rotate CCW 90 deg in pixels
"""

from __future__ import annotations

from equiorient.algebra.d4 import ELEMENTS, mat_apply


def apply_to_xy(g_name: str, x: float, y: float) -> tuple:
    nx, ny = mat_apply(ELEMENTS[g_name].matrix, (x, y))
    return float(nx), float(ny)


def to_pixel(x: float, y: float, half: float = 96.0) -> tuple:
    return int(round(x + half)), int(round(half - y))


def transform_object(g_name: str, obj) -> "Object2":
    nx, ny = apply_to_xy(g_name, obj.x, obj.y)
    from equiorient.data.scene_generator_v2 import Object2
    return Object2(obj.obj_id, nx, ny, obj.shape, obj.size, obj.color)


def transform_scene(g_name: str, scene) -> "Scene2":
    from equiorient.data.scene_generator_v2 import Scene2
    return Scene2(
        scene.scene_id,
        transform_object(g_name, scene.target_a),
        transform_object(g_name, scene.target_b),
        [transform_object(g_name, d) for d in scene.distractors],
        scene.label,
        scene.delta,
    )
