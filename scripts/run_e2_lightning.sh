#!/usr/bin/env bash
# E2 extraction loop for Lightning (Scenario A). Resumable: skips .npz that exist.
set -u
mkdir -p results/e2

run_one () {  # backbone adapter outname
  out="results/e2/$3.npz"
  if [ -f "$out" ]; then echo "skip $out (exists)"; return 0; fi
  echo "=== extracting $3 ==="
  python -m equiorient.experiments.extract_real_latents \
    --backbone "$1" --adapter "$2" \
    --image-ids research/equiorient_iclr_push/e2_image_ids.json \
    --out "$out" || return 1
}

run_one qwen2vl_7b "" z_qwen2vl_zero_shot
for S in seedA seedB seedC; do
  run_one qwen2vl_7b "checkpoints/seed_campaign/qwen2vl_7b_general_lora_${S}/final" "z_qwen2vl_${S}"
done

echo "all qwen2vl extractions complete:"; ls -la results/e2/
