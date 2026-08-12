"""Materialize id-mapped VSR images for external-model upload:
copy from data/image_cache (md5-of-URL names) and download the rest
from COCO, writing external_eval/vsr_full_v1/images/idN.jpg.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "mimo" / "mimo_v25_zeroshot_predictions.csv"
CACHE = ROOT / "data" / "image_cache"
OUT = ROOT / "external_eval" / "vsr_full_v1" / "images"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with SRC.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    copied = downloaded = failed = 0
    for r in rows:
        dest = OUT / f"id{r['id']}.jpg"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        cached = CACHE / f"{hashlib.md5(r['image_url'].encode()).hexdigest()}.jpg"
        if cached.exists() and cached.stat().st_size > 0:
            shutil.copy2(cached, dest)
            copied += 1
        else:
            try:
                req = urllib.request.Request(
                    r["image_url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    dest.write_bytes(resp.read())
                downloaded += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL id={r['id']} {r['image_url']}: {e}")

    total = len([p for p in OUT.glob("*.jpg")])
    print(f"total={total} copied={copied} downloaded={downloaded} failed={failed}")
    print(f"folder: {OUT}")


if __name__ == "__main__":
    main()
