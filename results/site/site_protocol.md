# SITE External-Validation Protocol (Preregistered)

**Status: FROZEN on 2026-08-09, before any model evaluation.** Subset
definitions, metrics, and the decision rule are fixed in
`results/site/site_protocol.json` (example IDs included). No post-hoc subset
selection.

## Motivation

VSR experiments established that spatial orientation (facing / facing-away,
front / behind, parallel / perpendicular) is a persistent weakness for
Qwen2-VL-7B across conditions: zero-shot, LM-only LoRA, hard-negative LoRA,
vision/projector LoRA, probes (global, object-grounded, patch), and explicit
two-stage reasoning. SITE (ICCV 2025) is an independent benchmark with an
official spatial-relationship category — the external-validation check.

**Constraint: evaluation-only. No training or fine-tuning on SITE.**

## Frozen subsets

| Subset | Definition | n | Headline? |
|---|---|---|---|
| **Primary** | official category `spatial relationship reasoning` | 1,721 | **Yes** |
| **Secondary** | heuristic orientation keywords (non-official) | 3,272 | No (supporting only) |
| **Exploratory** | official category `movement prediction & navigation` | 1,103 | No |

Example IDs for all three are frozen in `site_protocol.json` (`frozen_ids`).
Overlaps: primary ∩ secondary = 872, secondary ∩ exploratory = 808,
primary ∩ exploratory = 0; union = 4,416 unique examples, evaluated once.

## Evaluation protocol (step 1: 7B zero-shot)

- Model: **Qwen2-VL-7B-Instruct, frozen, zero-shot** — no LoRA, no VSR
  training data.
- Format: SITE native multiple-choice. Prompt replicated from the official
  lmms-eval task (`eval_scripts/sitebench/utils.py`):
  - Image: `Question: ...\nOptions:\nA: ...\nB: ...` + post-prompt
    "Give me the answer letter directly. The best answer is:"; `<image>`
    placeholders handled per official logic.
  - Video: pre-prompt "Select the best answer ... letter of the correct
    option." + Question/Options + same post-prompt; 16 uniformly sampled
    frames (pyav; documented deviation: official harness decodes via
    torchvision/torchcodec, equivalent frame-sampling behavior).
- Generation: greedy (temperature 0, `do_sample=False`), max 128 tokens.
- Parsing: official `parse_multi_choice_response` (letter), no random
  fallback — unparseable → incorrect, counted as `unparseable`.
- Metrics per subset:
  - raw accuracy + 95% Wilson CI
  - chance-adjusted accuracy (official): `Σ(score − 1/n_opts) / Σ(1 − 1/n_opts)`
  - breakdown by modality (single-image / multi-image / video, n ≥ 30)
  - breakdown by source dataset (n ≥ 30)
  - media-missing and unparseable counts reported

## Decision rule (preregistered)

1. **If the primary subset shows the same broad weakness pattern**
   (spatial-relationship CAA clearly below the model's other SITE
   categories / below published baselines): run the existing **VSR-trained
   7B General LoRA** on the exact same SITE examples (preregistered step 2).
2. **Else if only the heuristic orientation subset shows the effect:**
   narrow the claim to object/direction-related orientation, not "spatial
   orientation" broadly.
3. **Else (neither shows the effect):** the VSR bottleneck is benchmark- or
   relation-specific; report that explicitly.

## Anti-cheery-picking rules

- The official spatial-relationship category is the headline subset; the
  keyword-derived orientation subset is supporting analysis and must be
  labeled non-official in any write-up.
- No subset is added, dropped, or re-weighted after seeing results.
- All evaluations of a condition use the identical frozen example list.

## Artifacts

- `results/site/site_protocol.json` — frozen config + example IDs
- `results/site/needed_media.txt` — media files required by the subsets
- `scripts/download_site_media.py` — zip-by-zip media acquisition
- `scripts/eval_site_zeroshot.py` — step-1 evaluation
- `results/site/site_dataset_report.md` — dataset inspection
