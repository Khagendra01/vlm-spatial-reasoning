"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPRECATED / DRIFTED (protocol correction 2026-08-11, SPATIAL_REASONING_
DECISION_LOG "battery drift" entry). Code audit found this battery diverges
from the frozen Paper-2 protocol: the wrong-image 2px substitution is
mislabeled "with_sample", the shuffle mapping was re-hashed (no longer the
frozen protocol permutation), and the heavy battery (with_sample,
with_shuffle) is not part of the frozen protocol. Retained VERBATIM as audit
history only. The corrected seed-campaign battery = the legacy Tier-A/B/C
drivers via scripts/grounding/run_seed_battery.py. Do NOT use this module
for any reportable campaign result.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Frozen battery row builders for the seed campaign (configs/seed_campaign/).

Conditions (frozen 2026-08-11, user-approved): normal, with_sample (2px),
with_shuffle, relcomp (strict complement pairs, semantic distance 0 < 0.3),
facing, hflip, hflip_inv.

Provenance of frozen constants:
- STRICT_COMPLEMENT_PAIRS: src/grounding/semantic.py (Tier-B relcomp flip law)
- HARDNEG_RELATION_PAIRS: scripts/build_hardneg_manifest.py
- FAMILY_MAP: src/training/build_train_sets.py RELATION_FAMILIES (canonical)
- 392px cap: src/grounding/config.py MAX_LONG_SIDE (docs/TECHNIQUES.md s4)
- SHUFFLE_SEED: src/grounding/config.py (frozen; permutation is a constant)

