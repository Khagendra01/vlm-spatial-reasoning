#!/usr/bin/env bash
# ONE-COMMAND Lightning bootstrap. After creating a studio (A10G 24GB), paste:
#   bash <(curl -sL https://raw.githubusercontent.com/Khagendra01/vlm-spatial-reasoning/research/equiorient-iclr-push/scripts/lightning_bootstrap.sh)
# Or clone first and run: bash scripts/lightning_bootstrap.sh
set -e

REPO=vlm-spatial-reasoning
BRANCH=research/equiorient-iclr-push

if [ ! -d "$REPO" ]; then
  git clone "https://github.com/Khagendra01/${REPO}.git"
fi
cd "$REPO"
git fetch origin "$BRANCH" paper2/wacv2027
git checkout "$BRANCH"

echo "== [1/6] deps =="
pip install -q torch transformers peft accelerate pillow scipy pytest requests

echo "== [2/6] CPU unit tests =="
python -m pytest tests/test_e2_bridge.py -q

echo "== [3/6] materialize Paper-2 artifacts (adapters + hflip CSVs) =="
git checkout origin/paper2/wacv2027 -- \
  checkpoints/seed_campaign results/grounding/predictions/tierc_full || \
  echo "WARN: some paper2 paths missing; extraction may skip adapters"

echo "== [4/6] VRAM smoke test (THE decision point) =="
python scripts/lightning_smoke_test.py | tee smoke.log

if ! grep -q "INFERENCE-FIT.*PASS" smoke.log; then
  echo "RESULT: this GPU cannot host Qwen2-VL bf16 — use the L40S studio (48GB), not T4."
  exit 1
fi

echo "== [5/6] fetching the frozen 245 E2 images (~40 MB) =="
python scripts/fetch_e2_images.py

echo "== [6/6] E2 extraction loop (resumable) =="
bash scripts/run_e2_lightning.sh

# E1-7B pilot (preregistered: up to 2 seeds x 3 arms) — only if TRAIN-FIT passed
if grep -q "TRAIN-FIT.*PASS" smoke.log; then
  echo "TRAIN-FIT passed — E1-7B pilot eligible on this machine."
  echo "Launch via phase-2 canonical runner with backbone=Qwen2-VL-7B,"
  echo "seeds limited to the preregistered pilot set (see runbook §4)."
else
  echo "TRAIN-FIT failed — E1 proceeds via preregistered SmolVLM fallback"
  echo "(deviation #1/#2 already logged pre-GPU in the preregistration file)."
fi

echo ""
echo "================ DONE — next steps ================"
echo "1) Commit artifacts:"
echo "   git add results/e2 smoke.log && git commit -m 'e2: lightning extraction' "
echo "2) Push (needs your GitHub token):"
echo "   git push origin HEAD:research/equiorient-iclr-push"
echo "3) STOP the studio (top-right power icon) to save free hours."
echo "4) If TRAIN-FIT was FAIL, also log the SmolVLM deviation in"
echo "   research/EQUIORIENT_ICLR_PUSH_PREREGISTRATION.md BEFORE any training."
