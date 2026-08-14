# Paper-2 R1 Seed Campaign: Frozen Scientific Claim Hierarchy

**Status: FROZEN (Step 2 of the post-compute pipeline), 2026-08-14.**
Every number below is sourced from results/seed_campaign/numerical_audit.json (independent recomputation; verdict PASS; committed-target diffs = 0.0). Terminology follows the frozen definitions (analyze_tier_c.py): A_transform = transformed-answer accuracy; C_pair = pair consistency (answer-update rate for flip laws, stability rate for invariant); both_correct = joint correctness; G = A_normal - A_shuffle; dG = G_tuned - G_zero_shot.

## Tier-0: Terminology contract (immutable)

- `A_transform` = P(transformed prediction == expected transformed label). Never called "flip rate".
- `C_pair` = P(pair consistency): hflip_flip/relcomp/facingcomp = P(transformed != normal); hflip_invariant = P(transformed == normal). Never called "paired both-images correctness".
- `both_correct` = P(normal-correct AND transformed obeys the law). Joint correctness, never consistency.
- Seeds are independent draws: report means/SDs and ranges; never "monotonic across seeds".
- Qwen3-VL extension: only dA/dG/A_transform computed; no C_pair claim.

## Tier-1: Primary confirmatory claims (preregistered; 7B + HardNeg + 2B)

### C1 (benchmark gain, dA)

- 7B seed-0: dA +0.0542; fresh seeds: r1_seedA +0.0547, r1_seedB +0.0456, r1_seedC +0.0515; mean +0.0506 +/- 0.0046.
- 2B seed-0: dA +0.0287; fresh seeds: r1_seedA +0.0305, r1_seedB +0.0323, r1_seedC +0.0319; mean +0.0316 +/- 0.0009.
- **Claim**: ordinary spatial LoRA fine-tuning improves benchmark accuracy reproducibly across training seeds and both confirmatory backbone families (audited: dA positive for all fresh seeds, both families).

### C2 (correct-image dependence, G and dG)

- 7B seed-0: G 0.3522, dG +0.0456; fresh seeds G: r1_seedA 0.3544, r1_seedB 0.3444, r1_seedC 0.3531; dG mean +0.0440 +/- 0.0054.
- 2B seed-0: G 0.2975, dG +0.0305; fresh seeds G: r1_seedA 0.3007, r1_seedB 0.2957, r1_seedC 0.2993; dG mean +0.0316 +/- 0.0026.
- **Claim**: tuning widens the normal-minus-shuffle gap (G) and the zero-shot-relative change (dG) is positive for every fresh seed in both confirmatory families — fine-tuning increases dependence on the correct visual evidence (audited).

### C3 (semantic pair consistency, dC via relcomp)

- 7B relcomp C_pair: seed-0 0.6772; fresh seeds r1_seedA 0.6637, r1_seedB 0.6547, r1_seedC 0.6652.
- 2B relcomp C_pair: seed-0 0.5015; fresh seeds r1_seedA 0.4985, r1_seedB 0.5045, r1_seedC 0.5105.
- **Claim**: semantic pair consistency changes with tuning but stays stable across fresh seeds (no axis-specific divergence); its magnitude and relation-specific behavior differ from dA/dG (three-way decomposition).

### C4 (transformation behavior under global reflection, Tier C)

- 7B hflip_flip: A_transform zero-shot 0.6367 -> seed-0 0.6571; C_pair zero-shot 0.6163 -> seed-0 0.6857; fresh-seed C_pair r1_seedA 0.6490, r1_seedB 0.6898, r1_seedC 0.6653.
- 2B hflip_flip: A_transform zero-shot 0.4980 -> seed-0 0.5224; C_pair zero-shot 0.3184 -> seed-0 0.3469; fresh-seed C_pair r1_seedA 0.3429, r1_seedB 0.3633, r1_seedC 0.3714.
- **Claim**: answer-update behavior under horizontal reflection (C_pair) is broadly higher after General adaptation than zero-shot and remains close to the legacy General checkpoint across fresh seeds (audited: all fresh 2B C_pair > 2B zero-shot; all fresh-seed C_pair within 0.05 of seed-0). A_transform, C_pair and both_correct are reported as three separate quantities.

## Tier-2: Post-confirmatory claim (Qwen3-VL-8B, exploratory extension)

- dA +0.0323; dG +0.0355; hflip_flip A_transform +0.0449 (transformed-accuracy gain only).
- **Claim (scoped)**: the primary adaptation pattern (dA positive, dG positive, transformed accuracy under reflection improves) directionally replicates on a contemporary backbone. C_pair was NOT computed for this extension; no response-law-compliance claim is made. Labeled post-confirmatory / exploratory architecture extension, not preregistered.

## Tier-3: Explicitly NOT claimed

- No claim that the normal-minus-shuffle gap is a novel metric (VRS = A(real) - A(shuffle) already defined in Beyond Accuracy 2026).
- No VisualFLIP reproduction: our hflip is a global horizontal reflection, not minimal local editing; C_pair is a collapse-style paired answer-update metric "following VisualFLIP" with the intervention difference stated.
- No claim that accuracy equals grounding, or that shuffled images are a novel test.
- No claim about VisualFLIP/COCO-style minimal-edit counterfactuals (dataset gated; re-check before deadline).
- No Qwen3-VL C_pair / response-law claim.

## Evidence provenance

Audited artifacts (results/seed_campaign/): numerical_audit.json (PASS), NUMERICAL_AUDIT.md, ANALYSIS.md; raw predictions archived under cloud_artifacts/extracted/; all checkpoints on origin research/spatial-grounding-audit.
