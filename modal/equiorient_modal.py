"""EquiOrient Phase-1 pilot on Modal (serverless GPU, $30/mo starter credit).

The cloud box CLONES the repo from GitHub (pinned commit) at function
start — no local mounts, fully reproducible from any machine. Pay-per-
second, no idle billing, model cached in a Volume across runs, multi-seed
trivially parallel (10 GPU concurrency on Starter).

Setup (one time, interactive):
    pip install modal
    python -m modal setup                # browser auth (done 2026-08-15)
    python -m modal secret create hf-token HF_TOKEN=hf_...   # gated model

Usage:
    python modal/equiorient_modal.py tiny            # CPU gate (~free)
    python modal/equiorient_modal.py pilot           # full pilot (L40S)
    python modal/equiorient_modal.py pilot --variant v2   # Amendment D

Frozen contract: configs/equiorient_pilot_freeze_v2.yaml (Amendment D:
harder regime, 5 objects/scene, seed 20260815, epochs 2) — v1 freeze
(yaml v1) supported via --variant v1.
"""

from __future__ import annotations

import sys

import modal

# ---------------------------------------------------------------------------
# Image: frozen stack (mirrors cloud_setup/setup_equiorient.sh)
# ---------------------------------------------------------------------------
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "zip")
    # torch/torchvision ONLY from the cu128 index (not on PyPI)
    .pip_install("torch==2.8.0+cu128", "torchvision==0.23.0+cu128",
                 index_url="https://download.pytorch.org/whl/cu128")
    # the rest from PyPI (torch already satisfied -> pip leaves it alone)
    .pip_install("transformers==4.57.6", "peft", "pillow", "pyyaml",
                 "scikit-learn")
)

app = modal.App("equiorient-pilot", image=image)

# ---------------------------------------------------------------------------
# Volumes: model cache + results persist across runs (1 TiB free tier)
# ---------------------------------------------------------------------------
HF_CACHE = modal.Volume.from_name("equiorient-hf-cache", create_if_missing=True)
RESULTS = modal.Volume.from_name("equiorient-results", create_if_missing=True)

# Pinned repo commit: update after each push (freeze traceability).
REPO_URL = ("https://github.com/Khagendra01/vlm-spatial-reasoning.git")
BRANCH = "research/equiorient"
PINNED_COMMIT = "7389e3d"  # Amendment D release (2026-08-15)
SPARSE_CONE = ["src", "scripts", "configs", "cloud_setup", "modal",
               "research", "results/equiorient/pilot_data",
               "results/equiorient/pilot_data_v2", "requirements.txt"]


def _env(hf_token: str):
    return {"HF_TOKEN": hf_token, "HF_HOME": "/root/hf-cache"}


def _clone_repo() -> None:
    """Clone (sparse, partial) + checkout the pinned commit."""
    import subprocess

    dst = "/root/repo"

    def run(cmd):
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"CMD FAILED {cmd[0]} rc={p.returncode}\n"
                               f"stdout: {p.stdout[-2000:]}\n"
                               f"stderr: {p.stderr[-2000:]}")
        return p

    run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
         "--sparse", "--branch", BRANCH, REPO_URL, dst])
    run(["git", "-C", dst, "sparse-checkout", "set", *SPARSE_CONE])
    run(["git", "-C", dst, "fetch", "--quiet", "--depth", "1",
         "origin", PINNED_COMMIT])
    run(["git", "-C", dst, "checkout", "--quiet", "--force", PINNED_COMMIT])


def _run_harness(mode: str, variant: str) -> dict:
    """Runs pilot_harness.py inside the sandbox and returns the matrix."""
    import json
    import subprocess

    _clone_repo()
    tiny = ["--tiny"] if mode == "tiny" else []
    freeze = ("configs/equiorient_pilot_freeze_v2.yaml" if variant == "v2"
              else "configs/equiorient_pilot_freeze.yaml")
    data = ("results/equiorient/pilot_data_v2" if variant == "v2"
            else "results/equiorient/pilot_data")
    out_dir = f"/root/results/pilot_run_{variant}_{mode}"
    cmd = [
        "python", "/root/repo/scripts/equiorient/pilot_harness.py",
        *tiny,
        "--freeze", f"/root/repo/{freeze}",
        "--data", f"/root/repo/{data}",
        "--out", out_dir,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
        raise RuntimeError(f"harness failed ({proc.returncode})")
    matrix_path = f"{out_dir}/result_matrix.json"
    if not __import__("os").path.exists(matrix_path):
        raise RuntimeError("no result_matrix.json produced")
    return json.loads(open(matrix_path, encoding="utf-8").read())


@app.function(volumes={"/root/hf-cache": HF_CACHE,
                       "/root/results": RESULTS},
              secrets=[modal.Secret.from_name("hf-token")],
              timeout=60 * 60,  # 1 h for the tiny gate
              )
def run_tiny(variant: str = "v1") -> dict:
    import os
    os.environ.update(_env(os.environ["HF_TOKEN"]))
    return _run_harness("tiny", variant)


@app.function(gpu=["L40S", "A100-40GB"],
              volumes={"/root/hf-cache": HF_CACHE,
                       "/root/results": RESULTS},
              secrets=[modal.Secret.from_name("hf-token")],
              timeout=3 * 60 * 60,  # 3 h headroom for a full pilot
              )
def run_pilot(variant: str = "v1") -> dict:
    import os
    os.environ.update(_env(os.environ["HF_TOKEN"]))
    return _run_harness("pilot", variant)


@app.local_entrypoint()
def main(mode: str = "pilot", variant: str = "v2"):
    # NOTE: multi-seed (Gate 6) will map() run_pilot per seed — Starter
    # allows 10 GPU concurrency. Phase-1 freeze is single-seed.
    if mode == "tiny":
        m = run_tiny.remote(variant=variant)
    else:
        m = run_pilot.remote(variant=variant)
    print("RESULT_MATRIX:", m)


if __name__ == "__main__":
    sys.exit(main())
