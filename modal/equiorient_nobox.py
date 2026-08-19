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


def _data_key(target_size: tuple, n_distractor_range: tuple,
              noise_amp: int) -> str:
    """Deterministic key for a difficulty config. Identical data across
    arms/seeds (matched-arm contract) is guaranteed by (generator seed,
    key) => one canonical build."""
    import hashlib
    return hashlib.sha256(
        f"{target_size}|{n_distractor_range}|{noise_amp}".encode()
    ).hexdigest()[:12]


# ------------------------------------------------------------------ #
# CPU-ONLY data builder. NEVER pays GPU rates for PNG rendering.
# ------------------------------------------------------------------ #
@app.function(volumes={"/root/phase2_data": DATA},
              timeout=60 * 30)
def prepare_data(target_size_min: float = 3.0, target_size_max: float = 5.0,
                 n_dist_min: int = 12, n_dist_max: int = 20,
                 noise_amp: int = 12,
                 n_dev: int = 512, n_train: int = 2048,
                 n_val: int = 512, n_test: int = 1024) -> dict:
    """Clone repo + render the deterministic dataset ON CPU.

    Stores under /root/phase2_data/<key>/ so every arm/seed of a frozen
    confirmatory config reuses the exact same img/PNG files (matched
    examples) instead of rebuilding per GPU run. Returns the data key
    that the GPU runner must consume as --data.
    """
    import subprocess, shutil
    from pathlib import Path

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

    ts = (target_size_min, target_size_max)
    nd = (n_dist_min, n_dist_max)
    key = _data_key(ts, nd, noise_amp)
    out = Path("/root/phase2_data") / key
    if (out / "manifest.json").exists():          # idempotent: same key, no rebuild
        return {"data_key": key, "rebuilt": False, "repo_commit": head,
                "n_examples": int(0)}

    tmp = Path("/root/phase2_data") / f"_tmp_{key}"
    shutil.rmtree(tmp, ignore_errors=True)
    import equiorient.data.manifests_nobox as mf
    mf.build(tmp, n_dev=n_dev, n_train=n_train, n_val=n_val,
             n_test=n_test, target_size=ts,
             n_distractor_range=nd, noise_amp=noise_amp)
    shutil.rmtree(out, ignore_errors=True)        # atomic-ish swap
    tmp.rename(out)
    import json
    return {"data_key": key, "rebuilt": True, "repo_commit": head,
            "n_examples": int(
                len(json.loads((out / "manifest.json").read_text())["examples"]))}


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
            noise_amp: int = 12, data_key: str = "") -> dict:
    import os
    os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]
    os.environ["HF_HOME"] = "/root/hf-cache"
    # data must ALREADY exist in the volume (build on CPU once via
    # prepare_data); if a caller supplies no key, resolve from config. This
    # path NEVER renders PNGs on a billed GPU container.
    import hashlib, shutil
    from pathlib import Path
    ts = (target_size_min, target_size_max)
    nd = (n_dist_min, n_dist_max)
    key = data_key or _data_key(ts, nd, noise_amp)
    data_src = Path("/root/phase2_data") / key
    if not (data_src / "manifest.json").exists():
        raise RuntimeError(
            f"data_key {key} missing — call prepare_data first")
    data_dir = str(data_src)      # harness reads PNGs relative to data_dir
    head = ""
    import subprocess
    dst = "/root/repo"
    if not (Path(dst) / "equiorient").exists():
        def run(cmd):
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                raise RuntimeError(
                    f"CMD FAILED {cmd[0]}\n{p.stderr[-2000:]}")
            return p
        run(["git", "clone", "--quiet", "--depth", "1",
             "--filter=blob:none", "--sparse", "--branch", BRANCH,
             REPO_URL, dst])
        run(["git", "-C", dst, "sparse-checkout", "set", *SPARSE_CONE])
        if PINNED_COMMIT and head != PINNED_COMMIT:
            raise RuntimeError(f"PIN MISMATCH {head[:8]}")
    head = subprocess.run(
        ["git", "-C", dst, "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd="/root/repo").stdout.strip()
    sys.path.insert(0, "/root/repo")
    import json
    out_dir = Path("/root/results") / "phase2_nobox"
    cmd = ["python", "-m", "equiorient.experiments.train_nobox",
           "--mode", mode,
           "--arm", arm, "--seed", str(seed),
           "--n_train", str(n_train), "--lambda", str(lam),
           "--epochs", str(epochs), "--batch", str(batch),
           "--lr", str(lr),
           "--data", data_dir,
           "--out", str(out_dir)]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd="/root/repo")
    print(p.stdout[-4000:])
    if p.returncode != 0:
        print(p.stderr[-4000:])
        raise RuntimeError(f"train failed rc={p.returncode}")
    res = json.loads((out_dir / f"result_{arm}_s{seed}.json").read_text())
    res["repo_commit"] = head
    res["data_key"] = key
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
         noise_amp: int = 12,
         array: str = "", seeds: str = "", batch_parallel: int = 100):
    """Suggested confirmatory invocations:
      python modal/equiorient_nobox.py --array \
          --mode confirmatory --n-train 128 --epochs 40 --lr 0.0005 \
          --target-size-min 4.0 --target-size-max 7.0 \
          --n-dist-min 6 --n-dist-max 10 --noise-amp 8
    --array: comma list of arms (default augmentation,equiorient,wrong_geometry)
    --seeds: comma list (default primary 15 seeds 101..1501)
    --batch-parallel: max concurrent Modal function calls (Modal bills
        per-running function second; queueing is free).
    """
    if gate:
        print("GATE:", run_gate.remote())
        return
    if probe:
        print("PROBE:", probe_features.remote(
            target_size_min=target_size_min, target_size_max=target_size_max,
            n_dist_min=n_dist_min, n_dist_max=n_dist_max,
            noise_amp=noise_amp))
        return
    if not array:
        prep = prepare_data.remote(
            target_size_min=target_size_min, target_size_max=target_size_max,
            n_dist_min=n_dist_min, n_dist_max=n_dist_max,
            noise_amp=noise_amp)
        info = next(iter(prep))
        print(f"[single] data ready: {info}", flush=True)
        m = run_arm.remote(arm=arm, seed=seed, mode=mode, n_train=n_train,
                           epochs=epochs, lr=lr,
                           target_size_min=target_size_min,
                           target_size_max=target_size_max,
                           n_dist_min=n_dist_min, n_dist_max=n_dist_max,
                           noise_amp=noise_amp, data_key=info["data_key"])
        print("RESULT:", m)
        return

    # ---- batch mode: 1 CPU data build + concurrent GPU runs ------------- #
    arms = [a.strip() for a in array.split(",") if a.strip()]
    if seeds:
        seed_list = [int(s) for s in seeds.split(",") if s.strip()]
    else:
        seed_list = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010,
                     1111, 1212, 1313, 1414, 1515]
    jobs = [(a, s) for a in arms for s in seed_list]
    print(f"[batch] {len(jobs)} jobs ({len(arms)} arms x {len(seed_list)} "
          f"seeds) mode={mode} n_train={n_train} epochs={epochs} "
          f"lr={lr} difficulty=({target_size_min},{target_size_max})/"
          f"({n_dist_min},{n_dist_max})/n{noise_amp}", flush=True)

    # 1) CPU-only data build ONCE for this difficulty config.
    prep = prepare_data.remote(
        target_size_min=target_size_min, target_size_max=target_size_max,
        n_dist_min=n_dist_min, n_dist_max=n_dist_max,
        noise_amp=noise_amp)
    info = next(iter(prep))
    print(f"[batch] data ready: {info}", flush=True)

    # 2) Concurrent GPU runs: Modal auto-scales these cached function
    # invocations (each .remote is a separate container that runs in
    # parallel and is queued by Modal when warm-pool + quota are full).
    # Completed runs are written to the RESULTS volume by the harness
    # (result_<arm>_s<seed>.json + per-epoch progress files), so even
    # if the local process dies or credit runs out mid-batch, every
    # *finished* run is already persisted.
    import json
    results = []
    calls = [run_arm.spawn(arm=j[0], seed=j[1], mode=mode, n_train=n_train,
                           epochs=epochs, lr=lr,
                           target_size_min=target_size_min,
                           target_size_max=target_size_max,
                           n_dist_min=n_dist_min, n_dist_max=n_dist_max,
                           noise_amp=noise_amp, data_key=info["data_key"])
             for j in jobs]
    for i, c in enumerate(calls):
        r = c.get()
        results.append(r)
        print(f"[batch] {i + 1}/{len(calls)} DONE {r['arm']} s{r['seed']} "
              f"dev={r.get('dev_eval', {}).get('unseen_accuracy')}",
              flush=True)

    # 3) Dump all results to the results volume for later export.
    from pathlib import Path
    out_dir = Path("/root/results") / "phase2_nobox"
    if results:
        allr = {"mode": mode, "n_train": n_train, "epochs": epochs, "lr": lr,
                "difficulty": {"target_size": [target_size_min,
                                               target_size_max],
                               "n_distractor_range": [n_dist_min, n_dist_max],
                               "noise_amp": noise_amp},
                "data_key": info["data_key"], "results": results}
        (out_dir / f"batch_{info['data_key']}_{mode}.json").write_text(
            json.dumps(allr, indent=1), encoding="utf-8")
    print("[batch] ALL DONE")


if __name__ == "__main__":
    sys.exit(main())
