"""
Two-stage object-centric reasoning for orientation statements.

  Stage 1 (localize): frozen Qwen2-VL grounding -> subject/reference boxes.
  Stage 2 (reason):   explicit relation module over the localized geometry
                      and/or region features -> predicted relation.
  Decision: True  iff predicted_relation == claimed_relation.

Versions:
  A) geometry-only      : box centers, angle, relative position, sizes,
                          overlap, IoU, containment (no pixels).
  B) geometry + visual  : A + subject/reference region embeddings (merger
                          level, from the frozen encoder).

Compared against the 7B LM-only LoRA control (65.69% orientation) with
paired exact McNemar on the 137 orientation test statements.
"""
import os, sys, json, csv, pickle
from pathlib import Path
from collections import Counter

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from scipy.stats import binomtest

OUT = Path("results")
ORIENT = ["facing", "facing away from", "parallel to", "perpendicular to"]
REL = {r: i for i, r in enumerate(ORIENT)}

def geometry_features(bs, br, W, H):
    """Rich 2D geometry from subject/ref boxes in original pixels."""
    x1s, y1s, x2s, y2s = bs
    x1r, y1r, x2r, y2r = br
    ws, hs = x2s - x1s, y2s - y1s
    wr, hr = x2r - x1r, y2r - y1r
    cxs, cys = (x1s + x2s) / 2, (y1s + y2s) / 2
    cxr, cyr = (x1r + x2r) / 2, (y1r + y2r) / 2
    dx, dy = (cxr - cxs) / W, (cyr - cys) / H
    d = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)
    as_, ar = ws / max(hs, 1e-6), wr / max(hr, 1e-6)
    a_s, a_r = (ws * hs) / (W * H), (wr * hr) / (W * H)
    inter_w = max(0, min(x2s, x2r) - max(x1s, x1r))
    inter_h = max(0, min(y2s, y2r) - max(y1s, y1r))
    inter = inter_w * inter_h
    union = ws * hs + wr * hr - inter
    iou = inter / max(union, 1e-6)
    subj_in_ref = int(cxs >= x1r and cxs <= x2r and cys >= y1r and cys <= y2r)
    ref_in_subj = int(cxr >= x1s and cxr <= x2s and cyr >= y1s and cyr <= y2s)
    return np.array([
        cxs / W, cys / H, cxr / W, cyr / H,
        dx, dy, d, np.sin(theta), np.cos(theta),
        int(dx > 0), int(dy > 0), int(abs(dx) > abs(dy)),
        ws / W, hs / H, wr / W, hr / H,
        np.log(as_), np.log(ar),
        np.log(a_s + 1e-6), np.log(a_r + 1e-6),
        np.log((a_s + 1e-6) / (a_r + 1e-6)),
        inter / (W * H), iou,
        subj_in_ref, ref_in_subj,
    ], dtype=np.float64)

def mcnemar_p(a_correct, b_correct):
    b_ = sum(1 for x, y in zip(a_correct, b_correct) if x and not y)
    c_ = sum(1 for x, y in zip(a_correct, b_correct) if not x and y)
    n = b_ + c_
    if n == 0:
        return 1.0, b_, c_
    return float(binomtest(min(b_, c_), n, 0.5, alternative="two-sided").pvalue), b_, c_

