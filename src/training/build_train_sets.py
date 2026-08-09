"""
Build reproducible training manifests for LoRA experiments.

Creates two training sets:
1. general_train.jsonl  – representative sample across all relation families
2. targeted_train.jsonl – ~70% weak families (orientation/depth/horizontal), ~30% other

Both manifests preserve approximately equal total size for fair comparison.
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.datasets.vsr import load_vsr


RELATION_FAMILIES = {
    "horizontal": [
        "left of", "right of", "at the left side of", "at the right side of",
        "at the side of", "beside", "next to", "alongside", "across from",
    ],
    "vertical": [
        "above", "below", "over", "under", "beneath", "on top of",
    ],
    "depth": [
        "in front of", "behind", "at the back of", "ahead of",
    ],
    "orientation": [
        "facing", "facing away from", "parallel to", "perpendicular to",
    ],
    "containment": [
        "in", "inside", "contains", "within", "enclosed by",
    ],
    "proximity": [
        "near", "far from", "far away from", "close to", "away from",
    ],
    "topology_contact": [
        "touching", "on", "at", "at the edge of", "against", "attached to",
        "connected to", "detached from",
    ],
    "compositional": [
        "part of", "has as a part", "consists of", "surrounding",
        "in the middle of", "among",
    ],
}

WEAK_FAMILIES = {"orientation", "depth", "horizontal"}


def get_family(relation: str) -> str:
    for family, relations in RELATION_FAMILIES.items():
        if relation in relations:
            return family
    return "unknown"


def build_family_index(records: list) -> dict:
    """Group records by family."""
    index = defaultdict(list)
    for i, r in enumerate(records):
        family = get_family(r["relation"])
        index[family].append(i)
    return dict(index)


def sample_general(
    records: list,
    family_index: dict,
    n_total: int,
    seed: int = 42,
) -> list:
    """
    Stratified sampling proportional to family size, capped per relation.
    Ensures every relation family is represented.
    """
    rng = np.random.RandomState(seed)

    # Compute proportional allocation
    family_sizes = {f: len(idxs) for f, idxs in family_index.items()}
    total = sum(family_sizes.values())
    family_alloc = {f: max(2, int(n_total * n / total)) for f, n in family_sizes.items()}

    # Adjust to hit exact target
    allocated = sum(family_alloc.values())
    while allocated > n_total:
        largest = max(family_alloc, key=family_alloc.get)
        family_alloc[largest] -= 1
        allocated -= 1
    while allocated < n_total:
        smallest = min(family_alloc, key=family_alloc.get)
        family_alloc[smallest] += 1
        allocated += 1

    # Sample within each family
    selected = []
    for family, n_alloc in family_alloc.items():
        candidates = family_index.get(family, [])
        if not candidates:
            continue
        # Sub-group by relation for diversity
        rel_groups = defaultdict(list)
        for idx in candidates:
            rel_groups[records[idx]["relation"]].append(idx)

        # Round-robin across relations
        rel_keys = sorted(rel_groups.keys())
        sampled = []
        for ridx in range(len(rel_keys)):
            rel = rel_keys[ridx % len(rel_keys)]
            pool = rel_groups[rel]
            rng.shuffle(pool)
            sampled.extend(pool)

        # Take up to n_alloc
        selected.extend(sampled[:n_alloc])

    # Trim or pad
    rng.shuffle(selected)
    return selected[:n_total]


def sample_targeted(
    records: list,
    family_index: dict,
    n_total: int,
    seed: int = 42,
) -> list:
    """
    Targeted sampling: ~70% weak families, ~30% other.
    Within the 70%, mildly oversample orientation.
    """
    rng = np.random.RandomState(seed)

    n_weak = int(n_total * 0.70)
    n_other = n_total - n_weak

    # Split weak families: orientation gets a small boost
    weak_indices = []
    for fam in WEAK_FAMILIES:
        weak_indices.extend(family_index.get(fam, []))

    # Oversample orientation by ~20%
    orientation_indices = family_index.get("orientation", [])
    depth_indices = family_index.get("depth", [])
    horizontal_indices = family_index.get("horizontal", [])

    # Proportional with orientation boost
    raw_weak = {
        "orientation": len(orientation_indices),
        "depth": len(depth_indices),
        "horizontal": len(horizontal_indices),
    }
    total_weak = sum(raw_weak.values())
    if total_weak == 0:
        weak_alloc = {f: n_weak // 3 for f in raw_weak}
    else:
        # Boost orientation by 20%
        adjusted = dict(raw_weak)
        adjusted["orientation"] = int(adjusted["orientation"] * 1.2)
        adj_total = sum(adjusted.values())
        weak_alloc = {f: max(1, int(n_weak * n / adj_total)) for f, n in adjusted.items()}

    # Adjust to hit n_weak
    allocated = sum(weak_alloc.values())
    while allocated > n_weak:
        largest = max(weak_alloc, key=weak_alloc.get)
        weak_alloc[largest] -= 1
        allocated -= 1
    while allocated < n_weak:
        smallest = min(weak_alloc, key=weak_alloc.get)
        weak_alloc[smallest] += 1
        allocated += 1

    # Sample weak families
    selected_weak = []
    family_map = {"orientation": orientation_indices, "depth": depth_indices, "horizontal": horizontal_indices}
    for fam, n_alloc in weak_alloc.items():
        candidates = family_map.get(fam, [])
        rng.shuffle(candidates)
        selected_weak.extend(candidates[:n_alloc])

    # Sample other families (rehearsal)
    other_indices = []
    for fam, idxs in family_index.items():
        if fam not in WEAK_FAMILIES:
            other_indices.extend(idxs)
    rng.shuffle(other_indices)
    selected_other = other_indices[:n_other]

    # Combine and shuffle
    selected = selected_weak + selected_other
    rng.shuffle(selected)
    return selected[:n_total]


def save_manifest(records: list, indices: list, path: str):
    """Save manifest as JSONL."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for idx in indices:
            r = records[idx]
            row = {
                "id": idx,
                "statement": r["statement"],
                "label": r["label"],
                "relation": r["relation"],
                "family": get_family(r["relation"]),
                "image": r["image"],
            }
            f.write(json.dumps(row) + "\n")


