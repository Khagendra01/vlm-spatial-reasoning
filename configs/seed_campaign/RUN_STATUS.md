# Seed Campaign R1 — Run Status & Machine Handoff

Created 2026-08-11 at machine closure. Everything below is committed to this
branch (research/spatial-grounding-audit) so the campaign is resumable from
any machine with the same dataset artifacts.

## What the campaign is

Re-train the two general-VSR LoRA backbones (Qwen2-VL-7B-Instruct,
SmolVLM2-2.2B-Instruct) under 3 fresh seeds (A=101, B=202, C=303) with every
training-run input identical to the seed-0 runs EXCEPT the seed; evaluate
all adapters (incl. the legacy seed-0 ones) on the frozen 7-condition battery
(normal, with_sample 2px, with_shuffle, relcomp, facing, hflip, hflip_inv)
under the 392px contract; analyze seed variance; stamp the decision log.

Full frozen spec: `configs/seed_campaign/SEED_CAMPAIGN.json`
Battery rationale: `configs/seed_campaign/BATTERY_JUSTIFICATION.md`
Decision log: `SPATIAL_REASONING_DECISION_LOG.md` (campaign freeze entry)

## Machine / environment config (the closing device)

- cwd: /home/ubuntu/vlm-spatial-reasoning (repo root; scripts os.chdir there)
- GPU: single NVIDIA RTX A6000 (49 GB); Python 3.x with requirements.txt
- HF cache populated (Qwen/Qwen2-VL-7B-Instruct, HuggingFaceTB/SmolVLM2-2.2B-Instruct)
- data/image_cache/ holds every VSR test image as <md5(image_url)>.jpg;
  this dir is GITIGNORED and must be re-downloaded on a new machine
  (see src/grounding/images.py download_images; ~2195 files).
- The GPU run was launched with: nohup bash scripts/run_seed_campaign_queue.sh
  (queue logs: results/seed_campaign/runs/*.log; *.log files are gitignored but
  were force-added here for auditability).
- opencode.json: adds external-directory allow for /tmp/** (opencode-only).

## What was completed (committed)

1. configs/seed_campaign/SEED_CAMPAIGN.json — the frozen campaign spec
   (seeds, recipes, RNG semantics, battery, artifacts, analysis plan, drift notes).
2. configs/seed_campaign/BATTERY_JUSTIFICATION.md — battery contract constants.
3. SPATIAL_REASONING_DECISION_LOG.md — campaign freeze entry (FROZEN BEFORE TRAINING).
4. scripts/run_seed_campaign.py — training driver. 7B leg = verbatim copy of
   scripts/run_7b_pipeline.py PHASE 2 train_lora (collate_batch, TRAIN_PROMPT,
   split seed=42, batch=1, 2 epochs, lr=1e-4 wd=0.01, warmup steps//10, LoRA
   r8/a16/d0.05 q/k/v/o, clip 1.0, bf16, 2048); 2B leg = legacy
   src/training/lora.py train() with micro_batch=1, grad_accum=16 (CLI
   defaults the seed-0 run used; effective bs=16), split seed=42.
   Both seed the RNG (torch/cuda/numpy) per run; the 95/5 SPLIT IS FROZEN AT
   SEED=42 for every run (manifest-identical assignment).
5. scripts/run_seed_campaign_queue.sh — sequential queue for all 6 runs
   (order: 7B A,B,C then 2B A,B,C) into
   checkpoints/seed_campaign/{qwen2vl_7b,smolvlm2_2b}_general_lora_seed{A,B,C}/final
   (+ training_log.json per run incl. seed, spec_ref, per-10-step losses).
6. src/evaluation/battery.py — frozen battery ROW BUILDERS (conditions,
   strict-complement relcomp, hardneg relation pairs, family map, 392px
   sample_image; rows persisted once to results/seed_campaign/rows/*.jsonl).
   NOT YET RUNTIME-VALIDATED (id-loader fix applied at closure).
7. scripts/eval_seed_battery.py — battery eval driver (per backbone/adapter,
   392px contract, canonical prompt, greedy, max_new_tokens=5, output metrics
   + predictions mirroring legacy naming under results/seed_campaign/).

## What was in flight at closure

- Training queue was RUNNING: 7B seedA had completed model load and was in
  the training loop (see results/seed_campaign/runs/qwen2vl_7b_seedA.log);
  no adapter was saved yet (7B saves only at final). All other seeds queued.
- No battery evals had been run (they wait for training completion on the
  single GPU).

## Pending work (resume checklist)

1. Verify battery rows build + spot-check:
   python -c "from src.evaluation import battery; print(battery.row_counts())"
   Expected: normal 2195, with_sample 2195, with_shuffle 2195, facing ~137,
   relcomp fewer (strict-complement eligible ids), hflip/hflip_inv pairs of
   facing eligible ids. Rows land in results/seed_campaign/rows/*.jsonl
   (deterministic: HF test ids + frozen eligible-id files, committed).
2. Train the 6 adapters (resume remaining runs with the queue script;
   7B ~3800 steps/seed, 2B ~238 optimizer steps/seed; the queue script
   overwrites nothing that is missing — rerun the whole queue on a fresh
   machine is safe/identical).
3. Battery evals, 8 adapters (6 campaign + legacy seed-0:
   checkpoints/qwen2vl_7b_general_lora/final AND checkpoints/general_lora/final
   — both committed), e.g.:
   python scripts/eval_seed_battery.py --backbone qwen2vl_7b --adapter <path> --tag <seedA|seedB|seedC|seed0>
4. Analysis (not yet written): per-condition mean+/-std vs seed-0, per-family
   drift, hflip/hflip_inv asymmetry, with_sample/with_shuffle invariance,
   adaptation curves from training_log.json step_samples; output
   results/seed_campaign/ANALYSIS.md; append results entry to
   SPATIAL_REASONING_DECISION_LOG.md.

## Key numbers / invariants (already recovered, do not re-derive)

- seed-0 2B (checkpoints/general_lora/final training_log.json): epochs 2,
  effective bs 16, total_steps 238, epoch losses 0.513 / 0.414, 6253s, A6000.
- Canonical VSR accuracies (results/PAPER_RESULTS_SUMMARY.md): 2B General LoRA
  0.766, 7B General LoRA 0.847 (n=2195 test).
- 7B seed-0 eval (results/7B_general_lora_metrics_20260809_094930.json):
  global 0.8469, per-family incl. orientation 0.6569 (n=137).
- 392px cap: src/grounding/config.py MAX_LONG_SIDE=392 (docs/TECHNIQUES.md s4).
- Battery shuffle permutation: SHUFFLE_SEED=20260810 (constant, recorded in
  results/seed_campaign/rows/shuffle_mapping.json at build time).