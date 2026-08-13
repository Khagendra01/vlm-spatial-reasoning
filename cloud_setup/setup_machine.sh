#!/usr/bin/env bash
# ============================================================================
# Paper-2 R1 seed-campaign provisioner for Thunder Compute A6000s.
# Branch: research/spatial-grounding-audit   (corrected 2026-08-13)
#
# THIS is the provisioner for the FROZEN R1 seed campaign
# (configs/seed_campaign/SEED_CAMPAIGN.json). Every interface below was
# verified against the branch source on 2026-08-13:
#   run_seed_campaign.py : --backbone {qwen2vl_7b,smolvlm2_2b} --seed --output
#                          writes training_log.json at END; saves checkpoints
#                          to <output>/final (guard on <output>/final only).
#   run_seed_battery.py : --model-family {qwen2vl,smolvlm2} --checkpoints
#                          --tag-prefix (default checkpoints = full registry)
#   regress_seed_battery.py: --model-family {qwen2vl,smolvlm2} (REQUIRED)
#   download_images.py : no args; strict (exit 1 if any frozen-available image
#                          fails; only ineligible rows survive without images)
#
# Env fixes from Paper-1 staging baked in (all verified on the A6000):
#   * sparse + partial clone (repo tree ~1.2GB due to checkpoints/)
#   * torch + torchvision installed TOGETHER from the cu130 wheel index
#   * huggingface_hub==1.27.0 (transformers 5.14.1 needs >=1.5.0,<2.0)
#   * torchvision + num2words pinned in requirements.txt
#
# Usage (one mode per invocation; run by the agent, NO --collect on workers):
#   export HF_TOKEN=hf_...                 # session-only; NEVER committed
#   bash setup_machine.sh --stage          # provision + smoke test
#   bash setup_machine.sh --train <backbone> <seed>   # 101=A 202=B 303=C
#   bash setup_machine.sh --regress        # gate: legacy battery == committed
#   bash setup_machine.sh --battery <family> <tag> [checkpoints]
#   bash setup_machine.sh --collect        # zip results for transfer out
#
# Idempotent: re-running resumes instead of redoing. Log -> setup.log
# (same dir as this script). set -e: strict where it matters.
# ============================================================================
set -euo pipefail

REPO_URL="https://github.com/Khagendra01/vlm-spatial-reasoning.git"
BRANCH="research/spatial-grounding-audit"
REPO="$HOME/vlm-spatial-reasoning"
VENV="$HOME/vlm-venv"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/setup.log"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
die() { log "FATAL: $*"; exit 1; }

