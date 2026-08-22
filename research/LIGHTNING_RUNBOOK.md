# Lightning AI Runbook — EquiOrient ICLR Push ($0 track)

Last updated: 2026-08-22 (revised for the REAL tiered starter bucket).
Branch: `research/equiorient-iclr-push`.
Prereq reading: `research/EQUIORIENT_ICLR_PUSH_PREREGISTRATION.md`
(see PLANNED DEVIATIONS section — compute-driven, logged pre-GPU).

## 0. The actual budget (from the studio picker)

| Machine | VRAM | Free | Hosts |
|---|---|---|---|
| T4 | 16 GB | 36 h | SmolVLM2 training (fp16), small evals |
| L40S | 48 GB | 5 h | **Qwen2-VL bf16 inference + training** |
| A100 / H100 | 80 GB | 3 + 3 h | Qwen2-VL continuation |
| H200 | 141 GB | 2 h | reserve |

Treat the premium tiers as ONE POOLED ~13h budget ("up to 80 hrs to
start" = finite grant, not monthly). Hours burn while a session is open —
STOP the studio whenever idle.

## Allocation plan (Option 2, preregistered)

```
SESSION A — L40S (~3h of the pool):
   bootstrap one-command → smoke test → E2 ALL Qwen extractions
   → as many E1-7B pilot runs as fit (target: 2 seeds × 3 arms)
SESSION B — Colab/Kaggle T4/P100 (free, ~15h needed):
   E1 SmolVLM2-2B full campaign: 15 seeds × 3 arms in fp16
   (fp16 is a preregistered deviation #1; NOT quantization)
RESERVE — A100/H100 leftovers:
   E1-7B pilot overflow, E3 wrong-law eval sweep
```

## 1. THE one command (does smoke test → image fetch → full E2 extraction)

After creating the studio (A10G), paste this in the terminal and walk away:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Khagendra01/vlm-spatial-reasoning/research/equiorient-iclr-push/scripts/lightning_bootstrap.sh)
```

It runs: clone/checkout → deps → CPU unit tests → materialize Paper-2
adapters + CSVs → **VRAM smoke test** → fetch the frozen 245 images (~40MB,
no cache upload needed) → resumable E2 extraction loop for all Qwen2-VL
checkpoints. Ends by printing the exact commit/push commands and a reminder
to STOP the studio.

Manual step-by-step equivalent (if you prefer to run pieces yourself):

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
