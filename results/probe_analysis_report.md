# Representation Probe: How Much Orientation Is in the Frozen 7B Vision Features?

## Question

Earlier analysis said 95.8% of persistent failures are *reasoning* failures, not
vision limitations (only 2/48 were small/occluded objects). But that judged
"vision sufficiency" by **inspection**, not measurement. Here we measure it:
how much orientation information can a **probe** extract from the frozen
Qwen2-VL-7B-Instruct vision features, with no language model and no fine-tuning?

## Setup

- Model: Qwen2-VL-7B-Instruct base (no LoRA), vision tower frozen.
- Features: ViT patch embeddings (1280d) and post-merger features (3584d, the
  actual input the LLM receives), mean-pooled per image.
- Examples: all 647 VSR orientation statements (facing / facing away from /
  parallel to / perpendicular to), train = audited-clean (excludes 24 hard-negative
  audit rejects), val, test(137) — no test examples used for training.
- Tasks: T1 facing vs facing-away (binary), T2 parallel vs perpendicular
  (binary), T3 4-way multiclass.
- Probes: linear logistic regression, MLP (256-hidden), and a **patch-vote
  probe** (per-patch LR + majority vote, which preserves spatial structure
  that mean-pooling destroys).
- Metrics: 5-fold CV on train, test accuracy with Wilson 95% CI vs majority baseline.

## Results

### T1: facing vs facing away (test n=103, majority 64.2%)

| Probe | CV acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|
| ViT linear (pooled) | 0.563±0.053 | 0.650 | 0.604 | [0.55, 0.74] |
| ViT MLP | 0.557±0.076 | 0.553 | 0.520 | [0.45, 0.65] |
| Merger linear | 0.541±0.035 | 0.689 | 0.645 | [0.59, 0.77] |
| Merger MLP | 0.572±0.078 | 0.524 | 0.492 | [0.42, 0.62] |
| ViT patch-vote | — | 0.621 | — | [0.53, 0.71] |
| Merger patch-vote | — | 0.602 | — | [0.51, 0.69] |

**The probes essentially predict the majority class.** Test acc ≈ majority
(64.2%); balanced acc 49–65% across settings; CV barely above 50%. The MLP
does **not** recover more than the linear probe — no evidence of
nonlinearly-accessible facing information either.

### T2: parallel vs perpendicular (test n=34, majority 64.7%)

| Probe | CV acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|
| ViT linear (pooled) | 0.603±0.116 | 0.618 | 0.610 | [0.44, 0.77] |
| ViT MLP | 0.559±0.186 | 0.676 | 0.693 | [0.50, 0.82] |
| Merger linear | 0.574±0.063 | 0.647 | 0.614 | [0.47, 0.79] |
| Merger MLP | 0.479±0.138 | 0.647 | 0.633 | [0.47, 0.79] |
| ViT patch-vote | — | **0.735** | — | [0.57, 0.85] |
| Merger patch-vote | — | 0.676 | — | [0.51, 0.81] |

The only task with a real signal: patch-vote reaches 73.5% (+8.8 over
majority). Geometry (axis alignment) is partially readable from local patch
structure — but even here the pooled linear probe stays near chance.

### T3: 4-way orientation (test n=137, majority 49.6%)

| Probe | CV acc | Test acc | Test bal-acc | 95% CI |
|---|---|---|---|---|
| ViT linear | 0.437±0.025 | 0.526 | 0.405 | [0.44, 0.61] |
| ViT MLP | 0.428±0.037 | 0.526 | 0.429 | [0.44, 0.61] |
| Merger linear | 0.442±0.038 | 0.533 | 0.440 | [0.45, 0.61] |
| Merger MLP | 0.447±0.048 | 0.474 | 0.432 | [0.39, 0.56] |
| ViT patch-vote | — | 0.518 | — | [0.44, 0.60] |
| Merger patch-vote | — | 0.526 | — | [0.44, 0.61] |

At chance everywhere. "Perpendicular to" collapses to 8–33% (worst class),
"facing away from" to 33–46%.

## Generative reference on the same test images

| Relation | 7B zero-shot | 7B General LoRA | best probe |
|---|---|---|---|
| facing | 73.4% | 75.0% | 65.0% |
| facing away from | 48.7% | 59.0% | ~41–46% |
| parallel to | 63.6% | 63.6% | 68.2% (MLP) |
| perpendicular to | 58.3% | 41.7% | 75.0% (MLP) |

The generative model's *statement-truth* accuracy (True/False on the same
images, a different but related task) **exceeds every probe on the hard
"facing" class** — the LLM is extracting something the object-agnostic probes
cannot.

## Interpretation

1. **Object-intrinsic orientation (facing/facing-away) is barely decodable
   from the frozen vision representation** — not linearly, not with an MLP,
   not with patch-vote. This is a genuine measurement, not an inspection
   judgment, and it complicates the earlier "vision is fine" conclusion.
2. **Axis-alignment geometry (parallel/perpendicular) is weakly readable**,
   and only when spatial structure is preserved (patch-vote). Mean-pooling
   destroys most of it.
3. **The LLM beats the probes on "facing"** — it must be exploiting
   non-perceptual signals (text priors, object-identity statistics, or
   attention readouts the probes lack). This keeps *reasoning* in the loop as
   a bottleneck, consistent with the audit (37.5% clear-image reasoning
   failures).

## Caveats

- Probes are **object-agnostic**. VSR orientation is object-pair-relative
  ("the X is facing the Y"); a global/pooled probe cannot group features per
  object, so it may understate what an *object-grounded* readout could find.
- Mean-pooling is lossy by construction; patch-vote partially compensates.
- Probe task (classify relation) differs from generative task (judge
  statement truth) — the comparison is indicative, not exact.
- Small test sets (T2: n=34) → wide CIs.

## Implication for the causal pathway

- The earlier finding stands: **most visible failures are reasoning
  failures** (clear images, wrong decisions).
- But the probe adds a second, measured fact: **the frozen vision
  representation encodes object-intrinsic orientation only weakly**. The
  vision features the LLM conditions on are not rich in this information,
  even if the pixels are.
- The two-step causal model (perception → representation → reasoning) is
  thus **partially bottlenecked at representation as well as reasoning**.
- **Status update (object-grounded probe, see `grounded_probe_report.md`):**
  conditioning the readout on subject/reference object regions does NOT
  recover orientation signal (T1 grounded CV 57–60% ≈ majority; T2, T3 at
  chance). The weak decodability is not an artifact of global pooling.
  Hard-negative training produced a statistically null tradeoff and that
  branch is closed. The measured evidence now points to the frozen vision
  representation itself (and the projector interface) as the bottleneck →
  **vision-side / projector adaptation is the justified next intervention.**

## Files

- `results/probe/probe_results.json` — pooled-level probe results
- `results/probe/patch_probe_results.json` — patch-vote probe results
- `results/probe/probe_report.md` — generated table version of this analysis
- `results/probe/embeddings_vit.npz`, `embeddings_merger.npz` — extracted features
