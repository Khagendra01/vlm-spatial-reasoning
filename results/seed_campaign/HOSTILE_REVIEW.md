# Paper-2 Hostile Review (Step 6)

**Date:** 2026-08-14. Four reviewer roles; every finding either fixed or
explicitly accepted as a documented limitation. GPU off.

---

## R1: Novelty reviewer

**Verdict: Accept with minor revisions** (novelty claim is appropriately
narrowed).

- The paper does NOT claim the normal-minus-shuffle gap as novel; it
  explicitly credits VRS (Beyond Accuracy 2026). Correct.
- The paper does NOT claim VisualFLIP reproduction; it states the global
  reflection vs minimal local edit difference, and names the pair metrics
  "collapse-style... following VisualFLIP". Correct and safe.
- The paper does NOT claim accuracy==grounding or shuffled images as a new
  test. Correct.
- The remaining novelty (joint multi-seed cross-backbone decomposition of
  ordinary fine-tuning) survived the Step-3 literature audit; nothing found
  during the compute campaign (Aug 2026) does the same experiment.
- **Finding (accepted):** a reviewer could still say "the components are
  individually known" — the paper's contribution is the *jointness* and
  *seed robustness*, which is stated explicitly in the intro and related
  work.

## R2: Statistics reviewer

**Verdict: Accept with minor revisions.**

- Seeds are independent draws; the paper reports per-seed values, means, and
  SDs, and never "monotonic across seeds". Correct.
- **Finding 1 (fixed):** the paper must not pool examples across seeds into
  one giant n. The paper reports per-seed means/SDs, not pooled McNemar
  over 2195x3. Verified: no pooled claim exists.
- **Finding 2 (accepted):** with 3 seeds per family, SDs are 2-df
  estimates; the paper reports them as descriptive, not inferential. The
  claim hierarchy marks them as descriptive.
- **Finding 3 (accepted):** the fresh-seed C_pair "within 0.05" tolerance
  is a pre-specified audit threshold (claim-level audit), not a post-hoc
  significance test. Documented.

## R3: Causal-language reviewer

**Verdict: Accept with minor revisions.**

- **Finding 1 (fixed in draft):** "visual response" was previously used for
  hflip metrics; now the paper says "transformation behavior" and "global
  horizontal reflection", with A_transform/C_pair/both_correct defined by
  frozen formulas.
- **Finding 2 (fixed in draft):** the paper says "correct-image dependence"
  for G/dG, never "causal grounding"; stronger causal language is reserved
  for genuine counterfactual evidence (stated in Limitations).
- **Finding 3 (accepted):** the Qwen3-VL extension is labeled
  post-confirmatory, and no C_pair claim is made for it. Verified in the
  text and in the audit (q3vl_only_supported_quantities: PASS).

## R4: Numerical auditor (script)

**Verdict: PASS** (after auditor bug fix — see below).

- `scripts/hostile_numerical_review.py` extracts every 4-decimal number
  from all `.tex` files (including `sec/`), maps it to the audit JSON
  ground truth, and hard-fails on any mismatch > 1e-4.
- Hostile test: planted `+0.0501` in place of `+0.0506` -> FAIL detected;
  restored -> PASS. (The first auditor run missed `sec/` and range
  `--`-separated numbers; both scanner bugs were found by this hostile
  test and fixed.)
- All committed seed-0 values (7B 0.82414579, 2B 0.76492027) verified
  byte-exact.

## Accepted limitations (no fix, documented in paper)
1. Two backbone families + one scoped extension.
2. Tier-C is global reflection, not VisualFLIP minimal edits.
3. Within-backbone comparisons only; no resolution-independence claim.
4. No text-only control adapter (future work).
5. 2-df seed SDs (descriptive).

## Final verdict: PASS — paper ready for submission freeze.
