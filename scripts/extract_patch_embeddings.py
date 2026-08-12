"""Extract per-image patch embeddings (ViT + merger) for the 647 orientation
examples, saving spatial grids so region pooling is possible."""
import os, sys, time, hashlib, pickle
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import torch
from PIL import Image
from datasets import load_dataset
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

MODEL = "Qwen/Qwen2-VL-7B-Instruct"
ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
CACHE = Path("data/image_cache")
OUT = Path("results/probe/patch_embeddings.pkl")

def cache_path(url):
    return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def main():
    examples = {}
    for split in ["train", "validation", "test"]:
        ds = load_dataset("cambridgeltl/vsr_random", split=split)
        for idx, r in enumerate(ds):
            if r["relation"] in ORIENT:
                examples[(split, idx)] = r["image_link"]
    print(f"{len(examples)} orientation examples")

    processor = AutoProcessor.from_pretrained(MODEL)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.eval()
    visual = model.model.visual

    keys = list(examples.keys())
    data = {}
    t0 = time.time()
    for start in range(0, len(keys), 8):
        batch = keys[start:start + 8]
        imgs = [Image.open(cache_path(examples[k])).convert("RGB") for k in batch]
        inputs = processor(images=imgs, return_tensors="pt")
        pv = inputs["pixel_values"].to("cuda", dtype=torch.bfloat16)
        grid = inputs["image_grid_thw"].to("cuda")
        with torch.inference_mode():
            out = visual(pv, grid_thw=grid)
            hs = out.last_hidden_state
            merged = visual.merger(hs)
        off_v = off_m = 0
        for k, g in zip(batch, grid.cpu().tolist()):
            t, h, w = g
            n_vit = t * h * w
            n_mer = t * (h // 2) * (w // 2)
            img = Image.open(cache_path(examples[k]))
            data[k] = {
                "vit": hs[off_v:off_v + n_vit].float().cpu().numpy(),
                "merger": merged[off_m:off_m + n_mer].float().cpu().numpy(),
                "grid_vit": (h, w),
                "grid_merger": (h // 2, w // 2),
                "size": img.size,
            }
            off_v += n_vit
            off_m += n_mer
        del inputs, out, hs, merged
        torch.cuda.empty_cache()
        if (start // 8) % 10 == 0:
            print(f"{start+len(batch)}/{len(keys)} ({time.time()-t0:.0f}s)")
    with open(OUT, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved {len(data)} images to {OUT} in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
