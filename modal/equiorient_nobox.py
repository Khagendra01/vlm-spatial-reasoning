"""EquiOrient NO-BOX dev/confirmatory runner on Modal (serverless L40S).

Usage:
    python modal/equiorient_nobox.py --arm equiorient --seed 101 --n_train 128
    python modal/equiorient_nobox.py --mode dev --arm augmentation --seed 101
    python modal/equiorient_nobox.py --gate

Sandbox clones research/equiorient-no-box, rebuilds the deterministic
dataset into the data volume, runs the NO-BOX harness (train_nobox).
Results land in the results volume under /phase2_nobox/.
"""

from __future__ import annotations

import sys

import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "zip")
    .pip_install("torch==2.8.0+cu128", "torchvision==0.23.0+cu128",
                 index_url="https://download.pytorch.org/whl/cu128")
    .pip_install("transformers==4.57.6", "peft", "pillow", "pyyaml",
                 "scikit-learn")
)

app = modal.App("equiorient-nobox", image=image)

HF_CACHE = modal.Volume.from_name("equiorient-hf-cache", create_if_missing=True)
RESULTS = modal.Volume.from_name("equiorient-results", create_if_missing=True)
DATA = modal.Volume.from_name("equiorient-phase2-data", create_if_missing=True)

REPO_URL = "https://github.com/Khagendra01/vlm-spatial-reasoning.git"
BRANCH = "research/equiorient-no-box"
PINNED_COMMIT = ""  # empty = HEAD + recorded in results
SPARSE_CONE = ["equiorient", "modal", "configs", "cloud_setup"]


def _prepare(target_size: tuple = (3.0, 5.0),
             n_distractor_range: tuple = (12, 20),
             noise_amp: int = 12) -> str:
    import subprocess

    def run(cmd):
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"CMD FAILED {cmd[0]}\n{p.stderr[-2000:]}")
        return p

    dst = "/root/repo"
    run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
         "--sparse", "--branch", BRANCH, REPO_URL, dst])
    run(["git", "-C", dst, "sparse-checkout", "set", *SPARSE_CONE])
    head = run(["git", "-C", dst, "rev-parse", "HEAD"]).stdout.strip()
    if PINNED_COMMIT and head != PINNED_COMMIT:
        raise RuntimeError(f"PIN MISMATCH {head[:8]} != {PINNED_COMMIT}")
    sys.path.insert(0, dst)
    import shutil
    import equiorient.data.manifests_nobox as mf
    from pathlib import Path
    out = Path("/root/phase2_data")
    shutil.rmtree(out, ignore_errors=True)
    mf.build(out, n_dev=512, n_train=2048, n_val=512, n_test=1024,
             target_size=target_size,
             n_distractor_range=n_distractor_range,
             noise_amp=noise_amp)
    return head


@app.function(gpu="L40S",
              volumes={"/root/hf-cache": HF_CACHE,
                       "/root/results": RESULTS,
                       "/root/phase2_data": DATA},
              secrets=[modal.Secret.from_name("hf-token")],
              timeout=6 * 60 * 60)
def run_arm(arm: str, seed: int, n_train: int = 128, lam: float = 1.0,
            epochs: int = 2, batch: int = 8, mode: str = "dev",
            lr: float = 1e-4,
            target_size_min: float = 3.0, target_size_max: float = 5.0,
            n_dist_min: int = 12, n_dist_max: int = 20,
            noise_amp: int = 12) -> dict:
    import os
    os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]
    os.environ["HF_HOME"] = "/root/hf-cache"
    head = _prepare(target_size=(target_size_min, target_size_max),
                    n_distractor_range=(n_dist_min, n_dist_max),
                    noise_amp=noise_amp)
    import json
    from pathlib import Path
    out_dir = Path("/root/results") / "phase2_nobox"
    cmd = ["python", "-m", "equiorient.experiments.train_nobox",
           "--mode", mode,
           "--arm", arm, "--seed", str(seed),
           "--n_train", str(n_train), "--lambda", str(lam),
           "--epochs", str(epochs), "--batch", str(batch),
           "--lr", str(lr),
           "--data", "/root/phase2_data",
           "--out", str(out_dir)]
    import subprocess
    p = subprocess.run(cmd, capture_output=True, text=True, cwd="/root/repo")
    print(p.stdout[-4000:])
    if p.returncode != 0:
        print(p.stderr[-4000:])
        raise RuntimeError(f"train failed rc={p.returncode}")
    res = json.loads((out_dir / f"result_{arm}_s{seed}.json").read_text())
    res["repo_commit"] = head
    return res


@app.function(volumes={"/root/phase2_data": DATA},
              timeout=60 * 60)
def run_gate() -> dict:
    head = _prepare()
    import subprocess
    p = subprocess.run(["python", "-m", "equiorient.tests.test_nobox_gate"],
                       capture_output=True, text=True, cwd="/root/repo")
    print(p.stdout[-3000:])
    if p.returncode != 0:
        print(p.stderr[-3000:])
        raise RuntimeError("NO-BOX GATE FAILED in cloud")
    return {"gate": "PASS", "repo_commit": head}


@app.function(gpu="L40S",
              volumes={"/root/hf-cache": HF_CACHE,
                       "/root/results": RESULTS,
                       "/root/phase2_data": DATA},
              secrets=[modal.Secret.from_name("hf-token")],
              timeout=6 * 60 * 60)
