"""
Download SITE media for the frozen preregistered subsets.

The official release hosts media only inside 15 zips (~130GB total).
This script downloads zips one at a time (resume-able), extracts ONLY the
entries needed by the frozen subsets, and deletes the zip to respect the
~74GB disk budget.

Media root: data/site_media/<relative path from 'visual' field>
"""
import os, sys, json, subprocess, time
from pathlib import Path

os.chdir("/home/ubuntu/vlm-spatial-reasoning")

NEEDED = Path("results/site/needed_media.txt")
MEDIA_ROOT = Path("data/site_media")
ZIP_DIR = Path("/tmp/opencode/site_zips")
BASE_URL = "https://huggingface.co/datasets/franky-veteran/SITE-Bench/resolve/main/data_chunked_{:02d}.zip"

def main():
    needed = set(p for p in Path(NEEDED).read_text().splitlines() if p)
    print(f"Needed files: {len(needed)}")
    ZIP_DIR.mkdir(parents=True, exist_ok=True)

    for i in range(1, 16):
        # remaining needed files not yet on disk
        missing = [p for p in needed if not (MEDIA_ROOT / p).exists()]
        if not missing:
            print(f"All {len(needed)} needed files present — done.")
            break
        print(f"Remaining missing: {len(missing)}")

        zip_path = ZIP_DIR / f"data_chunked_{i:02d}.zip"
        if zip_path.exists() and zip_path.stat().st_size > 1e6:
            print(f"Zip {i:02d} already downloaded ({zip_path.stat().st_size/1e9:.1f}GB)")
        else:
            url = BASE_URL.format(i)
            print(f"Downloading {url} ...", flush=True)
            t0 = time.time()
            r = subprocess.run(["curl", "-sL", "-C", "-", "-o", str(zip_path), url])
            if r.returncode != 0:
                print(f"  curl failed rc={r.returncode}")
                continue
            print(f"  downloaded {zip_path.stat().st_size/1e9:.1f}GB in {time.time()-t0:.0f}s")

        # list entries, extract needed
        print(f"Listing zip {i:02d} ...", flush=True)
        listing = subprocess.run(["unzip", "-Z1", str(zip_path)], capture_output=True, text=True).stdout.splitlines()
        zset = set(listing)
        hits = [p for p in missing if p in zset]
        print(f"  zip has {len(zset)} entries; needed hits: {len(hits)}", flush=True)
        if hits:
            t0 = time.time()
            for h in hits:
                out = MEDIA_ROOT / h
                out.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["unzip", "-o", "-j", str(zip_path), h, "-d", str(out.parent)],
                               capture_output=True)
            # verify
            got = sum(1 for h in hits if (MEDIA_ROOT / h).exists())
            print(f"  extracted {got}/{len(hits)} in {time.time()-t0:.0f}s", flush=True)

        # free disk
        os.remove(zip_path)
        print(f"  removed zip {i:02d}", flush=True)

    missing = [p for p in needed if not (MEDIA_ROOT / p).exists()]
    present = len(needed) - len(missing)
    print(f"\nDone. Present: {present}/{len(needed)}. Still missing: {len(missing)}")

if __name__ == "__main__":
    main()
