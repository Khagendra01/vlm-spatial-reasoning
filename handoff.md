# HANDOFF.md — Seed Campaign R1: local prep done, resume on GPU cloud

**Branch:** `research/spatial-grounding-audit` (all state below is committed and
pushed to origin; this file travels with the clone).
**Campaign spec (frozen):** `configs/seed_campaign/SEED_CAMPAIGN.json`
**Prior handoff (A6000 closure):** `configs/seed_campaign/RUN_STATUS.md`
**Decision log:** `SPATIAL_REASONING_DECISION_LOG.md` (append-only)

---

## 1. Current state (TL;DR)

- Battery rows: **BUILT, VALIDATED, COMMITTED** (commit `43e0aa0`).
  Counts: normal 2195 / with_sample 2195 / with_shuffle 2195 / relcomp 666 /
  facing 103 / hflip 103 / hflip_inv 103. Files: `results/seed_campaign/rows/*.jsonl`
  (+ `shuffle_mapping.json`). **Do not rebuild** — identical rows are required
  across all adapters.
- Battery driver bugs fixed in `src/evaluation/battery.py` (commit `43e0aa0`):
  - `_load_test_rows()` now reads the frozen `results/grounding/protocol/vsr_test_ids.json`
    manifest for IDs (the HF hub test split has **no `id` column**; old loader
    produced `id=None` rows that silently zeroed facing/relcomp/hflip).
  - `_eligible_ids()` now handles the `{"entries": {id: meta, ...}, "law", "n_eligible"}`
    shape of the protocol JSONs.
- **2B seed-A training was started on a local RTX 3060 Ti and ABORTED at ~2h
  (no checkpoint saved — the driver only saves at step 100/238). Nothing to
  resume; restart from scratch on the GPU machine.** Logs kept for audit:
  `results/seed_campaign/runs/smolvlm2_2b_seedA.log` (+ `.err.log`).
- Local machine verdict: 3060 Ti runs 2B training at >65 s/step (est. 5-8 h/
  seed) vs **26 s/step on the A6000 (~104 min/seed)**. **Do not train on the
  3060 Ti.** It also cannot hold 7B (bf16 needs ~15 GB VRAM).
- Filename fix `6140814`: 12 result PNGs with `:` renamed to `_` repo-wide.

## 2. What remains (resume checklist)

1. **Train 6 adapters** (below). Order: 2B seeds A,B,C then 7B A,B,C (or use
   the queue script for everything).
2. **Battery evals, 8 adapters** (6 campaign + legacy seed-0 7B and 2B —
   seed-0 checkpoints are committed: `checkpoints/qwen2vl_7b_general_lora/final`,
   `checkpoints/general_lora/final`).
3. **Analysis** (not yet written): per SEED_CAMPAIGN.json `analysis_plan` →
   `results/seed_campaign/ANALYSIS.md`; append results entry to
   `SPATIAL_REASONING_DECISION_LOG.md`.

## 3. Fresh-machine environment setup (Linux GPU box, e.g. the A6000)

```bash
git clone -b research/spatial-grounding-audit https://github.com/Khagendra01/vlm-spatial-reasoning.git
cd vlm-spatial-reasoning
pip install -r requirements.txt          # now includes peft + num2words (both required)
pip install torch --index-url https://download.pytorch.org/whl/cu128   # or matching CUDA
```

- **Image cache** (gitignored; ~1874 unique files): `python scripts/grounding/download_images.py`
  (verify: `python -c "import json; from src.grounding.images import ensure_cached; d=json.load(open('results/grounding/protocol/vsr_test_ids.json')); print(len(ensure_cached([m['image_link'] for m in d['examples']], strict=False)))"` → 0)
- **HF models** auto-download on first use (SmolVLM2-2.2B ~5 GB; Qwen2-VL-7B ~15 GB).
  If `HF_HUB_ENABLE_HF_TRANSFER=1` is set, also `pip install hf_transfer` (or unset it).
- A6000 box re-spin (from RUN_STATUS.md): cwd `/home/ubuntu/vlm-spatial-reasoning`,
  HF cache + image cache already populated there.

## 4. Training — exact commands

2B (one per seed; tag A=101, B=202, C=303). ~104 min/seed on A6000:

```bash
python scripts/run_seed_campaign.py --backbone smolvlm2_2b --seed 101 \
  --output checkpoints/seed_campaign/smolvlm2_2b_general_lora_seedA
# ... seed 202 -> ..._seedB ; seed 303 -> ..._seedC
```