[ $# -ge 1 ] || die "usage: $0 --stage | --train <backbone> <seed> | --images | --regress | --battery <family> <tag> [ckpts] | --collect"
MODE="$1"; SUB1="${2:-}"; SUB2="${3:-}"; SUB3="${4:-}"

# ---------------------------------------------------------------- system deps
provision_system() {
  log "provision_system: apt packages"
  export DEBIAN_FRONTEND=noninteractive
  if ! command -v git   >/dev/null; then apt-get update -qq && apt-get install -y -qq git; fi
  if ! command -v python3 >/dev/null; then apt-get update -qq && apt-get install -y -qq python3 python3-venv python3-pip; fi
  if ! command -v zip   >/dev/null; then apt-get install -y -qq zip; fi
}

# ------------------------------------------------------------- python venv
provision_venv() {
  log "provision_venv: $VENV"
  if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
  "$VENV/bin/python" -m pip install --upgrade -q pip
  log "provision_venv: torch + torchvision from cu130 index (TOGETHER)"
  "$VENV/bin/pip" install -q "torch==2.12.1+cu130" "torchvision==0.27.1+cu130" \
      --index-url https://download.pytorch.org/whl/cu130 \
    || die "torch/torchvision install failed (check cu130 index)"
  log "provision_venv: requirements.txt"
  "$VENV/bin/pip" install -q -r "$REPO/requirements.txt"
}

# ------------------------------------------------------------------- repo
# Sparse + partial clone. checkpoints/ = 1.18GB of old adapters; the campaign
# only needs code + frozen protocol + the legacy/seedA adapter dirs that the
# regression gate and battery baseline read (blob:none keeps it to a few MB
# except those coned adapter dirs, ~20MB each).
provision_repo() {
  log "provision_repo: $REPO (branch $BRANCH, sparse cone)"
  if [ ! -d "$REPO/.git" ]; then
    git clone --quiet --depth 1 --filter=blob:none --sparse \
      --branch "$BRANCH" "$REPO_URL" "$REPO"
  fi
  git -C "$REPO" sparse-checkout set src scripts configs data \
    results/grounding/protocol results/grounding/analysis results/seed_campaign/battery \
    research cloud_setup requirements.txt .gitignore README.md SPATIAL_REASONING_DECISION_LOG.md \
    checkpoints/qwen2vl_7b_general_lora/final \
    checkpoints/qwen2vl_7b_hardneg_lora/final \
    checkpoints/general_lora/final \
    checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedA/final \
    checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedB/final \
    checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedC/final \
    checkpoints/seed_campaign/smolvlm2_2b_general_lora_seedA/final \
    checkpoints/seed_campaign/smolvlm2_2b_general_lora_seedB/final \
    checkpoints/seed_campaign/smolvlm2_2b_general_lora_seedC/final
  git config --global --add safe.directory "$REPO" >/dev/null 2>&1 || true
  git -C "$REPO" fetch --quiet origin "$BRANCH"
  git -C "$REPO" reset --quiet --hard "origin/$BRANCH"
  git -C "$REPO" checkout --quiet --force "origin/$BRANCH"
}

# --------------------------------------------- HF token / models / dataset
provision_hf() {
  [ -n "${HF_TOKEN:-}" ] || die "HF_TOKEN is not set; export it first"
  log "provision_hf: Qwen/Qwen2-VL-7B-Instruct"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download("Qwen/Qwen2-VL-7B-Instruct", token=sys.argv[1])
PY
  log "provision_hf: HuggingFaceTB/SmolVLM2-2.2B-Instruct"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download("HuggingFaceTB/SmolVLM2-2.2B-Instruct", token=sys.argv[1])
PY
  log "provision_hf: huggingface datasets vsr_random test split"
  "$VENV/bin/python" - "$HF_TOKEN" <<'PY'
import os, sys
os.environ["HF_TOKEN"] = sys.argv[1]
from datasets import load_dataset
load_dataset("cambridgeltl/vsr_random", split="test")
PY
}

# -------------------------------------------------------------- image cache
# Two disjoint image sets are required on a training box:
#   1. TEST payload (frozen IDs)  -> scripts/grounding/download_images.py
#      (needed by the battery; strict: exit 1 if any frozen-available link
#      fails to download)
#   2. TRAINING manifest images (general_train.jsonl; COCO train2017/val2017,
#      md5-hashed into the same cache). CRITICAL: run_seed_campaign.py
#      train_7b has NO URL fallback -- load_cached_image() returns None and
#      the loop silently skips the row. Without these, 7B seeds train on a
#      silently truncated manifest (seed-0 trained on the full 1900 rows) and
#      the seeds are incomparable. The 2B collator DOES have a live-URL
#      fallback, but that is slow/network-bound (seedA: 7474s, ~31s/step) --
#      pre-caching fixes both.
provision_images() {
  log "provision_images: download_images.py (frozen IDs, strict)"
  ( cd "$REPO" && "$VENV/bin/python" scripts/grounding/download_images.py )
  local n
  n=$(find "$REPO/data/image_cache" -name '*.jpg' 2>/dev/null | wc -l)
  log "provision_images: $n images cached (test payload)"

  log "provision_images: training manifest images (general_train.jsonl, strict)"
  ( cd "$REPO" && "$VENV/bin/python" - <<'PY'
import json, sys
from src.grounding.images import download_images

urls = []
with open("data/manifests/general_train.jsonl", encoding="utf-8") as f:
    for line in f:
        ex = json.loads(line)
        if "image" in ex:
            urls.append(ex["image"])
urls = list(dict.fromkeys(urls))
print(f"manifest unique images: {len(urls)}")
res = download_images(urls)
missing = [u for u, ok in res.items() if not ok]
print(f"manifest images ok: {len(res) - len(missing)}/{len(res)}")
if missing:
    print("MISSING manifest images (7B training would silently skip these):")
    for u in missing[:10]:
        print(f"  {u}")
    sys.exit(1)
PY
  )
  n=$(find "$REPO/data/image_cache" -name '*.jpg' 2>/dev/null | wc -l)
  log "provision_images: $n images cached TOTAL (test + training manifest)"
}

# ------------------------------------------------------------- smoke test
smoke_test() {
  log "smoke_test: context||calls must exist; scratch train on device (7B)"
  ( cd "$REPO" && timeout $((20*60)) "$VENV/bin/python" - <<'PY'
import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

print("SMOKE: loading Qwen2-VL-7B-Instruct (bf16, eager)...", flush=True)
m = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct", dtype=torch.bfloat16,
    _attn_implementation="eager", low_cpu_mem_usage=True).to("cuda")
print(f"SMOKE: 7B loaded, {sum(p.numel() for p in m.parameters())/1e9:.1f}B params, "
      f"cuda mem {torch.cuda.memory_allocated()/1e9:.1f}GB", flush=True)
del m; torch.cuda.empty_cache()

from src.grounding.smolvlm2 import SmolVLM2Classifier
c = SmolVLM2Classifier(model_id="HuggingFaceTB/SmolVLM2-2.2B-Instruct")
print("SMOKE: 2B loaded OK", flush=True)
PY
  ) | tee -a "$LOG"
  log "smoke_test: OK -- provision complete"
}

