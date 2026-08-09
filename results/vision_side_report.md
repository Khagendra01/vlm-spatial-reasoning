# Vision-Side Adaptation: Projector LoRA and Upper-Vision+Projector LoRA

## Question

Probes showed orientation weakly decodable from the frozen vision
representation — even with object conditioning. The next causal question:
**can adapting the visual/multimodal representation improve orientation
reasoning beyond LM-only LoRA?**

## Conditions (all identical recipe)

Same manifest (2000 VSR train statements), same prompt, same collation,
2 epochs, batch_size=1, AdamW lr=1e-4 wd=0.01, linear warmup 10%,
LoRA r=8 α=16 dropout 0.05, grad clipping 1.0 — exactly the LM-only
General LoRA control recipe.

| Condition | LoRA targets | Trainable |
|---|---|---|
| 7B zero-shot | — | 0 |
| LM-only LoRA (control) | LM q/k/v/o | ~0.3M |
| Projector LoRA | `visual.merger.mlp.0/2` (patch-merger) | 152K |
| Upper-vision + projector LoRA | merger + blocks 24–31 (qkv/proj/fc1/fc2) | 1.46M |

Evaluation: full VSR test (2195 statements), same greedy protocol as control.
Paired exact McNemar vs control.

## Results

| Condition | Overall | Orientation | Facing | Facing Away | Parallel | Perpendicular |
|---|---|---|---|---|---|---|
| 7B zero-shot | 80.9% | 63.5% | 73.4% | 48.7% | 63.6% | 58.3% |
| LM-only LoRA (control) | **84.7%** | **65.7%** | 75.0% | **59.0%** | 63.6% | 41.7% |
| Projector LoRA | 82.9% | 64.2% | **78.1%** | 56.4% | 50.0% | 41.7% |
| Vision+projector LoRA | 83.1% | 64.2% | 76.6% | 51.3% | 63.6% | 41.7% |

### Paired McNemar (exact binomial) vs LM-only control

| Subset | Projector p | Vision+proj p |
|---|---|---|
| Overall (n=2195) | **0.0043** (worse) | **0.0122** (worse) |
| Orientation (n=137) | 0.86 | 0.85 |
| facing (n=64) | 0.77 | 1.00 |
| facing away (n=39) | 1.00 | 0.58 |
| parallel (n=22) | 0.25 | 1.00 |
| perpendicular (n=12) | 1.00 | 1.00 |

## Interpretation (decision-tree outcome)

1. **Projector-only LoRA does not help orientation** (64.2% vs 65.7% control,
   p=0.86) and **significantly degrades overall** (82.9% vs 84.7%, p=0.004).
   The bottleneck is not a simple multimodal-alignment/readout deficiency
   addressable by adapting the patch-merger.
2. **Upper-vision + projector LoRA behaves identically to projector-only** on
   orientation (64.2% — not even a marginal gain over projector-only), and is
   also significantly worse overall (p=0.012). Freezing-or-adapting the last 8
   vision blocks makes no difference for orientation. The frozen vision
   representation is not "materially limiting" in a way that 1.46M LoRA params
   can unlock.
3. **Neither helps → strongest branch of the decision tree:** orientation
   reasoning has now resisted scaling (2B→7B), prompting, LM-side LoRA,
   hard-negative training, linear/nonlinear/object-grounded probing, and
   visual-side (projector + vision-block) adaptation. The only signal that
   moves: a small, non-significant *facing* bump (75.0→78.1%) at the cost of
   *facing-away* (59.0→56.4%) — a specialization tradeoff, not a fix.
4. Orientation accuracy tracks the LM-only control's *overall* value
   everywhere; vision-side adaptation adds nothing on top of LM-side LoRA,
   while hurting the easy families (the 114–110 discordant losses are
   concentrated outside orientation).

**Refined causal picture:** the orientation ceiling sits in the
decision-level interaction between visual evidence and language priors —
the LLM *can* extract more than the probes (73–78% on facing), so the
features are usable; what is missing is a reliable *object-intrinsic
direction* readout in the full model, which neither representation
adaptation nor LM-side training supplies. This points toward structured
interventions at the reasoning interface (e.g., explicit relational/visual
reasoning modules, two-stage "localize → then answer" prompting with
vision-derived geometry) rather than further single-model fine-tuning knobs.

## Files

- `checkpoints/qwen2vl_7b_projector_lora/final`, `.../vision_proj_lora/final`
- `results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv`
- `results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222300.csv`
- `results/vision_side_comparison.json`
- `scripts/train_vision_lora.py`, `scripts/compare_vision_side.py`
