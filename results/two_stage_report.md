# Two-Stage Object-Centric Reasoning vs End-to-End Generative Control

## Question

Does explicit object-centric decomposition succeed where end-to-end
generative reasoning fails?

```
image + statement
      ↓
localize subject + reference        (frozen Qwen2-VL grounding)
      ↓
explicit relation module            (geometry and/or region features)
      ↓
True / False                        (predicted relation == claimed relation)
```

## Setup

- **Stage 1:** subject/reference boxes from frozen Qwen2-VL grounding
  (612/647 examples; 10 no-box test statements count as wrong — honest
  pipeline failure).
- **Stage 2 (two versions):**
  - **A) geometry-only:** 24-dim features — box centers, Δx/Δy, distance,
    angle, directional bits, sizes, aspect ratios, areas, relative size,
    overlap, IoU, containment. No pixels.
  - **B) geometry + visual:** A + subject/reference region embeddings
    (merger level [subj, ref, subj−ref, subj·ref], frozen encoder).
- Relation module: linear LR + MLP(256); 5-fold CV; decision
  True ⟺ predicted == claimed relation.
- Control: 7B LM-only LoRA (65.69% orientation; facing 75.0, facing-away
  59.0, parallel 63.6, perpendicular 41.7). Paired exact McNemar on all 137
  test statements.

## Results — True/False accuracy on orientation statements (n=137)

| Condition | Overall | facing | facing away | parallel | perp |
|---|---|---|---|---|---|
| 7B LM-only LoRA (control) | **65.7%** | **75.0%** | **59.0%** | **63.6%** | 41.7% |
| A geometry-only (linear) | 58.3% | 66.1% | 56.8% | 25.0% | 66.7% |
| A geometry-only (mlp) | 58.3% | 69.4% | 54.1% | 25.0% | 58.3% |
| B geometry+visual (linear) | 55.9% | 59.7% | 48.6% | 56.2% | 58.3% |
| B geometry+visual (mlp) | 55.9% | ~59–67% | ~49% | ~56% | 58.3% |

Paired McNemar vs control (all p-values exact binomial):

| Condition | p | control-loss | control-gain |
|---|---|---|---|
| A linear | **0.0003** | 45 | 16 |
| A mlp | **<0.0001** | 47 | 14 |
| B linear | **0.0037** | 44 | 20 |
| B mlp | **0.0004** | 47 | 18 |

The 4-way relation classifier is weak relative to the empirical majority baseline:
CV accuracy is 44–46% versus a 49.9% majority-class baseline. Uniform random
chance for four balanced classes would be 25%, so these results should not be
called “at chance.” Adding the visual region embeddings does not help
(B ≈ A; if anything worse).

## Interpretation

**No — explicit object-centric decomposition does NOT succeed where
end-to-end generative reasoning fails.** The two-stage pipeline is
significantly *worse* than the 7B LM-only LoRA control on orientation
statements (55.9–58.3% vs 65.7%, all p ≤ 0.004), and it loses to the
control on every relation except perpendicular (n=12, noise).

Mechanistic reading:

1. **2D box geometry cannot express object-intrinsic direction.** "Facing"
   is a property of the *subject's* front/back orientation; the relative
   geometry of two boxes is silent about it. The classifier remains near or
   below the 49.9% majority baseline on 4-way relation classification
   (44–46% CV), and parallel-to (the one relation that IS expressible via axis
   alignment) still only reaches 25% with geometry-only — geometry is that
   weak here.
2. **The region visual features do not rescue it** (B ≈ A), consistent with
   the object-grounded probe: object-intrinsic orientation is not cleanly
   decodable from frozen region features either.
3. **The generative model's residual signal (facing 75%) is therefore not
   reproducible from decomposable parts of the frozen representation.** It
   lives in the full multimodal interaction + language priors — exactly the
   component the "localize → explicit module" decomposition strips away.

**Paper claim:** orientation is genuinely difficult even after explicit
object grounding and geometric decomposition. The default generative
interface is not merely "poor at extracting relational structure" — it is
currently the *best* available extractor on this task, which deepens the
result: a persistent bottleneck that resists scale, prompting, LM-side
LoRA, hard negatives, frozen-feature probing, vision/projector adaptation,
AND explicit two-stage decomposition.

## Caveats

- Boxes come from the same frozen Qwen2-VL family; localization errors
  bound the pipeline (10 no-box test statements scored as wrong).
- The relation module is a small learned classifier; a *strong* second
  stage (e.g., an LM prompted with boxes as text) is the one untested
  variant of this family.
- n=137 orientation test statements; per-relation cells are small
  (12–64).

## Files

- `results/two_stage_results.json`
- `scripts/two_stage_reasoning.py`
