# Orientation Deep-Dive: Persistent Failure Analysis

## Setup

We defined **persistent orientation failures** as examples wrong under multiple conditions:
- Set A (gold): wrong in both 7B zero-shot AND 7B LoRA (20 cases)
- Set C: wrong in ≥3 of 4 conditions (38 cases)
- Set E: wrong in both 2B zero-shot AND 7B zero-shot (28 cases)
- **Union = 48 cases** (our annotation set)

Conditions compared: 2B zero-shot, 2B General LoRA, 7B zero-shot, 7B General LoRA.

## Failure Mode Distribution (48 cases annotated)

| Failure Mode | Count | % | Interpretation |
|---|---|---|---|
| **clear_image_model_reasoning_failure** | 18 | 37.5% | Image is clear, pose is obvious, model still gets it wrong |
| camera_viewpoint_ambiguity | 8 | 16.7% | Perspective/angle makes spatial relationship genuinely hard |
| parallel_perpendicular_geometry | 6 | 12.5% | Models fail on angular/geometric assessment |
| annotation_questionable | 5 | 10.4% | Ground-truth label itself may be incorrect |
| intrinsic_orientation_ambiguous | 4 | 8.3% | Object has no clear intrinsic "front" (banana, bed, hair dryer) |
| front_back_object_ambiguous | 4 | 8.3% | Reference object's position requires inference |
| small_occluded_object | 2 | 4.2% | Reference object is tiny or partially hidden |
| subject_reference_inversion | 1 | 2.1% | Model confuses which object is the reference |

## Key Findings

### 1. The dominant failure is reasoning, not vision

**37.5% of persistent failures are clear images where the model simply reasons wrong.** The objects are visible, the pose is unambiguous, the spatial relationship is human-readable — and the model still fails. This is the single most important finding.

Examples:
- ID 33: Cat facing out of sink, facing away from it. Label=True. Image clear. Models wrong.
- ID 156: Knight looking left, horse on right. Person faces away from horse. Clear. Models wrong.
- ID 1202: Vulture facing elephant in background. Clear. 7B got it wrong despite 2B getting it right.

### 2. Only 4.2% are vision-limitation cases

Small/occluded objects account for just 2/48 failures. **The vision encoder is not the bottleneck.** SigLIP frozen or not, the visual features are sufficient for orientation in 95.8% of hard cases.

### 3. "Facing away from" dominates both failures and annotations

- 18/48 (37.5%) persistent failures are "facing away from" statements
- 15/48 (31.3%) are "facing" statements
- Together "facing"/"facing away from" = 68.8% of all persistent failures
- This relation pair is where the models are most confused

### 4. Annotation quality limits the ceiling

5/48 (10.4%) labels are questionable. Examples:
- ID 239: Cat IN toilet facing INTO bowl, labeled "facing away from" (seems wrong)
- ID 1905: Teddy bear facing camera not baby, labeled "facing the person" (seems wrong)
- ID 362: Cat looking at keyboard, labeled "not facing" (seems wrong)

If ~10% of orientation labels are unreliable, the achievable ceiling is ~90% even with perfect models.

### 5. 7B models REGRESS on clear cases

9 examples where 2B zero-shot got it right but 7B zero-shot got it wrong:
- 4/9 are clear_image_model_reasoning_failure
- 3/9 are camera_viewpoint_ambiguity
- 1/9 is parallel_perpendicular_geometry
- 1/9 is front_back_object_ambiguous

**Scaling from 2B→7B makes some clear cases harder, not easier.** This is evidence that larger VLMs don't simply "understand spatial relations better" — they can acquire systematic biases.

### 6. LoRA helps on clear cases but not on ambiguous ones

Among the 18 clear_image_model_reasoning_failure cases:
- 14 are wrong in 3/4 conditions (LoRA fixes some)
- 4 are wrong in 2/4 conditions (7B-persistent, LoRA doesn't fix)

LoRA can partially correct clear-case reasoning failures but cannot fix the hardest ones.

## Intervention Recommendation

### Priority 1: Hard negatives (NOT vision adaptation)

Since 37.5% of failures are clear images with wrong reasoning, and only 4.2% are vision limitations:

**Hard-negative training** targeting:
- "facing" vs "facing away from" inversions (the dominant confusion)
- Subject/reference object swaps
- "parallel" vs "perpendicular" geometric pairs

This is the most promising intervention because:
1. The failures are reasoning failures, not perception failures
2. Hard negatives directly address the confusion patterns
3. LoRA already partially works on clear cases — hard negatives should push further

### Priority 2: Annotation audit

10.4% of labels are questionable. Before any training intervention:
- Audit the full 137 orientation test set for label quality
- Remove or correct questionable annotations
- This raises the achievable ceiling for all conditions

### Priority 3: Vision encoder adaptation (deferred)

Only 4.2% of persistent failures are vision-limited. Vision-side LoRA (on SigLIP) is NOT justified by this analysis. Defer until hard negatives are tested.

## Appendix: Per-Relation Accuracy Across 4 Conditions

| Relation | N | 2B Zero | 2B LoRA | 7B Zero | 7B LoRA |
|---|---|---|---|---|---|
| facing | 64 | 70.3% | 68.8% | 73.4% | **75.0%** |
| facing away from | 39 | 53.8% | 53.8% | 48.7% | **59.0%** |
| parallel to | 22 | 59.1% | 59.1% | 63.6% | 63.6% |
| perpendicular to | 12 | 58.3% | 58.3% | 58.3% | 41.7% |

**"facing away from" is the hardest relation** (53.8% → 48.7% → 59.0%) and the most annotation-questionable.
