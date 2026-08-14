# Paper-2 R1: SUBMISSION FREEZE (Step 7)

**Frozen:** 2026-08-14. No further compute, analysis, or number changes
permitted without a decision-log entry and a new freeze commit.

## Frozen artifacts (this commit)

| Artifact | Path |
|---|---|
| Main paper (LaTeX source) | FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/paper2_source/ |
| Figures (3) | results/seed_campaign/figures/fig{1,2,3}_*.png |
| Publication tables | results/seed_campaign/figures/PUBLICATION_TABLES.md |
| Numerical audit (PASS) | results/seed_campaign/numerical_audit.json + NUMERICAL_AUDIT.md |
| Claim hierarchy (frozen) | results/seed_campaign/CLAIM_HIERARCHY.md |
| Literature/novelty audit | results/seed_campaign/LITERATURE_NOVELTY_AUDIT.md |
| Hostile review (PASS) | results/seed_campaign/HOSTILE_REVIEW.md |
| Analysis (corrected) | results/seed_campaign/ANALYSIS.md |
| Decision log | SPATIAL_REASONING_DECISION_LOG.md |
| Raw artifacts archive | results/seed_campaign/cloud_artifacts/ |

## Frozen scientific claims (summary)

1. **C1 (dA):** positive for all fresh seeds, both confirmatory backbones
   (7B +0.0506±0.0046; 2B +0.0316±0.0009). AUDITED PASS.
2. **C2 (dG):** positive for all fresh seeds, both confirmatory backbones
   (7B +0.0440±0.0054; 2B +0.0316±0.0026). AUDITED PASS.
3. **C3 (dC):** fresh-seed relcomp C_pair within 0.05 of legacy General in
   both families. AUDITED PASS.
4. **C4 (Tier-C):** all fresh 2B hflip C_pair > 2B zero-shot; three
   separate quantities (A_transform / C_pair / both_correct) never
   collapsed. AUDITED PASS.
5. **Post-confirmatory:** Qwen3-VL-8B dA/dG/A_transform only; no C_pair
   claim. AUDITED PASS.

## Frozen terminology contract

- A_transform = transformed-answer accuracy (never "flip rate").
- C_pair = pair consistency (answer-update / stability rate).
- both_correct = joint correctness.
- G = A_normal - A_shuffle; dG = G_tuned - G_zero_shot.
- Seeds = independent draws; ranges/means/SDs only.
- hflip = global horizontal reflection; collapse-style pair metrics
  "following VisualFLIP", difference stated.
- Qwen3-VL = post-confirmatory external validation.

## Compute state

GPU: OFF. Instances deleted. No Paper-2 model compute permitted without
explicit unlock (e.g., VisualFLIP official dataset release -> 1 GPU-hour
bonus validation, requires decision-log entry).

## Submission checklist

- [x] Step 1 numerical audit (PASS, hostile-tested)
- [x] Step 2 claim hierarchy frozen
- [x] Step 3 literature/novelty audit + novelty sentence
- [x] Step 4 canonical figures/tables
- [x] Step 5 paper + supplement (LaTeX source)
- [x] Step 6 hostile reviews (4 roles; numerical auditor hostile-tested)
- [x] Step 7 submission freeze (this file)
- [ ] Compile main.tex + suppl.tex (tectonic; local tooling absent --
      compile on Paper-1 toolchain or CI)
- [ ] OpenReview enrollment (Aug 21) / main.pdf (Aug 28) / suppl+code
      (Aug 30)
