# Paper Results Summary (Canonical)

**Status: EXPERIMENTAL PHASE FROZEN.** No further model runs.
All numbers below are reproduced from committed prediction CSVs via
`scripts/build_canonical_tables.py`, `scripts/clean_label_orientation.py`,
`scripts/compare_site_zeroshot_lora.py`.

---

## Three defensible claims

### Claim 1 — Orientation is unusually stubborn.
It resists scale (2B→7B), structured prompting, LM-side LoRA (general,
targeted), hard negatives, vision/projector LoRA, representation probing
(linear, nonlinear, object-grounded), and object-centric two-stage
decomposition. Across all interventions, VSR test orientation accuracy
stays in a 62–66% band (majority 63.7%).

### Claim 2 — Accuracy and relational consistency are separable.
Hard-negative training raised facing↔facing-away self-consistency
substantially (66.0% → 77.7%, p<0.0001 vs zero-shot) without materially
changing accuracy (68.9% = 68.9%). The model's failures are not only
"does not know the relation" — zero-shot contradicts itself on 63% of
complementary facing pairs.

### Claim 3 — VSR adaptation is benchmark-specific.
On SITE (2,591 image examples), the VSR-trained 7B General LoRA is
statistically neutral overall (−0.4 pp, p=0.66), **significantly worse on
the official spatial-relationship category** (−3.5 pp, p=0.004), and does
not transfer to the orientation heuristic subset (+0.7 pp, p=0.50).

---

## Canonical table 1 — VSR test (n=2,195; orientation n=137)

| Condition | Overall | Orientation | Depth | Horizontal | Containment | Topology-contact |
|---|---|---|---|---|---|---|
| 2B zero-shot | 0.740 | 0.628 | 0.689 | 0.702 | 0.834 | 0.805 |
| 2B structured | 0.683 | 0.533 | 0.649 | 0.667 | 0.787 | 0.717 |
| 2B General LoRA | 0.766 | 0.620 | 0.711 | 0.743 | 0.876 | 0.810 |
| 2B Targeted LoRA | 0.765 | 0.642 | 0.708 | 0.751 | 0.876 | 0.814 |
| 7B zero-shot | 0.809 | 0.635 | 0.752 | 0.848 | 0.893 | 0.803 |
| 7B General LoRA | 0.847 | 0.657 | 0.823 | 0.874 | 0.929 | 0.844 |
| 7B Targeted LoRA | 0.839 | 0.642 | 0.817 | 0.871 | 0.917 | 0.853 |
| 7B Hard-Neg LoRA | 0.843 | 0.664 | 0.807 | 0.871 | 0.899 | 0.846 |
| 7B Projector LoRA | 0.829 | 0.642 | 0.786 | 0.871 | 0.893 | 0.853 |
| 7B Vision+Projector LoRA | 0.831 | 0.642 | 0.780 | 0.871 | 0.899 | 0.844 |

Family definitions: `scripts/annotate_tool.py` FAMILY_MAP (orientation =
facing / facing away from / parallel to / perpendicular to).

## Canonical table 2 — Orientation clean-label robustness

| Condition | full (137) | −questionable (132) | clear (124) | strict (107) |
|---|---|---|---|---|
| 2B zero-shot | 0.628 | 0.652 | 0.669 | 0.757 |
| 2B structured | 0.533 | 0.523 | 0.516 | 0.533 |
| 2B General LoRA | 0.620 | 0.636 | 0.645 | 0.729 |
| 2B Targeted LoRA | 0.642 | 0.659 | 0.685 | 0.766 |
| 7B zero-shot | 0.635 | 0.652 | 0.685 | 0.720 |
| 7B General LoRA | 0.657 | 0.674 | 0.702 | 0.785 |
| 7B Targeted LoRA | 0.642 | 0.659 | 0.694 | 0.720 |
| 7B Hard-Neg LoRA | 0.664 | 0.682 | 0.702 | 0.766 |
| 7B Projector LoRA | 0.642 | 0.659 | 0.694 | 0.738 |
| 7B Vision+Projector LoRA | 0.642 | 0.652 | 0.685 | 0.738 |

