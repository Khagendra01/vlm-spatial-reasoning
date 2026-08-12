"""
Patch-level probe: does orientation info survive at the patch level (position-
resolved), even if mean-pooling destroys it?

Method: train a logistic regression on ALL individual patch embeddings
(class label of the image), then aggregate per image by majority vote.
This allows spatial structure to be used through patch voting, without
modeling geometry explicitly.

Levels: vit patches (1280d) and merger patches (3584d).
"""
import os, sys, json
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from collections import Counter

OUT = Path("results/probe")

TASKS = {
    "T1_facing_vs_facingaway": ["facing", "facing away from"],
    "T2_parallel_vs_perp": ["parallel to", "perpendicular to"],
    "T3_4way": None,
}

def wilson_ci(correct, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0, center - margin), min(1, center + margin)

def main():
    import torch
    from PIL import Image
    import hashlib
    from datasets import load_dataset
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    MODEL = "Qwen/Qwen2-VL-7B-Instruct"
    ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
    CACHE = Path("data/image_cache")

    audit = {}
    with open("results/orientation_train_audit.csv") as f:
        import csv
        for r in csv.DictReader(f):
            audit[r["id"]] = r["final_status"].strip()

    # Collect examples
    examples = {}
    for split in ["train", "validation", "test"]:
        ds = load_dataset("cambridgeltl/vsr_random", split=split)
        for idx, r in enumerate(ds):
            if r["relation"] in ORIENT:
                examples[(split, idx)] = {
                    "split": split, "idx": idx, "relation": r["relation"],
                    "image": r["image_link"],
                }

    # Load model
    processor = AutoProcessor.from_pretrained(MODEL)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    model.eval()
    visual = model.model.visual

    # Extract per-image patch tensors
    def cache_path(url):
        return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

    keys = list(examples.keys())
    image_patches_vit = {}
    image_patches_mer = {}
    import time
    t0 = time.time()
    for start in range(0, len(keys), 4):
        bk = keys[start:start + 4]
        imgs = [Image.open(cache_path(examples[k]["image"])).convert("RGB") for k in bk]
        inputs = processor(images=imgs, return_tensors="pt")
        pv = inputs["pixel_values"].to("cuda", dtype=torch.bfloat16)
        grid = inputs["image_grid_thw"].to("cuda")
        with torch.inference_mode():
            out = visual(pv, grid_thw=grid)
            hs = out.last_hidden_state
            merged = visual.merger(hs)
        off_v = off_m = 0
        for k, g in zip(bk, grid.cpu().tolist()):
            t, h, w = g
            n_vit = t * h * w
            n_mer = t * (h // 2) * (w // 2)
            image_patches_vit[k] = hs[off_v:off_v + n_vit].float().cpu().numpy()
            image_patches_mer[k] = merged[off_m:off_m + n_mer].float().cpu().numpy()
            off_v += n_vit
            off_m += n_mer
        del inputs, out, hs, merged
        torch.cuda.empty_cache()
    print(f"Patch extraction done: {time.time()-t0:.0f}s "
          f"({sum(v.shape[0] for v in image_patches_vit.values())} vit patches)")

    results = {}
    lines = ["# Patch-Level Probe (majority vote over patch classifier)\n"]

    for level, patches in [("vit", image_patches_vit), ("merger", image_patches_mer)]:
        for task_name, classes in TASKS.items():
            sel = [k for k in keys if classes is None or examples[k]["relation"] in classes]
            tr = [k for k in sel if examples[k]["split"] == "train"
                  and audit.get(str(examples[k]["idx"]), "clean") != "exclude"]
            va = [k for k in sel if examples[k]["split"] == "validation"]
            te = [k for k in sel if examples[k]["split"] == "test"]
            class_names = classes if classes is not None else sorted(set(examples[k]["relation"] for k in sel))
            labels = {c: i for i, c in enumerate(class_names)}

            X_tr = np.concatenate([patches[k] for k in tr])
            y_tr = np.concatenate([[labels[examples[k]["relation"]]] * patches[k].shape[0] for k in tr])
            scaler = StandardScaler().fit(X_tr)
            X_tr = scaler.transform(X_tr)
            clf = LogisticRegression(max_iter=2000, C=1.0)
            clf.fit(X_tr, y_tr)
            print(f"{level}::{task_name} trained on {X_tr.shape[0]} patches")

            for split_name, keys_sel in [("val", va), ("test", te)]:
                preds = []
                for k in keys_sel:
                    X = scaler.transform(patches[k])
                    votes = clf.predict(X)
                    pred = Counter(votes.tolist()).most_common(1)[0][0]
                    preds.append(pred)
                y_true = [labels[examples[k]["relation"]] for k in keys_sel]
                acc = accuracy_score(y_true, preds)
                maj = max(Counter(y_true).values()) / len(y_true) if y_true else 0
                lo, hi = wilson_ci(int((np.array(preds) == np.array(y_true)).sum()), len(y_true))
                results[f"{level}::{task_name}::{split_name}"] = {
                    "acc": float(acc), "majority": float(maj), "ci": [lo, hi],
                }
                print(f"  {split_name}: acc={acc:.3f} majority={maj:.3f} CI=[{lo:.3f},{hi:.3f}]")

    with open(OUT / "patch_probe_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved:", OUT / "patch_probe_results.json")

if __name__ == "__main__":
    main()
