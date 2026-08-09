"""
Re-evaluate probes + generative models on the "human-clear" test subset.

Motivation: a chunk of VSR orientation test labels are human-ambiguous
(annotation_questionable, camera_viewpoint_ambiguity, ...). Probe and
generative accuracy measured against disputed labels understates the
achievable ceiling. This script re-runs everything on subsets that keep only
human-clear examples (test split only; training untouched).

Variants:
  clear        = exclude annotation_questionable + camera_viewpoint_ambiguity
  strict       = also exclude intrinsic_orientation_ambiguous,
                 front_back_object_ambiguous, small_occluded_object

Methods re-evaluated (identical training as before, no test contamination):
  - ungrounded probes (vit/merger, linear/MLP) on T1/T2/T3
  - grounded visual probes (vit/merger, linear/MLP)
  - generative 7B zero-shot and General LoRA statement accuracy
"""
import os, sys, json, csv
from pathlib import Path

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

import numpy as np
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score

OUT = Path("results/probe")
ANNOT = "results/orientation_persistent_annotations.csv"
GEN_ZS = "results/qwen2vl_7b_predictions_20260809_064919.csv"
GEN_LORA = "results/7B_general_lora_predictions_20260809_094930.csv"

TASKS = {
    "T1_facing_vs_facingaway": ["facing", "facing away from"],
    "T2_parallel_vs_perp": ["parallel to", "perpendicular to"],
    "T3_4way": None,
}

# ── annotated test ids and modes ──
annotated = {}
with open(ANNOT) as f:
    for r in csv.DictReader(f):
        annotated[int(r["id"])] = r["annotation"].strip()

QUES = {"annotation_questionable", "camera_viewpoint_ambiguity"}
STRICT_EXTRA = {"intrinsic_orientation_ambiguous", "front_back_object_ambiguous",
                "small_occluded_object"}

# ── generative predictions (test ids = index in test split) ──
def load_gen(path):
    d = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            d[int(r["id"])] = r["correct"].strip() == "True"
    return d

gen_zs = load_gen(GEN_ZS)
gen_lora = load_gen(GEN_LORA)

def wilson_ci(correct, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0, center - margin), min(1, center + margin))

def eval_set(model, scaler, X, y, Xva, yva):
    """CV on train already done in caller; here fit train, predict test."""
    m = model()
    m.fit(scaler.transform(X), y)
    p = m.predict(scaler.transform(Xva))
    acc = float(accuracy_score(yva, p)) if len(yva) else 0.0
    bal = float(balanced_accuracy_score(yva, p)) if len(yva) else 0.0
    maj = max(Counter(yva.tolist()).values()) / len(yva) if len(yva) else 0.0
    lo, hi = wilson_ci(int((p == yva).sum()), len(yva)) if len(yva) else (0, 0)
    return acc, bal, maj, [lo, hi]