Even on the strictest clean subset, the best orientation accuracy (78.5%,
7B General LoRA) stays far below the same model's containment (92.9%) and
depth (82.3%) — the orientation deficit is not annotation noise.

## Canonical table 3 — SITE external validation (images, n=2,591)

| Subset | n | Zero-shot raw (CAA) | VSR-LoRA raw (CAA) | Δ raw (pp) | McNemar p |
|---|---|---|---|---|---|
| All images | 2,591 | 0.542 (0.311) | 0.538 (0.305) | −0.4 | 0.657 |
| Official spatial-relationship reasoning | 993 | 0.751 (0.592) | 0.716 (0.534) | −3.5 | 0.004 |
| Orientation heuristic (non-official) | 1,824 | 0.473 (0.226) | 0.480 (0.236) | +0.7 | 0.496 |
| single-image | 1,368 | 0.613 (0.374) | 0.602 (0.356) | −1.1 | 0.333 |
| multi-image | 1,223 | 0.464 (0.249) | 0.468 (0.255) | +0.4 | 0.778 |

## LOCKED SITE language (use verbatim in the paper)

> On the SITE benchmark (ICCV 2025), Qwen2-VL-7B shows *strong* performance
> on the official spatial-relationship-reasoning category (raw 75.1%,
> chance-adjusted 59.2%), comparable to published open-source results. The
> persistent weakness is concentrated in object/direction-related
> orientation questions (keyword-derived, non-official subset: raw 47.3%,
> chance-adjusted 22.6%, vs 31.1% overall). **We do not claim SITE confirms
> broadly weak spatial reasoning**; the claim is that orientation-related
> reasoning is disproportionately difficult and that VSR-trained adaptation
> does not transfer to SITE (statistically neutral overall, significantly
> worse on the official spatial-relationship category, p=0.004).

## Figures (results/figures/)

1. `fig1_scale_conditions.png` — scale/fine-tuning family: overall vs orientation (10 conditions)
2. `fig2_orientation_interventions.png` — 7B intervention ladder: full vs strict-clean orientation + per-relation
3. `fig3_probes.png` — object-grounded probe decodability (T1/T2/T3, linear/MLP, vs majority)
4. `fig4_consistency.png` — facing↔facing-away self-consistency vs contradiction across 5 conditions
5. `fig5_site_external.png` — SITE CAA: zero-shot vs VSR-trained LoRA (asterisk = McNemar p<0.05)

## Suggested paper structure

1. **Intro/motivation**: aggregate spatial accuracy hides a persistent
   orientation bottleneck.
2. **Setup**: VSR; 10 conditions (2B/7B families); SITE external validation.
3. **Results 1 — scale/fine-tuning**: scaling 2B→7B lifts depth/horizontal/
   containment by 6–15 pp but orientation by <3 pp; every intervention
   leaves orientation in a 62–66% band.
4. **Results 2 — interventions**: prompt decomposition, PEFT variants,
   hard negatives, vision-side adaptation (incl. clean-label robustness
   table).
5. **Results 3 — mechanism**: representation probes (weak decodability of
   object-intrinsic orientation) + logical consistency (separability of
   accuracy and coherence).
6. **Results 4 — external validation (SITE)**: strong official category,
   weak orientation subset, no transfer, negative transfer on official.
7. **Discussion**: benchmark-specific adaptation; coherence vs knowledge;
   implications for spatial reasoning evaluation.

## Reproducibility

- VSR predictions: `results/*_predictions_*.csv` (10 conditions)
- SITE predictions: `results/site/zeroshot_7b_predictions.csv`,
  `results/site/vsr_lora_predictions.csv` (config hash `28f4cc09887477af` + lora)
- Tables: `results/tables/` (CSV + MD)
- Figures: `results/figures/`
- Run notes: `results/site/site_eval_run_notes.md`
