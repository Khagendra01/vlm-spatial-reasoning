"""Deterministic derangement for the shuffled-image condition (Tier A).

Frozen seed 20260810 (configs/grounding_protocol.yaml). Construction:
1. rng = random.Random(seed); shuffle the eligible ID list once.
2. Map each element to the NEXT element in the shuffled order (cycle).
This is guaranteed to be a derangement (no self-pairs) for n >= 2, is a
bijection, and depends only on the seed -> fully deterministic across
platforms and Python versions (random.Random with a fixed seed is stable).

The mapping is saved once and hashed; every compared model condition reads
the SAME mapping file. No regeneration after results.
"""

import json
import random

from . import config


def build_derangement(ids: list, seed: int) -> dict:
    """Deterministic derangement of `ids` (cycle construction)."""
    if len(ids) < 2:
        raise ValueError("derangement requires at least 2 elements")
    if len(set(ids)) != len(ids):
        raise ValueError("ids must be unique")
    rng = random.Random(seed)
    order = list(ids)
    rng.shuffle(order)
    mapping = {order[i]: order[(i + 1) % len(order)] for i in range(len(order))}
    _validate_derangement(ids, mapping)
    return mapping


def _validate_derangement(ids: list, mapping: dict) -> None:
    if set(mapping.keys()) != set(ids):
        raise ValueError("mapping keys must equal the ID set")
    if set(mapping.values()) != set(ids):
        raise ValueError("mapping values must be a permutation of the ID set")
    for eid in ids:
        if mapping[eid] == eid:
            raise ValueError(f"self-pair found for {eid}: mapping violates derangement")


def freeze_shuffle_mapping(payload_ids: dict) -> dict:
    """Build and write the frozen shuffle_mapping.json from the IDs payload."""
    ids = [r["example_id"] for r in payload_ids["examples"] if r["image_available"]]
    mapping = build_derangement(ids, config.SHUFFLE_SEED)
    doc = {
        "protocol_version": "v0.1",
        "algorithm": "cycle derangement: shuffle eligible IDs with random.Random(seed), map each to next in cycle",
        "seed": config.SHUFFLE_SEED,
        "forbid_self_pair": True,
        "source_split": "test",
        "same_mapping_all_models": True,
        "count_eligible": len(ids),
        "mapping": mapping,
    }
    config.PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SHUFFLE_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    doc["file_sha256"] = config.sha256_file(config.SHUFFLE_MAPPING_FILE)
    with open(config.SHUFFLE_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    return doc


def load_shuffle_mapping() -> dict:
    """Load the frozen mapping and re-verify derangement properties."""
    if not config.SHUFFLE_MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"frozen shuffle mapping missing: {config.SHUFFLE_MAPPING_FILE}. "
            "Run scripts/grounding/freeze_protocol.py first."
        )
    with open(config.SHUFFLE_MAPPING_FILE, "r", encoding="utf-8") as f:
        doc = json.load(f)
    mapping = doc["mapping"]
    if doc.get("seed") != config.SHUFFLE_SEED:
        raise RuntimeError("shuffle mapping seed does not match frozen config")
    _validate_derangement(list(mapping.keys()), mapping)
    return doc