def main():
    # ── ungrounded features ──
    # per example: split, idx, relation, emb (mean-pooled)
    ungr = {}
    for level in ["vit", "merger"]:
        d = np.load(OUT / f"embeddings_{level}.npz", allow_pickle=True)
        ungr[level] = (d["emb"], d["split"], d["idx"], d["relation"])

    # ── grounded features (region-pooled visual) ──
    import pickle
    from scripts.run_grounded_probe import pool_region
    patch_data = pickle.load(open(OUT / "patch_embeddings.pkl", "rb"))
    gd = json.loads((OUT / "grounded_boxes.json").read_text())
    gboxes, gex = gd["boxes"], gd["examples"]
    audit = {}
    with open("results/orientation_train_audit.csv") as f:
        for r in csv.DictReader(f):
            audit[r["id"]] = r["final_status"].strip()

    d = np.load(OUT / "embeddings_vit.npz", allow_pickle=True)
    rel_by_key = {(sp, int(ix)): rl for sp, ix, rl in
                  zip(d["split"], d["idx"], d["relation"])}

    def grounded_rows(level):
        psize = {"vit": 14, "merger": 28}[level]
        rows = []
        for k, e in gex.items():
            sp, ix = k.split(":")
            ix = int(ix)
            r = rel_by_key.get((sp, ix))
            if r is None:
                continue
            b = gboxes[k]
            if b["subject"] is None or b["reference"] is None:
                continue
            pd = patch_data[(sp, ix)]
            gh, gw = pd[f"grid_{level}"]
            w, h = pd["size"]
            fv = pool_region(pd[level], b["subject"], gh, gw, w, h, psize)
            fr = pool_region(pd[level], b["reference"], gh, gw, w, h, psize)
            if fv is None or fr is None:
                continue
            rows.append((sp, ix, r, np.concatenate([fv, fr, fv - fr, fv * fr])))
        return rows

    results = {"variants": {"clear": sorted(QUES),
                            "strict": sorted(QUES | STRICT_EXTRA)}}
    out_lines = ["# Human-Clear Test Subset Evaluation\n",
                 "Annotated persistent-failure test ids excluded: "
                 f"{len(annotated)} total.\n",
                 f"- clear: 137 - 13 = 124 examples (exclude {sorted(QUES)})\n",
                 f"- strict: 137 - 23 = 114 examples (+ {sorted(STRICT_EXTRA)})\n"]

    for task_name, classes in TASKS.items():
        for variant in ["full", "clear", "strict"]:
            if variant == "full":
                excl = set()
            elif variant == "clear":
                excl = {i for i, m in annotated.items() if m in QUES}
            else:
                excl = {i for i, m in annotated.items() if m in QUES | STRICT_EXTRA}

            res = {}
            # ── ungrounded ──
            for level in ["vit", "merger"]:
                emb, sp, ix, rel = ungr[level]
                mask = np.ones(len(rel), dtype=bool)
                if classes is not None:
                    mask &= np.isin(rel, classes)
                te_mask = (sp == "test") & mask & ~np.isin(ix, list(excl))
                tr_mask = (sp == "train") & mask
                # audited-clean train
                clean = np.array([audit.get(str(i), "clean") != "exclude" for i in ix[tr_mask]])
                tr_mask_c = np.where(tr_mask)[0][clean]

                X_tr, y_tr = emb[tr_mask_c], rel[tr_mask_c]
                X_te, y_te = emb[te_mask], rel[te_mask]
                class_names = classes if classes is not None else sorted(set(rel[mask].tolist()))
                labels = {c: i for i, c in enumerate(class_names)}
                y_tr = np.array([labels[c] for c in y_tr])
                y_te = np.array([labels[c] for c in y_te])
                if len(X_te) == 0:
                    continue
                for mn, mf in [("linear", lambda: LogisticRegression(max_iter=2000, C=1.0)),
                               ("mlp", lambda: MLPClassifier(hidden_layer_sizes=(256,), max_iter=3000,
                                                             early_stopping=True, n_iter_no_change=20))]:
                    sc = StandardScaler().fit(X_tr)
                    acc, bal, maj, ci = eval_set(mf, sc, X_tr, y_tr, X_te, y_te)
                    res[f"ungrounded_{level}_{mn}"] = {"acc": acc, "bal": bal, "maj": maj, "ci": ci, "n": len(X_te)}

            # ── grounded ──
            for level in ["vit", "merger"]:
                rows = grounded_rows(level)
                tr = [r for r in rows if r[0] == "train" and audit.get(str(r[1]), "clean") != "exclude"
                      and (classes is None or r[2] in classes)]
                te = [r for r in rows if r[0] == "test" and r[1] not in excl
                      and (classes is None or r[2] in classes)]
                if not te:
                    continue
                class_names = classes if classes is not None else sorted(set(r[2] for r in rows))
                labels = {c: i for i, c in enumerate(class_names)}
                X_tr = np.stack([r[3] for r in tr]); y_tr = np.array([labels[r[2]] for r in tr])
                X_te = np.stack([r[3] for r in te]); y_te = np.array([labels[r[2]] for r in te])
                for mn, mf in [("linear", lambda: LogisticRegression(max_iter=2000, C=1.0)),
                               ("mlp", lambda: MLPClassifier(hidden_layer_sizes=(256,), max_iter=3000,
                                                             early_stopping=True, n_iter_no_change=20))]:
                    sc = StandardScaler().fit(X_tr)
                    acc, bal, maj, ci = eval_set(mf, sc, X_tr, y_tr, X_te, y_te)
                    res[f"grounded_{level}_{mn}"] = {"acc": acc, "bal": bal, "maj": maj, "ci": ci, "n": len(X_te)}

            # ── generative ──
            te_ids = [int(ix) for i, ix in enumerate(ix[te_mask])]
            if te_ids:
                for gname, g in [("gen_zeroshot", gen_zs), ("gen_lora", gen_lora)]:
                    n_c = sum(1 for i in te_ids if g.get(i, False))
                    acc = n_c / len(te_ids) if te_ids else 0
                    lo, hi = wilson_ci(n_c, len(te_ids))
                    res[gname] = {"acc": acc, "ci": [lo, hi], "n": len(te_ids)}
            results[f"{task_name}::{variant}"] = res
            print(f"{task_name} [{variant}] n={te_mask.sum()}")
            for k, v in sorted(res.items()):
                print(f"  {k}: acc={v['acc']:.3f} bal={v.get('bal', float('nan')):.3f} "
                      f"maj={v.get('maj', float('nan')):.3f} ci={v.get('ci')} n={v['n']}")
        out_lines.append(f"## {task_name}\n")
        out_lines.append("| method | full | clear (n) | strict (n) |")
        out_lines.append("|---|---|---|---|")
        for method in ["ungrounded_vit_linear", "ungrounded_vit_mlp",
                       "ungrounded_merger_linear", "ungrounded_merger_mlp",
                       "grounded_vit_linear", "grounded_vit_mlp",
                       "grounded_merger_linear", "grounded_merger_mlp",
                       "gen_zeroshot", "gen_lora"]:
            cells = []
            for v in ["full", "clear", "strict"]:
                r = results.get(f"{task_name}::{v}", {}).get(method)
                cells.append(f"{r['acc']:.3f} (n={r['n']})" if r else "-")
            out_lines.append(f"| {method} | " + " | ".join(cells) + " |")
        out_lines.append("")

    (OUT / "clear_subset_results.json").write_text(json.dumps(results, indent=1))
    (OUT / "clear_subset_report.md").write_text("\n".join(out_lines))
    print("Saved:", OUT / "clear_subset_results.json", OUT / "clear_subset_report.md")

if __name__ == "__main__":
    main()
