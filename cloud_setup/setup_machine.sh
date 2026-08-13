#!/usr/bin/env bash
# ============================================================================
# One-command provisioner for the seed-variance job on Thunder Compute A6000s.
#
# Usage (inside `tnr connect <index>` on each machine):
#   export HF_TOKEN=hf_...                      # required; NEVER commit it
#   bash setup_machine.sh --stage               # provision + 60-step smoke test
#   bash setup_machine.sh --run general 101     # full seed run + consistency
#   bash setup_machine.sh --run general 202
#   bash setup_machine.sh --run hardneg 101
#   bash setup_machine.sh --run hardneg 202
#   bash setup_machine.sh --collect             # zip results for transfer back
#
# Idempotent: re-running any step resumes instead of redoing work.
# Everything is logged to setup.log (same directory as this script).
# ============================================================================
set -euo pipefail

REPO_URL="https://github.com/Khagendra01/vlm-spatial-reasoning.git"
BRANCH="paper-draft-v1"
REPO="$HOME/vlm-spatial-reasoning"
VENV="$HOME/vlm-venv"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/setup.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }

MODE="${1:-}"
[ -n "$MODE" ] || die "usage: $0 --stage | --run <condition> <seed> | --collect"

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
provision_venv() {
  log "provision_venv: $VENV"
  if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
  fi
  "$VENV/bin/python" -m pip install --upgrade -q pip
  log "provision_venv: installing torch + torchvision (cu130 index)"
  "$VENV/bin/pip" install -q "torch==2.12.1+cu130" "torchvision==0.27.1+cu130" \
      --index-url https://download.pytorch.org/whl/cu130 \
    || die "torch install failed (check the cu130 wheel index)"
  log "provision_venv: installing requirements.txt"
  "$VENV/bin/pip" install -q -r "$REPO/requirements.txt"
}

# ------------------------------------------------------------------- repo
# NOTE: sparse + partial clone (--filter=blob:none). The repo tree is ~1.2GB
# because checkpoints/ contains hundreds of old LoRA adapters that the
# seed-variance job does NOT need (it trains fresh LoRAs). Cloning everything
# times out; the cone below keeps the clone to a few MB of blobs.
provision_repo() {
  log "provision_repo: $REPO (branch $BRANCH, sparse cone)"
  if [ ! -d "$REPO/.git" ]; then
    git clone --quiet --depth 1 --filter=blob:none --sparse \
      --branch "$BRANCH" "$REPO_URL" "$REPO"
  fi
  git -C "$REPO" sparse-checkout set src scripts configs data cloud_setup \
    docs requirements.txt .gitignore README.md SEED_VARIANCE_JOB.md
  git -C "$REPO" fetch --quiet origin "$BRANCH"
  git -C "$REPO" checkout --quiet --force "origin/$BRANCH"
}

# --------------------------------------------- HF token / models / dataset
provision_hf() {
  [ -n "${HF_TOKEN:-}" ] || die "HF_TOKEN is not set; export it first"
  log "provision_hf: downloading 7B model Qwen/Qwen2-VL-7B-Instruct"
  HF_HUB_ENABLE_HF_TRANSFER=0 "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import os, sys
from huggingface_hub import snapshot_download
snapshot_download("Qwen/Qwen2-VL-7B-Instruct", token=sys.argv[1])
PY
  log "provision_hf: downloading 2B model HuggingFaceTB/SmolVLM2-2.2B-Instruct"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import os, sys
from huggingface_hub import snapshot_download
snapshot_download("HuggingFaceTB/SmolVLM2-2.2B-Instruct", token=sys.argv[1])
PY
  log "provision_hf: preloading cambridgeltl/vsr_random test split"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import os, sys
os.environ["HF_TOKEN"] = sys.argv[1]
from datasets import load_dataset
load_dataset("cambridgeltl/vsr_random", split="test")
PY
}

