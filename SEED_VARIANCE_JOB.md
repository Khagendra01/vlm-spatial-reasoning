# Multi-seed job spec — run LAST, on the GPU machine (not on this box)

Reviewer Priority-3 experiment. Everything else in the revision is already
done and committed; this is the only remaining new-compute item.

## Task

Run **2 additional training seeds** (101, 202; canonical default is seed 42)
for the two highest-value conditions:

| condition | seeds | outputs |
|---|---|---|
| 7B General LoRA | 101, 202 | results/seed_variance/general/{101,202}/ |
| 7B Hard-Neg LoRA | 101, 202 | results/seed_variance/hardneg/{101,202}/ |

Report, per condition, across the 3 seeds (42 + 101 + 202):
**overall VSR, orientation, facing accuracy, facing consistency**
(mean / min / max, and the between-condition deltas vs seed-to-seed SD).

## Machine requirements (hard preflight enforced by the script)

- >= 40 GB VRAM GPU (canonical runs used 1x RTX A6000 48 GB) — the runner
  refuses to proceed otherwise, because memory tricks would change the recipe.
- Ubuntu 24.04, Python 3.12, `pip install -r requirements.txt`
  (torch 2.12.1+cu130, transformers 5.14.1, peft 0.20.0, datasets 5.0.1).
- HF read access for `Qwen/Qwen2-VL-7B-Instruct`.
- Repo checkout at `paper-draft-v1` (includes `data/manifests/*.jsonl` and
  the image cache). If `data/` is not in the checkout, sync it from the
  original training machine (manifests: general_train.jsonl,
  hardneg_train.jsonl; image cache at data/image_cache/).

## Pre-stage model and data before renting four machines

Use the first A6000 as a staging machine. Supply the Hugging Face token only
through the provider's secret/environment-variable mechanism:

```bash
export HF_TOKEN='(set through the machine secret manager; never commit it)'
huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential false
python - <<'PY'
from huggingface_hub import snapshot_download
import os
snapshot_download("Qwen/Qwen2-VL-7B-Instruct", token=os.environ["HF_TOKEN"])
PY
python - <<'PY'
from datasets import load_dataset
load_dataset("cambridgeltl/vsr_random", split="test")
PY
```

Then verify the repository manifests and image cache required by the runner:

```bash
test -f data/manifests/general_train.jsonl
test -f data/manifests/hardneg_train.jsonl
python -c "from pathlib import Path; print(len(list(Path('data/image_cache').glob('*'))))"
```

If the image cache is not already present, pre-download it using the
repository's portable downloader before starting training. Do not rely on
four machines downloading the same model and images simultaneously: that
adds avoidable startup time and can trigger Hub/network rate limits. After
the first machine is validated, repeat the setup on the other three machines
or copy the provider's prepared disk/image if supported. Confirm on every
machine that `HF_TOKEN` is available, the model loads, and the cache paths are
local before launching a seed job.

## GPU choice

The runner uses one CUDA device, bf16, eager attention, gradient
checkpointing, and batch size 1; multiple GPUs will not speed one run unless
the script is rewritten for distributed training. The canonical A6000 48 GB
is therefore a valid baseline, not a requirement on the GPU model.

Recommended choices:

1. **L40S / RTX 6000 Ada 48 GB** — best cost/speed balance when available;
   enough VRAM with newer tensor hardware than the A6000.
2. **A100 80 GB** — conservative choice if priced near an L40S; high memory
   bandwidth and ample headroom, though often less cost-efficient.
3. **H100 80 GB** — fastest minimum-wall-clock choice; worthwhile when its
   hourly price is no more than roughly 2--2.5 times an L40S/A6000.
4. **A6000 48 GB** — cheapest safe fallback and closest to the canonical run.

Avoid 24 GB cards (RTX 4090, L4, A10) and 32 GB cards for this unmodified
recipe: the preflight intentionally rejects them. Avoid two small GPUs: this
code is single-device and will not combine their VRAM. Before renting, run a
100-step benchmark and record GPU name, peak VRAM, elapsed time, and cost;
choose by **cost per completed seed**, not peak TFLOPS. To minimize wall time,
run the four jobs in parallel on four GPUs with separate
`CUDA_VISIBLE_DEVICES` values; to minimize cost, use one L40S/A6000
sequentially.

## Exact commands (run from the repository root)

```bash
# condition general
python scripts/run_seed_variance.py --condition general --seed 101
python scripts/run_seed_variance.py --condition general --seed 202
# condition hardneg
python scripts/run_seed_variance.py --condition hardneg --seed 101
python scripts/run_seed_variance.py --condition hardneg --seed 202
# aggregate (overall + orientation; facing + consistency separately below)
python scripts/aggregate_seed_variance.py
```

Each seed run writes ONLY `results/seed_variance/{condition}/{seed}/`
(predictions.csv + metrics.json). The frozen canonical snapshot is never
touched (guardrail).

## Facing accuracy + facing consistency per seed

Run the canonical consistency evaluation against each seed checkpoint
(inference on the flipped complementary statements; ~660 statements per run):

```bash
python scripts/eval_consistency_flips.py --condition seed_checkpoint \
    --lora-path results/seed_variance/general/101/checkpoint \
    --orig-csv results/seed_variance/general/101/predictions.csv \
    --out-csv results/seed_variance/general/101/consistency_flips.csv
# ... repeat for general/202, hardneg/101, hardneg/202
```

The facing (FF) family consistency and facing accuracy for each seed are read
from the printed stats and from
`results/consistency_stats_seed_*.json`. Original verdicts come from the
seed's own predictions.csv, so consistency is measured within each
checkpoint.

## What to send back

1. The full `results/seed_variance/` directory (committed on the GPU machine
   or zipped).
2. `results/seed_variance/summary.json` (from aggregate_seed_variance.py).
3. A line stating the exact hardware/software versions (nvidia-smi + pip
   freeze diff vs requirements.txt).

## What happens on this machine afterward (I will do it)

- Commit `results/seed_variance/` and update the single-checkpoint note in
  main.tex + App. D with mean/min/max over seeds and the calibrated
  between-condition deltas (softening "X outperforms Y" language where the
  measured training-run SD says so).
- Re-run `scripts/make_paper_figures.py` (canonical numbers must remain
  byte-identical), rebuild PDFs, commit.
- If the extra seeds move any headline claim, the change is logged additively
  (versioned files; frozen canonical table untouched).
