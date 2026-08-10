"""Tier-A intervention builders (evidence-ablation axis E).

Every condition produces, for each example, the exact multimodal input plus
deterministic transform metadata. Language is NEVER changed in Tier A; only
the image (or its absence) varies. Text-only uses the architecture-compatible
interface (no image item in the chat content), not a placeholder.

Determinism requirements (protocol section 4 / 12):
- normal: original cached image;
- shuffle: original statement + replacement image from the frozen derangement
  (identical mapping for every checkpoint/condition);
- blank: original statement + the frozen blank image (spec hashed);
- text_only: original statement, no image content.
"""

from . import config
from .images import build_blank_image, load_cached_image, preprocess_for_vlm


def build_condition_inputs(records: list, condition: str,
                           shuffle_doc: dict = None,
                           link_lookup: dict = None) -> list:
    """Return list of input dicts for the given condition.

    Each input dict:
      example_id, statement, label, relation, family,
      image (PIL or None), transform metadata fields.
    `records` are frozen-ID records (eligibility payload rows).

    `link_lookup` maps example_id -> image_link for the FULL eligible set.
    It is required for the shuffle condition when `records` is a subset
    (pilot/smoke): the frozen derangement is global, so a subset example's
    replacement may fall outside the subset.
    """
    if condition == "shuffle" and shuffle_doc is None:
        raise ValueError("shuffle condition requires the frozen shuffle mapping")
    if condition not in config.CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; must be one of {config.CONDITIONS}")

    if link_lookup is None:
        link_lookup = {r["example_id"]: r["image_link"] for r in records}
    elif set(r["example_id"] for r in records) - set(link_lookup):
        raise ValueError("link_lookup must cover all records being processed")

    blank_pil = build_blank_image()
    mapping = (shuffle_doc or {}).get("mapping", {})

    out = []
    for rec in records:
        eid = rec["example_id"]
        statement = rec["statement"]
        label = rec["label"]
        relation = rec["relation"]
        family = rec["family"]
        base = {
            "example_id": eid,
            "statement": statement,
            "label": label,
            "relation": relation,
            "family": family,
            "image_link": rec["image_link"],
        }
        if condition == "normal":
            img = load_cached_image(rec["image_link"])
            out.append({
                **base,
                "image": preprocess_for_vlm(img) if img is not None else None,
                "source_image_id": rec["image_link"],
                "replacement_image_id": None,
                "transformed_image_id": rec["image_link"],
                "transform_name": "normal",
                "transform_version": config.TRANSFORM_VERSION,
                "transform_metadata": {"axis": "evidence", "condition": "normal"},
            })
        elif condition == "shuffle":
            replacement_id = mapping[eid]
            if replacement_id not in link_lookup:
                raise RuntimeError(
                    f"replacement {replacement_id} for {eid} missing from link lookup"
                )
            repl_link = link_lookup[replacement_id]
            img = load_cached_image(repl_link)
            out.append({
                **base,
                "image": preprocess_for_vlm(img) if img is not None else None,
                "source_image_id": rec["image_link"],
                "replacement_image_id": replacement_id,
                "transformed_image_id": repl_link,
                "transform_name": "shuffle_image",
                "transform_version": config.TRANSFORM_VERSION,
                "transform_metadata": {
                    "axis": "evidence",
                    "condition": "shuffle",
                    "algorithm": "cycle derangement",
                    "seed": config.SHUFFLE_SEED,
                    "replacement_example_id": replacement_id,
                    "forbid_self_pair": True,
                    "mapping_file_sha256": shuffle_doc.get("file_sha256", ""),
                },
            })
        elif condition == "blank":
            out.append({
                **base,
                "image": preprocess_for_vlm(blank_pil),
                "source_image_id": rec["image_link"],
                "replacement_image_id": None,
                "transformed_image_id": "blank",
                "transform_name": "blank_image",
                "transform_version": config.TRANSFORM_VERSION,
                "transform_metadata": {
                    "axis": "evidence",
                    "condition": "blank",
                    "spec_file": str(config.BLANK_SPEC_FILE.relative_to(config.REPO_ROOT)),
                },
            })
        elif condition == "text_only":
            out.append({
                **base,
                "image": None,
                "source_image_id": rec["image_link"],
                "replacement_image_id": None,
                "transformed_image_id": None,
                "transform_name": "text_only",
                "transform_version": config.TRANSFORM_VERSION,
                "transform_metadata": {
                    "axis": "evidence",
                    "condition": "text_only",
                    "note": "no image item in chat content; architecture-compatible interface",
                },
            })
    return out


def all_inputs_match_labels(inputs: list, records: list) -> bool:
    """Pairing sanity: identical example IDs and labels between inputs and records."""
    return all(
        i["example_id"] == r["example_id"] and i["label"] == r["label"]
        for i, r in zip(inputs, records)
    )
