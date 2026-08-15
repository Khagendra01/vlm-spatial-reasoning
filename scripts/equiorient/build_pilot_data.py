"""EquiOrient Phase-1 pilot — frozen data builder (CPU, pre-GPU).

Generates the FROZEN pilot dataset from the Gate-2 generator:
17 scenes (10 train / 4 val / 3 holdout) x 4 transforms (I, H, V, V o H),
each with object boxes and per-pair relation ground truth, serialized as a
manifest consumed by pilot_harness.py. Deterministic (seed 20260814).

Output: results/equiorient/pilot_data/
  scene_XXXX__<transform>.png   (320x320 render, object ids drawn)
  manifest.json                 (per-example: boxes, relations, labels)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

WT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WT))

from src.equiorient import Relation, Transform  # noqa: E402
from src.equiorient.datasets import generate_pack  # noqa: E402

OUT = WT / "results" / "equiorient" / "pilot_data"
OUT.mkdir(parents=True, exist_ok=True)

scenes = generate_pack(num_scenes=17, seed=20260814)
transforms = [Transform.I, Transform.H, Transform.V, Transform.VH]

examples = []
for scene in scenes:
    for t in transforms:
        tsc = scene.transformed(t)
        img = tsc.render()
        d = ImageDraw.Draw(img)
        for o in tsc.objects:
            d.text((o.cx - 8, o.cy - o.size - 14), o.obj_id, fill=(20, 20, 20))
        fname = f"{scene.scene_id}__{t.value}.png"
        img.save(OUT / fname)
        boxes = {o.obj_id: [o.cx, o.cy, o.size] for o in tsc.objects}
        pair_rels = {}
        for a in tsc.objects:
            for b in tsc.objects:
                if a is b:
                    continue
                key = f"{a.obj_id}>{b.obj_id}"
                pair_rels[key] = {r.value: tsc.relation(a, b, r)
                                  for r in Relation}
        examples.append({
            "scene_id": scene.scene_id,
            "transform": t.value,
            "png": fname,
            "boxes": boxes,
            "pair_relations": pair_rels,
        })

manifest = {
    "num_scenes": len(scenes),
    "transforms": [t.value for t in transforms],
    "canvas": [320, 320],
    "scene_split": {
        "train": [s.scene_id for s in scenes[:10]],
        "validation": [s.scene_id for s in scenes[10:14]],
        "holdout": [s.scene_id for s in scenes[14:17]],
    },
    "relations": [r.value for r in Relation],
    "examples": examples,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                   encoding="utf-8")
print(f"wrote {len(examples)} examples to {OUT}")
print("train:", len(manifest["scene_split"]["train"]),
      "val:", len(manifest["scene_split"]["validation"]),
      "holdout:", len(manifest["scene_split"]["holdout"]))
