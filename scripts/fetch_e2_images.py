"""Fetch E2 subset images into the md5-named VSR image cache.

Downloads only the frozen 245 subset images (~40MB) directly from their
public COCO URLs — no need to upload the 703MB cache archive.
Safe to re-run: existing files are skipped.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import requests

CACHE = Path("data/image_cache")


def cache_path(url: str) -> Path:
    return CACHE / (hashlib.md5(url.encode()).hexdigest() + ".jpg")


def main(ids_path="research/equiorient_iclr_push/e2_image_ids.json"):
    ids_map = json.load(open(ids_path))
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = {e: u for e, u in sorted(ids_map.items()) if not cache_path(u).exists()}
    print(f"{len(ids_map)} needed, {len(todo)} to download")
    ok = fail = 0
    for i, (eid, url) in enumerate(todo.items()):
        dest = cache_path(url)
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            dest.write_bytes(r.content)
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  miss {eid}: {e}")
            fail += 1
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(todo)}")
            time.sleep(1)
    print(f"done: {ok} fetched, {fail} failed, "
          f"{len(ids_map) - len(todo)} already cached")


if __name__ == "__main__":
    main(*sys.argv[1:])
