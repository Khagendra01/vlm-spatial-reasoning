"""EquiOrient Phase-2 dev/confirmatory runner on Modal (serverless L40S).

Usage:
    python modal/equiorient_phase2.py --arm augmentation --seed 101
    python modal/equiorient_phase2.py --arm equiorient   --seed 101
    python modal/equiorient_phase2.py --gate              # brutal suite (CPU)
    python modal/equiorient_phase2.py --arm augmentation --seed 101 --mode confirmatory
    python modal/equiorient_phase2.py --launch_all       # launch all 30 jobs

The sandbox clones research/equiorient-phase2 (pinned via HEAD assert),
regenerates the deterministic dataset (seeds) into the data volume, and
runs the harness. The Qwen3-VL-8B model is reused from the Phase-1
hf-cache volume (no re-download). Results land in the results volume.
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

app = modal.App("equiorient-phase2", image=image)

HF_CACHE = modal.Volume.from_name("equiorient-hf-cache", create_if_missing=True)
RESULTS = modal.Volume.from_name("equiorient-results", create_if_missing=True)
DATA = modal.Volume.from_name("equiorient-phase2-data", create_if_missing=True)

REPO_URL = "https://github.com/Khagendra01/vlm-spatial-reasoning.git"
BRANCH = "research/equiorient-phase2"
PINNED_COMMIT = ""  # optional hard pin; empty = HEAD + recorded in results
SPARSE_CONE = ["equiorient", "modal", "configs", "cloud_setup"]


def _prepare() -> str:
    """Clone repo, build the deterministic dataset, return head sha."""
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
    import equiorient.data.manifests as mf
    from pathlib import Path
    out = Path("/root/phase2_data")
    # ALWAYS rebuild: the data volume persists across runs and must never
    # serve a stale dataset (dev-gate catch 2026-08-15: stale labels).
    shutil.rmtree(out, ignore_errors=True)
    mf.build(out, n_dev=512, n_train=2048, n_val=512, n_test=1024)
    return head


@app.function(gpu=["L40S", "A100-40GB"],
              volumes={"/root/hf-cache": HF_CACHE,
                       "/root/results": RESULTS,
                       "/root/phase2_data": DATA},
              secrets=[modal.Secret.from_name("hf-token")],
              timeout=6 * 60 * 60)
def run_arm(arm: str, seed: int, n_train: int = 512, lam: float = 1.0,
            epochs: int = 2, batch: int = 8, tiny: bool = False,
            mode: str = "dev") -> dict:
    import os
    os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]
    os.environ["HF_HOME"] = "/root/hf-cache"
    head = _prepare()
    import json
    from pathlib import Path
    out_dir = Path("/root/results") / f"phase2_{mode}"
    cmd = ["python", "-m", "equiorient.experiments.train",
           "--mode", mode,
           "--arm", arm, "--seed", str(seed),
           "--n_train", str(n_train), "--lambda", str(lam),
           "--epochs", str(epochs), "--batch", str(batch),
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
    p = subprocess.run(["python", "-m", "equiorient.tests.test_phase2_gate"],
                       capture_output=True, text=True, cwd="/root/repo")
    print(p.stdout[-3000:])
    if p.returncode != 0:
        print(p.stderr[-3000:])
        raise RuntimeError("PHASE-2 GATE FAILED in cloud")
    return {"gate": "PASS", "repo_commit": head}


@app.local_entrypoint()
def main(arm: str = "augmentation", seed: int = 101, tiny: bool = False,
         gate: bool = False, mode: str = "dev", launch_all: bool = False):
    if gate:
        print("GATE:", run_gate.remote())
        return
    if launch_all:
        SEEDS = [101, 202, 303, 404, 505]
        ARMS = ["original_sft", "augmentation", "output_consistency",
                "latent_invariance", "equiorient", "wrong_geometry"]
        for s in SEEDS:
            for a in ARMS:
                print(f"Launching {a} seed={s} mode={mode}")
                run_arm.spawn(arm=a, seed=s, mode=mode)
        print(f"Launched {len(SEEDS) * len(ARMS)} jobs")
        return
    m = run_arm.remote(arm=arm, seed=seed, tiny=tiny, mode=mode)
    print("RESULT:", m)


if __name__ == "__main__":
    sys.exit(main())
