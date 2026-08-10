# VLM Spatial Reasoning

A research project exploring spatial reasoning capabilities of Vision-Language Models (VLMs).

## Project Structure

```
vlm-spatial-reasoning/
├── README.md
├── configs/           # Configuration files for experiments
├── data/              # Datasets and data processing scripts
├── src/
│   ├── models/        # Model implementations
│   ├── datasets/      # Dataset loaders and processors
│   ├── evaluation/    # Evaluation metrics and scripts
│   └── training/      # Training loops and utilities
├── scripts/           # Utility and automation scripts
├── notebooks/         # Jupyter notebooks for analysis
│   └── exploratory_analysis.ipynb
├── results/           # Experiment results and logs
├── figures/           # Generated figures and visualizations
├── paper/             # LaTeX source and figures for the paper
└── requirements.txt   # Python dependencies
```

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Usage

[Add usage instructions here]

## SITE External Validation

SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025) is used as an
evaluation-only external-validation benchmark for our VSR orientation
finding. Key documents:

- `results/site/site_protocol.md` — preregistered protocol (subsets, metrics, decision rule)
- `results/site/site_protocol.json` — frozen subset definitions incl. example IDs
- `results/site/orientation_subset_definition.md` — the heuristic orientation
  subset: why it exists (official release has no orientation tag), the exact
  keyword list, frozen IDs, and its known limitations (non-official, supporting only)
- `results/site/zeroshot_image_report.md` — step-1 results (7B zero-shot, images)
- `results/site/site_dataset_report.md` — dataset inspection
- `results/site/site_eval_run_notes.md` — engineering issues and fixes

## Techniques & conventions

`docs/TECHNIQUES.md` documents the empirically-derived conventions used
across the project: Qwen2-VL grounding coordinate space (per-axis [0,1000]),
one-box-per-query grounding, patch-grid region pooling, the `max_pixels`
regression and the 392 px resolution cap, pyav video frame sampling, and
OOM-safe batched generation.

## License

[Add license here]
