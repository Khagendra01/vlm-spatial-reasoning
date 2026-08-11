# Grounding Study Decision Log

This file records scientific/protocol decisions for `research/spatial-grounding-audit`.

Any material change after results are observed must be logged here. The goal is to preserve a clear distinction between **pre-result confirmatory design**, **bug fixes**, and **post-result exploratory extensions**.

---

## 2026-08-10 — Project split from orientation study

**Status:** pre-result / confirmatory foundation  
**Decision:** treat the prior orientation-focused project as frozen and standalone. Create a new branch for the spatial-grounding-after-LoRA study.  
**Reason:** the new research question concerns what capability changes under spatial adaptation, not why orientation remains weak.  
**Affected results already seen?** No new grounding-audit results seen.  
**Outcome:** branch `research/spatial-grounding-audit` created from frozen `master` commit `3c6bb351edd40b2155a7beac98aeea1cfc7de0ef`.

---

## 2026-08-10 — Upgrade question from two-way to three-way decomposition

**Status:** pre-result / confirmatory foundation  
**Old framing:** benchmark accuracy gain (`ΔA`) vs grounding gain (`ΔG`).  
**New framing:** benchmark accuracy (`ΔA`) vs semantic/logical consistency (`ΔC`) vs visual-grounding/evidence-sensitivity (`ΔG`).  
**Reason:** the existing prior-paper checkpoints provide a natural contrast in which semantic consistency behavior can change without corresponding ordinary facing accuracy change. This allows a sharper scientific question: do accuracy, coherence, and visual evidence sensitivity co-move under adaptation?  
**Affected grounding results already seen?** No. Existing consistency findings from the prior frozen project were known before this protocol revision and motivate, rather than result from, this design.  
**Confirmatory impact:** central paper question updated before new grounding experiments.

---

## 2026-08-10 — Primary model roles

**Status:** pre-result / confirmatory  
**Decision:**

- primary comparison P1 = 7B zero-shot → 7B General LoRA;
- key diagnostic D1 = 7B General LoRA → 7B HardNeg LoRA;
- replication R1 = 2B zero-shot → 2B General LoRA.

**Reason:** P1 measures whether ordinary benchmark improvement is accompanied by grounding improvement. D1 probes whether a consistency-oriented adaptation contrast changes grounding even when prior facing accuracy is unchanged. R1 tests whether the main adaptation decomposition generalizes to a smaller backbone.  
**Caveat frozen into protocol:** prior pooled strict-family General-vs-HardNeg consistency McNemar `p=0.29`; D1 must not be described as globally significant consistency improvement unless new correctly scoped evidence supports it.  
**Affected grounding results already seen?** No.

---

## 2026-08-10 — Evidence hierarchy revised

**Status:** pre-result / confirmatory  
**Old emphasis:** normal, text-only, blank, shuffled treated roughly equally as Tier-A grounding probes.  
**New hierarchy:**

1. correct vs deterministic shuffled/wrong image = primary cheap grounding/evidence-dependence test;
2. visual counterfactuals with text fixed = strongest causal evidence when expected relation behavior is known;
3. original+counterfactual both-correct = strong paired metric;
4. blank image = secondary;
5. text-only = exploratory/diagnostic.

**Reason:** text-only can change the multimodal interface, while wrong-image comparisons preserve an ordinary visual call path. Geometry-changing visual counterfactuals are stronger than extreme ablations because they test relation-specific causal response rather than generic sensitivity to image corruption.  
**Affected grounding results already seen?** No.

---

## 2026-08-10 — Semantic and visual interventions separated

**Status:** pre-result / confirmatory  
**Decision:** do not group relation inversion, subject/object reversal, and image reflection under one generic counterfactual metric.

- semantic axis (`S`): pixels fixed, language changes → primarily measures `C`;
- visual axis (`V`): language fixed, pixels/world change → primarily measures `G`;
- evidence-ablation axis (`E`): correct visual evidence removed/replaced → supports `G`.

**Reason:** a model may learn answer algebra/semantic consistency without learning to update from changed visual evidence. The paper must make this distinction explicit.  
**Affected grounding results already seen?** No.

---

## 2026-08-10 — Horizontal reflection retained but not sufficient

**Status:** pre-result / confirmatory + planned extension  
**Decision:** horizontal reflection is a valid visual counterfactual for relation families where expected truth behavior is guaranteed, especially left/right. It is not treated as a universal spatial-grounding test.  
**Reason:** reflection does not provide the intrinsic object-rotation manipulation needed for facing/facing-away and does not uniformly transform all spatial relation families.  
**Follow-up:** controlled geometry-changing scene pairs may be added after the VSR-native audit if they resolve ambiguity.  
**Affected grounding results already seen?** No.

---

## 2026-08-10 — No new training before first milestone

**Status:** pre-result / confirmatory execution rule  
**Decision:** use existing 7B zero/General/HardNeg and 2B zero/General assets. Do not retrain merely to begin the grounding audit.  
**Reason:** the current scientific bottleneck is evaluation design, not model training.  
**Affected grounding results already seen?** No.

