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


def build(out_dir: Path, seed: int = 20260819,
          n_dev: int = 512, n_train: int = 2048,
          n_val: int = 512, n_test: int = 1024,
          target_size: tuple = (3.0, 5.0),
          n_distractor_range: tuple = (12, 20),
          noise_amp: int = 12,
          bg_color: tuple = (155, 152, 148)) -> dict:
    """Generate the no-box dataset + manifests. Deterministic."""
    import equiorient.data.renderer as R
    R.BG = bg_color
    R.SIZE = int(2 * R.HALF)
    from PIL import Image
    Image.new("RGB", (R.SIZE, R.SIZE), R.BG)  # sanity

    out_dir.mkdir(parents=True, exist_ok=True)
    dev = generate_pack(n_dev, seed, id_offset=0,
                        target_size=target_size,
                        n_distractor_range=n_distractor_range)
    train_pool = generate_pack(n_train, seed + 1, id_offset=n_dev,
                               target_size=target_size,
                               n_distractor_range=n_distractor_range)
    val = generate_pack(n_val, seed + 2,
                        id_offset=n_dev + n_train,
                        target_size=target_size,
                        n_distractor_range=n_distractor_range)
    test = generate_pack(n_test, seed + 3,
                         id_offset=n_dev + n_train + n_val,
                         target_size=target_size,
                         n_distractor_range=n_distractor_range)

    ids = {s.scene_id: split for split, pack in
           (("dev", dev), ("train", train_pool), ("val", val),
            ("test", test))
           for s in pack}
    assert len(ids) == n_dev + n_train + n_val + n_test, "scene id collision"

    manifest = {
        "seed": seed,
        "generator_variant": "nobox_v1",
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
    }


def _transform_scene(g_name, scene):
    from equiorient.data.transforms import transform_scene
    return transform_scene(g_name, scene)