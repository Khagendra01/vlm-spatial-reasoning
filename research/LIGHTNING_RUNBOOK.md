# Lightning AI Runbook — EquiOrient ICLR Push ($0 track)

Last updated: 2026-08-22. Branch: `research/equiorient-iclr-push`.
Prereq reading: `research/EQUIORIENT_ICLR_PUSH_PREREGISTRATION.md`.

## 0. Account setup (~10 min)

1. Sign up https://lightning.ai (no card needed). Free tier ≈ 80 GPU-hrs/month.
2. New Studio → pick **A10G (24 GB)** as the GPU. If A10G is unavailable, L4
   also works; do NOT pick T4 (16GB — fails Qwen2-VL bf16).
3. Studio storage persists between sessions; GPU hours only burn while a
   session is active. **Stop the studio when done** (top-right power icon).

## 1. Smoke test (~20 min) — decides everything

Open a terminal in the studio:

```bash
git clone https://github.com/Khagendra01/vlm-spatial-reasoning
cd vlm-spatial-reasoning
git checkout research/equiorient-iclr-push
pip install torch transformers peft accelerate pillow scipy pytest

# sanity: our CPU tests should pass here too
python -m pytest tests/test_e2_bridge.py -q

python scripts/lightning_smoke_test.py
```

Read the DECISION line at the end:
- `All-E1+E2 on this A10G` → Scenario A. Continue with §2 and §3.
- `E1 switches to SmolVLM2 fallback` → Scenario B. Before any training,
  append a dated deviation entry to the preregistration file (backbone swap,
  reason = VRAM smoke test result), commit, then use §4.

## 2. E2 extraction on Lightning (~2–4 h total; resumable per checkpoint)

```bash
mkdir -p results/e2
for CFG in \
  "qwen2vl_7b '' z_qwen2vl_zero_shot" \
  "qwen2vl_7b checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedA/final z_qwen2vl_seedA" \
  "qwen2vl_7b checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedB/final z_qwen2vl_seedB" \
  "qwen2vl_7b checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedC/final z_qwen2vl_seedC"
do
  set -- $CFG
  python -m equiorient.experiments.extract_real_latents \
    --backbone "$1" --adapter "$(eval echo "$2")" \
    --image-ids research/equiorient_iclr_push/e2_image_ids.json \
    --image-cache data/image_cache \
    --out "results/e2/$3.npz"
done
```

Notes:
- VSR image cache (`data/image_cache`, md5(url).jpg) must be staged into the
  studio first (upload zip or fetch by URL — extractor skips missing files,
  so partial caches are safe but reduce n; check the printed `n=` per run).
- Each checkpoint writes its own `.npz`; losing a session loses nothing
  committed. Commit `results/e2/*.npz` after each success.

## 3. E2 analysis (CPU, anywhere)

```bash
python -m equiorient.experiments.run_e2_analysis \
  --latents 'results/e2/z_*.npz' \
  --csv results/grounding/predictions/tierc_full/zero_shot_hflip_flip.csv \
  --csv results/grounding/predictions/tierc_full/general_lora_hflip_flip.csv \
  --labels qwen2vl_zero_shot qwen2vl_general_lora_seed0 \
  --protocol-ids results/grounding/protocol/vsr_test_ids.json \
  --out results/e2/e2_analysis.json
```

## 4. E1 training on Lightning (Scenario A) or Kaggle (Scenario B)

- Scenario A (7B fits): reuse phase-2 canonical launcher
  `run_n128_clean.py` with backbone=Qwen2-VL-7B, arms equiorient/aug/wrong,
  15 matched seeds. Monitor with `nvidia-smi` in a second terminal.
- Scenario B (SmolVLM fallback): same launcher, backbone=SmolVLM2-2B;
  can also run inside Kaggle's 30h/wk P100 quota if Lightning hours run low.

## House rules (burned once already elsewhere)

1. **Stop the studio** when not actively running something — idle GPU burns
   the monthly allowance.
2. Commit every finished artifact (`results/e2/*.npz`) before stopping.
3. Log every deviation in the preregistration file *before* looking at
   downstream results.
