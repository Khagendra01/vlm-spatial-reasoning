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

## Template for future entries

### YYYY-MM-DD — Decision title

**Status:** pre-result confirmatory / verified bug fix / post-result exploratory  
**Old rule:**  
**New rule:**  
**Reason:**  
**Affected results already seen?**  
**Expected impact:**  
**Files/commits:**
