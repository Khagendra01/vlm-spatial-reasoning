"""NO-BOX manifests builder (dev-calibrated difficulty).

Mirrors equiorient.data.manifests.build but uses the no-box scene
generator (scene_generator_nobox) whose target pair is identifiable from
the pixels alone (red a / blue b, gray distractors).

Tunable difficulty knobs (DEV phase only — freeze before confirmatory):
  target_size          : (min, max) target radius in px (bigger = easier)
  n_distractor_range   : (min, max) gray distractors per scene
  noise_amp            : per-pixel noise amplitude (0 = none)
  bg_color             : background RGB (closer to objects = harder)

Everything else (split-by-scene, sparse exposure I + one generator,
SHA-256-seeded per-image noise, D4 label action) is identical to the
boxed Phase-2 builder.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from equiorient.algebra.d4 import ELEMENTS, GENERATORS
from equiorient.data.renderer import add_noise, render
from equiorient.data.scene_generator_nobox import generate_pack


def _sha256(paths: list) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()


def _mass_centroid_accuracy(pack: list, attr, values) -> float:
    """How often does "direction from centroid(A) to centroid(B)" predict
    the label, where centroid(X) is the area-weighted mean position of
    objects whose attr in values?

    values = (set_for_a_side, set_for_b_side) ordered so the predicted
    direction is (centroid(a_side) - centroid(b_side)), matching the
    labell semantics (direction b -> a).
    """
    from equiorient.algebra.label_action import direction_of
    n = 0
    hits = 0
    for s in pack:
        va, vb = values
        na = [o for o in s.objects() if getattr(o, attr, None) in va]
        nb = [o for o in s.objects() if getattr(o, attr, None) in vb]
        if not na or not nb:
            continue
        def cen(objs):
            w = sum(o.size ** 2 for o in objs)
            return ((sum(o.x * o.size ** 2 for o in objs) / w,
                     sum(o.y * o.size ** 2 for o in objs) / w))
        ax, ay = cen(na)
        bx, by = cen(nb)
        pred = direction_of(ax - bx, ay - by)
        n += 1
        hits += int(pred == s.label)
    return round(hits / max(n, 1), 4)


def _variant_diagnostics(pack: list, variant: str) -> dict:
    """Centroid-shortcut diagnostics over a pack, per variant.

    * color: direction from blue-mass centroid to red-mass centroid.
      nobox_v1 => ~1.0 (THE discovered shortcut). nobox_v2_colorflip
      => ~0.5 (color is decorrelated from identity by construction).
    * shape: direction from square-mass centroid to circle-mass centroid.
      In nobox_v1 shapes are random per scene so this is ~chance(0.125);
      in nobox_v2_colorflip a is always circle / b always square so it
      may remain ~1.0 — an honest disclosure of the residual shortcut
      that shape-based identity still permits.
    """
    red = {(222, 60, 52)}
    blue = {(48, 98, 214)}
    circle = {"circle"}
    square = {"square"}
    return {
        # color: a-side is always red in v1 (blue->red == label). In v2
        # color is random per scene -> ~0.5 (shortcut removed).
        "color_blue_to_red": _mass_centroid_accuracy(
            pack, "color", (red, blue)),
        # shape: a-side is "circle" in v2 (a is always the circle).
        # In v1 shapes are random per scene -> ~chance (residual absent).
        "shape_circle_to_square": _mass_centroid_accuracy(
            pack, "shape", (circle, square)),
    }


def build(out_dir: Path, seed: int = 20260819,
          n_dev: int = 512, n_train: int = 2048,
          n_val: int = 512, n_test: int = 1024,
          target_size: tuple = (3.0, 5.0),
          n_distractor_range: tuple = (12, 20),
          noise_amp: int = 12,
          bg_color: tuple = (155, 152, 148),
          variant: str = "nobox_v1") -> dict:
    """Generate the no-box dataset + manifests. Deterministic."""
    import equiorient.data.renderer as R
    R.BG = bg_color
    R.SIZE = int(2 * R.HALF)
    from PIL import Image
    Image.new("RGB", (R.SIZE, R.SIZE), R.BG)  # sanity

    out_dir.mkdir(parents=True, exist_ok=True)
    dev = generate_pack(n_dev, seed, id_offset=0,
                        target_size=target_size,
                        n_distractor_range=n_distractor_range,
                        variant=variant)
    train_pool = generate_pack(n_train, seed + 1, id_offset=n_dev,
                               target_size=target_size,
                               n_distractor_range=n_distractor_range,
                               variant=variant)
    val = generate_pack(n_val, seed + 2,
                        id_offset=n_dev + n_train,
                        target_size=target_size,
                        n_distractor_range=n_distractor_range,
                        variant=variant)
    test = generate_pack(n_test, seed + 3,
                         id_offset=n_dev + n_train + n_val,
                         target_size=target_size,
                         n_distractor_range=n_distractor_range,
                         variant=variant)

    ids = {s.scene_id: split for split, pack in
           (("dev", dev), ("train", train_pool), ("val", val),
            ("test", test))
           for s in pack}
    assert len(ids) == n_dev + n_train + n_val + n_test, "scene id collision"

    manifest = {
        "seed": seed,
        "generator_variant": variant,
        "difficulty": {"target_size": list(target_size),
                       "n_distractor_range": list(n_distractor_range),
                       "noise_amp": noise_amp,
                       "bg_color": list(bg_color)},
        "splits": {"dev": n_dev, "train_pool": n_train,
                   "val": n_val, "test": n_test},
        "generators": list(GENERATORS),
        "unseen": ["R2", "R3", "RH", "R2H", "R3H"],
        "canvas": [2 * 96, 2 * 96],
        "examples": [],
    }
    train_used = 0
    for split, pack in (("dev", dev), ("train", train_pool),
                        ("val", val), ("test", test)):
        for s in pack:
            if split == "train":
                g = GENERATORS[train_used % 2]
                train_used += 1
                gs = ("I", g)
            else:
                gs = tuple(ELEMENTS.keys())
            for g in gs:
                ts = _transform_scene(g, s)
                img = render(ts)
                digest = hashlib.sha256(
                    f"{s.scene_id}|{g}".encode("utf-8")).hexdigest()
                noise_seed = int(digest[:8], 16)
                img = add_noise(img, noise_seed, amp=noise_amp)
                fname = f"{s.scene_id}__{g}.png"
                img.save(out_dir / fname)
                manifest["examples"].append({
                    "scene_id": s.scene_id,
                    "split": split,
                    "transform": g,
                    "png": fname,
                    "label": ts.label,
                    "delta": ts.delta,
                    "boxes": {o.obj_id: [o.x, o.y, o.size]
                              for o in ts.objects()},
                })
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return {
        "manifest": str(out_dir / "manifest.json"),
        "train_scene_manifest_sha256": _sha256(
            [out_dir / "manifest.json"]),
        "n_examples": len(manifest["examples"]),
        "centroid_shortcuts": _variant_diagnostics(
            train_pool, variant),   # color~1.0 = shortcut present in v1
    }


def _transform_scene(g_name, scene):
    from equiorient.data.transforms import transform_scene
    return transform_scene(g_name, scene)