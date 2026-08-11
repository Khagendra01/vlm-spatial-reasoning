#!/bin/bash
# Seed campaign queue: sequential background runner for scripts/run_seed_campaign.py
# Runs 3 seeds x 2 backbones; logs live in this dir (repo-local, no external paths).
cd /home/ubuntu/vlm-spatial-reasoning
RUNS="results/seed_campaign/runs"
mkdir -p "$RUNS"

for spec in "qwen2vl_7b:101:seedA" "qwen2vl_7b:202:seedB" "qwen2vl_7b:303:seedC" "smolvlm2_2b:101:seedA" "smolvlm2_2b:202:seedB" "smolvlm2_2b:303:seedC"; do
  IFS=':' read -r bb seed tag <<< "$spec"
  out="checkpoints/seed_campaign/${bb}_general_lora_${tag}"
  echo "[$(date +%H:%M:%S)] START $bb seed=$seed $tag" >> "$RUNS/queue_status.log"
  python scripts/run_seed_campaign.py --backbone "$bb" --seed "$seed" --output "$out" > "$RUNS/${bb}_${tag}.log" 2>&1
  rc=$?
  echo "[$(date +%H:%M:%S)] DONE $bb $tag rc=$rc" >> "$RUNS/queue_status.log"
done
echo "[$(date +%H:%M:%S)] QUEUE COMPLETE" >> "$RUNS/queue_status.log"