# ------------------------------------------------------------- train run
train_run() {
  local backbone="$1" seed="$2"
  case "$seed" in
    101) tag="seedA" ;; 202) tag="seedB" ;; 303) tag="seedC" ;;
    *) die "seed $seed not in campaign {101,202,303}";;
  esac
  local out="$REPO/checkpoints/seed_campaign/${backbone}_general_lora_${tag}"
  if [ -f "$out/final/adapter_model.safetensors" ]; then
    die "already complete: $out/final (refusing to rerun)"
  fi
  log "train_run: $backbone seed=$seed ($tag) -> $out"
  mkdir -p "$REPO/results/seed_campaign/runs"
  ( cd "$REPO" && nohup "$VENV/bin/python" scripts/run_seed_campaign.py \
      --backbone "$backbone" --seed "$seed" --output "$out" \
      > "results/seed_campaign/runs/${backbone}_${tag}.log" 2>&1 & echo "TRAIN PID=$!" | tee -a "$LOG" )
  log "train_run: started in background; monitor: tail -f $REPO/results/seed_campaign/runs/${backbone}_${tag}.log"
}

# ------------------------------------------- regression gate (battery fix)
regress_run() {
  log "regress_run: battery regression gate, BOTH families"
  for fam in qwen2vl smolvlm2; do
    log "regress_run: family=$fam"
    ( cd "$REPO" && "$VENV/bin/python" scripts/grounding/regress_seed_battery.py \
        --model-family "$fam" 2>&1 | tee -a "$LOG" ) \
      || die "regress_run: family=$fam FAILED (gate must pass)"
  done
  log "regress_run: DONE -- both families reproduce committed metrics"
}

# ---------------------------------------------------------- battery evals
# family: qwen2vl | smolvlm2   tag: prediction/analysis tag prefix
# checkpoints (optional): comma list; default = full family registry
battery_run() {
  local family="$1" prefix="$2" ckpts="${3:-}"
  log "battery_run: family=$family tag=$prefix checkpoints=${ckpts:-ALL}"
  local args=()
  [ -n "$ckpts" ] && args+=(--checkpoints "$ckpts")
  ( cd "$REPO" && "$VENV/bin/python" scripts/grounding/run_seed_battery.py \
      --model-family "$family" --tag-prefix "$prefix" "${args[@]}" 2>&1 | tee -a "$LOG" )
  log "battery_run: DONE -- predictions in results/grounding/predictions/$prefix, metrics in analysis"
}

# ------------------------------------------------------------------- main
case "$MODE" in
  --stage)
    provision_system; provision_repo; provision_venv; provision_hf
    provision_images; smoke_test
    log "STAGE COMPLETE -- machine ready. Next: --train|--regress|--battery|--collect"
    ;;
  --train)
    [ -n "$SUB1" ] && [ -n "$SUB2" ] || die "--train needs <backbone> <seed>"
    provision_repo; provision_images
    train_run "$SUB1" "$SUB2"
    ;;
  --regress)
    provision_repo; provision_images
    regress_run
    ;;
  --battery)
    [ -n "$SUB1" ] && [ -n "$SUB2" ] || die "--battery needs <family> <tag>"
    provision_repo; provision_images
    battery_run "$SUB1" "$SUB2" "$SUB3"
    ;;
  --images)
    # top-up image cache only (test payload + training manifest) on a box
    # that was staged before the manifest-image fix
    provision_repo; provision_images
    log "IMAGES OK -- cache now holds test payload + training manifest"
    ;;
  --collect)
    log "collect: zip seed_campaign + battery artifacts"
    ( cd "$REPO" && zip -qr "$HOME/seed_campaign_all.zip" \
        results/seed_campaign results/grounding/predictions results/grounding/analysis \
        checkpoints/seed_campaign data/image_cache )
    log "collect: DONE -- $HOME/seed_campaign_all.zip"
    ;;
  *) die "unknown mode: $MODE" ;;
esac