# SITE External Validation — 7B Zero-Shot Image Results (Preregistered Step 1)

**Status: IMAGE SUBSET COMPLETE.** Videos and the 7B VSR-LoRA condition are
NOT run (deferred per protocol until this review).

## Protocol reference

- Frozen subsets: `results/site/site_protocol.json` (config hash
  `28f4cc09887477af` in `results/site/run_metadata.json`)
- Model: Qwen2-VL-7B-Instruct, frozen, zero-shot, greedy
- Format: SITE native multiple-choice; official prompt + parsing
- Efficiency changes (protocol-neutral, recorded): max_new_tokens 16
  (validated 125/125 identical parses), 392px image cap (constant; this
  transformers build ignores max_pixels), sdpa backend
- Images only: single-image 1,368 + multi-image 1,223 = 2,591 examples

## Results

| Subset | n | Raw acc | 95% Wilson CI | CAA |
|---|---|---|---|---|
| **All images** | 2,591 | 54.2% | [52.3, 56.1] | 31.1% |
| **Primary: spatial relationship reasoning** (official) | 993 | 75.1% | [72.3, 77.7] | **59.2%** |
| **Secondary: orientation heuristic** (non-official) | 1,824 | 47.3% | [45.0, 49.6] | **22.6%** |

CAA (chance-adjusted accuracy) = Σ(score − 1/n_opts) / Σ(1 − 1/n_opts),
official SITE metric.

### By modality (all images)

| Modality | n | Raw acc | CAA |
|---|---|---|---|
| single-image | 1,368 | 61.3% | 37.4% |
| multi-image | 1,223 | 46.4% | 25.0% |

### By source dataset (n ≥ 30)

| Source | n | Raw | CAA | | Source | n | Raw | CAA |
|---|---|---|---|---|---|---|---|---|
| CLEVR | 108 | 92.6% | 88.3% | | MMTBench | 251 | 51.4% | 33.4% |
| IconQA | 141 | 91.5% | 86.8% | | SpatialEval | 100 | 53.0% | 29.3% |
| VSR (in SITE) | 71 | 85.9% | 71.8% | | SPEC | 133 | 51.1% | 34.8% |
| GQA | 61 | 82.0% | 66.7% | | SAT | 183 | 46.5% | −7.1% |
| MME | 46 | 82.6% | 65.2% | | VStarBench | 39 | 46.2% | −7.7% |
| VQA | 105 | 80.0% | 68.1% | | MuirBench | 69 | 37.7% | 18.1% |
| CVBench | 35 | 77.1% | 54.3% | | exoego4d | 316 | 36.4% | 15.2% |
| MMVP | 61 | 72.1% | 44.3% | | egoexo4d | 288 | 34.7% | 13.0% |
| ThreeDSRBench | 141 | 63.1% | 31.8% | | MMIU | 152 | 34.2% | 4.4% |
| SeedBench | 89 | 61.8% | 49.1% | | MMERealWorld | 89 | 32.6% | 15.7% |
| Blink | 51 | 60.8% | 23.8% | | LogicVista | 37 | 18.9% | −7.0% |

## Decision-rule outcome (preregistered)

1. **Primary subset (official spatial relationship reasoning): NOT broadly
   weak.** CAA 59.2% — comparable to or above published open-source results
   on this category (e.g., Qwen2.5-VL-7B 51.5% CAA per the SITE leaderboard).
2. **Orientation heuristic subset: weak.** CAA 22.6% vs 31.1% overall and
   59.2% primary — a large, consistent drop, driven by orientation/
   direction-vocabulary questions (facing, direction, view, rotation,
   left/right, parallel/perpendicular...).

**Conclusion (matches decision-rule branch 2):** the VSR orientation finding
**generalizes to SITE**, but specifically for **object/direction-related
orientation** — not spatial relationship reasoning broadly. The claim is
narrowed accordingly: *VLMs show a persistent, benchmark-independent weakness
in object-intrinsic orientation (facing/direction), while general spatial
relationship reasoning is comparatively strong.*

## Caveats

- The orientation subset is keyword-derived (non-official tag); labeled as
  such; supporting analysis, not the headline.
- 392px input cap (constant protocol parameter) may under-serve fine
  orientation cues; effect should be uniform across subsets, and the
  orientation deficit is large enough that it cannot be explained by
  resolution alone (high-resolution multi-image subsets like CLEVR do fine).
- Videos deferred; movement/navigation orientation in video is a separate
  extension.

## Next steps (per protocol, awaiting decision)

- If the primary-subset weakness claim is desired at higher fidelity: rerun
  the primary subset at native resolution (max_pixels regression documented).
- 7B VSR-LoRA on SITE: only if justified after this review.
- Video subset: secondary extension, deferred.

## Files

- Predictions: `results/site/zeroshot_7b_predictions.csv` (2,591 rows)
- Metrics: `results/site/zeroshot_image_metrics.json`
- Run metadata + config hash: `results/site/run_metadata.json`