def print_distribution(path: str):
    """Print family/relation distribution of a manifest."""
    counts = defaultdict(lambda: defaultdict(int))
    total = 0
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            counts[row["family"]][row["relation"]] += 1
            total += 1

    print(f"\n  Total: {total}")
    print(f"  {'Family':<22} {'N':>5} {'%':>6}")
    print(f"  {'-'*35}")
    for family in sorted(counts.keys(), key=lambda f: -sum(counts[f].values())):
        fam_total = sum(counts[family].values())
        print(f"  {family:<22} {fam_total:>5} {fam_total/total*100:>5.1f}%")
        for rel in sorted(counts[family].keys(), key=lambda r: -counts[family][r]):
            print(f"    {rel:<20} {counts[family][rel]:>5}")


def main():
    print("Loading VSR training split...")
    records = load_vsr(split="train")
    print(f"Total training examples: {len(records)}")

    family_index = build_family_index(records)
    print(f"Families found: {sorted(family_index.keys())}")

    # Decide manifest size: use ~2000 examples (manageable for LoRA on small GPU)
    n_total = min(2000, len(records))

    # General manifest
    general_indices = sample_general(records, family_index, n_total)
    general_path = "data/manifests/general_train.jsonl"
    save_manifest(records, general_indices, general_path)
    print(f"\n{'='*50}")
    print(f"GENERAL MANIFEST: {general_path}")
    print_distribution(general_path)

    # Targeted manifest
    targeted_indices = sample_targeted(records, family_index, n_total)
    targeted_path = "data/manifests/targeted_train.jsonl"
    save_manifest(records, targeted_indices, targeted_path)
    print(f"\n{'='*50}")
    print(f"TARGETED MANIFEST: {targeted_path}")
    print_distribution(targeted_path)


if __name__ == "__main__":
    main()
