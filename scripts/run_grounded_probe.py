"""
Object-grounded representation probe.

For each orientation example, use grounded bounding boxes (subject + reference
object, from frozen Qwen2-VL grounding) to pool region features instead of
mean-pooling the whole image.

Feature sets (kept SEPARATE):
  F_vis  = [subj, ref, subj - ref, subj * ref]     (region-pooled embeddings)
  F_geom = normalized geometry: centers, dx/dy, widths/heights, rel size, IoU
  F_vis_geom = concat(F_vis, F_geom)

Probes: linear LR + small MLP. Tasks: T1 facing/facing-away, T2 parallel/perp,
T3 4-way. Same splits as the ungrounded probe: train = audited-clean, val, test.
"""
import os, sys, json, csv
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import numpy as np
import torch
from PIL import Image
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score

OUT = Path("results/probe")
DIMS = {"vit": 1280, "merger": 3584}

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

def pool_region(emb, box, gh, gw, orig_w, orig_h, patch_size):
    """emb: (gh*gw, d) patch embeddings row-major. box: [x1,y1,x2,y2] in original pixels."""
    if box is None:
        return None
    x1, y1, x2, y2 = box
    x1, x2 = min(max(x1, 0), orig_w), min(max(x2, 0), orig_w)
    y1, y2 = min(max(y1, 0), orig_h), min(max(y2, 0), orig_h)
    if x2 <= x1 or y2 <= y1:
        return None
    sx = gw * patch_size / orig_w
    sy = gh * patch_size / orig_h
    x1, x2 = x1 * sx, x2 * sx
    y1, y2 = y1 * sy, y2 * sy
    # patch (i,j) covers [i*ps,(i+1)*ps) x [j*ps,(j+1)*ps); select centers inside box
    js = np.arange(gw)
    is_ = np.arange(gh)
    cx = (js + 0.5) * patch_size
    cy = (is_ + 0.5) * patch_size
    mj = (cx >= x1) & (cx < x2)
    mi = (cy >= y1) & (cy < y2)
    rows, cols = np.where(np.outer(mi, mj))
    if len(rows) == 0:
        cxi = int(round(((x1 + x2) / 2) / patch_size - 0.5))
        cyi = int(round(((y1 + y2) / 2) / patch_size - 0.5))
        cxi = min(max(cxi, 0), gw - 1)
        cyi = min(max(cyi, 0), gh - 1)
        return emb[cyi * gw + cxi]
    idx = rows * gw + cols
    return emb[idx].mean(axis=0)

