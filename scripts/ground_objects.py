"""Ground subject/reference objects with frozen Qwen2-VL-7B (manual box tokens).

Two batched passes (subject query for all images, then reference query),
one box per query for reliability.
Coordinate convention: Qwen2-VL outputs boxes in per-axis [0,1000] space
(x_norm = x_px * 1000 / w, y_norm = y_px * 1000 / h); rescale to pixels.
"""
import os, sys, json, re, time, hashlib
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")
from scripts.parse_orientation import parse_orientation_statement

import torch
from PIL import Image
from datasets import load_dataset
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

MODEL = "Qwen/Qwen2-VL-7B-Instruct"
ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
CACHE = Path("data/image_cache")
OUT = Path("results/probe/grounded_boxes.json")

def cache_path(url):
    return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

BOX_RE = re.compile(r"<\|box_start\|>\((-?\d+),\s*(-?\d+)\),\s*\((-?\d+),\s*(-?\d+)\)<\|box_end\|>")

def rescale_1000(box, w, h):
    if box is None:
        return None
    x1, y1, x2, y2 = box
    return [x1 * w / 1000.0, y1 * h / 1000.0, x2 * w / 1000.0, y2 * h / 1000.0]

def main():
    examples = {}
    for split in ["train", "validation", "test"]:
        ds = load_dataset("cambridgeltl/vsr_random", split=split)
        for idx, r in enumerate(ds):
            if r["relation"] in ORIENT:
                subj, rel, ref = parse_orientation_statement(r["caption"])
                if subj is None:
                    continue
                examples[(split, idx)] = {
                    "split": split, "idx": idx, "statement": r["caption"],
                    "subject": subj, "reference": ref, "url": r["image_link"],
                }
    print(f"Parsed {len(examples)} orientation examples")

    processor = AutoProcessor.from_pretrained(MODEL)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.eval()

    keys = list(examples.keys())
    boxes = {k: {"subject": None, "reference": None, "image_size": None} for k in keys}
    failures = {"no_box": 0}
    t0 = time.time()

    def run_queries(keys_subset, get_obj, tag):
        nonlocal failures
        for start in range(0, len(keys_subset), 4):
            batch = keys_subset[start:start + 4]
            imgs = [Image.open(cache_path(examples[k]["url"])).convert("RGB") for k in batch]
            texts = [f"Locate the {get_obj(k)} in this image. Return exactly one bounding "
                     f"box in the format <|box_start|>(x1,y1),(x2,y2)<|box_end|>."
                     for k in batch]
            msgs = [[{"role": "user", "content": [
                {"type": "image", "image": img}, {"type": "text", "text": t},
            ]}] for img, t in zip(imgs, texts)]
            inputs = processor.apply_chat_template(
                msgs, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt", padding=True,
            )
            inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}
            with torch.inference_mode():
                out = model.generate(**inputs, max_new_tokens=128, do_sample=False)
            decoded = processor.batch_decode(
                out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=False)
            for k, d in zip(batch, decoded):
                m = BOX_RE.search(d)
                if m is None:
                    failures["no_box"] += 1
                    continue
                x1, y1, x2, y2 = map(float, m.groups())
                w, h = boxes[k]["image_size"]
                boxes[k][tag] = rescale_1000([x1, y1, x2, y2], w, h)
            del inputs, out
            torch.cuda.empty_cache()
            if (start // 4) % 12 == 0:
                print(f"pass '{tag}' {start+len(batch)}/{len(keys_subset)} "
                      f"({time.time()-t0:.0f}s) failures={failures}", flush=True)

    # image sizes first
    for k in keys:
        img = Image.open(cache_path(examples[k]["url"]))
        boxes[k]["image_size"] = list(img.size)

    run_queries(keys, lambda k: examples[k]["subject"], "subject")
    run_queries(keys, lambda k: examples[k]["reference"], "reference")

    OUT.write_text(json.dumps({"examples": {f"{s}:{i}": e for (s, i), e in examples.items()},
                               "boxes": {f"{s}:{i}": b for (s, i), b in boxes.items()}},
                              indent=1))
    n_miss = sum(1 for b in boxes.values()
                 if b["subject"] is None or b["reference"] is None)
    print(f"Saved {len(boxes)} to {OUT}; missing-any={n_miss}; failures={failures}; "
          f"{time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
