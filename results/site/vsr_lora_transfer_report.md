# SITE External Validation — VSR-Trained 7B General LoRA Cross-Dataset Transfer

**Preregistered step 2.** Same frozen protocol as the zero-shot run
(config hash `28f4cc09887477af` + LoRA adapter; same prompts, image cap,
parser, example ordering, 2,591 image examples). No training on SITE.

## Paired results: zero-shot vs VSR-trained General LoRA

| Subset | n | Zero-shot raw (CAA) | LoRA raw (CAA) | Δ raw | McNemar p |
|---|---|---|---|---|---|
| All images | 2,591 | 54.2% (31.1) | 53.8% (30.5) | −0.4 pp | 0.66 |
| **Primary: spatial relationship reasoning** (official) | 993 | **75.1% (59.2)** | **71.6% (53.4)** | **−3.5 pp** | **0.004 (worse)** |
| Secondary: orientation heuristic (non-official) | 1,824 | 47.3% (22.6) | 48.0% (23.7) | +0.7 pp | 0.50 |
| single-image | 1,368 | 61.3% (37.4) | 60.2% (35.6) | −1.1 pp | 0.33 |
| multi-image | 1,223 | 46.4% (25.0) | 46.8% (25.5) | +0.4 pp | 0.78 |

Paired agreement: 76.6% of examples receive the same answer under both
conditions (83.6% on the primary subset).

## Decision-rule outcome

- LoRA does **not** improve the orientation subset (p=0.50; 162 fixed vs
  149 broken) → no cross-benchmark transfer of VSR training to SITE
  orientation.
- LoRA does **not** improve official spatial-relationship reasoning — it
  **significantly degrades** it (87 lost vs 52 fixed, p=0.004).
- Overall: statistically null with a small negative trend.

**Conclusion:** VSR-training gains are partly **benchmark-specific** —
adapting to VSR transfers poorly to an independent benchmark and actively
hurts general spatial-relationship reasoning there — while the orientation
weakness remains **stubborn under both zero-shot and VSR-adapted inference**
(CAA 22.6% → 23.7%, ns).

## Combined story (zero-shot + LoRA)

1. SITE official spatial-relationship reasoning is strong for this model
   (CAA 59.2% zero-shot) — orientation is the weak spot, not spatial
   reasoning broadly.
2. The orientation deficit generalizes across benchmarks (VSR: 65.7%
   ceiling vs easy relations; SITE orientation subset: CAA 22.6% vs 31.1%
   overall).
3. Neither scaling-style adaptation (LM-side LoRA), representation
   adaptation, hard negatives, nor cross-benchmark transfer moves it —
   VSR-trained adapters do not transfer, and even degrade the official
   category.

## Files

- `results/site/vsr_lora_predictions.csv` (2,591 rows, all valid)
- `results/site/vsr_lora_vs_zeroshot.json` (full paired metrics)
- `scripts/compare_site_zeroshot_lora.py`
- `scripts/eval_site_zeroshot.py` (--lora flag; protocol otherwise unchanged)