def main():
    import hashlib
    from datasets import load_dataset
    from transformers import AutoProcessor

    CACHE = Path("data/image_cache")

    def cache_path(url):
        return CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

    # â”€â”€ Load groundings â”€â”€
    gd = json.loads((OUT / "grounded_boxes.json").read_text())
    boxes = gd["boxes"]
    examples = gd["examples"]

    # â”€â”€ Audit status â”€â”€
    audit = {}
    with open("results/orientation_train_audit.csv") as f:
        for r in csv.DictReader(f):
            audit[r["id"]] = r["final_status"].strip()

    # â”€â”€ Load per-image patch data â”€â”€
    import pickle
    with open(OUT / "patch_embeddings.pkl", "rb") as f:
        patch_data = pickle.load(f)
    # patch_data[(split, idx)] = {"vit": (N,1280), "merger": (N,3584),
    #                             "grid_vit": (h,w), "grid_merger": (h2,w2), "size": (w,h)}

    # index maps for relation lookup
    d = np.load(OUT / "embeddings_vit.npz", allow_pickle=True)
    split_all, idx_all, rel_all = d["split"], d["idx"], d["relation"]
    rel_by_key = {(sp, int(ix)): rl for sp, ix, rl in zip(split_all, idx_all, rel_all)}

    failures = {"no_box": 0, "fallback": 0}
    results = {}
    for level, feat_dim in DIMS.items():
        psize = {"vit": 14, "merger": 28}[level]
        for task_name, classes in TASKS.items():
            rows = []
            for k, e in examples.items():
                sp, ix = k.split(":")
                ix = int(ix)
                r = rel_by_key.get((sp, ix))
                if r is None:
                    continue
                if classes is not None and r not in classes:
                    continue
                b = boxes[k]
                subj, ref = b.get("subject"), b.get("reference")
                if subj is None or ref is None:
                    failures["no_box"] += 1
                    continue
                pd = patch_data[(sp, ix)]
                es = pd[level]
                gh, gw = pd[f"grid_{level}"]
                ow, oh = pd["size"]
                fv = pool_region(es, subj, gh, gw, ow, oh, psize)
                fr = pool_region(es, ref, gh, gw, ow, oh, psize)
                if fv is None or fr is None:
                    failures["no_box"] += 1
                    continue
                rows.append({"split": sp, "idx": ix, "relation": r,
                             "subj": fv, "ref": fr,
                             "box_s": subj, "box_r": ref, "img": (ow, oh)})
            print(f"[{level}] {task_name}: {len(rows)} examples, failures={failures}")

            # feature sets
            feats = {}
            for r in rows:
                s, o = r["subj"], r["ref"]
                vis = np.concatenate([s, o, s - o, s * o])
                ge = r["box_s"] + r["box_r"]
                # normalized geometry: subject
                x1s, y1s, x2s, y2s = ge[0], ge[1], ge[2], ge[3]
                x1r, y1r, x2r, y2r = ge[4], ge[5], ge[6], ge[7]
                W, H = r["img"]
                ws, hs = x2s - x1s, y2s - y1s
                wr, hr = x2r - x1r, y2r - y1r
                cxs, cys = (x1s + x2s) / 2 / W, (y1s + y2s) / 2 / H
                cxr, cyr = (x1r + x2r) / 2 / W, (y1r + y2r) / 2 / H
                dx, dy = cxr - cxs, cyr - cys
                rel_size = np.log((ws * hs + 1) / (wr * hr + 1))
                inter_w = max(0, min(x2s, x2r) - max(x1s, x1r))
                inter_h = max(0, min(y2s, y2r) - max(y1s, y1r))
                inter = inter_w * inter_h
                union = ws * hs + wr * hr - inter
                iou = inter / max(union, 1e-6)
                geom = np.array([cxs, cys, cxr, cyr, dx, dy,
                                 ws / W, hs / H, wr / W, hr / H, rel_size, iou])
                r["f_vis"] = vis
                r["f_geom"] = geom

            tr = [r for r in rows if r["split"] == "train"
                  and audit.get(str(r["idx"]), "clean") != "exclude"]
            va = [r for r in rows if r["split"] == "validation"]
            te = [r for r in rows if r["split"] == "test"]
            class_names = classes if classes is not None else sorted(set(r["relation"] for r in rows))
            labels = {c: i for i, c in enumerate(class_names)}

            for featset, key in [("f_vis", "visual"),
                                 ("f_geom", "geometry"),
                                 ("vis_geom", "visual_geometry")]:
                def getX(r):
                    if key == "visual_geometry":
                        return np.concatenate([r["f_vis"], r["f_geom"]])
                    return r[featset]
                X_tr = np.stack([getX(r) for r in tr])
                y_tr = np.array([labels[r["relation"]] for r in tr])
                X_va = np.stack([getX(r) for r in va]) if va else np.zeros((0, X_tr.shape[1]))
                y_va = np.array([labels[r["relation"]] for r in va]) if va else np.zeros(0, dtype=int)
                X_te = np.stack([getX(r) for r in te]) if te else np.zeros((0, X_tr.shape[1]))
                y_te = np.array([labels[r["relation"]] for r in te]) if te else np.zeros(0, dtype=int)

                n_tr = len(X_tr)
                majority = max(Counter(y_tr.tolist()).values()) / n_tr if n_tr else 0
                rkey = f"{level}::{task_name}::{key}"
                results[rkey] = {"n_train": int(n_tr), "n_val": int(len(X_va)),
                                 "n_test": int(len(X_te)), "majority": float(majority),
                                 "dim": int(X_tr.shape[1])}

                for model_name, model_fn in [
                    ("linear", lambda: LogisticRegression(max_iter=2000, C=1.0)),
                    ("mlp", lambda: MLPClassifier(hidden_layer_sizes=(256,), max_iter=3000,
                                                  early_stopping=True, n_iter_no_change=20)),
                ]:
                    scaler = StandardScaler().fit(X_tr)
                    Xtr = scaler.transform(X_tr)
                    Xva = scaler.transform(X_va)
                    Xte = scaler.transform(X_te)
                    cv_accs = []
                    if n_tr >= 10:
                        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                        for tr_i, va_i in skf.split(Xtr, y_tr):
                            m = model_fn()
                            m.fit(Xtr[tr_i], y_tr[tr_i])
                            cv_accs.append(accuracy_score(y_tr[va_i], m.predict(Xtr[va_i])))
                    m = model_fn()
                    m.fit(Xtr, y_tr)
                    test_pred = m.predict(Xte)
                    test_acc = float(accuracy_score(y_te, test_pred)) if len(y_te) else 0
                    test_bal = float(balanced_accuracy_score(y_te, test_pred)) if len(y_te) else 0
                    lo, hi = wilson_ci(int((test_pred == y_te).sum()), len(y_te)) if len(y_te) else (0, 0)
                    per_class = {}
                    for c in class_names:
                        cm = y_te == labels[c]
                        if cm.sum() > 0:
                            per_class[c] = float(accuracy_score(y_te[cm], test_pred[cm]))
                    results[rkey][model_name] = {
                        "cv_acc_mean": float(np.mean(cv_accs)) if cv_accs else None,
                        "cv_acc_std": float(np.std(cv_accs)) if cv_accs else None,
                        "val_acc": float(accuracy_score(y_va, m.predict(Xva))) if len(y_va) else None,
                        "test_acc": test_acc, "test_balanced": test_bal,
                        "test_ci": [lo, hi], "per_class": per_class,
                    }
                    print(f"  {rkey} [{model_name}] CV={results[rkey][model_name]['cv_acc_mean']} "
                          f"test={test_acc:.3f} (bal {test_bal:.3f}) maj={majority:.3f} "
                          f"per_class={ {k: round(v,3) for k,v in per_class.items()} }")

    (OUT / "grounded_probe_results.json").write_text(json.dumps(results, indent=2))
    print("Saved:", OUT / "grounded_probe_results.json")

if __name__ == "__main__":
    main()