---

## 2026-08-11 — Baseline reconciliation: 392px cap explains Paper-1 vs Paper-2 normal accuracy

**Status:** verified analysis (bug-fix class: root cause of a numerical discrepancy, no protocol values changed)

**Old rule:** implicit assumption that the Tier-A normal condition replicates the Paper-1 evaluation contract.

**New rule:** the Tier-A/Paper-2 contract intentionally differs from Paper-1 in exactly one behaviorally relevant way — the uniform 392px long-side image cap (docs/TECHNIQUES.md section 4, config.MAX_LONG_SIDE, recorded in every run's metadata). Any cross-paper comparison of absolute normal accuracy must state this contract difference. The cap is a within-run constant across checkpoints and conditions (run fairness preserved), so all Tier-A/B/C paired and difference metrics remain valid.

**Reason (evidence):** Paper-1 zero-shot normal = 0.80911 (1776/2195, results/qwen2vl_7b_metrics_20260809_064919.json). Tier-A full zero-shot normal = 0.76993 (1690/2195). Raw-output comparison aligned by dataset index: 208/2195 examples changed prediction; 0 examples shared the same raw output with a different parsed label (parser contributes nothing). A GPU reproduction of all 208 disagreements under four contract variants (zero-shot Qwen2-VL-7B, current transformers 5.14.1):
- Paper-1 exact (raw image, padding=True): 201/208 match Paper-1;
- Tier-A exact (392-cap, padding+truncation): 204/208 match Tier-A;
- raw image + truncation: 201/208 match Paper-1 (truncation inert);
- 392-cap without truncation: 204/208 match Tier-A.
The 392px cap alone reproduces ~97% of the discrepancy; the residual ~3% is unpinnable (Paper-1 env recorded only as transformers>=4.48.0, no exact versions).

**Affected results already seen?** All Tier-A/B/C absolute accuracies; none of the paired ΔA/ΔG/ΔC differences (checkpoint-equal contract, fairness by construction). Tier-A normal 0.76993 must NOT be compared to Paper-1 0.80911 without citing this cap difference.

**Expected impact:** documentation only. Options deferred to principal: (a) keep 392px contract as canonical Paper-2 and cite the reconciliation; (b) re-run Tier A/B/C under the full-resolution Paper-1 contract for direct comparability (new freeze + runs required, no change to any existing numbers).

**Files/commits:** evidence at /tmp/opencode/repro_summary.json, disagreement IDs /tmp/opencode/disagreement_ids.json; reconciliation record results/grounding/analysis/baseline_reconciliation.md.

---

## 2026-08-11 — Facing/facing-away D1 diagnostic (protocol implementation correction)

**Status:** pre-result protocol implementation correction (frozen before any facingcomp prediction is inspected)

**Old rule:** the Tier-B relcomp validity table soft-excludes `facing <-> facing away from` (oblique orientations make the pair non-exhaustive), so the implemented Tier-B strict-complement transform set contains only depth/horizontal/vertical complements and does not include the orientation construct that motivated HardNeg's inclusion in Paper 2.

**New rule:** a dedicated `facingcomp` transform (flip law: `facing <-> facing away from`, expected = NOT original label) is frozen with its own validity table (`results/grounding/protocol/facing_transform_validity.csv`) and eligible-ID document (`results/grounding/protocol/facing_eligible_ids.json`), both committed before any facingcomp prediction is inspected. Existing Tier-B artifacts and results remain unchanged; the two files are separate from `semantic_transform_validity.csv`/`semantic_eligible_ids.json`.

**Reason:** Paper 1 treated facing/facing-away as a strict complementary family and found the General-vs-HardNeg facing/facing-away consistency dissociation that motivated HardNeg's inclusion. The implemented Tier-B relation-complement eligibility table inadvertently omitted this orientation complement. This is a predeclared diagnostic, not a post-hoc addition after an unfavorable result: the whole reason HardNeg was put into the protocol before experimentation was this exact facing contrast. The conceptual difference (Paper-1 strict-complement treatment vs Tier-B soft exclusion) is documented here and in the freeze files so Paper 2 states it explicitly.

**Affected results already seen?** None for facingcomp (frozen pre-result). Existing Tier-B/C results are unaffected and unchanged.

**Expected impact:** direct measurement of the original D1 facing construct: P1 zero->General and D1 General->HardNeg flip-law compliance on facing/facing-away examples only, alongside both-correct and invalid rates.

**Files/commits:** freeze commit (facing artifacts) precedes any facingcomp run.

---

## Template for future entries

### YYYY-MM-DD — Decision title

**Status:** pre-result confirmatory / verified bug fix / post-result exploratory  
**Old rule:**  
**New rule:**  
**Reason:**  
**Affected results already seen?**  
**Expected impact:**  
**Files/commits:**