def main():
    # ── Load ──
    gd = json.loads((OUT / "probe/grounded_boxes.json").read_text())
    boxes, examples = gd["boxes"], gd["examples"]
    with open(OUT / "probe/patch_embeddings.pkl", "rb") as f:
        patch_data = pickle.load(f)

    audit = {}
    with open("results/orientation_train_audit.csv") as f:
        for r in csv.DictReader(f):
            audit[r["id"]] = r["final_status"].strip()

    control = {}
    with open("results/7B_general_lora_predictions_20260809_094930.csv") as f:
        for r in csv.DictReader(f):
            if r["relation"] in ORIENT:
                control[int(r["id"])] = r["correct"] == "True"

    d = np.load(OUT / "probe/embeddings_vit.npz", allow_pickle=True)
    rel_by_key = {(sp, int(ix)): rl for sp, ix, rl in zip(d["split"], d["idx"], d["relation"])}

    def pool_region(es, box, gh, gw, W, H, psize=28):
        x1, y1, x2, y2 = box
        x1, x2 = min(max(x1, 0), W), min(max(x2, 0), W)
        y1, y2 = min(max(y1, 0), H), min(max(y2, 0), H)
        if x2 <= x1 or y2 <= y1:
            return None
        sx, sy = gw * psize / W, gh * psize / H
        x1, x2 = x1 * sx, x2 * sx
        y1, y2 = y1 * sy, y2 * sy
        cx = (np.arange(gw) + 0.5) * psize
        cy = (np.arange(gh) + 0.5) * psize
        mj = (cx >= x1) & (cx < x2)
        mi = (cy >= y1) & (cy < y2)
        rr, cc = np.where(np.outer(mi, mj))
        if len(rr) == 0:
            cxi = min(max(int(round(((x1 + x2) / 2) / psize - 0.5)), 0), gw - 1)
            cyi = min(max(int(round(((y1 + y2) / 2) / psize - 0.5)), 0), gh - 1)
            return es[cyi * gw + cxi]
        return es[rr * gw + cc].mean(axis=0)

    # ── Build rows ──
    data, n_no_box = [], 0
    for k, e in examples.items():
        sp, ix = k.split(":")
        ix = int(ix)
        rel = rel_by_key.get((sp, ix))
        if rel is None:
            continue
        b = boxes[k]
        if b["subject"] is None or b["reference"] is None:
            n_no_box += 1
            continue
        pd = patch_data[(sp, ix)]
        gh, gw = pd["grid_merger"]
        W, H = pd["size"]
        fv = pool_region(pd["merger"], b["subject"], gh, gw, W, H)
        fr = pool_region(pd["merger"], b["reference"], gh, gw, W, H)
        if fv is None or fr is None:
            n_no_box += 1
            continue
        data.append({"split": sp, "idx": ix, "relation": rel,
                     "geom": geometry_features(b["subject"], b["reference"], W, H),
                     "vis": np.concatenate([fv, fr, fv - fr, fv * fr])})
    print(f"Examples with boxes: {len(data)} (missing/degenerate: {n_no_box})")

    sets = {
        "A_geometry": lambda r: r["geom"],
        "B_geometry_visual": lambda r: np.concatenate([r["geom"], r["vis"]]),
    }

    results = {}
    mcn = {}
    for set_name, fextract in sets.items():
        X = np.stack([fextract(r) for r in data])
        y = np.array([REL[r["relation"]] for r in data])
        trm = np.array([r["split"] == "train" and audit.get(str(r["idx"]), "clean") != "exclude" for r in data])
        vam = np.array([r["split"] == "validation" for r in data])
        tem = np.array([r["split"] == "test" for r in data])
        X_tr, y_tr = X[trm], y[trm]
        X_va, y_va = X[vam], y[vam]
        X_te, y_te = X[tem], y[tem]
        te_rel = [r["relation"] for r in data if r["split"] == "test"]
        te_idx = [r["idx"] for r in data if r["split"] == "test"]
        print(f"\n=== {set_name}: train {X_tr.shape[0]} val {X_va.shape[0]} test {X_te.shape[0]} ===")

        for model_name, model_fn in [
            ("linear", lambda: LogisticRegression(max_iter=3000, C=1.0)),
            ("mlp", lambda: MLPClassifier(hidden_layer_sizes=(256,), max_iter=4000,
                                          early_stopping=True, n_iter_no_change=30)),
        ]:
            scaler = StandardScaler().fit(X_tr)
            Xtr, Xva, Xte = scaler.transform(X_tr), scaler.transform(X_va), scaler.transform(X_te)
            cv = []
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            for tri, vai in skf.split(Xtr, y_tr):
                m = model_fn()
                m.fit(Xtr[tri], y_tr[tri])
                cv.append(accuracy_score(y_tr[vai], m.predict(Xtr[vai])))
            m = model_fn()
            m.fit(Xtr, y_tr)
            yp_te = m.predict(Xte)
            yp_va = m.predict(Xva)

            claimed = np.array([REL[r] for r in te_rel])
            decision = yp_te == claimed
            label = np.array([1 if control.get(ix, False) else 0 for ix in te_idx])
            acc = accuracy_score(label, decision)
            per_rel = {}
            for rl in ORIENT:
                cm = np.array([r == rl for r in te_rel])
                if cm.sum():
                    per_rel[rl] = float(accuracy_score(label[cm], decision[cm]))

            key = f"{set_name}::{model_name}"
            results[key] = {
                "cv_rel_acc": float(np.mean(cv)), "cv_rel_std": float(np.std(cv)),
                "rel_4way_test_acc": float(accuracy_score(y_te, yp_te)),
                "rel_4way_test_bal": float(balanced_accuracy_score(y_te, yp_te)),
                "val_4way_acc": float(accuracy_score(y_va, yp_va)),
                "TF_overall": acc, "TF_per_relation": per_rel,
                "n_test": int(len(X_te)),
            }
            print(f"  {model_name}: 4way CV={np.mean(cv):.3f}±{np.std(cv):.3f} "
                  f"test={accuracy_score(y_te, yp_te):.3f} | TF overall={acc:.3f} "
                  f"per-rel={ {k: round(v,3) for k,v in per_rel.items()} }")

            # McNemar vs control on all 137 (no-box decisions count as wrong)
            all_137 = sorted(control.keys())
            c_corr = [control[ix] for ix in all_137]
            n_corr = [bool(decision[te_idx.index(ix)]) if ix in te_idx else False for ix in all_137]
            p, b_, c_ = mcnemar_p(c_corr, n_corr)
            mcn[key] = {"p": p, "ctrl_loss": b_, "ctrl_gain": c_}
            print(f"  McNemar vs control: p={p:.4f} (ctrl-loss {b_}, ctrl-gain {c_})")

    # ── Control reference ──
    test_rel = {int(ix): rl for sp, ix, rl in zip(d["split"], d["idx"], d["relation"]) if sp == "test"}
    ctrl_acc = {"overall": sum(control.values()) / len(control)}
    for rl in ORIENT:
        idxs = [ix for ix, r in test_rel.items() if r == rl]
        ctrl_acc[rl] = sum(control.get(ix, False) for ix in idxs) / len(idxs)
    print("\nControl (LM-only LoRA):", {k: round(v, 4) for k, v in ctrl_acc.items()})

    (OUT / "two_stage_results.json").write_text(json.dumps(
        {"results": results, "control": ctrl_acc, "mcnemar": mcn, "n_no_box": n_no_box},
        indent=2))
    print("Saved: results/two_stage_results.json")

if __name__ == "__main__":
    main()
