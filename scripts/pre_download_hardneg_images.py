"""Pre-download all images needed for hard-negative experiment."""
import os, json, hashlib, time
import urllib.request
from io import BytesIO
from PIL import Image
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_DIR = Path(__file__).resolve().parents[1] / "data/image_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG = "/tmp/hn_download.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def get_cache_path(url: str) -> Path:
    return CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def download_one(url: str) -> tuple[str, bool, float]:
    cache_path = get_cache_path(url)
    if cache_path.exists():
        return url, True, 0.0
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        img = Image.open(BytesIO(data)).convert("RGB")
        img.save(cache_path, "JPEG", quality=95)
        return url, True, time.time() - t0
    except Exception:
        return url, False, time.time() - t0

def main():
    urls = set()
    # Manifest images (general + targeted)
    for manifest in ["data/manifests/general_train.jsonl", "data/manifests/targeted_train.jsonl"]:
        with open(manifest) as f:
            for line in f:
                urls.add(json.loads(line)["image"])
    # Orientation train pool (from HF dataset, full train split)
    from datasets import load_dataset
    ds = load_dataset("cambridgeltl/vsr_random", split="train")
    ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
    for r in ds:
        if r["relation"] in ORIENT:
            urls.add(r["image_link"])
    # Test split images
    test_ds = load_dataset("cambridgeltl/vsr_random", split="test")
    for r in test_ds:
        urls.add(r["image_link"])

    log(f"Unique URLs: {len(urls)}")
    already = sum(1 for u in urls if get_cache_path(u).exists())
    log(f"Already cached: {already}")
    to_download = [u for u in urls if not get_cache_path(u).exists()]
    log(f"To download: {len(to_download)}")

    t0 = time.time()
    success, fail = 0, 0
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(download_one, url): url for url in to_download}
        for i, future in enumerate(as_completed(futures)):
            url, ok, dt = future.result()
            if ok:
                success += 1
            else:
                fail += 1
                log(f"FAIL: {url}")
            if (i + 1) % 500 == 0:
                log(f"  {i+1}/{len(to_download)} | ok={success} fail={fail} | {time.time()-t0:.0f}s")
    log(f"DONE: ok={success} fail={fail} total_time={time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
