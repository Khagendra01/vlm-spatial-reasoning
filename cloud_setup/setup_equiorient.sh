#!/usr/bin/env bash
# ============================================================================
# One-command provisioner for the EquiOrient Phase-1 pilot on Thunder Compute.
#
# Branch: research/equiorient (NOT paper-draft-v1 — this is the Paper-3 line).
# Frozen stack (configs/equiorient_pilot_freeze.yaml, commit 91185d7):
#   backbone  Qwen/Qwen3-VL-8B-Instruct @ 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
#   transformers ==4.57.6   torch 2.x bf16 (cu128 wheels)   sdpa attention
#   peft (fused qkv/proj/c_fc/c_proj LoRA r16 a32 d0.05), text backbone + lm_head FROZEN
#
# Usage (inside `tnr connect <index>` on each machine):
#   export HF_TOKEN=hf_...                      # required (Qwen3-VL-8B is gated); NEVER commit it
#   bash setup_equiorient.sh --stage            # apt + venv + torch/transformers/peft + sparse clone
#                                               #   + Qwen3-VL-8B download + CPU --tiny harness smoke
#   bash setup_equiorient.sh --run              # launch full pilot (nohup; ~24-48h, one seed)
#   bash setup_equiorient.sh --collect          # zip results/equiorient/pilot_run for tnr scp
#
# Idempotent: re-running any step resumes instead of redoing work.
# Everything is logged to setup_equiorient.log (same directory as this script).
# ============================================================================
set -euo pipefail

REPO_URL="https://github.com/Khagendra01/vlm-spatial-reasoning.git"
BRANCH="research/equiorient"
REPO="$HOME/vlm-spatial-reasoning"
VENV="$HOME/vlm-venv"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/setup_equiorient.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }

MODE="${1:-}"
[ -n "$MODE" ] || die "usage: $0 --stage | --run | --collect"

# ---------------------------------------------------------------- system deps
provision_system() {
  log "provision_system: apt packages"
  export DEBIAN_FRONTEND=noninteractive
  if ! command -v git >/dev/null; then
    apt-get update -qq && apt-get install -y -qq git
  fi
  if ! command -v python3 >/dev/null; then
    apt-get update -qq && apt-get install -y -qq python3 python3-venv
  fi
  if ! command -v zip >/dev/null; then
    apt-get install -y -qq zip
  fi
}

# ------------------------------------------------------------- python venv
# Frozen env mirrors the machine where pilot_harness.py was validated
# (torch 2.8.0+cu128 / transformers 4.57.6). cu128 wheels from the pytorch
# index; PyPI has no +cu128 wheels.
provision_venv() {
  log "provision_venv: $VENV"
  if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
  fi
  "$VENV/bin/python" -m pip install --upgrade -q pip
  log "provision_venv: installing torch 2.8.0+cu128 (+torchvision) from cu128 index"
  "$VENV/bin/pip" install -q "torch==2.8.0+cu128" "torchvision==0.23.0+cu128" \
      --index-url https://download.pytorch.org/whl/cu128 \
    || die "torch install failed (check the cu128 wheel index)"
  log "provision_venv: installing frozen EquiOrient stack"
  "$VENV/bin/pip" install -q \
      "transformers==4.57.6" peft pillow pyyaml accelerate datasets huggingface_hub \
    || die "pip install of the EquiOrient stack failed"
}

# ------------------------------------------------------------------- repo
# Sparse + partial clone (--filter=blob:none): the tree carries old
# checkpoints/ adapters; the cone below keeps the clone to a few MB of blobs.
# cone includes results/equiorient/pilot_data (committed at f107453) so the
# pilot runs on the EXACT committed manifest, not a box-local regeneration.
provision_repo() {
  log "provision_repo: $REPO (branch $BRANCH, sparse cone)"
  if [ ! -d "$REPO/.git" ]; then
    git clone --quiet --depth 1 --filter=blob:none --sparse \
      --branch "$BRANCH" "$REPO_URL" "$REPO"
  fi
  git -C "$REPO" sparse-checkout set src scripts configs cloud_setup research \
    results/equiorient/pilot_data requirements.txt .gitignore README.md
  git -C "$REPO" fetch --quiet origin "$BRANCH"
  git -C "$REPO" checkout --quiet --force "origin/$BRANCH"
}

# ------------------------------------------------------ HF model (gated)
provision_hf() {
  [ -n "${HF_TOKEN:-}" ] || die "HF_TOKEN is not set; export it first"
  log "provision_hf: Qwen/Qwen3-VL-8B-Instruct @ 0c351dd0 (frozen revision)"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import sys
from huggingface_hub import snapshot_download
REV = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
snapshot_download("Qwen/Qwen3-VL-8B-Instruct", revision=REV, token=sys.argv[1])
PY
}

# ------------------------------------------------------------- CPU smoke
# The --tiny harness test is the ideal gate: it exercises the full
# pre-flight -> 12-run -> lambda-select -> holdout + ablation path with a
# tiny random Qwen3-VL on CPU (no weights, ~3 min). Validates the exact
# env + committed data end-to-end before any GPU spend.
smoke_tiny() {
  log "smoke_tiny: pilot_harness.py --tiny on CPU"
  ( cd "$REPO" && "$VENV/bin/python" scripts/equiorient/pilot_harness.py \
      --tiny \
      --freeze configs/equiorient_pilot_freeze.yaml \
      --data results/equiorient/pilot_data \
      --out results/equiorient/pilot_smoke 2>&1 | tee -a "$LOG" )
  log "smoke_tiny: OK — harness executes end-to-end on this box"
}

# ------------------------------------------------------------- full pilot
full_run() {
  local out="$REPO/results/equiorient/pilot_run"
  [ -f "$out/result_matrix.json" ] \
    && die "already exists: $out/result_matrix.json (refusing to rerun)"
  mkdir -p "$out"
  log "full_run: pilot_harness.py (full Qwen3-VL-8B, ~24-48h, nohup; log ~/pilot_run.log)"
  ( cd "$REPO" && nohup "$VENV/bin/python" scripts/equiorient/pilot_harness.py \
      --freeze configs/equiorient_pilot_freeze.yaml \
      --data results/equiorient/pilot_data \
      --out "$out" > ~/pilot_run.log 2>&1 & echo "PID $!" | tee -a "$LOG" )
  log "full_run: started in background — watch with:"
  log "  tail -f ~/pilot_run.log"
  log "  state: $out/run.log  (harness milestones)"
}

# ------------------------------------------------------------------- main
case "$MODE" in
  --stage)
    provision_system; provision_venv; provision_repo; provision_hf; smoke_tiny
    log "STAGE COMPLETE — machine ready. Next: --run (requires orchestrator GPU unlock)"
    ;;
  --run)
    provision_system; provision_venv; provision_repo; provision_hf
    full_run
    ;;
  --collect)
    log "collect: zipping results/equiorient/pilot_run"
    ( cd "$REPO" && zip -qr "$HOME/equiorient_pilot_run.zip" \
        results/equiorient/pilot_run )
    log "collect: DONE — transfer with:  tnr scp <machine>:$HOME/equiorient_pilot_run.zip ."
    ;;
  *) die "unknown mode: $MODE" ;;
esac
