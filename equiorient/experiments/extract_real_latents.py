"""E2 latent extraction for natural VSR images (GPU-deferred).

Extracts post-merge vision features z(x) and z(hflip(x)) per checkpoint.
hflip is applied AFTER the uniform 392px long-side resize to exactly match
the Tier-C behavioral transform (tier_c_v0.1). Primary pooling: global mean
over all merged tokens (preregistered; no object boxes on real images).

Run on GPU later:
  python -m equiorient.experiments.extract_real_latents \
      --backbone qwen2vl_7b --adapter checkpoints/.../final \
      --image-ids research/equiorient_iclr_push/e2_image_ids.json \
      --image-cache data/image_cache --out results/e2/z_qwen2vl_7b_seedA.npz
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

LONG_SIDE = 392


def cache_path(image_cache_dir: str | Path, url: str) -> Path:
    return Path(image_cache_dir) / (hashlib.md5(url.encode()).hexdigest() + ".jpg")


def preprocess_392(pil_img, flip: bool = False):
    """Uniform long-side 392 resize; optional FLIP_LEFT_RIGHT (tier_c_v0.1)."""
    w, h = pil_img.size
    scale = LONG_SIDE / max(w, h)
    img = pil_img.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                         Image.BILINEAR)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img


def preprocess_pair(pil_img):
    resized = preprocess_392(pil_img)
    return resized, resized.transpose(Image.FLIP_LEFT_RIGHT)


class LatentExtractor:
    """Vision-tower feature extractor for one backbone (+optional LoRA)."""

    def __init__(self, backbone: str, adapter: str | None = None,
                 device: str = "cuda", dtype="bfloat16"):
        import torch
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        self.torch = torch
        self.device = device
        self.backbone = backbone
        if backbone == "qwen2vl_7b":
            name = "Qwen/Qwen2-VL-7B-Instruct"
            self.processor = AutoProcessor.from_pretrained(
                name, min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                name, torch_dtype=getattr(torch, dtype), attn_implementation="sdpa")
        elif backbone == "smolvlm2_2b":
            from transformers import AutoModelForImageTextToText
            name = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"
            self.processor = AutoProcessor.from_pretrained(name)
            self.model = AutoModelForImageTextToText.from_pretrained(
                name, torch_dtype=getattr(torch, dtype))
        else:
            raise ValueError(backbone)
        if adapter:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, adapter)
        self.model.to(device).eval()

    def _pixels(self, pil_img):
        inp = self.processor(images=pil_img, text="", return_tensors="pt")
        return (inp["pixel_values"].to(self.device, dtype=self.model.dtype),
                inp["image_grid_thw"].to(self.device))

    def _vision_features(self, pix, grid):
        visual = getattr(self.model, "visual", None) or self.model.model.vision_tower
        out = visual(pix, grid_thw=grid)
        feats = out[1][0] if isinstance(out, tuple) and len(out) == 2 else out
        return feats.squeeze(0).float()

    @torch.no_grad()
    def extract_pair(self, pil_img):
        """Returns (z_x, z_flipx) global mean-pooled vectors.

        Both sides share the identical 392px long-side resize; only the
        flipped side gets FLIP_LEFT_RIGHT (tier_c_v0.1 order).
        """
        resized, flipped = preprocess_pair(pil_img)
        z_list = []
        for im in (resized, flipped):
            pix, grid = self._pixels(im)
            f = self._vision_features(pix, grid)
            z_list.append(f.mean(dim=0).cpu().numpy())
        return z_list[0], z_list[1]


def run_extraction(backbone: str, adapter: str | None, image_ids_path: str,
                   image_cache: str, out_path: str, device: str = "cuda"):
    ids_map = json.load(open(image_ids_path))
    ext = LatentExtractor(backbone, adapter, device=device)
    zx_all, zt_all, eids = [], [], []
    for eid, url in sorted(ids_map.items()):
        p = cache_path(image_cache, url)
        if not p.exists():
            continue
        from PIL import Image
        img = Image.open(p).convert("RGB")
        zx, zt = ext.extract_pair(img)
        zx_all.append(zx); zt_all.append(zt); eids.append(eid)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path,
                        example_ids=np.array(eids),
                        zx=np.stack(zx_all), ztx=np.stack(zt_all),
                        backbone=backbone, adapter=adapter or "base")
    print(f"wrote {out_path}: n={len(eids)} dim={len(zx_all[0])}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", required=True,
                    choices=["qwen2vl_7b", "smolvlm2_2b"])
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--image-ids", required=True)
    ap.add_argument("--image-cache", default="data/image_cache")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    run_extraction(a.backbone, a.adapter, a.image_ids, a.image_cache,
                   a.out, a.device)