Rows are built ONCE and persisted to results/seed_campaign/rows/{cond}.jsonl;
all adapters are evaluated on the identical frozen row sets (sampling policy:
constant, without replacement).
"""

import json
import random
import shutil
from pathlib import Path

from PIL import Image

from datasets import load_dataset


def _load_test_rows() -> list:
    """VSR test rows with the frozen `vsr_test:<index>` id scheme.

    Authoritative source: results/grounding/protocol/vsr_test_ids.json
    (frozen at protocol freeze time: 2195 examples, dataset-index order,
    id scheme `vsr_test:<dataset_index>`). The HF hub copy of the test
    split has NO `id` column (verified 2026-08-11), so the frozen file is
    required for row identity; the hub dataset is used only as a
    cross-check (count + spot equality) and never for row content.
    """
    frozen = PROTOCOL_DIR / "vsr_test_ids.json"
    if not frozen.exists():
        raise FileNotFoundError(
            f"frozen id manifest missing: {frozen} "
            "(commit includes results/grounding/protocol/vsr_test_ids.json)")
    manifest = json.load(open(frozen))["examples"]
    if len(manifest) != 2195:
        raise ValueError(f"frozen id manifest has {len(manifest)} examples, expected 2195")
    rows = [{
        "id": m["example_id"],
        "image": m.get("image_link", ""),
        "statement": m["statement"],
        "label": bool(m["label"]),
        "relation": m.get("relation", ""),
    } for m in sorted(manifest, key=lambda m: m["dataset_index"])]
    # cross-check against the hub dataset (positional alignment by index)
    try:
        ds = load_dataset("cambridgeltl/vsr_random", split="test")
        if len(ds) != len(rows):
            raise ValueError(
                f"hub test split count {len(ds)} != frozen manifest {len(rows)}")
        for i in (0, 1, len(rows) // 2, len(rows) - 1):
            hub = ds[i]
            frz = rows[i]
            if (frz["statement"] != hub.get("caption", "")
                    or bool(frz["label"]) != bool(hub.get("label", False))
                    or frz["image"] != hub.get("image_link", "")):
                raise ValueError(
                    f"frozen manifest row {i} diverges from hub dataset: "
                    f"{frz} vs {hub}")
    except Exception as e:
        raise RuntimeError(f"hub cross-check failed: {e}") from e
    return rows

CAMPAIGN_ID = "seed_campaign_r1"
ROWS_DIR = Path("results/seed_campaign/rows")
PROTOCOL_DIR = Path("results/grounding/protocol")

MAX_LONG_SIDE = 392
SAMPLE_DELTA_PX = 2
SHUFFLE_SEED = 20260810

STRICT_COMPLEMENT_PAIRS = {
    "left of": "right of",
    "right of": "left of",
    "at the left side of": "at the right side of",
    "at the right side of": "at the left side of",
    "above": "below",
    "below": "above",
    "in front of": "behind",
    "behind": "in front of",
}

HARDNEG_RELATION_PAIRS = [
    ("facing", "facing away from"),
    ("parallel to", "perpendicular to"),
]

FAMILY_MAP = {
    "horizontal": ["left of", "right of", "at the left side of", "at the right side of",
                   "at the side of", "beside", "next to", "alongside", "across from"],
    "vertical": ["above", "below", "over", "under", "beneath", "on top of"],
    "depth": ["in front of", "behind", "at the back of", "ahead of"],
    "orientation": ["facing", "facing away from", "parallel to", "perpendicular to"],
    "containment": ["in", "inside", "contains", "within", "enclosed by"],
    "proximity": ["near", "far from", "far away from", "close to", "away from"],
    "topology_contact": ["touching", "on", "at", "at the edge of", "against",
                         "attached to", "connected to", "detached from"],
    "compositional": ["part of", "has as a part", "consists of", "surrounding",
                      "in the middle of", "among"],
}
REL_FAMILY = {r: f for f, rels in FAMILY_MAP.items() for r in rels}


def _rows_path(condition: str) -> Path:
    return ROWS_DIR / f"{condition}.jsonl"


def _eligible_ids(transform_file: str, transform_name: str) -> list:
    """Extract the frozen eligible-ID list (handles dict wrappers)."""
    d = json.load(open(PROTOCOL_DIR / transform_file))["transforms"][transform_name]
    if isinstance(d, dict):
        # canonical protocol shape: {"entries": {id: meta, ...} | [id, ...],
        #                            "law": ..., "n_eligible": N}
        if "entries" in d:
            e = d["entries"]
            if isinstance(e, dict):
                return list(e.keys())
            if isinstance(e, list):
                return e
        vals = {k: v for k, v in d.items() if isinstance(v, list)}
        if vals:
            return vals[max(vals, key=lambda k: len(vals[k]))]
        raise ValueError(f"no id list in {transform_file}:{transform_name}: {list(d)}")
    return d


def _swap_relation(statement: str, fr: str, to: str) -> str:
    return statement.replace(f" {fr} ", f" {to} ")


def _record(row: dict, condition: str, **extra) -> dict:
    out = {"id": row["id"], "statement": row["statement"], "label": bool(row["label"]),
           "relation": row.get("relation", ""), "family": REL_FAMILY.get(row.get("relation", ""), ""),
           "image": row["image"], "condition": condition, "source_id": str(row.get("id", row.get("source_id", "")))}
    out.update(extra)
    return out


def build_rows(condition: str, force: bool = False) -> list:
    p = _rows_path(condition)
    if p.exists() and not force:
        return [json.loads(l) for l in open(p)]
    if condition == "normal":
        rows = [_record(r, condition) for r in _load_test_rows()]
    elif condition == "with_sample":
        rows = build_rows("normal")
        for r in rows:
            r["condition"] = "with_sample"
            r["image_variant"] = "resize_2px_after_392"
    elif condition == "with_shuffle":
        rows = build_rows("normal")
        for r in rows:
            r["condition"] = "with_shuffle"
        ids = [r["id"] for r in rows]
        rng = random.Random(SHUFFLE_SEED)
        perm = list(range(len(rows)))
        rng.shuffle(perm)
        rows = [rows[i] for i in perm]
        ROWS_DIR.mkdir(parents=True, exist_ok=True)
        json.dump({"seed": SHUFFLE_SEED, "n": len(rows), "permutation": perm,
                   "note": "constant permutation; identical for all adapters"},
                  open(ROWS_DIR / "shuffle_mapping.json", "w"), indent=2)
    elif condition == "facing":
        ids = set(_eligible_ids("facing_eligible_ids.json", "facingcomp"))
        rows = [r for r in _load_test_rows() if str(r["id"]) in ids]
        rows = [_record(r, condition) for r in rows]
    elif condition == "relcomp":
        ids = set(_eligible_ids("semantic_eligible_ids.json", "relcomp"))
        base = {str(r["id"]): r for r in _load_test_rows()}
        rows = []
        for rid in sorted(ids):
            r = base.get(str(rid))
            if r is None:
                continue
            rel = r["relation"]
            comp = STRICT_COMPLEMENT_PAIRS.get(rel)
            if comp is None:
                continue
            stmt = _swap_relation(r["statement"], rel, comp)
            rows.append(_record(dict(r, statement=stmt, relation=comp,
                                     label=not r["label"]), condition))
    elif condition in ("hflip", "hflip_inv"):
        ids = set(_eligible_ids("facing_eligible_ids.json", "facingcomp"))
        base = {str(r["id"]): r for r in _load_test_rows()}
        rows = []
        for rid in sorted(ids):
            r = base.get(str(rid))
            if r is None:
                continue
            for a, b in HARDNEG_RELATION_PAIRS:
                if r["relation"] == a or r["relation"] == b:
                    other = b if r["relation"] == a else a
                    stmt = _swap_relation(r["statement"], r["relation"], other)
                    target = not r["label"] if condition == "hflip" else r["label"]
                    rows.append(_record(dict(r, statement=stmt, relation=other,
                                             label=target), condition,
                                        source_statement=r["statement"],
                                        original_label=r["label"]))
                    break
    else:
        raise ValueError(f"unknown condition {condition}")
    ROWS_DIR.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return rows


def row_counts() -> dict:
    return {c: len(build_rows(c)) for c in
            ["normal", "with_sample", "with_shuffle", "relcomp", "facing", "hflip", "hflip_inv"]}


def sample_image(row: dict):
    """Loaded + 392px-capped image; 2px resize for with_sample (frozen contract)."""
    from src.grounding import images as gimages
    img = gimages.load_cached_image(row["image"])
    if img is None:
        return None
    img = gimages.preprocess_for_vlm(img, MAX_LONG_SIDE)
    if row.get("image_variant") == "resize_2px_after_392":
        w, h = img.size
        scale = max(1, max(w, h) - SAMPLE_DELTA_PX) / max(w, h)
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BILINEAR)
    return img