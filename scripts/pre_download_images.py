"""Pre-download all VSR images to local cache for fast training."""
import os, json, hashlib, time
import urllib.request
from io import BytesIO
from PIL import Image
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_DIR = Path(__file__).resolve().parents[1] / "data/image_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_path(url: str) -> Path:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.jpg"

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
    except Exception as e:
        return url, False, time.time() - t0

def main():
    urls = set()
    for manifest in ["general_train.jsonl", "targeted_train.jsonl"]:
        path = f"{CACHE_DIR.parent}/manifests/{manifest}"
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                ex = json.loads(line)
                urls.add(ex["image"])
    
    print(f"Found {len(urls)} unique URLs to download")
    print(f"Cache dir: {CACHE_DIR}")
    print(f"Already cached: {sum(1 for u in urls if get_cache_path(u).exists())}")
    
    to_download = [u for u in urls if not get_cache_path(u).exists()]
    print(f"To download: {len(to_download)}")
    
    if not to_download:
        print("All images cached!")
        return
    
    t0 = time.time()
    success = 0
    fail = 0
    
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_one, url): url for url in to_download}
        for i, future in enumerate(as_completed(futures)):
            url, ok, dt = future.result()
            if ok:
                success += 1
            else:
                fail += 1
            if (i + 1) % 50 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                print(f"  {i+1}/{len(to_download)} | {rate:.1f} img/s | {success} ok, {fail} fail | {elapsed:.0f}s")
    
    total_time = time.time() - t0
    print(f"\nDone: {success} downloaded, {fail} failed in {total_time:.0f}s")
    print(f"Cache size: {sum(f.stat().st_size for f in CACHE_DIR.iterdir()) / 1e6:.1f} MB")

if __name__ == "__main__":
    main()
