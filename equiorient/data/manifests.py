"""Phase-2 manifests: scene-split + sparse transform exposure.

Splitting happens by SCENE ID BEFORE any transform (no leakage). Each
training scene contributes IDENTITY + exactly ONE generator transform
(H or R), balanced 50/50 -- no training scene gets every transformation.
Dev scenes are never used in training. Test/val scenes contribute all 8
D4 views (for evaluation of the unseen elements).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from equiorient.algebra.d4 import ELEMENTS, GENERATORS
from equiorient.data.renderer import add_noise, render
from equiorient.data.scene_generator_v2 import generate_pack


def _sha256(paths: list) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()


def build(out_dir: Path, seed: int = 20260815,
          n_dev: int = 512, n_train: int = 2048,
          n_val: int = 512, n_test: int = 1024) -> dict:
    """Generate the full Phase-2 dataset + manifests. Deterministic."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dev = generate_pack(n_dev, seed, id_offset=0)
    train_pool = generate_pack(n_train, seed + 1, id_offset=n_dev)
    val = generate_pack(n_val, seed + 2, id_offset=n_dev + n_train)
    test = generate_pack(n_test, seed + 3,
                         id_offset=n_dev + n_train + n_val)

    # unique scene ids across splits
    ids = {s.scene_id: split for split, pack in
           (("dev", dev), ("train", train_pool), ("val", val),
            ("test", test))
           for s in pack}
    assert len(ids) == n_dev + n_train + n_val + n_test, "scene id collision"

    manifest = {
        "seed": seed,
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
                # sparse exposure: identity + exactly one generator
                g = GENERATORS[train_used % 2]
                train_used += 1
                gs = ("I", g)
            else:
                gs = tuple(ELEMENTS.keys())
            for g in gs:
                ts = _transform_scene(g, s)
                img = render(ts)
                # deterministic per-image noise (seeded from scene+view)
                img = add_noise(img, abs(hash((s.scene_id, g))) & 0xFFFFFFFF)
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
    # scene-manifest hashes for the freeze ledger
    pngs = sorted(out_dir.glob("*.png"))
    return {
        "manifest": str(out_dir / "manifest.json"),
        "train_scene_manifest_sha256": _sha256(
            [out_dir / "manifest.json"]),
        "n_examples": len(manifest["examples"]),
    }


def _transform_scene(g_name, scene):
    from equiorient.data.transforms import transform_scene
    return transform_scene(g_name, scene)
