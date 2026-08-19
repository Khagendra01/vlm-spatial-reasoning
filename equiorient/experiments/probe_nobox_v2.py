"""Feature probe for v2_colorflip: measure decodability of each
attribute from frozen deepstack features.

For each attribute, trains a linear classifier on cell features and
reports held-out accuracy:

  1. target_location: which cell contains target a (the circle)?
  2. reference_location: which cell contains target b (the square)?
  3. shape: which cells contain circles vs squares vs distractors?
  4. color: which cells contain red vs blue vs gray objects?
  5. pair_relation: direction from b to a (8-way compass)

The probe uses ONLY the frozen Qwen3 vision features — no training,
no LoRA, no head. This tells us what information is AVAILABLE in the
features before any task-specific learning.

Usage:
    python -m equiorient.experiments.probe_nobox_v2 --data /path/to/v2data
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.label_action import LABELS
from equiorient.experiments.train_nobox import NoBoxRunner, load_manifest


def cell_grid(grid):
    """Return (h, w) of the cell grid from the image_grid_thw tensor."""
    return int(grid[0][1]), int(grid[0][2])


def pos_to_cell(x, y, h, w, canvas=192.0):
    """Map world coords to cell index."""
    cx = max(min(int(x / canvas * w), w - 1), 0)
    cy = max(min(int(y / canvas * h), h - 1), 0)
    return cy * w + cx


def probe_attribute(runner, manifest, split, attribute, n_max=300):
    """Probe a single attribute from frozen features.

    Returns dict with accuracy, chance baseline, n_examples.
    """
    examples = [e for e in manifest["examples"]
                if e["split"] == split and e["transform"] == "I"]
    if n_max:
        examples = examples[:n_max]

    feats_list = []
    labels_list = []
    n_processed = 0

    runner.model.eval()
    with torch.no_grad():
        for e in examples:
            feat, grid = runner.vision_features(e["png"], requires_grad=False)
            h, w = cell_grid(grid)
            T = h * w
            f = feat.float().cpu().numpy()  # (T, feat_dim)
            boxes = e["boxes"]

            if attribute == "target_location":
                # which cell is target a?
                ca = boxes["a"]
                y = pos_to_cell(ca[0], ca[1], h, w)
            elif attribute == "reference_location":
                # which cell is target b?
                cb = boxes["b"]
                y = pos_to_cell(cb[0], cb[1], h, w)
            elif attribute == "shape":
                # per-cell: 0=gray, 1=circle(a), 2=square(b)
                y_arr = np.zeros(T, dtype=int)
                # mark cells near a (circle) and b (square)
                for obj_id, color_expected, label_val in [
                    ("a", None, 1), ("b", None, 2)]:
                    ox, oy = boxes[obj_id][:2]
                    # find cells within the object radius
                    obj_info = None
                    for obj in (e.get("objects_list", []) or []):
                        if hasattr(obj, 'obj_id') and obj.obj_id == obj_id:
                            obj_info = obj
                            break
                    # use a radius heuristic from the box data
                    # boxes[obj_id] = [x, y, size]
                    size = boxes[obj_id][2] if len(boxes[obj_id]) > 2 else 4.0
                    for ci in range(T):
                        cell_x = (ci % w + 0.5) * 192.0 / w
                        cell_y = (ci // w + 0.5) * 192.0 / h
                        dist = math.hypot(cell_x - ox, cell_y - oy)
                        if dist < size * 1.5:
                            y_arr[ci] = label_val
                # replicate for all T cells
                labels_list.append(y_arr)
                feats_list.append(f)
                n_processed += 1
                continue
            elif attribute == "color":
                # per-cell: 0=gray, 1=red, 2=blue
                y_arr = np.zeros(T, dtype=int)
                # find red and blue objects
                from equiorient.data.scene_generator_nobox import (
                    TARGET_A_COLOR, TARGET_B_COLOR)
                for obj_id, expected_color, label_val in [
                    ("a", TARGET_A_COLOR, None), ("b", TARGET_B_COLOR, None)]:
                    ox, oy = boxes[obj_id][:2]
                    # determine actual color from the scene's variant
                    # For v2: color is random per scene, but stored in manifest
                    # We can detect from the rendered pixel or infer from
                    # the obj data. Since manifest doesn't store object color,
                    # we detect from the image center pixel at obj location.
                    # Simpler: use the fact that a and b are the ONLY colored
                    # objects. Red = whichever object has R channel > 150.
                    # For the probe, we check if the pixel at the obj center
                    # is reddish or bluish.
                    px, py = int(ox / 192.0 * w), int(oy / 192.0 * h)
                    # We don't have the raw pixel here. Use position heuristic
                    # or just mark "colored" vs "gray" for each object.
                    # Actually, for v2 we know: a=red/blue, b=blue/red.
                    # The probe doesn't need to know which — just that
                    # the two colored objects are distinguishable from gray.
                    # For COLOR probe: mark cells near ANY colored object.
                    # We can't distinguish red/blue from manifest alone.
                    # SKIP: use the rendered image pixel check.
                    pass
                labels_list.append(y_arr)
                feats_list.append(f)
                continue
            elif attribute == "pair_relation":
                # 8-way label of the scene
                y = LABELS.index(e["label"])
                labels_list.append(np.full(T, y, dtype=int))
                feats_list.append(f)
                continue
            else:
                raise ValueError(f"unknown attribute: {attribute}")

            labels_list.append(np.full(T, y, dtype=int))
            feats_list.append(f)
            n_processed += 1

    X = np.concatenate(feats_list, axis=0)  # (N_actual*T, feat_dim)
    if attribute in ("shape", "color"):
        Y = np.concatenate(labels_list, axis=0)  # (N_actual*T,)
    else:
        Y = np.concatenate(labels_list, axis=0)  # (N_actual*T,)

    # train/test split by scene
    n_scenes = n_processed
    n_tr = n_scenes // 2
    T = X.shape[0] // max(n_scenes, 1)
    Xtr = X[:n_tr * T]
    Ytr = Y[:n_tr * T]
    Xte = X[n_tr * T:]
    Yte = Y[n_tr * T:]
    n_t = n_scenes - n_tr

    if attribute in ("target_location", "reference_location"):
        # per-scene: find the top-1 cell prediction, check if it's correct
        sc = StandardScaler().fit(Xtr)
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(
            sc.transform(Xtr), Ytr)
        probs = clf.predict_proba(sc.transform(Xte))[:, 1].reshape(-1, T)
        # actually we need all classes for top-1
        probs_full = clf.predict_proba(sc.transform(Xte))
        n_classes = probs_full.shape[1]
        probs_reshaped = probs_full.reshape(-1, T, n_classes)
        correct = 0
        for k in range(n_t):
            pred_cell = int(probs_reshaped[k].mean(axis=0).argmax())
            true_cell = int(Yte[k * T])  # same for all cells in scene
            correct += int(pred_cell == true_cell)
        acc = correct / max(n_t, 1)
        chance = 1.0 / (T)  # random guess over cells
    elif attribute == "pair_relation":
        sc = StandardScaler().fit(Xtr)
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(
            sc.transform(Xtr), Ytr)
        probs = clf.predict_proba(sc.transform(Xte))
        # per-scene: majority vote across cells
        correct = 0
        for k in range(n_t):
            scene_probs = probs[k * T:(k + 1) * T].mean(axis=0)
            pred = int(scene_probs.argmax())
            true = int(Yte[k * T])
            correct += int(pred == true)
        acc = correct / max(n_t, 1)
        chance = 1.0 / 8
    elif attribute == "shape":
        sc = StandardScaler().fit(Xtr)
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(
            sc.transform(Xtr), Ytr)
        probs = clf.predict_proba(sc.transform(Xte))
        # per-cell accuracy
        pred = probs.argmax(axis=1)
        acc = float((pred == Yte).mean())
        # chance for 3-class imbalance
        from collections import Counter
        cnt = Counter(Yte.tolist())
        chance = max(cnt.values()) / len(Yte)
    else:
        acc = chance = 0.0

    return {"attribute": attribute, "accuracy": round(acc, 4),
            "chance": round(chance, 4), "n_scenes": n_t,
            "n_cells_per_scene": T}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to v2 data dir")
    ap.add_argument("--n_dev", type=int, default=300)
    ap.add_argument("--out", default="results/equiorient_no_box/probe_v2.json")
    a = ap.parse_args()

    data_dir = Path(a.data)
    manifest = load_manifest(data_dir)
    runner = NoBoxRunner(data_dir, Path("/dev/shm"))
    runner.load_model()

    attrs = ["target_location", "reference_location", "shape",
             "pair_relation"]
    results = {}
    for attr in attrs:
        print(f"Probing {attr}...", flush=True)
        r = probe_attribute(runner, manifest, "dev", attr, n_max=a.n_dev)
        results[attr] = r
        print(f"  {attr}: acc={r['accuracy']:.4f} chance={r['chance']:.4f}")

    out = {"data_dir": str(data_dir), "n_dev": a.n_dev,
           "results": results}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
