#!/usr/bin/env python3
"""Freeze Tier-A protocol artifacts (PRE-RESULT, deterministic, CPU-only).

Writes and validates:
  results/grounding/protocol/vsr_test_ids.json       (exact eligible IDs)
  results/grounding/protocol/shuffle_mapping.json    (frozen derangement)
  results/grounding/protocol/blank_image_spec.json   (+ blank_image.png)
  results/grounding/protocol/run_config_snapshot.json

Usage:
  python scripts/grounding/freeze_protocol.py [--no-download]

The shuffle seed, eligibility rule, and algorithms are frozen in the config;
this script must be run before ANY model evaluation and its outputs committed.
Never rerun after results are observed (protocol section 14).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config
from src.grounding.eligibility import freeze_ids_file, load_ids_payload
from src.grounding.hashing import (env_snapshot, git_branch, git_commit,
                                   write_json)
from src.grounding.images import write_blank_spec
from src.grounding.shuffle import freeze_shuffle_mapping


def main():
    no_download = "--no-download" in sys.argv
    print("=" * 70)
    print("FREEZE TIER-A PROTOCOL ARTIFACTS (pre-result)")
    print("=" * 70)
    print(f"git: {git_branch()} @ {git_commit()}")
    print(f"protocol hash: {config.protocol_hash()}")

    # 1. IDs (downloads missing images unless --no-download)
    print("\n[1/4] Freezing exact example IDs (eligibility)...")
    from src.grounding.eligibility import load_test_records
    records = load_test_records()
    payload = freeze_ids_file(records, download_images_first=not no_download)
    n_eligible = sum(1 for r in payload["examples"] if r["image_available"])
    print(f"  total test rows: {payload['count_total']}, eligible: {n_eligible}")
    print(f"  ids file sha256: {payload['file_sha256']}")

    # 2. Shuffle mapping over eligible IDs
    print("\n[2/4] Freezing shuffle derangement (seed %d)..." % config.SHUFFLE_SEED)
    mapping_doc = freeze_shuffle_mapping(payload)
    n_self = sum(1 for k, v in mapping_doc["mapping"].items() if k == v)
    print(f"  eligible mapped: {mapping_doc['count_eligible']}, self-pairs: {n_self}")
    print(f"  mapping sha256: {mapping_doc['file_sha256']}")

    # 3. Blank image spec
    print("\n[3/4] Freezing blank image spec...")
    spec = write_blank_spec()
    print(f"  blank sha256: {spec['sha256']}")

    # 4. Config snapshot
    print("\n[4/4] Writing run config snapshot...")
    snapshot = {
        "protocol_version": "v0.1",
        "protocol_yaml": str(config.PROTOCOL_YAML.relative_to(config.REPO_ROOT)),
        "protocol_hash": config.protocol_hash(),
        "authority": str(config.PROTOCOL_AUTHORITY.relative_to(config.REPO_ROOT)),
        "decision_log": str(config.DECISION_LOG.relative_to(config.REPO_ROOT)),
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "prompt_hash": config.prompt_hash(),
        "parser_hash": config.parser_hash(),
        "shuffle_seed": config.SHUFFLE_SEED,
        "bootstrap_seed": config.BOOTSTRAP_SEED,
        "checkpoints": {k: {"model_id": v["model_id"], "adapter_path": str(v["adapter_path"]) if v["adapter_path"] else None} for k, v in config.CHECKPOINTS.items()},
        "conditions": config.CONDITIONS,
        "env": env_snapshot(),
    }
    snap_path = write_json(config.SNAPSHOT_FILE, snapshot)
    print(f"  snapshot sha256: {snap_path}")

    # 5. Verification summary
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print("reload ids .......... ok" if _reload_ids_ok() else "reload ids .......... FAILED")
    print("derangement .......... ok" if _reload_mapping_ok() else "derangement .......... FAILED")
    print("blank spec .......... ok" if _reload_blank_ok() else "blank spec .......... FAILED")
    print("\nFreeze complete. Commit these files before any model run:")

    for p in (config.IDS_FILE, config.SHUFFLE_MAPPING_FILE,
              config.BLANK_SPEC_FILE, config.BLANK_IMAGE_FILE, config.SNAPSHOT_FILE):
        print(f"  {p.relative_to(config.REPO_ROOT)}")


def _reload_ids_ok() -> bool:
    try:
        payload = load_ids_payload()
        return payload["count_total"] > 0
    except Exception:
        return False


def _reload_mapping_ok() -> bool:
    try:
        from src.grounding.shuffle import load_shuffle_mapping
        doc = load_shuffle_mapping()
        return doc["count_eligible"] > 0
    except Exception:
        return False


def _reload_blank_ok() -> bool:
    try:
        spec = json.loads(config.BLANK_SPEC_FILE.read_text(encoding="utf-8"))
        return config.sha256_file(config.BLANK_IMAGE_FILE) == spec["sha256"]
    except Exception:
        return False


if __name__ == "__main__":
    main()
