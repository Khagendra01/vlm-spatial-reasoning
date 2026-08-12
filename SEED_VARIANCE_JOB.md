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
