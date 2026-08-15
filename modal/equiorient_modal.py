"""EquiOrient Phase-1 pilot on Modal (serverless GPU, $30/mo starter credit).

Replaces the Thunder Compute runbook flow (create instance -> stage ->
run -> collect -> teardown) with Modal Sandboxes: pay-per-second, no idle
billing, model cached in a Volume across runs, multi-seed trivially
parallel (10 GPU concurrency on Starter).

Setup (one time, interactive):
    pip install modal
    python -m modal setup            # opens a browser tab for auth

Usage:
    python modal/equiorient_modal.py tiny          # CPU gate (free-ish)
    python modal/equiorient_modal.py pilot         # full pilot (L40S)
    python modal/equiorient_modal.py pilot --seed 3   # 3-way parallel

Frozen contract (configs/equiorient_pilot_freeze.yaml, commit 91185d7):
    Qwen/Qwen3-VL-8B-Instruct @ 0c351dd0, transformers==4.57.6,
    torch cu128, sdpa, vision LoRA qkv/proj/c_fc/c_proj r16 a32, frozen
    text/lm_head, six arms, lambda grid {0.1,1.0,10.0} on scene_0010-13,
    V o H held out, causal ablation, depth probe (Amendment C).
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Image: the frozen stack (mirrors cloud_setup/setup_equiorient.sh)
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


def _mounts():
    return [
        modal.Mount.from_local_dir(REPO / "src",
                                   remote_path="/root/equiorient/src"),
        modal.Mount.from_local_dir(REPO / "scripts" / "equiorient",
                                   remote_path="/root/equiorient/scripts"),
        modal.Mount.from_local_dir(REPO / "configs",
                                   remote_path="/root/equiorient/configs"),
        modal.Mount.from_local_dir(
            REPO / "results" / "equiorient" / "pilot_data",
            remote_path="/root/equiorient/pilot_data"),
    ]


def _env(hf_token: str):
    return {"HF_TOKEN": hf_token, "HF_HOME": "/root/hf-cache"}


def _run_harness(mode: str) -> dict:
    """Runs pilot_harness.py inside the sandbox and returns the matrix."""
    import json
    import subprocess

    tiny = ["--tiny"] if mode == "tiny" else []
    out_dir = f"/root/equiorient/results/pilot_run_{mode}"
    cmd = [
        "python", "/root/equiorient/scripts/pilot_harness.py", *tiny,
        "--freeze", "/root/equiorient/configs/equiorient_pilot_freeze.yaml",
        "--data", "/root/equiorient/pilot_data",
        "--out", out_dir,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
        raise RuntimeError(f"harness failed ({proc.returncode})")
    matrix_path = Path(out_dir) / "result_matrix.json"
    if not matrix_path.exists():
        raise RuntimeError("no result_matrix.json produced")
    return json.loads(matrix_path.read_text())


@app.function(volumes={"/root/hf-cache": HF_CACHE,
                       "/root/equiorient/results": RESULTS},
              mounts=_mounts(), secrets=[modal.Secret.from_name("hf-token")],
              timeout=60 * 60,  # 1 h for the tiny gate
              )
def run_tiny() -> dict:
    import os
    os.environ.update(_env(os.environ["HF_TOKEN"]))
    return _run_harness("tiny")


@app.function(gpu="L40S",
              volumes={"/root/hf-cache": HF_CACHE,
                       "/root/equiorient/results": RESULTS},
              mounts=_mounts(), secrets=[modal.Secret.from_name("hf-token")],
              timeout=3 * 60 * 60,  # 3 h headroom for a full pilot
              )
def run_pilot() -> dict:
    import os
    os.environ.update(_env(os.environ["HF_TOKEN"]))
    return _run_harness("pilot")


@app.local_entrypoint()
def main(mode: str = "pilot"):
    # NOTE: multi-seed (Gate 6) will call run_pilot.remote() once per seed
    # in a map() — Starter allows 10 GPU concurrency. The Phase-1 freeze is
    # single-seed; the harness seed parameterization lands with the
    # confirmatory amendment.
    if mode == "tiny":
        m = run_tiny.remote()
    else:
        m = run_pilot.remote()
    print("RESULT_MATRIX:", m)


if __name__ == "__main__":
    sys.exit(main())