# -------------------------------------------------------------- image cache
provision_images() {
  log "provision_images: downloading missing VSR images into data/image_cache"
  ( cd "$REPO" && "$VENV/bin/python" scripts/pre_download_all.py )
}

# ------------------------------------------------------------- smoke test
smoke_test() {
  local scratch_seed=9999
  log "smoke_test: 60-step run (condition general, scratch seed $scratch_seed)"
  ( cd "$REPO" && "$VENV/bin/python" scripts/run_seed_variance.py \
      --condition general --seed $scratch_seed --max-steps 60 2>&1 \
      | tee -a "$LOG" )
  log "smoke_test: cleaning scratch outputs"
  rm -rf "$REPO/results/seed_variance/general/$scratch_seed"
  log "smoke_test: 2B model load check (SmolVLM2 wrapper on this venv)"
  ( cd "$REPO" && "$VENV/bin/python" - <<'PY'
from src.models.smolvlm import SmolVLMClassifier
m = SmolVLMClassifier()
print(f"2B loaded OK: {type(m.model).__name__}", flush=True)
del m
PY
  )
  log "smoke_test: OK — provision complete (7B smoke + 2B load verified)"
}

# ------------------------------------------------------------- full run
full_run() {
  local condition="$1" seed="$2"
  local out="$REPO/results/seed_variance/$condition/$seed"
  [ -f "$out/metrics.json" ] && die "already exists: $out (refusing to rerun)"
  log "full_run: $condition seed $seed (nohup; log run_${condition}_${seed}.log)"
  mkdir -p "$out"
  ( cd "$REPO" && nohup "$VENV/bin/python" scripts/run_seed_variance.py \
      --condition "$condition" --seed "$seed" \
      > "run_${condition}_${seed}.log" 2>&1 & echo "PID $!" | tee -a "$LOG" )
  log "full_run: started in background — watch with:"
  log "  tail -f $REPO/../run_${condition}_${seed}.log"
}

# ------------------------------------------------------- consistency + zip
finish_run() {
  local condition="$1" seed="$2"
  local out="$REPO/results/seed_variance/$condition/$seed"
  [ -f "$out/metrics.json" ] || die "run not finished: $out (no metrics.json)"
  log "finish_run: consistency evaluation for $condition/$seed"
  ( cd "$REPO" && "$VENV/bin/python" scripts/eval_consistency_flips.py \
      --condition seed_checkpoint \
      --lora-path "$out/checkpoint" \
      --orig-csv "$out/predictions.csv" \
      --out-csv "$out/consistency_flips.csv" 2>&1 | tee -a "$LOG" )
  log "finish_run: zipping results"
  ( cd "$REPO" && zip -qr "$HOME/seed_variance_${condition}_${seed}.zip" \
      "results/seed_variance/$condition/$seed" )
  log "finish_run: DONE — transfer back with tnr scp:"
  log "  tnr scp <machine>:$HOME/seed_variance_${condition}_${seed}.zip ."
}

# ------------------------------------------------------------------- main
case "$MODE" in
  --stage)
    provision_system; provision_venv; provision_repo; provision_hf
    provision_images; smoke_test
    log "STAGE COMPLETE — machine ready. Next: --run general 101"
    ;;
  --run)
    [ $# -eq 3 ] || die "--run needs <condition> <seed>"
    provision_system; provision_venv; provision_repo; provision_hf
    provision_images
    full_run "$2" "$3"
    log "launching. After the run finishes, run: bash $0 --finish $2 $3"
    ;;
  --finish)
    [ $# -eq 3 ] || die "--finish needs <condition> <seed>"
    finish_run "$2" "$3"
    ;;
  --collect)
    log "collect: zipping all seed results"
    ( cd "$REPO" && zip -qr "$HOME/seed_variance_all.zip" results/seed_variance )
    log "collect: DONE — $HOME/seed_variance_all.zip"
    log "transfer:  tnr scp <machine>:$HOME/seed_variance_all.zip ."
    ;;
  *) die "unknown mode: $MODE" ;;
esac
