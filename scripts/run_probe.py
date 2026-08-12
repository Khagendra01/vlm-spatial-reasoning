"""
Representation probe: how much orientation information is linearly (and
nonlinearly) accessible in the frozen 7B vision representation?

Tasks:
  T1: facing vs facing away        (binary)
  T2: parallel vs perpendicular    (binary)
  T3: 4-way orientation multiclass

Models:
  - Linear probe:  LogisticRegression (L2-normalized features)
  - Nonlinear:     MLPClassifier (1 hidden layer)

Procedure: 5-fold stratified CV on train; fit on full train; eval val + test.
No VSR test examples are used for training.
"""
import os, sys, json, csv
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from collections import Counter

OUT = Path("results/probe")

def wilson_ci(correct, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0, center - margin), min(1, center + margin)

TASKS = {
    "T1_facing_vs_facingaway": ["facing", "facing away from"],
    "T2_parallel_vs_perp": ["parallel to", "perpendicular to"],
    "T3_4way": None,  # all four
}

def load_level(name):
    d = np.load(OUT / f"embeddings_{name}.npz", allow_pickle=True)
    return d["emb"], d["split"], d["idx"], d["relation"]

def main():
    # â”€â”€ Audit status for train examples (from the hard-negative audit) â”€â”€
    audit = {}
    with open("results/orientation_train_audit.csv") as f:
        for r in csv.DictReader(f):
            audit[r["id"]] = r["final_status"].strip()

    # â”€â”€ Generative reference: 7B zero-shot predictions on test â”€â”€
    gen = {}
    with open("results/qwen2vl_7b_predictions_20260809_064919.csv") as f:
        for r in csv.DictReader(f):
            gen[r["id"]] = r
    gen_lora = {}
    with open("results/7B_general_lora_predictions_20260809_094930.csv") as f:
        for r in csv.DictReader(f):
            gen_lora[r["id"]] = r

    results = {"summary": {}, "tasks": {}}
    report_lines = []

    for level in ["vit", "merger"]:
        emb, split, idx, relation = load_level(level)

        for task_name, classes in TASKS.items():
            if classes is not None:
                mask = np.isin(relation, classes)
            else:
                mask = np.ones(len(relation), dtype=bool)

            X, y, sp, ix = emb[mask], relation[mask], split[mask], idx[mask]
            class_names = classes if classes is not None else sorted(set(y.tolist()))
            labels = {c: i for i, c in enumerate(class_names)}
            y_num = np.array([labels[c] for c in y])

            # Split by split
            tr = sp == "train"
            va = sp == "validation"
            te = sp == "test"

            X_tr, y_tr, ix_tr = X[tr], y_num[tr], ix[tr]
            X_va, y_va = X[va], y_num[va]
            X_te, y_te, ix_te = X[te], y_num[te], ix[te]

            # Filter train to audited-clean examples (final_status != exclude)
            clean_mask = np.array([audit.get(str(i), "clean") != "exclude" for i in ix_tr])
            X_tr_c, y_tr_c, ix_tr_c = X_tr[clean_mask], y_tr[clean_mask], ix_tr[clean_mask]

            n_tr = len(X_tr_c)
            majority = max(Counter(y_tr_c.tolist()).values()) / n_tr
            key = f"{level}::{task_name}"
            results["tasks"][key] = {"n_train": int(n_tr), "n_val": int(len(X_va)),
                                     "n_test": int(len(X_te)),
                                     "train_class_counts": dict(Counter(y_tr_c.tolist())),
                                     "majority_baseline": float(majority),
                                     "test_class_counts": dict(Counter(y_te.tolist()))}

            for model_name, model_fn in [
                ("linear", lambda: LogisticRegression(max_iter=2000, C=1.0)),
                ("mlp", lambda: MLPClassifier(hidden_layer_sizes=(256,), max_iter=3000,
                                              early_stopping=True, n_iter_no_change=20)),
            ]:
                # Normalize
                scaler = StandardScaler().fit(X_tr_c)
                Xtr = scaler.transform(X_tr_c)
                Xva = scaler.transform(X_va)
                Xte = scaler.transform(X_te)

                # 5-fold CV
                cv_accs = []
                skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                for tr_i, va_i in skf.split(Xtr, y_tr_c):
                    m = model_fn()
                    m.fit(Xtr[tr_i], y_tr_c[tr_i])
                    cv_accs.append(accuracy_score(y_tr_c[va_i], m.predict(Xtr[va_i])))
                cv_mean = float(np.mean(cv_accs))
                cv_std = float(np.std(cv_accs))

                # Full train
                m = model_fn()
                m.fit(Xtr, y_tr_c)

                val_acc = float(accuracy_score(y_va, m.predict(Xva)))
                val_bal = float(balanced_accuracy_score(y_va, m.predict(Xva)))

                test_pred = m.predict(Xte)
                test_acc = float(accuracy_score(y_te, test_pred))
                test_bal = float(balanced_accuracy_score(y_te, test_pred))
                per_class = {}
                for c in class_names:
                    cm = y_te == labels[c]
                    if cm.sum() > 0:
                        per_class[c] = float(accuracy_score(y_te[cm], test_pred[cm]))
                lo, hi = wilson_ci(int((test_pred == y_te).sum()), len(y_te))

                results["tasks"][key][model_name] = {
                    "cv_acc_mean": cv_mean, "cv_acc_std": cv_std,
                    "val_acc": val_acc, "val_balanced": val_bal,
                    "test_acc": test_acc, "test_balanced": test_bal,
                    "test_ci": [lo, hi], "per_class": per_class,
                }
                print(f"{key} [{model_name}] CV={cv_mean:.3f}+/-{cv_std:.3f} "
                      f"val={val_acc:.3f} test={test_acc:.3f} (bal {test_bal:.3f}) "
                      f"majority={majority:.3f} per_class={ {k: round(v,3) for k,v in per_class.items()} }")

            # â”€â”€ Generative reference on the SAME test images â”€â”€
            gen_acc, gen_acc_lora = {}, {}
            for c in class_names:
                ids_c = ix_te[y_te == labels[c]]
                correct = sum(1 for i in ids_c if gen[str(i)]["correct"] == "True")
                correct_l = sum(1 for i in ids_c if gen_lora[str(i)]["correct"] == "True")
                gen_acc[c] = correct / len(ids_c) if len(ids_c) else 0.0
                gen_acc_lora[c] = correct_l / len(ids_c) if len(ids_c) else 0.0
            results["tasks"][key]["generative_ref"] = {
                "7B_zeroshot_statement_acc": gen_acc,
                "7B_gen_lora_statement_acc": gen_acc_lora,
            }
            print(f"  generative 7B zero-shot statement acc on same images: { {k: round(v,3) for k,v in gen_acc.items()} }")

    # â”€â”€ Write JSON + report â”€â”€
    with open(OUT / "probe_results.json", "w") as f:
        json.dump(results, f, indent=2)

    lines = ["# Representation Probe: Orientation Information in Frozen 7B Vision Representation\n",
             "Extraction: Qwen2-VL-7B-Instruct base (no LoRA), frozen vision tower.",
             "Levels: ViT patch embeddings (1280d, mean-pooled) | post-merger features (3584d, mean-pooled).",
             "Train: audited-clean VSR train orientation examples | Val: VSR validation | Test: VSR test (137).",
             "No VSR test examples used for training.\n"]
    for key in results["tasks"]:
        t = results["tasks"][key]
        level, task = key.split("::")
        lines.append(f"## {task} ({level})  n_train={t['n_train']} n_test={t['n_test']} majority={t['majority_baseline']:.2f}")
        lines.append("| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |")
        lines.append("|---|---|---|---|---|---|")
        for mn in ["linear", "mlp"]:
            m = t[mn]
            lines.append(f"| {mn} | {m['cv_acc_mean']:.3f}Â±{m['cv_acc_std']:.3f} | {m['val_acc']:.3f} | "
                         f"{m['test_acc']:.3f} | {m['test_balanced']:.3f} | [{m['test_ci'][0]:.3f}, {m['test_ci'][1]:.3f}] |")
        lines.append("")
        lines.append("Per-class test accuracy:")
        for mn in ["linear", "mlp"]:
            pc = ", ".join(f"{k}: {v:.3f}" for k, v in t[mn]["per_class"].items())
            lines.append(f"- {mn}: {pc}")
        gen_ref = t.get("generative_ref", {})
        if gen_ref:
            zs = ", ".join(f"{k}: {v:.3f}" for k, v in gen_ref["7B_zeroshot_statement_acc"].items())
            gl = ", ".join(f"{k}: {v:.3f}" for k, v in gen_ref["7B_gen_lora_statement_acc"].items())
            lines.append(f"- Generative 7B zero-shot statement accuracy on same images: {zs}")
            lines.append(f"- Generative 7B General LoRA statement accuracy on same images: {gl}")
        lines.append("")

    lines.append("""## Interpretation guide
- Linear probe >> chance AND >> generative decision on same images:
  orientation info IS in the frozen representation; the generative pathway fails to use it.
- Linear weak but MLP strong: info present but not linearly accessible.
- Both weak: representation itself lacks orientation info (shift to vision-side adaptation).
- Note: probe classifies the RELATION (facing vs facing-away, etc.); the generative
  reference is statement-truth accuracy (True/False) on the same images. Tasks differ,
  so the comparison is indicative, not exact.
""")
    (OUT / "probe_report.md").write_text("\n".join(lines))
    print("Saved:", OUT / "probe_results.json", OUT / "probe_report.md")

if __name__ == "__main__":
    main()
