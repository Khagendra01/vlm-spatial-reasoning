# Object-Grounded Representation Probe

## Question

The ungrounded probe (global mean-pooling) showed orientation weakly decodable
from frozen Qwen2-VL-7B vision features. But VSR is object-pair-relational
("X is facing Y"), and a global readout doesn't know which objects to compare.
This probe conditions the readout on **subject and reference object regions**:
does orientation signal appear once the probe is object-conditioned?

## Setup

- Same frozen Qwen2-VL-7B-Instruct features, same splits as the ungrounded
  probe (train = audited-clean 423, val, test 137; no test used for training).
- **Grounding:** subject/reference boxes obtained with frozen Qwen2-VL
  grounding (94.6% of 647 images have both boxes; failures are mostly
  genuinely absent objects). Boxes rescaled from Qwen 1000-space to pixels.
- **Region pooling:** per-image patch embeddings (ViT 14px grid, merger 28px
  grid), mean-pooled over patches whose centers fall inside each box.
- **Feature sets (kept separate):**
  - `visual` = [subj, ref, subj−ref, subj·ref] (5120d / 14336d)
  - `geometry` = 12d normalized box features: centers, Δx/Δy, widths/heights,
    relative size, IoU
  - `visual_geometry` = concat
- Probes: linear LR + MLP(256); 5-fold CV, test accuracy + balanced acc vs
  majority.

## Results (test acc / balanced acc; majority in parens)

### T1 facing vs facing-away (majority 63.7%)

| Readout | ungrounded CV | **grounded visual** | grounded geometry | grounded vis+geom |
|---|---|---|---|---|
| vit linear | 56.3% | 59.8% / 61.6 (57.9) | 61.1 / 60.6 (48.9) | 58.8 / 63.6 (59.0) |
| vit mlp | 55.7% | 59.5 / 66.7 (64.1) | 61.8 / 62.6 (51.6) | 56.3 / 59.6 (53.6) |
| merger linear | 54.1% | 57.2 / 65.7 (63.3) | 61.1 / 60.6 (48.9) | 57.9 / 65.7 (63.3) |
| merger mlp | 57.2% | 56.3 / 52.5 (49.0) | **61.1 / 71.7 (66.5)** | 56.6 / 67.7 (61.7) |

**Object-conditioned visual features: no jump.** Grounded CV 56–60% ≈
ungrounded CV ≈ majority. Test numbers hover at majority (63–67% vs 63.7%
baseline). The single above-chance cell is the **geometry-only merger MLP**
(71.7% test, balanced 66.5%) — a box-statistics signal, not a vision-feature
signal — and its CV (61.1%) is still below majority, so it is not robust.
Per-class it is lopsided (facing 87%, facing-away 46%).

### T2 parallel vs perpendicular (majority 57.0%)

| Readout | ungrounded | grounded visual | grounded geometry | grounded vis+geom |
|---|---|---|---|---|
| vit linear | 60.3 CV / 61.8 | 51.2 / 53.6 (51.0) | 44.2 / 50.0 | 51.2 / 53.6 |
| vit mlp | 55.9 / 67.6 | 45.4 / 46.4 | 45.4 / 46.4 | 42.9 / 67.9 (65.6) |
| merger linear | 57.4 / 64.7 | 51.2 / 53.6 (50.0) | 44.2 / 50.0 | 51.3 / 53.6 |
| merger mlp | 47.9 / 64.7 | 49.0 / 53.6 | 50.0 / 42.9 | 44.3 / 57.1 |

Grounding did **not** help T2; region-pooling performed *worse* than the
ungrounded patch-vote probe (73.5% ungrounded patch-vote vs ~54–68% grounded).

### T3 4-way orientation (majority 49.9%)

| Readout | ungrounded | grounded visual | grounded geometry | grounded vis+geom |
|---|---|---|---|---|
| vit linear | 43.7 / 52.6 | 45.3 / 50.4 (41.6) | 48.1 / 48.8 | 46.3 / 52.8 (44.0) |
| vit mlp | 42.8 / 52.6 | 43.1 / 41.7 | 46.1 / 52.0 | 46.9 / 45.7 |
| merger linear | 44.2 / 53.3 | 43.9 / 52.0 (43.9) | 48.1 / 48.8 | 43.9 / 50.4 |
| merger mlp | 44.7 / 47.4 | 41.1 / 44.9 | 47.6 / 48.0 | 44.9 / 52.8 (38.6) |

At chance everywhere, same as ungrounded.

## Interpretation (decision outcome)

The user's decision rule: if the object-grounded probe jumps substantially on
facing/facing-away → orientation is locally encoded but needs object-conditioned
readout → target the projector/reasoning interface. If it stays near chance →
the frozen visual representation genuinely lacks object-intrinsic orientation.

**Outcome: the grounded probe stays near chance on the visual features.**
- T1 visual CV 56–60% vs 63.7% majority — no improvement from object
  conditioning, no improvement from nonlinearity.
- The one jump (geometry-only, 71.7% test) is box statistics from the model's
  own grounding, not vision-feature content; it does not survive CV.
- T2 (parallel/perp) was the only task with *any* ungrounded signal (patch-vote
  73.5%) and grounding did not improve it. If anything, the asymmetry is the
  reverse of the hoped-for one: geometric scene orientation was weakly
  readable globally, object-intrinsic facing is not readable even grounded.

**Conclusion:** the frozen vision representation does not contain
robustly decodable object-intrinsic orientation information, and the absence
is not an artifact of global pooling. This is the measurement needed to make
**vision-side / projector adaptation scientifically justified** — it targets a
measured deficiency, not a speculative knob.

## Caveats

1. Boxes are model-generated (frozen Qwen2-VL grounding), not ground truth;
   imperfect localization blunts but does not fabricate the result. A
   detection-model cross-check (e.g., OWL-ViT) is a possible follow-up.
2. Region pooling mean-pools box interiors, including background patches;
   attention-weighted pooling within boxes could be sharper.
3. T2 has small n (86 train / 28 test) → wide CIs.
4. Geometry features derive from the model's own boxes, so the modest
   geometry signal may partly reflect the grounding model's perceptual
   biases, not scene truth.

## Files

- `results/probe/grounded_boxes.json` — subject/reference boxes (612/647 both)
- `results/probe/patch_embeddings.pkl` — per-patch ViT + merger embeddings
- `results/probe/grounded_probe_results.json` — full results
- `scripts/ground_objects.py`, `scripts/extract_patch_embeddings.py`,
  `scripts/run_grounded_probe.py`