7B (or everything): the queue script is resumable/overwrites-nothing:

```bash
nohup bash scripts/run_seed_campaign_queue.sh   # 7B A,B,C then 2B A,B,C
```

Verify: `training_log.json` per run records `seed`, `split_seed=42`,
`backbone`, epoch losses. Seed-0 2B sanity targets: epoch losses 0.513 / 0.414.
Hardware caveat: seed-0 was A6000 — run all campaign seeds on the SAME machine
for a clean cross-seed comparison (GPU model is not part of the frozen contract).

## 5. Battery evals — exact commands

Rows are committed; the eval driver (`scripts/eval_seed_battery.py`) reads
`results/seed_campaign/rows/` (392px contract, greedy, max_new_tokens=5).
Per adapter, e.g.:

```bash
python scripts/eval_seed_battery.py --backbone smolvlm2_2b \
  --adapter checkpoints/seed_campaign/smolvlm2_2b_general_lora_seedA/final --tag seedA
# tags: seedA|seedB|seedC (campaign), seed0 (legacy: --adapter checkpoints/general_lora/final)
# 7B: --backbone qwen2vl_7b --adapter checkpoints/seed_campaign/qwen2vl_7b_general_lora_seedA/final
#      legacy seed0: --adapter checkpoints/qwen2vl_7b_general_lora/final
```

8 adapters total. Outputs mirror legacy naming under `results/seed_campaign/`.

## 6. Commit/push conventions

- `results/seed_campaign/runs/*.log` and checkpoint `training_log.json` are
  gitignored but **force-added** for auditability (`git add -f`).
- Adapters (LoRA r=8, small) are committed per RUN_STATUS.md precedent.

## 7. Gotchas learned on Windows (don't repeat)

- `pip install torch==2.8.0` does NOT upgrade `2.8.0+cpu` (PEP 440 local
  version) — pin `torch==2.8.0+cu128` explicitly.
- PowerShell 5.1 pipes CRLF into native stdin → git `--index-info` keeps a
  trailing `\r` in paths; feed LF via a temp file + `cmd /c "... < file"`.
- `Start-Process python` may resolve a different interpreter than the shell —
  use the full path to the venv/python with the deps.
- `hf_transfer` on Windows can fail with `os error 32` (file lock) — set
  `HF_HUB_ENABLE_HF_TRANSFER=0`.
- `num2words` is required by the SmolVLM processor (now in requirements.txt).
- 2B training on 3060 Ti: fits VRAM (7.9/8 GB) but ~3-5x slower than A6000 — use only for prep/analysis.

## 8. Key references

- `configs/seed_campaign/SEED_CAMPAIGN.json` (frozen spec; seeds, RNG, battery, analysis plan)
- `configs/seed_campaign/BATTERY_JUSTIFICATION.md` (contract constants)
- `configs/seed_campaign/RUN_STATUS.md` (A6000 machine config + key invariants)
- `SPATIAL_REASONING_DECISION_LOG.md` (freeze + closure entries)

## 2026-08-12 machine decommission (cloud box terminated)

- All repo content pushed (branch `research/spatial-grounding-audit`, commits up to c46b447 + weights commit).
- Trained weights in git: seed-0 (general_lora 2B, qwen2vl_7b_* variants) + campaign smolvlm2_2b_general_lora_seedA (checkpoint-100/200/final + training_log.json). Campaign seedB/C 2B + all 7B legs produced NO checkpoints (deadlock rc/TypeError pre-ff51ab5; deadlock investigation open - see DECISION_LOG 2026-08-12 entry).
- Env: requirements.freeze.txt = exact pip versions on this box (torch/transformers/peft pins matter for the first-backward deadlock repro).
- NOT in git (recreate on new box): HF hub model cache (SmolVLM2-2.2B-Instruct, Qwen2-VL-7B-Instruct ~7GB), data/image_cache (539MB COCO training images; regenerable via collator urllib fallback or `load_manifest` fetch), grounding image cache (~1874 unique images; re-download via run_tier_a image cache verification), results/grounding/private/ hashes (gitignored by design).
- Resume on new box: pip install -r requirements.freeze.txt, python scripts/grounding/freeze_protocol.py (ids), then run_seed_campaign.py legs via the queue pattern; battery = scripts/grounding/run_seed_battery.py gated by regress_seed_battery.py.
