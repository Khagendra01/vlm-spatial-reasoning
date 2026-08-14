"""Generate the Gate-2 human-inspection pack for EquiOrient.

Produces side-by-side original|transformed PNG pairs (annotated with object
ids and the expected relation law) plus a machine-readable manifest CSV/JSON,
stratified by relation x transform, for the protocol-required 50-pair human
spot-check (execution guide Gate 1 / Amendment A6).
"""
import csv
import json
import sys
from pathlib import Path

from PIL import Image

WT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WT))

from src.equiorient import Relation, Transform, expected_after  # noqa: E402
from src.equiorient.datasets import generate_pack  # noqa: E402

OUT = WT / "results" / "equiorient" / "human_inspection"
OUT.mkdir(parents=True, exist_ok=True)

NUM_SCENES = 17
TRANSFORMS = [Transform.H, Transform.V, Transform.VH]

scenes = generate_pack(num_scenes=NUM_SCENES, seed=20260814)
rows = []
png_paths = []

for scene in scenes:
    img = scene.render()
    for t in TRANSFORMS:
        tsc = scene.transformed(t)
        timg = tsc.render()
        # side-by-side with captions
        pad = 12
        label_h = 26
        W = img.width * 2 + pad * 3
        H = img.height + label_h * 2 + pad * 2
        canvas = Image.new("RGB", (W, H), (235, 235, 235))
        from PIL import ImageDraw
        d = ImageDraw.Draw(canvas)
        d.text((pad, 4), f"{scene.scene_id} | {t.value} | "
               f"expected_after per algebra (rel -> rel)", fill=(0, 0, 0))
        canvas.paste(scene.annotate(img.copy()), (pad, label_h))
        canvas.paste(tsc.annotate(timg.copy()),
                     (img.width + 2 * pad, label_h))
        d.text((pad, label_h * 2 + img.height + 4),
               "LEFT: original   RIGHT: transformed (ids on both)",
               fill=(60, 60, 60))
        fname = f"{scene.scene_id}__{t.value}.png"
        canvas.save(OUT / fname)
        png_paths.append(fname)

        # manifest rows: one per (scene, pair, relation, transform)
        for a in scene.objects:
            for b in scene.objects:
                if a is b:
                    continue
                for r in Relation:
                    before = scene.relation(a, b, r)
                    ta = {o.obj_id: o for o in tsc.objects}[a.obj_id]
                    tb = {o.obj_id: o for o in tsc.objects}[b.obj_id]
                    after = tsc.relation(ta, tb, r)
                    expect = expected_after(r, t)
                    rows.append({
                        "scene_id": scene.scene_id,
                        "transform": t.value,
                        "pair": f"{a.obj_id}>{b.obj_id}",
                        "relation": r.value,
                        "before": before,
                        "after": after,
                        "expected_after": expect.value,
                        "law_ok": (after == before) == (expect == r),
                        "png": fname,
                    })

# manifest
with open(OUT / "manifest.json", "w", encoding="utf-8") as f:
    json.dump({"num_scenes": NUM_SCENES,
               "transforms": [t.value for t in TRANSFORMS],
               "num_rows": len(rows),
               "rows": rows}, f, indent=1)
with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# stratification report: how many rows per (relation, transform)
from collections import Counter  # noqa: E402
strat = Counter((r["relation"], r["transform"]) for r in rows
                if r["law_ok"])
print(f"PNG pairs: {len(png_paths)}  manifest rows: {len(rows)}")
print(f"all law_ok: {all(r['law_ok'] for r in rows)}")
print("stratification (relation x transform, law-ok rows):")
for (rel, tr), n in sorted(strat.items()):
    print(f"  {rel:15s} x {tr:6s}: {n}")
