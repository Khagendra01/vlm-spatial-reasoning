"""
Extract frozen vision-encoder embeddings for all VSR orientation examples
(train/validation/test) from the 7B base model (NO LoRA).

Two representation levels per image:
  1. ViT patch embeddings (mean-pooled, 1280-dim)  -- pure vision tower output
  2. Post-merger features (mean-pooled, 3584-dim)  -- exactly what the LLM receives

Saves: results/probe/embeddings_vit.npz and embeddings_merger.npz
"""
import os, sys, csv, time, hashlib
from pathlib import Path
from collections import Counter

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
CACHE = Path("data/image_cache")
OUT = Path("results/probe")
OUT.mkdir(parents=True, exist_ok=True)

def cache_path(url):
    return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def main():
    import numpy as np
    import torch
    import urllib.request
    from io import BytesIO
    from PIL import Image
    from datasets import load_dataset
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    MODEL = "Qwen/Qwen2-VL-7B-Instruct"

    # â”€â”€ Collect examples â”€â”€
    examples = {}  # key: (split, idx)
    for split in ["train", "validation", "test"]:
        ds = load_dataset("cambridgeltl/vsr_random", split=split)
        for idx, r in enumerate(ds):
            if r["relation"] not in ORIENT:
                continue
            examples[(split, idx)] = {
                "split": split, "idx": idx, "statement": r["caption"],
                "relation": r["relation"], "label": bool(r["label"]),
                "image": r["image_link"],
            }
    print(f"Total orientation examples: {len(examples)}")
    print(Counter(k[0] for k in examples))

    # Download missing images (val split not pre-downloaded)
    missing = [(k, v) for k, v in examples.items() if not cache_path(v["image"]).exists()]
    print(f"Missing images: {len(missing)}")
    for k, v in missing:
        try:
            req = urllib.request.Request(v["image"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            Image.open(BytesIO(data)).convert("RGB").save(cache_path(v["image"]), "JPEG", quality=95)
        except Exception as e:
            print(f"FAIL {k}: {e}")

    # â”€â”€ Load model â”€â”€
    processor = AutoProcessor.from_pretrained(MODEL)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.eval()
    visual = model.model.visual
    print(f"Model loaded: {torch.cuda.memory_allocated()/1e9:.1f}GB")

    # â”€â”€ Extract embeddings in batches â”€â”€
    keys = list(examples.keys())
    all_vit, all_merger = [], []
    t0 = time.time()
    for start in range(0, len(keys), 8):
        batch_keys = keys[start:start + 8]
        imgs = []
        for k in batch_keys:
            p = cache_path(examples[k]["image"])
            imgs.append(Image.open(p).convert("RGB"))
        inputs = processor(images=imgs, return_tensors="pt")
        pv = inputs["pixel_values"].to("cuda", dtype=torch.bfloat16)
        grid = inputs["image_grid_thw"].to("cuda")
        with torch.inference_mode():
            out = visual(pv, grid_thw=grid)
            hs = out.last_hidden_state  # (total_patches, 1280)
            merged = visual.merger(hs)  # (total_patches_merged, 3584)
        # split per image using grid
        vit_parts, mer_parts = [], []
        off_v, off_m = 0, 0
        for g in grid.cpu().tolist():
            t, h, w = g
            n_vit = t * h * w
            n_mer = t * (h // 2) * (w // 2)  # merger does 2x2 spatial patch merge
            vit_parts.append(hs[off_v:off_v + n_vit].mean(dim=0))
            off_v += n_vit
            mer_parts.append(merged[off_m:off_m + n_mer].mean(dim=0))
            off_m += n_mer
        assert off_v == hs.shape[0], f"ViT split mismatch: {off_v} != {hs.shape[0]}"
        assert off_m == merged.shape[0], f"merger split mismatch: {off_m} != {merged.shape[0]}"
        all_vit.extend(vit_parts)
        all_merger.extend(mer_parts)
        del inputs, out, hs, merged
        torch.cuda.empty_cache()
        if (start // 8 + 1) % 20 == 0:
            print(f"  [{start+len(batch_keys)}/{len(keys)}] {time.time()-t0:.0f}s")
    print(f"Extraction done: {time.time()-t0:.0f}s")

    # â”€â”€ Organize â”€â”€
    out_data = {
        "split": [], "idx": [], "relation": [], "statement": [],
        "label": [], "image": [],
    }
    for k in keys:
        m = examples[k]
        out_data["split"].append(m["split"])
        out_data["idx"].append(m["idx"])
        out_data["relation"].append(m["relation"])
        out_data["statement"].append(m["statement"])
        out_data["label"].append(m["label"])
        out_data["image"].append(m["image"])

    vit = torch.stack(all_vit).float().cpu().numpy()
    merger = torch.stack(all_merger).float().cpu().numpy()
    print("vit:", vit.shape, "merger:", merger.shape)

    np.savez_compressed(OUT / "embeddings_vit.npz",
                        emb=vit, split=np.array(out_data["split"]),
                        idx=np.array(out_data["idx"]), relation=np.array(out_data["relation"]),
                        statement=np.array(out_data["statement"]),
                        label=np.array(out_data["label"]))
    np.savez_compressed(OUT / "embeddings_merger.npz",
                        emb=merger, split=np.array(out_data["split"]),
                        idx=np.array(out_data["idx"]), relation=np.array(out_data["relation"]),
                        statement=np.array(out_data["statement"]),
                        label=np.array(out_data["label"]))
    print("Saved:", OUT / "embeddings_vit.npz", OUT / "embeddings_merger.npz")

if __name__ == "__main__":
    main()
