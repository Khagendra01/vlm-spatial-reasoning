"""Exact example-ID eligibility for the Tier-A confirmatory audit.

The VSR test split has no native row ID, so each row receives a deterministic
frozen ID `vsr_test:<index>` in dataset order plus a content hash
(md5 of image_link | caption | label | relation) so that any dataset revision
or reordering is detected loudly at load time.

Eligibility rule (frozen pre-result): a test row is eligible iff its image is
available in the cache at freeze time. Train/validation rows can never enter
the audit (configs/grounding_protocol.yaml: forbid_train_validation...).
"""

import hashlib
import json
import re
from pathlib import Path

from . import config
from .families import get_family
from .images import is_cached, load_cached_image

_SUBJECT_RE = re.compile(r"^The (.+?) is ", re.IGNORECASE)
_OBJECT_RE = re.compile(r" (?:is|are|has as a part|consists of|contains|is part of|is inside|is within|is enclosed by|is surrounded by|is in the middle of|is among|is at the edge of|is attached to|is connected to|is detached from|is facing|is facing away from|is parallel to|is perpendicular to|is touching|is on top of|is next to|is beside|is near|is far from|is far away from|is close to|is away from|is across from|is alongside|is at the side of|is at the left side of|is at the right side of|is in front of|is behind|is at the back of|is ahead of|is to the left of|is to the right of|is above|is below|is over|is under|is beneath|is on|is in|is at)\s+the (.+?)[.?!]?$", re.IGNORECASE)


def content_hash(image_link: str, caption: str, label: bool, relation: str) -> str:
    payload = "|".join([image_link, caption, str(int(label)), relation])
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def parse_subject_object(caption: str) -> tuple:
    """Lightweight subject/object extraction (descriptive only for Tier A).

    Tier B (subject/object reversal) requires the full parser audit from the
    study plan; this extraction is NOT used for any transform in Tier A.
    """
    subject = ""
    obj = ""
    m = _SUBJECT_RE.match(caption.strip())
    if m:
        subject = m.group(1)
    m2 = _OBJECT_RE.search(caption.strip())
    if m2:
        obj = m2.group(1)
    return subject, obj


def load_test_records() -> list:
    """Load VSR test rows into audit records (frozen ID + content hash)."""
    from datasets import load_dataset

    ds = load_dataset(config.DATASET_ID, split=config.DATASET_SPLIT)
    records = []
    for idx, ex in enumerate(ds):
        image_link = ex.get("image_link") or ex.get("image") or ""
        caption = ex.get("caption", "")
        label = bool(ex.get("label", 0))
        relation = ex.get("relation", "")
        subject, obj = parse_subject_object(caption)
        records.append({
            "example_id": f"vsr_test:{idx:04d}",
            "dataset_index": idx,
            "image_link": image_link,
            "statement": caption,
            "label": label,
            "relation": relation,
            "family": get_family(relation),
            "subject": subject,
            "object": obj,
            "content_hash": content_hash(image_link, caption, label, relation),
        })
    return records


def freeze_ids_file(records: list, download_images_first: bool = True) -> dict:
    """Write the frozen vsr_test_ids.json (eligibility included).

    Returns the written payload. If download_images_first, missing images are
    downloaded before eligibility is decided so the file is authoritative.
    """
    if download_images_first:
        from .images import download_images
        download_images([r["image_link"] for r in records])
    payload = {
        "protocol_version": "v0.1",
        "dataset_id": config.DATASET_ID,
        "split": config.DATASET_SPLIT,
        "eligibility_rule": "test rows with image available in cache at freeze time",
        "id_scheme": "vsr_test:<dataset_index> (dataset row order, zero-based)",
        "count_total": len(records),
        "examples": [
            {
                "example_id": r["example_id"],
                "dataset_index": r["dataset_index"],
                "image_link": r["image_link"],
                "statement": r["statement"],
                "label": r["label"],
                "relation": r["relation"],
                "family": r["family"],
                "subject": r["subject"],
                "object": r["object"],
                "content_hash": r["content_hash"],
                "image_available": is_cached(r["image_link"])
                and load_cached_image(r["image_link"]) is not None,
            }
            for r in records
        ],
    }
    config.PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    payload["file_sha256"] = config.sha256_file(config.IDS_FILE)
    with open(config.IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return payload


def load_ids_payload() -> dict:
    """Load the frozen IDs file, verifying content hashes against a fresh load.

    Raises RuntimeError on any drift (dataset revision/reorder detection).
    """
    if not config.IDS_FILE.exists():
        raise FileNotFoundError(
            f"frozen IDs file missing: {config.IDS_FILE}. "
            "Run scripts/grounding/freeze_protocol.py first."
        )
    with open(config.IDS_FILE, "r", encoding="utf-8") as f:
        payload = json.load(f)
    current = {r["example_id"]: r for r in load_test_records()}
    frozen = {r["example_id"]: r for r in payload["examples"]}
    if set(current) != set(frozen):
        raise RuntimeError("example_id sets differ between frozen file and live dataset")
    for eid, fr in frozen.items():
        cur = current[eid]
        if fr["content_hash"] != cur["content_hash"]:
            raise RuntimeError(
                f"content hash drift for {eid}: frozen={fr['content_hash']} live={cur['content_hash']} "
                "(dataset changed; do NOT regenerate IDs silently)"
            )
    return payload


def eligible_records(payload: dict) -> list:
    """Records with image_available == True, in frozen order."""
    return [r for r in payload["examples"] if r["image_available"]]


def available_ids(payload: dict) -> list:
    return [r["example_id"] for r in eligible_records(payload)]


def subset_records(payload: dict, n: int) -> list:
    """First n eligible records in frozen dataset order (smoke/pilot subset)."""
    return eligible_records(payload)[:n]
