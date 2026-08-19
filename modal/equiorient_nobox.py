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


@app.local_entrypoint()
def main(arm: str = "equiorient", seed: int = 101, mode: str = "dev",
         n_train: int = 128, gate: bool = False, epochs: int = 2,
         lr: float = 1e-4,
         target_size_min: float = 3.0, target_size_max: float = 5.0,
         n_dist_min: int = 12, n_dist_max: int = 20,
         noise_amp: int = 12):
    if gate:
        print("GATE:", run_gate.remote())
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