def probe_features(n_dev: int = 200,
                   target_size_min: float = 3.0,
                   target_size_max: float = 5.0,
                   n_dist_min: int = 12, n_dist_max: int = 20,
                   noise_amp: int = 12) -> dict:
    """Linear-probe the frozen deepstack features for target-cell
    localizability WITHOUT any training.

    Asks: given the 64 (8x8) merged deepstack cell features of a scene,
    can a linear classifier trained on SOME scenes identify, in HELDOUT
    scenes, which cells contain target a / target b?

    Results (top-1 cell-pair recall) tell us whether the no-box pool can
    *in principle* learn to localize, or whether the visual features are
    the blocker (in which case difficulty must be relaxed: bigger
    targets, fewer distractors).
    """
    import os
    os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]
    os.environ["HF_HOME"] = "/root/hf-cache"
    head = _prepare(target_size=(target_size_min, target_size_max),
                    n_distractor_range=(n_dist_min, n_dist_max),
                    noise_amp=noise_amp)
    import json, torch
    import numpy as np
    from pathlib import Path
    from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
    from equiorient.experiments.train_nobox import NoBoxRunner, load_manifest

    mf_path = Path("/root/phase2_data/manifest.json")
    manifest = load_manifest(Path("/root/phase2_data"))
    runner = NoBoxRunner(Path("/root/phase2_data"), Path("/dev/shm"))
    runner.load_model()
    # collect cell features for the first n_dev train scenes (identity views)
    feats, y_cells = [], []
    n = 0
    with torch.no_grad():
        runner.model.eval()
        for e in manifest["examples"]:
            if e["split"] != "train" or e["transform"] != "I":
                continue
            if n >= n_dev:
                break
            feat, grid = runner.vision_features(e["png"], requires_grad=False)
            # feat: (T, 4096) post-merge (2D already); cell layout h x w
            h, w = int(grid[0][1]), int(grid[0][2])
            f = feat.float().cpu().numpy()  # (T, 4096)
            boxes = e["boxes"]
            ca = (max(min(int(boxes["a"][0] / 192.0 * w), w), 0),
                  max(min(int(boxes["a"][1] / 192.0 * h), h), 0))
            cb = (max(min(int(boxes["b"][0] / 192.0 * w), w), 0),
                  max(min(int(boxes["b"][1] / 192.0 * h), h), 0))
            ia = ca[1] * w + ca[0]
            ib = cb[1] * w + cb[0]
            feats.append(f)
            y_cells.append((ia, ib))
            n += 1
    X = np.concatenate(feats, axis=0)          # (n*T, 4096)
    T = X.shape[0] // n
    Y = np.zeros(len(X), dtype=int)
    for k, (ia, ib) in enumerate(y_cells):
        Y[k * T + ia] = 1
        Y[k * T + ib] = 1
    # train/test split by scene
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    n_tr = n // 2
    Xtr = X[:n_tr * T]
    Ytr = Y[:n_tr * T]
    Xte = X[n_tr * T:]
    Yte = Y[n_tr * T:]
    n_t = n - n_tr
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(Xtr), Ytr)
    probs = clf.predict_proba(sc.transform(Xte))[:, 1].reshape(-1, T)
    top_correct = 0
    for k, (ia, ib) in enumerate(y_cells[n_tr:]):
        top = set(np.argsort(-probs[k])[:2])
        if ia in top and ib in top:
            top_correct += 1
    linear_recall = top_correct / max(n_t, 1)

    # nonlinear probe: an MLP has much more capacity to learn "this cell
    # has a red/blue dot vs gray" — upper bound on localizability of the
    # frozen features regardless of the pooling head's architecture.
    from sklearn.neural_network import MLPClassifier
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300,
                        alpha=1e-3, random_state=0)
    mlp.fit(sc.transform(Xtr), Ytr)
    if hasattr(mlp, "predict_proba"):
        p2 = mlp.predict_proba(sc.transform(Xte))[:, 1].reshape(-1, T)
    else:
        p2 = mlp.predict(sc.transform(Xte)).astype(float).reshape(-1, T)
    top_correct2 = 0
    for k, (ia, ib) in enumerate(y_cells[n_tr:]):
        top = set(np.argsort(-p2[k])[:2])
        if ia in top and ib in top:
            top_correct2 += 1
    mlp_recall = top_correct2 / max(n_t, 1)

    return {"n_scenes": n_t, "T_cells": int(T),
            "linear_cell_pair_top2_recall": round(linear_recall, 4),
            "mlp_cell_pair_top2_recall": round(mlp_recall, 4),
            "pos_rate": round(float(Ytr.mean()), 4),
            "difficulty": {"target_size": [target_size_min, target_size_max],
                           "n_distractor_range": [n_dist_min, n_dist_max],
                           "noise_amp": noise_amp},
            "repo_commit": head,
            "explain": "top2 recall ~1.0 => features localizable; ~0 => not. "
                       "linear ~ probe of cross-attention strength; "
                       "mlp ~ upper bound for any learned pool."}


@app.local_entrypoint()
def main(arm: str = "equiorient", seed: int = 101, mode: str = "dev",
         n_train: int = 128, gate: bool = False, epochs: int = 2,
         lr: float = 1e-4, probe: bool = False,
         target_size_min: float = 3.0, target_size_max: float = 5.0,
         n_dist_min: int = 12, n_dist_max: int = 20,
         noise_amp: int = 12):
    if gate:
        print("GATE:", run_gate.remote())
        return
    if probe:
        print("PROBE:", probe_features.remote(
            target_size_min=target_size_min, target_size_max=target_size_max,
            n_dist_min=n_dist_min, n_dist_max=n_dist_max,
            noise_amp=noise_amp))
        return
    m = run_arm.remote(arm=arm, seed=seed, mode=mode, n_train=n_train,
                       epochs=epochs, lr=lr,
                       target_size_min=target_size_min,
                       target_size_max=target_size_max,
                       n_dist_min=n_dist_min, n_dist_max=n_dist_max,
                       noise_amp=noise_amp)
    print("RESULT:", m)


if __name__ == "__main__":
    sys.exit(main())
