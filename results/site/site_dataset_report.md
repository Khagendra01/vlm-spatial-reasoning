# SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025) — Dataset Inspection

## Source

- Paper: *SITE: towards Spatial Intelligence Thorough Evaluation* (ICCV 2025), arXiv:2505.05456
- Dataset (official): https://huggingface.co/datasets/franky-veteran/SITE-Bench (CC-BY-4.0)
- Code: https://github.com/wenqi-wang20/SITE-Bench

## Purpose

SITE is an **external-validation** benchmark for our VSR orientation finding. It is evaluation-only in this project: no training or fine-tuning on SITE.
This report documents which SITE subsets can serve as an independent test of the VSR orientation weakness.

## Overview: 8068 examples (official test splits only)

| Config | Count | Modality |
|---|---|---|
| image_test | 4449 | single-image / multi-image questions |
| video_test | 3619 | video questions |

## Counts by SI factor (official `category`)

| SI factor | Count | % |
|---|---|---|
| counting & existence | 1702 | 21.1% |
| object localization & positioning | 965 | 12.0% |
| 3d information understanding | 945 | 11.7% |
| multi-view & cross-image reasoning | 1632 | 20.2% |
| spatial relationship reasoning | 1721 | 21.3% |
| movement prediction & navigation | 1103 | 13.7% |

## Spatial orientation

Heuristic orientation-relevant subset (keyword match on question/options; **not an official tag**): **3272 examples (40.6%)**.

By category:
- counting & existence: 82
- object localization & positioning: 413
- 3d information understanding: 92
- multi-view & cross-image reasoning: 1005
- spatial relationship reasoning: 872
- movement prediction & navigation: 808

By modality:
- video: 1248
- single-image: 1012
- multi-image: 1012

Top source datasets in the orientation subset:
- MVBench: 404
- VSIBench: 324
- exoego4d: 316
- egoexo4d: 288
- ActivityNetQA: 269
- MMTBench: 237
- SAT: 183
- MMIU: 133
- TVQA: 126
- CLEVR: 106
- SPEC: 102
- SpatialEval: 100
- ThreeDSRBench: 95
- MMERealWorld: 89
- OpenEQA: 70

Top orientation keywords (question/option text):
- `left`: 1715
- `right`: 1675
- `view`: 677
- `facing`: 491
- `front`: 467
- `direction`: 426
- `behind`: 287
- `in front of`: 279
- `away from`: 121
- `face`: 114
- `rotation`: 108
- `orient`: 103
- `orientation`: 99
- `toward`: 95
- `towards`: 81
- `clockwise`: 66
- `rotate`: 35
- `rotated`: 35
- `turned`: 27
- `faces`: 26

## Intrinsic vs extrinsic

**Not available.** The official SITE-Bench release exposes only `question`, `options`, `category`, `answer`, `dataset`, `visual`. The intrinsic/extrinsic axis of the paper's taxonomy is not released per example; `intrinsic_extrinsic` is therefore `None` in normalized records.

## Modality counts

| Modality | Count | % |
|---|---|---|
| single-image | 2282 | 28.3% |
| multi-image | 2167 | 26.9% |
| video | 3619 | 44.9% |

## Which subsets can test our VSR orientation findings

1. **Spatial Relationship Reasoning** category (1721 examples): closest analogue to VSR statements (relative relations between objects), including left/right, front/behind, facing-type relations.
2. **Orientation-relevant heuristic subset** (3272 examples): questions containing orientation vocabulary (facing, direction, view, rotation, left/right, parallel/perpendicular...). Largest contributors: MVBench (404), VSIBench (324), exoego4d (316), egoexo4d (288), ActivityNetQA (269).
3. **Movement Prediction & Navigation** category (1103 examples): dynamic direction/orientation reasoning (video), a distinct extension beyond static VSR orientation.

Note: per-example ground truth in SITE is **multiple-choice**, so comparisons with VSR (True/False) require chance-adjustment (official metric: Chance-Adjusted Accuracy).