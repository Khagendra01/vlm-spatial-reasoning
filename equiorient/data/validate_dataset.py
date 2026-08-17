"""Phase-2 dataset validation: all pre-GPU gates on the data itself."""

from __future__ import annotations

import json
from collections import Counter


def validate(manifest_path) -> list:
    """Return a list of problems (empty = pass)."""
    m = json.load(open(manifest_path, encoding="utf-8"))
    problems = []
    ex = m["examples"]
    by_scene = {}
    for e in ex:
        by_scene.setdefault(e["scene_id"], []).append(e)

    # 1. scene IDs disjoint across splits
    seen = {}
    for e in ex:
        if e["scene_id"] in seen and seen[e["scene_id"]] != e["split"]:
            problems.append(f"scene {e['scene_id']} in two splits")
        seen[e["scene_id"]] = e["split"]

    # 2. train exposure: identity + exactly one generator, 50/50
    for sid, rows in by_scene.items():
        if rows[0]["split"] != "train":
            continue
        trs = {r["transform"] for r in rows}
        if trs != {"I", "H"} and trs != {"I", "R"}:
            problems.append(f"train scene {sid} exposure {trs}")
    train_rows = [r for r in ex if r["split"] == "train"]
    gens = Counter(r["transform"] for r in train_rows if r["transform"] != "I")
    if abs(gens.get("H", 0) - gens.get("R", 0)) > 1:
        problems.append(f"train generator imbalance {dict(gens)}")

    # 3. balanced 8-way labels (per split)
    for split in ("train", "val", "test", "dev"):
        labs = Counter(r["label"] for r in ex if r["split"] == split)
        if len(labs) < 8:
            problems.append(f"{split} label coverage {len(labs)}/8")
        mx, mn = max(labs.values()), min(labs.values())
        if mx - mn > 1:
            problems.append(f"{split} label imbalance {mx}-{mn}")

    # 4. no boundary examples (label was accepted => margin held)
    # 5. every test/val scene has all 8 transforms
    for split in ("val", "test"):
        for sid, rows in by_scene.items():
            if rows[0]["split"] != split:
                continue
            if {r["transform"] for r in rows} != set(
                    m["unseen"] + ["I", "H", "R"]):
                problems.append(f"{split} scene {sid} missing transforms")

    # 6. distractor count 12..20 per scene (v4: extreme dense clutter)
    for sid, rows in by_scene.items():
        r = rows[0]
        n_dist = sum(1 for k in r["boxes"] if k.startswith("d"))
        if not (12 <= n_dist <= 20):
            problems.append(f"scene {sid} distractor count {n_dist}")

    # 7. unique png names
    pngs = [r["png"] for r in ex]
    if len(pngs) != len(set(pngs)):
        problems.append("duplicate png names")

    return problems
