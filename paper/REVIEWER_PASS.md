# Reviewer-Style Pass — `paper-draft-v1`

Date: 2026-08-10
Basis: frozen experimental tag `paper-freeze-v1`; literature metadata verified against primary publication/arXiv records before inclusion.

## Overall assessment

The paper has a coherent diagnostic story and is substantially stronger when framed as **persistence + mechanism + transfer**, not as the first discovery that VLMs struggle with orientation. The original VSR paper already reported orientation relations as especially difficult. The current contribution is that the weakness persists in modern generative VLMs across scale and a broad intervention ladder, coexists with logical inconsistency, and transfers poorly under benchmark-specific adaptation.

## High-priority reviewer risks addressed

1. **Novelty relative to VSR itself**
   - Fixed in Related Work and Introduction.
   - The manuscript now explicitly states that VSR previously identified orientation weakness.
   - Our novelty is positioned as persistence in modern generative VLMs, intervention breadth, mechanism diagnostics, consistency/accuracy separation, and cross-benchmark transfer.

2. **Overclaiming SITE external validation**
   - Tightened throughout.
   - SITE's official spatial-relationship-reasoning category is described as strong.
   - The orientation result is explicitly labeled a non-official, keyword-derived supporting slice.
   - The paper no longer implies that SITE establishes broadly weak spatial reasoning.

3. **Hard-negative significance wording**
   - Tightened in abstract, introduction, and consistency section.
   - `66.0 -> 77.7%` facing consistency is reported descriptively.
   - The pooled strict-family hard-negative vs LM-only comparison is explicitly noted as non-significant (`p=0.29`).
   - The statistically supported result remains LM-only vs zero-shot (`p<0.0001`).

4. **Probe causal overreach**
   - Tightened using standard probing caveats.
   - The paper says orientation is weakly *accessible to the tested readouts*, not absent from the network.
   - The probe section cites Hewitt & Liang's warning that probe capacity can learn the target task.

5. **Clean-label apples-to-oranges comparison**
   - Fixed.
   - The strict orientation subset is no longer presented as a matched statistical comparison with full-test containment/depth.
   - The supported claim is that removing questionable labels improves scores but does not eliminate substantial orientation error.

6. **Parallel/perpendicular complement semantics**
   - Experimental setup now states that parallel/perpendicular is a soft complement because both may be false for oblique objects.

## Page-budget changes applied

- Abstract shortened and statistical caveat added.
- Introduction compressed while retaining the core result chain.
- Related Work added as four compact paragraphs rather than a long survey.
- Probe figure moved from the main paper to the appendix.
- Main paper now prioritizes four figures:
  1. scale/conditions,
  2. orientation interventions,
  3. logical consistency,
  4. SITE external validation.
- Main tables remain:
  1. canonical VSR conditions,
  2. compact SITE transfer table.
- Full clean-label table and probe detail remain in the appendix.
- Discussion reduced to three high-value paragraphs.

## Remaining reviewer vulnerabilities

### 1. Model-family breadth
The study uses two scales but not a broad set of unrelated VLM architectures. Reviewers may argue the main VSR mechanism findings are Qwen/SmolVLM-family specific. SITE helps with benchmark generalization, not architecture generalization. This should remain a limitation unless another model family is evaluated; do not add one merely for cosmetic breadth unless submission strategy demands it.

### 2. Small orientation test set
VSR orientation has `n=137`; perpendicular is much smaller. Relation-specific estimates can have wide uncertainty. Keep confidence intervals/statistical tests where available and avoid ranking small per-relation changes as meaningful.

### 3. Multiple comparisons
The project contains many interventions and family-level comparisons. The paper should distinguish prespecified/high-level tests from exploratory per-relation analysis. If space permits, add a short note that per-relation comparisons are descriptive unless corrected/explicitly tested.

### 4. SITE heuristic subset construction
The external orientation slice is not an official SITE factor. Reviewers may ask whether keyword selection creates source/category confounds. The current paper correctly labels it supporting evidence. A useful appendix addition would be the exact keyword rule and source/category distribution, without adding more model runs.

### 5. Mechanistic language
The evidence supports a mixed diagnostic account, not a complete causal decomposition. Prefer:
- "consistent with",
- "suggests",
- "weakly accessible under these probes",
- "relational incoherence contributes",
over:
- "proves the representation lacks orientation",
- "the bottleneck is in the vision encoder",
- "the failure is not visual."

### 6. Contemporary overlap on logical consistency
Recent work such as SAGE explicitly trains spatial consistency using geometric/linguistic duality. The paper now cites it and distinguishes our diagnostic contribution. Before submission, re-check 2026 concurrent work for additional consistency-based spatial VLM papers.

## Bibliography status

Verified entries currently include:
- VSR (TACL 2023)
- What'sUp (arXiv 2023)
- GSR-Bench (arXiv 2024)
- SITE (ICCV 2025)
- VSP (ICCV 2025)
- MM-Spatial (ICCV 2025)
- SpatialScore (CVPR 2026)
- Qwen2-VL (arXiv 2024)
- LoRA (arXiv 2021)
- Hewitt & Liang probing controls (EMNLP-IJCNLP 2019)
- SAGE spatial logical consistency (arXiv 2026)

## Next production steps

1. Compile under the standalone draft and fix any LaTeX/layout warnings.
2. Import the official target-venue template (CVPR/ICCV or chosen venue) and measure actual page count.
3. Add an exact citation for SmolVLM2 if a citable technical report/model paper is available; otherwise identify it by model card in a reproducibility footnote rather than inventing a paper citation.
4. Add the SITE heuristic construction details and source/category distribution to the appendix.
5. Run one final citation/claim audit: every literature claim should have a citation; every empirical number should trace to `paper-freeze-v1` artifacts.
6. Do not change frozen experimental results while editing prose.
