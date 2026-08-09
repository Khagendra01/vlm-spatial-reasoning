# Representation Probe: Orientation Information in Frozen 7B Vision Representation

Extraction: Qwen2-VL-7B-Instruct base (no LoRA), frozen vision tower.
Levels: ViT patch embeddings (1280d, mean-pooled) | post-merger features (3584d, mean-pooled).
Train: audited-clean VSR train orientation examples | Val: VSR validation | Test: VSR test (137).
No VSR test examples used for training.

## T1_facing_vs_facingaway (vit)  n_train=327 n_test=103 majority=0.64
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.563±0.053 | 0.512 | 0.650 | 0.604 | [0.554, 0.736] |
| mlp | 0.557±0.076 | 0.419 | 0.553 | 0.520 | [0.457, 0.646] |

Per-class test accuracy:
- linear: facing: 0.797, facing away from: 0.410
- mlp: facing: 0.656, facing away from: 0.385
- Generative 7B zero-shot statement accuracy on same images: facing: 0.734, facing away from: 0.487
- Generative 7B General LoRA statement accuracy on same images: facing: 0.750, facing away from: 0.590

## T2_parallel_vs_perp (vit)  n_train=96 n_test=34 majority=0.59
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.603±0.116 | 0.750 | 0.618 | 0.610 | [0.450, 0.761] |
| mlp | 0.559±0.186 | 0.625 | 0.676 | 0.693 | [0.508, 0.809] |

Per-class test accuracy:
- linear: parallel to: 0.636, perpendicular to: 0.583
- mlp: parallel to: 0.636, perpendicular to: 0.750
- Generative 7B zero-shot statement accuracy on same images: parallel to: 0.636, perpendicular to: 0.583
- Generative 7B General LoRA statement accuracy on same images: parallel to: 0.636, perpendicular to: 0.417

## T3_4way (vit)  n_train=423 n_test=137 majority=0.50
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.437±0.025 | 0.390 | 0.526 | 0.405 | [0.442, 0.607] |
| mlp | 0.428±0.037 | 0.407 | 0.526 | 0.429 | [0.442, 0.607] |

Per-class test accuracy:
- linear: facing: 0.719, facing away from: 0.410, parallel to: 0.409, perpendicular to: 0.083
- mlp: facing: 0.750, facing away from: 0.308, parallel to: 0.409, perpendicular to: 0.250
- Generative 7B zero-shot statement accuracy on same images: facing: 0.734, facing away from: 0.487, parallel to: 0.636, perpendicular to: 0.583
- Generative 7B General LoRA statement accuracy on same images: facing: 0.750, facing away from: 0.590, parallel to: 0.636, perpendicular to: 0.417

## T1_facing_vs_facingaway (merger)  n_train=327 n_test=103 majority=0.64
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.541±0.035 | 0.535 | 0.689 | 0.645 | [0.594, 0.771] |
| mlp | 0.572±0.078 | 0.512 | 0.524 | 0.492 | [0.429, 0.618] |

Per-class test accuracy:
- linear: facing: 0.828, facing away from: 0.462
- mlp: facing: 0.625, facing away from: 0.359
- Generative 7B zero-shot statement accuracy on same images: facing: 0.734, facing away from: 0.487
- Generative 7B General LoRA statement accuracy on same images: facing: 0.750, facing away from: 0.590

## T2_parallel_vs_perp (merger)  n_train=96 n_test=34 majority=0.59
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.574±0.063 | 0.688 | 0.647 | 0.614 | [0.479, 0.785] |
| mlp | 0.479±0.138 | 0.688 | 0.647 | 0.633 | [0.479, 0.785] |

Per-class test accuracy:
- linear: parallel to: 0.727, perpendicular to: 0.500
- mlp: parallel to: 0.682, perpendicular to: 0.583
- Generative 7B zero-shot statement accuracy on same images: parallel to: 0.636, perpendicular to: 0.583
- Generative 7B General LoRA statement accuracy on same images: parallel to: 0.636, perpendicular to: 0.417

## T3_4way (merger)  n_train=423 n_test=137 majority=0.50
| Probe | CV acc | Val acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|---|
| linear | 0.442±0.038 | 0.356 | 0.533 | 0.440 | [0.450, 0.614] |
| mlp | 0.447±0.048 | 0.356 | 0.474 | 0.432 | [0.393, 0.558] |

Per-class test accuracy:
- linear: facing: 0.719, facing away from: 0.436, parallel to: 0.273, perpendicular to: 0.333
- mlp: facing: 0.547, facing away from: 0.333, parallel to: 0.682, perpendicular to: 0.167
- Generative 7B zero-shot statement accuracy on same images: facing: 0.734, facing away from: 0.487, parallel to: 0.636, perpendicular to: 0.583
- Generative 7B General LoRA statement accuracy on same images: facing: 0.750, facing away from: 0.590, parallel to: 0.636, perpendicular to: 0.417

## Interpretation guide
- Linear probe >> chance AND >> generative decision on same images:
  orientation info IS in the frozen representation; the generative pathway fails to use it.
- Linear weak but MLP strong: info present but not linearly accessible.
- Both weak: representation itself lacks orientation info (shift to vision-side adaptation).
- Note: probe classifies the RELATION (facing vs facing-away, etc.); the generative
  reference is statement-truth accuracy (True/False) on the same images. Tasks differ,
  so the comparison is indicative, not exact.
