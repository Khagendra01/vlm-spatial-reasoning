"""
Download all 15 SITE media zips with hf_transfer (fast, auth'd), extract
only the needed entries, delete zips to bound disk usage.

Needed entries come from results/site/needed_media.txt.
"""
import os, sys, subprocess, time
from pathlib import Path

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

NEEDED = Path("results/site/needed_media.txt")
MEDIA_ROOT = Path("data/site_media")
ZIP_DIR = Path("/tmp/opencode/site_zips")
ZIP_DIR.mkdir(parents=True, exist_ok=True)

from huggingface_hub import hf_hub_download


def main():
    needed = set(p for p in NEEDED.read_text().splitlines() if p)
    print(f"Needed: {len(needed)}", flush=True)
    t0 = time.time()
    for i in range(1, 16):
        missing = [p for p in needed if not (MEDIA_ROOT / p).exists()]
        if not missing:
            print(f"All needed files present ({len(needed)}), done.", flush=True)
            break
        name = f"data_chunked_{i:02d}.zip"
        out = ZIP_DIR / name
        import zipfile
        ok = False
        if out.exists() and out.stat().st_size > 1e6:
            try:
                with zipfile.ZipFile(out) as zf:
                    ok = zf.testzip() is None
            except Exception:
                ok = False
        if not ok:
            t1 = time.time()
            path = hf_hub_download("franky-veteran/SITE-Bench", name,
                                   repo_type="dataset", local_dir=str(ZIP_DIR))
            out = Path(path)
            print(f"[{time.time()-t0:.0f}s] downloaded {name} "
                  f"{out.stat().st_size/1e9:.1f}GB ({time.time()-t1:.0f}s)",
                  flush=True)
        # extract needed entries
        import zipfile
        t1 = time.time()
        with zipfile.ZipFile(out) as zf:
            names = set(zf.namelist())
            hits = [p for p in missing if p in names]
            n_ok = 0
            for h in hits:
                dest = MEDIA_ROOT / h
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(h) as src, open(dest, "wb") as dst:
                    import shutil
                    shutil.copyfileobj(src, dst)
                n_ok += 1
        print(f"[{time.time()-t0:.0f}s] {name}: extracted {n_ok}/{len(hits)} "
              f"({time.time()-t1:.0f}s)", flush=True)
        out.unlink()
        print(f"  removed {name}", flush=True)

    present = sum(1 for p in needed if (MEDIA_ROOT / p).exists())
    print(f"Media present: {present}/{len(needed)} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
