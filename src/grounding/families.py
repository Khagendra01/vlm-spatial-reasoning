"""Centralized relation-family map for the grounding audit.

Per SPATIAL_GROUNDING_LORA_STUDY.md section 14, the relation-family map must be
centralized so scripts cannot silently disagree. This module is the single
source for the audit; it mirrors the historical map used by every prior run in
this repo (scripts/run_baseline.py, scripts/run_7b_pipeline.py).
"""

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


def get_family(relation: str) -> str:
    """Return the family name for a relation string, or 'other'."""
    for family, relations in RELATION_FAMILIES.items():
        if relation in relations:
            return family
    return "other"
