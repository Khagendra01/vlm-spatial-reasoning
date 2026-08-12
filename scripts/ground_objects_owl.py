"""Fallback grounding with OWL-ViT (zero-shot object detection, no training)."""
import os, sys, json, time, hashlib
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import torch
from PIL import Image
from transformers import AutoProcessor, OwlViTForObjectDetection

CACHE = Path("data/image_cache")
OUT = Path("results/probe/grounded_boxes_owl.json")

def cache_path(url):
    return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def main():
    gd = json.loads(Path("results/probe/grounded_boxes.json").read_text())
    examples = gd["examples"]

    processor = AutoProcessor.from_pretrained("google/owlv2-base-patch16-ensemble")
    model = OwlViTForObjectDetection.from_pretrained(
        "google/owlv2-base-patch16-ensemble").to("cuda")
    model.eval()

    keys = list(examples.keys())
    out = {}
    t0 = time.time()
    for start in range(0, len(keys), 16):
        batch = [(k, examples[k]) for k in keys[start:start + 16]]
        imgs = [Image.open(cache_path(e["url"])).convert("RGB") for _, e in batch]
        texts = [[e["subject"], e["reference"]] for _, e in batch]
        inputs = processor(text=texts, images=imgs, return_tensors="pt")
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
        with torch.inference_mode():
            outputs = model(**inputs)
        target_sizes = torch.tensor([i.size[::-1] for i in imgs]).to("cuda")
        results = processor.post_process_object_detection(
            outputs=outputs, target_sizes=target_sizes, threshold=0.05)
        for (k, e), r in zip(batch, results):
            boxes = r["boxes"].tolist()
            scores = r["scores"].tolist()
            labels = r["labels"].tolist()
            # best box per query (0=subject, 1=reference)
            best = {0: None, 1: None}
            for bx, sc, lb in zip(boxes, scores, labels):
                if lb in best and (best[lb] is None or sc > best[lb][0]):
                    best[lb] = (sc, bx)
            out[k] = {
                "subject": best[0][1] if best[0] else None,
                "reference": best[1][1] if best[1] else None,
                "scores": {"subject": best[0][0] if best[0] else 0,
                           "reference": best[1][0] if best[1] else 0},
                "image_size": list(Image.open(cache_path(e["url"])).size),
            }
        if (start // 16) % 5 == 0:
            n_fail = sum(1 for v in out.values() if v["subject"] is None or v["reference"] is None)
            print(f"{start+len(batch)}/{len(keys)} failures={n_fail} ({time.time()-t0:.0f}s)")
    Path(OUT).write_text(json.dumps(out, indent=1))
    n_fail = sum(1 for v in out.values() if v["subject"] is None or v["reference"] is None)
    print(f"Done {len(out)}; total failures={n_fail}; saved {OUT}")

if __name__ == "__main__":
    main()
