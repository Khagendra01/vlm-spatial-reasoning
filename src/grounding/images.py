"""Image cache and deterministic preprocessing for the grounding audit.

- Cache key: md5 hex of the HF `image_link` URL (matches every prior pipeline
  in this repo: run_7b_pipeline.py, run_7b_hardneg_pipeline.py).
- Downloader writes data/image_cache/<md5>.jpg (gitignored).
- preprocess_for_vlm enforces the uniform 392px long-side cap
  (docs/TECHNIQUES.md section 4): a constant across all examples and all
  four Tier-A conditions (fair by construction; recorded in run metadata).
- Blank image construction is deterministic and recorded in
  results/grounding/protocol/blank_image_spec.json + blank_image.png.
"""

import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

from PIL import Image

from . import config

_IMAGE_EXT = ".jpg"


def cache_path_for(image_link: str) -> Path:
    digest = hashlib.md5(image_link.encode("utf-8")).hexdigest()
    return config.IMAGE_CACHE_DIR / f"{digest}{_IMAGE_EXT}"


def is_cached(image_link: str) -> bool:
    return cache_path_for(image_link).exists()


def load_cached_image(image_link: str) -> Image.Image:
    """Return the cached RGB image or None if not present/unreadable."""
    path = cache_path_for(image_link)
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


def download_images(image_links, max_workers: int = None) -> dict:
    """Download missing images into the cache; returns {url: ok_bool}."""
    max_workers = max_workers or config.MAX_IMAGE_DOWNLOAD_WORKERS
    config.IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    todo = [url for url in dict.fromkeys(image_links) if not is_cached(url)]
    result = {url: True for url in image_links if is_cached(url)}
    if not todo:
        return result

    def fetch(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            img = Image.open(BytesIO(data)).convert("RGB")
            img.save(cache_path_for(url), format="JPEG", quality=95)
            return url, True
        except Exception as e:
            print(f"  WARNING: failed to download {url}: {e}")
            return url, False

    print(f"Downloading {len(todo)} images with {max_workers} workers...")
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(fetch, url) for url in todo]
        for fut in as_completed(futures):
            url, ok = fut.result()
            result[url] = ok
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(todo)}")
    return result


def preprocess_for_vlm(image: Image.Image, max_long_side: int = None) -> Image.Image:
    """Uniform preprocessing: RGB, long side capped at MAX_LONG_SIDE.

    Identical for normal/shuffle/blank inputs (text-only has no image).
    """
    max_long_side = max_long_side or config.MAX_LONG_SIDE
    image = image.convert("RGB")
    w, h = image.size
    if max(w, h) > max_long_side:
        scale = max_long_side / max(w, h)
        image = image.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BILINEAR)
    return image


# --------------------------------------------------------------------------
# Blank image (deterministic construction, recorded spec)
# --------------------------------------------------------------------------

def build_blank_image(size: int = None, color: tuple = None) -> Image.Image:
    size = size or config.BLANK_IMAGE_SIZE
    color = color or config.BLANK_IMAGE_COLOR
    return Image.new("RGB", (size, size), color)


def write_blank_spec() -> dict:
    """Write blank_image.png + blank_image_spec.json; returns spec dict."""
    img = build_blank_image()
    config.PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    img.save(config.BLANK_IMAGE_FILE, format="PNG")
    spec = {
        "name": "blank_image",
        "version": config.TRANSFORM_VERSION,
        "construction": {
            "mode": "RGB",
            "size_px": config.BLANK_IMAGE_SIZE,
            "color_rgb": list(config.BLANK_IMAGE_COLOR),
        },
        "preprocessing": {
            "cap_long_side_px": config.MAX_LONG_SIDE,
            "note": "blank goes through the identical preprocessing path as normal/shuffle images",
        },
        "file": str(config.BLANK_IMAGE_FILE.relative_to(config.REPO_ROOT)),
        "sha256": config.sha256_file(config.BLANK_IMAGE_FILE),
        "protocol_version": "v0.1",
    }
    with open(config.BLANK_SPEC_FILE, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, sort_keys=True)
    return spec
