# -*- coding: utf-8 -*-
"""
Complete VSR image-cache downloader for training/evaluation machines.

Downloads every image needed by the seed-variance runner into
data/image_cache/ using the same md5(url) filename scheme as the runner
(scripts/run_seed_variance.py, scripts/eval_consistency_flips.py):

  * VSR test split (2,195 rows; field "image_link")
  * training manifests under data/manifests/ (field "image"; defaults to
    general_train.jsonl + hardneg_train.jsonl + targeted_train.jsonl)

Idempotent: existing files are skipped. Failures are logged per URL and
retried once; the final summary states how many images are still missing so
the operator can re-run the script instead of guessing.

Usage:
    python scripts/pre_download_all.py
"""
import hashlib
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "image_cache"
MANIFESTS = ["general_train.jsonl", "hardneg_train.jsonl", "targeted_train.jsonl"]
WORKERS = 8
TIMEOUT = 30


def cache_path(url):
    return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"


def collect_urls():
    urls = set()
    # test split
    sys.path.insert(0, str(ROOT))
    from datasets import load_dataset
    ds = load_dataset("cambridgeltl/vsr_random", split="test")
    for ex in ds:
        if ex.get("image_link"):
            urls.add(ex["image_link"])
    # train manifests
    for name in MANIFESTS:
        p = ROOT / "data" / "manifests" / name
        if not p.exists():
            print(f"WARNING: manifest {p} missing; skipping", flush=True)
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                url = json.loads(line).get("image")
                if url:
                    urls.add(url)
    return sorted(urls)


def fetch(url):
    dst = cache_path(url)
    if dst.exists() and dst.stat().st_size > 0:
        return url, True, "cached"
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (seed-variance setup)"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                img = Image.open(BytesIO(r.read())).convert("RGB")
            dst.parent.mkdir(parents=True, exist_ok=True)
            img.save(dst, "JPEG")
            return url, True, f"ok(attempt {attempt})"
        except Exception as e:
            if attempt == 2:
                return url, False, repr(e)[:120]
            time.sleep(2)
    return url, False, "unreachable"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    urls = collect_urls()
    missing = [u for u in urls if not (cache_path(u).exists()
                                       and cache_path(u).stat().st_size > 0)]
    print(f"total unique URLs: {len(urls)} | already cached: "
          f"{len(urls) - len(missing)} | to download: {len(missing)}",
          flush=True)
    if not missing:
        print("cache complete", flush=True)
        return

    t0 = time.time()
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(fetch, u): u for u in missing}
        for i, fut in enumerate(as_completed(futs), 1):
            url, success, note = fut.result()
            if success:
                ok += 1
            else:
                fail += 1
                print(f"FAILED {url}: {note}", flush=True)
            if i % 200 == 0 or i == len(missing):
                print(f"  ... {i}/{len(missing)} (ok {ok}, failed {fail}, "
                      f"{time.time()-t0:.0f}s)", flush=True)

    still = [u for u in missing if not cache_path(u).exists()]
    print(f"done: {ok} downloaded, {fail} failed, "
          f"{len(still)} still missing (re-run to retry); "
          f"cache total: {len(list(CACHE.glob('*.jpg')))}", flush=True)
    if still:
        print("RE-RUN python scripts/pre_download_all.py to retry missing "
              "images", flush=True)


if __name__ == "__main__":
    main()
