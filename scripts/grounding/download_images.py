#!/usr/bin/env python3
"""Download VSR test images into data/image_cache on the evaluation box.

The frozen protocol artifacts (IDs, shuffle mapping, blank spec) are committed;
the image cache is NOT (gitignored). This script re-populates the cache from
the frozen IDs file without touching any frozen artifact.

Usage:
  python scripts/grounding/download_images.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config
from src.grounding.eligibility import load_ids_payload
from src.grounding.images import download_images


def main():
    payload = load_ids_payload()
    links = [r["image_link"] for r in payload["examples"]
             if r["image_available"]]
    print(f"ensuring {len(links)} images for {payload['count_total']} test rows...")
    result = download_images(links)
    ok = sum(1 for v in result.values() if v)
    missing = [u for u, v in result.items() if not v]
    print(f"available: {ok}/{len(result)}")
    if missing:
        print("MISSING (will be ineligible only if they were frozen unavailable):")
        for u in missing[:10]:
            print(f"  {u}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
