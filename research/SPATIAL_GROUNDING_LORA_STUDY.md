# What Does Spatial Fine-Tuning Actually Teach? — Research Plan

**Branch:** `research/spatial-grounding-audit`  
**Parent/frozen source:** `master` at `3c6bb351edd40b2155a7beac98aeea1cfc7de0ef`  
**Status:** PLANNED / PRIMARY PROTOCOL NOT YET EXECUTED  
**Primary benchmark:** VSR (`cambridgeltl/vsr_random`, held-out test)  
**Primary backbone:** `Qwen/Qwen2-VL-7B-Instruct`  
**Replication backbone:** `HuggingFaceTB/SmolVLM2-2.2B-Instruct`  
**Primary adaptation:** existing VSR General LoRA  
**Key diagnostic adaptation:** existing 7B Hard-Negative LoRA  

> **Protocol authority:** actual experimental runs are governed by `research/GROUNDING_PROTOCOL_FREEZE.md` and `configs/grounding_protocol.yaml`. If this narrative plan and the frozen protocol disagree, the frozen protocol wins. Any post-result protocol change must be logged in `research/DECISION_LOG.md` and labeled exploratory unless it fixes a verified bug.

---

## 1. Locked scientific question

> **When spatial fine-tuning improves accuracy or relational consistency, does it also increase causal sensitivity to the visual evidence that determines the spatial relation?**

The paper is not merely a grounding ablation and not merely a consistency study. It asks whether three commonly conflated forms of improvement actually move together:

```text
ΔA = change in benchmark accuracy
ΔC = change in semantic/logical consistency
ΔG = change in causal visual-grounding / evidence sensitivity
```

A fourth quantity is optional and secondary:

```text
ΔT = change in controlled out-of-distribution transfer
```

The central scientific question is whether spatial adaptation produces:

```text
ΔA ≈ ΔC ≈ ΔG
```

or whether these quantities dissociate.

### Working thesis

> **Accuracy gain, consistency gain, and visual-grounding gain are separable outcomes of spatial adaptation rather than interchangeable evidence of improved spatial reasoning.**

This is a hypothesis, not a conclusion. The paper must remain valid if the quantities do move together.

---

## 2. Scope boundary

This is a **new standalone project**. The previous orientation-focused study is frozen as a separate paper direction.

The prior paper established useful motivation, including that adaptation can improve relational coherence without a corresponding increase in ordinary facing accuracy. This project does not reopen the prior orientation paper. Instead, it uses existing checkpoints as controlled interventions to ask **what capability changed**.

### This project is NOT

- another orientation benchmark paper;
- another generic consistency-training paper;
- another blank-image ablation paper;
- a new LoRA method paper;
- a large scaling study;
- an attempt to infer exact internal mechanisms from behavioral tests.

### This project IS

A paired before/after behavioral decomposition of spatial adaptation into:

1. benchmark performance;
2. semantic/logical coherence;
3. causal dependence on correct visual evidence;
4. optional controlled transfer.

---

## 3. Existing checkpoints create a useful natural experiment

We already have the expensive training assets needed for the first study.

### Primary 7B sequence

```text
7B zero-shot
     |
     | VSR General LoRA
     v
7B General LoRA
     |
     | hard-negative spatial adaptation
     v
7B HardNeg LoRA
```

This gives two scientifically different transitions.

### Transition P1 — benchmark-improving adaptation

**7B zero-shot → 7B General LoRA**

Existing standard VSR results are approximately:

- zero-shot: 80.91%
- General LoRA: 84.69%
- ordinary VSR gain: +3.78 pp

This is the **primary causal comparison** for asking whether benchmark gain is accompanied by grounding gain.

### Transition D1 — consistency-oriented diagnostic

**7B General LoRA → 7B HardNeg LoRA**

In the prior facing/facing-away consistency analysis:

- original facing-family accuracy: 68.9% → 68.9%
- facing consistency: 66.0% → 77.7%

This is unusually valuable because it asks whether a behavioral consistency change is accompanied by a visual-evidence-sensitivity change even when ordinary facing accuracy is unchanged.

**Important caveat:** the pooled strict-family McNemar comparison between General and HardNeg was not statistically significant (`p=0.29`). Therefore this transition is a **key diagnostic**, not the sole confirmatory foundation of the paper, and no claim should state that HardNeg globally and significantly improves consistency over General unless a correctly scoped test supports it.

### Replication transition R1

**2B zero-shot → 2B General LoRA**

Existing standard VSR results are approximately:

- zero-shot: 73.99%
- General LoRA: 76.63%
- gain: +2.64 pp

This is the planned size replication after the primary 7B protocol is frozen.

### Other existing adapters

Targeted, projector, and vision+projector adapters may be used only as **exploratory extension conditions** unless promoted before the primary full run through a documented protocol revision. They should not be added opportunistically after seeing results merely to improve the story.

---

## 4. Primary research questions

### RQ1 — Accuracy change

How much does each adaptation transition change ordinary held-out VSR accuracy?

### RQ2 — Correct-scene dependence

Does adaptation increase the model's dependence on the **correct image**, rather than merely any image or the VSR statement template?

### RQ3 — Semantic coherence

Does adaptation improve behavior under logically linked textual transformations while the image is held fixed?

### RQ4 — Visual causal sensitivity

Does adaptation improve behavior when the **visual world changes while the statement stays fixed** and the correct answer is known to change or remain invariant?

### RQ5 — Dissociation

Can `ΔA`, `ΔC`, and `ΔG` move by materially different amounts under the same adaptation?

This is the conceptual center of the paper.

### RQ6 — Relation-family heterogeneity

Which spatial relation families show genuine evidence-sensitivity gains versus primarily benchmark/task-policy gains?

### RQ7 — Controlled transfer

Do any grounding improvements survive a small, independently controlled counterfactual scene set outside ordinary VSR?

This is secondary and should not block the first paper-quality result.

---

## 5. Main hypotheses

### H1 — General LoRA improves ordinary benchmark accuracy

Already supported by existing VSR results; the new work asks what that gain consists of.

### H2 — `ΔA`, `ΔC`, and `ΔG` need not be equal

Spatial adaptation may teach better answer policy or relation algebra without proportionally increasing visual evidence use.

### H3 — Genuine grounding improvement should be selectively tied to correct visual evidence

If the model becomes more grounded, its advantage should be stronger with the correct image than with deterministically wrong, blank, or absent visual evidence.

### H4 — Semantic consistency and visual causal sensitivity can dissociate

Passing a textual complement/inverse test does not by itself establish grounding. A grounded model should also respond correctly when the pixels change but the text does not.

### H5 — Effects are relation dependent

Horizontal, vertical, depth, containment, topology/contact, proximity, and orientation relations differ in what evidence they require. Aggregate VSR accuracy may hide heterogeneous capability changes.

### H6 — Hard-negative adaptation is a useful stress test

If HardNeg changes semantic consistency more than visual causal sensitivity, that supports a coherence/policy interpretation. If it also improves visual causal sensitivity, then ordinary accuracy may be missing a genuine capability gain. Either result is scientifically informative.

---

## 6. Experimental axes: never collapse these together

The study explicitly separates **semantic** and **visual** interventions.

## Axis S — Semantic/logical counterfactuals

**Pixels remain fixed; language changes.**

Examples:

- relation complement/inversion where logically valid;
- subject/object reversal with relation-specific expected behavior.

These measure whether the model obeys relational logic and linked-answer constraints.

They primarily contribute to `C` (consistency/coherence), not directly to `G`.

## Axis V — Visual counterfactuals

**Language remains fixed; pixels/world change.**

Examples:

- horizontal reflection for valid left/right cases;
- later controlled scene edits where a spatial relation is deliberately changed while object identity and wording are held constant.

These are the strongest tests of causal visual evidence sensitivity and contribute to `G`.

## Axis E — Visual evidence ablations/corruptions

**Language remains fixed; meaningful correct-scene evidence is removed or replaced.**

Examples:

- deterministic shuffled/wrong image;
- matched wrong image if the matching rule is frozen before full evaluation;
- blank image;
- text-only as a diagnostic.

These estimate how much performance depends on valid visual evidence but are weaker than clean geometry-changing visual counterfactuals.

---

## 7. Evidence hierarchy

Not all grounding tests are equally strong. The paper should respect this hierarchy.

### Primary evidence

1. **Correct image vs deterministic shuffled/wrong image** under the same multimodal interface.
2. **Visual counterfactuals** where the text is unchanged and the relation truth is known to change or remain invariant.
3. **Joint both-correct / expected-change behavior** on original + visual-counterfactual pairs.

### Secondary evidence

4. Blank-image condition.
5. Normal-vs-ablation performance gaps.

### Exploratory/diagnostic evidence

6. Text-only behavior.

Text-only is useful for template/language priors but should not be presented as the strongest grounding metric because removing the visual pathway can change interface semantics.

---

## 8. Tier A — first experiment: evidence dependence

Tier A is deliberately cheap and broad. It must be completed before new training.

### A1. Normal

Correct image + original VSR statement.

Purpose: reference benchmark condition.

### A2. Deterministic shuffled image — PRIMARY

Original statement + a different VSR test image.

Requirements:

- same held-out split only;
- deterministic derangement;
- fixed seed stored in protocol;
- no self-pairs;
- same mapping for every compared model condition;
- store original and replacement example/image IDs;
- do not regenerate the mapping after seeing results.

This is the primary cheap test of whether the **correct scene** matters while retaining an ordinary image input.

### A3. Matched wrong image — OPTIONAL PRIMARY UPGRADE

If implemented before full Tier-A evaluation, create a deterministic wrong-image match that reduces obvious distribution shift by matching predeclared metadata such as broad relation family and, where feasible, coarse object/statistical properties.

Rules:

- matching algorithm and fallback policy must be frozen before results;
- replacement image must still be known not to be the original scene;
- do not hand-pick visually plausible replacements;
- if matching cannot be made reliable, omit this condition rather than improvise.

### A4. Blank image — SECONDARY

Original statement + fixed constant image.

Purpose: remove semantic evidence while preserving a multimodal call path.

The exact image construction must be fixed and recorded.

### A5. Text-only — EXPLORATORY

Original statement with no meaningful visual evidence, using the fairest architecture-compatible interface.

Purpose: estimate linguistic/template-prior behavior.

Do not treat this as the main causal grounding test.

---

## 9. Tier B — semantic coherence tests

These tests belong to `ΔC`.

### B1. Strict relation complement/inversion

Use only relation mappings for which the expected truth behavior is logically valid.

Safe examples may include, subject to template verification:

- left ↔ right;
- above ↔ below;
- in front of ↔ behind;
- compatible containment inverse forms where argument structure is correct.

Never treat `parallel ↔ perpendicular` as a universal strict complement; oblique configurations make both false possible.

For every relation pair, store:

- transform name;
- relation family;
- strict/soft/unsafe status;
- expected label behavior;
- eligible example IDs;
- exclusion reason.

### B2. Subject/object reversal

Do not implement with generic string replacement.

Create a relation taxonomy:

- symmetric;
- asymmetric;
- inverse-pair;
- unsafe/ambiguous.

Validate subject/object extraction before using the transform. The historical simple `" is "` parser is not sufficient evidence of correctness for a paper-quality intervention.

### Semantic metrics

For strict linked pairs report:

- original accuracy;
- transformed accuracy;
- expected logical flip/stability rate;
- both-correct rate;
- original-only / transformed-only / both-wrong;
- exact paired tests where appropriate.

---

## 10. Tier C — visual causal counterfactuals

These tests belong most directly to `ΔG`.

### C1. Horizontal reflection

Mirror the image while keeping the statement fixed.

Primary valid use: left/right-type relations where horizontal reflection has a known truth effect.

Requirements:

- relation-specific expected behavior;
- no global label flip;
- invariant relations kept separate from flip-expected relations;
- same transformed pixels for every compared model;
- transformation metadata saved.

### C2. Controlled geometry-changing scene pairs — HIGH-VALUE EXTENSION

If Tier A/B/C1 produce a scientifically meaningful signal, add a **small controlled counterfactual set**, not a giant new benchmark.

Goal: create paired scenes where only the spatial relation of interest changes while nuisance factors remain controlled.

Potential relation families:

- left ↔ right;
- above ↔ below;
- front ↔ behind;
- containment relations where exact labels are unambiguous;
- facing ↔ facing-away through actual object orientation manipulation.

Design principles:

- same object identities within a pair where possible;
- same statement wording within the visual pair;
- balanced labels;
- balanced colors/shapes/backgrounds/viewpoints;
- irrelevant-edit controls;
- exact generated ground truth;
- no use of a model's own predicted labels as ground truth.

Useful controls:

- rotate/change an irrelevant object;
- background-only change;
- crop/lighting nuisance change;
- identity-preserving relation change;
- invariant relation cases.

A model that reacts to every pixel change is not grounded. We require **relation-specific expected response**.

---

## 11. Primary model matrix

### Confirmatory/core

| Role | Condition | Purpose |
|---|---|---|
| Primary baseline | 7B zero-shot | starting capability |
| Primary tuned | 7B General LoRA | benchmark-improving spatial adaptation |
| Key diagnostic | 7B HardNeg LoRA | consistency-oriented adaptation contrast |
| Replication baseline | 2B zero-shot | smaller-backbone replication |
| Replication tuned | 2B General LoRA | smaller-backbone adaptation |

### Exploratory only unless promoted before full run

- 7B Targeted LoRA;
- 7B Projector LoRA;
- 7B Vision+Projector LoRA;
- 2B Targeted LoRA;
- additional external models.

Do not expand the condition matrix simply because a core result is null.

---

## 12. Core quantities and metrics

Let `A_{m,c}` be accuracy for model condition `m` under evaluation condition `c`.

### 12.1 Accuracy change (`ΔA`)

For an adaptation transition `u → v`:

```text
ΔA = A_v,normal - A_u,normal
```

### 12.2 Correct-scene dependence

For model `m`:

```text
G_shuffle(m) = A_m,normal - A_m,shuffle
G_blank(m)   = A_m,normal - A_m,blank
G_text(m)    = A_m,normal - A_m,text
```

The primary ablation gap is `G_shuffle`.

### 12.3 Grounding change (`ΔG`)

For adaptation `u → v`:

```text
ΔG_shuffle = G_shuffle(v) - G_shuffle(u)
```

Analogous quantities may be reported for blank/text, but they are secondary/diagnostic.

For visual counterfactuals, define grounding sensitivity using paired expected response rather than only marginal accuracy.

### 12.4 Semantic consistency (`C` and `ΔC`)

For strict semantic pairs, `C` is the proportion obeying the expected linked-answer law.

```text
ΔC = C_v - C_u
```

Always distinguish:

- consistency;
- pair both-correct;
- marginal accuracy.

Consistency can increase by becoming coherently wrong.

### 12.5 Visual causal sensitivity

For a visual pair whose ground-truth answer should flip:

- expected prediction flip rate;
- both-correct rate;
- transformed accuracy;
- wrong-direction flip rate.

For an invariant visual control:

- expected stability rate;
- both-correct rate.

### 12.6 Joint grounded consistency

For matched semantic and visual transformations where the transformation laws are known, report the proportion of scene/query units satisfying **both** the semantic law and the visual causal law.

This is a stronger composite diagnostic than ordinary consistency alone.

### 12.7 Invalid output rate

Always report malformed/unparseable output. A drop in invalid outputs can increase benchmark accuracy without demonstrating improved spatial reasoning.

---

## 13. Interpretation matrix

### Case 1 — `ΔA > 0`, `ΔC > 0`, `ΔG ≈ 0`

Evidence consistent with improved task policy/coherence without proportional visual grounding improvement.

### Case 2 — `ΔA > 0`, `ΔC > 0`, `ΔG > 0`

Evidence consistent with adaptation improving both behavior and visual evidence use.

### Case 3 — `ΔA ≈ 0`, `ΔC > 0`, `ΔG ≈ 0`

Coherence-only improvement; especially relevant to the General→HardNeg diagnostic.

### Case 4 — `ΔA ≈ 0`, `ΔC > 0`, `ΔG > 0`

Ordinary accuracy is missing a genuine grounding improvement.

### Case 5 — relation-dependent mixture

Potentially the most informative outcome. Report the heterogeneity rather than forcing a single grounded/not-grounded label.

No single ablation is sufficient to claim an internal mechanism.

---

## 14. Relation-family analysis

At minimum preserve/report:

- orientation;
- depth;
- horizontal;
- vertical;
- containment;
- topology/contact;
- proximity where sample size permits.

Keep per-relation counts.

Primary conclusions should not rely on tiny cells. Small relation analyses are exploratory unless predeclared and sufficiently powered.

The relation-family map must be centralized for this project so scripts cannot silently disagree.

---

## 15. Statistical plan

Because conditions are evaluated on matched examples, use paired analyses.

### Required

- exact McNemar for paired binary correctness comparisons where applicable;
- paired/bootstrap confidence intervals for accuracy differences;
- bootstrap confidence intervals for `ΔG` and other gap differences;
- confidence intervals for consistency and visual expected-response changes;
- effect sizes alongside p-values.

### Confirmatory comparison order

1. 7B zero-shot vs 7B General;
2. 7B General vs 7B HardNeg as key diagnostic;
3. 2B zero-shot vs 2B General replication.

### Multiple comparisons

- define a small set of primary global tests;
- treat relation-level tests as secondary/exploratory unless predeclared;
- use an appropriate correction if many inferential relation-level claims are reported.

### Seeds

Do **not** retrain before the first capability decomposition is established.

If a core effect is meaningful:

- replicate General LoRA with 3 training seeds for the primary backbone;
- ideally also replicate 2B if compute permits;
- run the same frozen audit on every seed;
- report mean ± SD across seeds plus within-seed paired analyses.

HardNeg seed replication is optional and only justified if the diagnostic becomes central to the final claim.

---

## 16. Experimental order

### Phase 0 — protocol governance

- [x] dedicated branch;
- [x] integrated research plan;
- [x] branch parent recorded;
- [x] protocol authority defined;
- [ ] protocol/config committed and reviewed;
- [ ] prompt/parser/generation settings frozen;
- [ ] exact evaluation IDs frozen;
- [ ] implementation tests added.

### Phase 1 — minimal evaluator refactor

Goal: one intervention/evaluation path across model conditions.

Target interface:

```python
predict(image, statement)
predict_batch(images, statements)
```

Recommended modules:

```text
src/models/base.py
src/models/qwen2vl.py
src/evaluation/interventions.py
src/evaluation/grounding_metrics.py
src/evaluation/pairing.py
src/evaluation/statistics.py
```

Reuse the existing SmolVLM wrapper. Do not rewrite unrelated research code.

### Phase 2 — Tier-A implementation

Implement and test:

1. normal;
2. deterministic shuffled image;
3. blank image;
4. text-only diagnostic;
5. optional matched-shuffle only if the algorithm is frozen before the full run.

### Phase 3 — smoke tests

For 7B zero, General, HardNeg:

1. 10-example smoke;
2. ~200-example paired pilot for engineering validation only;
3. freeze bug fixes;
4. full VSR test.

The pilot is not for selecting whichever condition gives the preferred result.

### Phase 4 — primary Tier-A analysis

Compute:

- ordinary accuracy;
- condition-specific adaptation gains;
- correct→shuffle gaps;
- `ΔG_shuffle`;
- blank/text diagnostics;
- invalid rate;
- per-family breakdown;
- paired CIs/tests.

### Phase 5 — semantic counterfactuals

Freeze transform validity map and eligible IDs before full evaluation.

Run strict relation/inverse and validated subject/object transformations.

Compute `C` and `ΔC` separately from grounding metrics.

### Phase 6 — VSR visual counterfactuals

Implement validated horizontal reflection and any other VSR-native visual transform whose expected effect is logically guaranteed.

### Phase 7 — first synthesis

For 7B zero → General and General → HardNeg, compare:

```text
ΔA, ΔC, ΔG
```

This is the first point at which the main dissociation hypothesis can be evaluated.

### Phase 8 — 2B replication

Run the frozen protocol on 2B zero + General.

Do not change interventions based on 7B results.

### Phase 9 — controlled visual-counterfactual set

Only if it materially sharpens the grounding claim. Keep it small and exact rather than broad and noisy.

### Phase 10 — seed replication

Run only after the final primary protocol is stable.

### Phase 11 — optional external/reference models

Only after core analyses are complete and protocol is frozen.

---

## 17. Transformation validity rules

1. Every transform must specify expected truth behavior.
2. Ambiguous examples are excluded from strict metrics, not guessed.
3. No universal label-flip rule across relations.
4. Symmetric and asymmetric relations are separate.
5. `parallel ↔ perpendicular` is not a universal strict complement.
6. Base/tuned models receive identical transformed inputs.
7. Every transformed row stores parent ID + transform metadata.
8. Every transformation has unit tests and manual stratified spot checks.
9. Visual and semantic transformations must never be conflated in analysis.
10. A change that merely perturbs pixels without a known expected relation effect is a nuisance control, not a grounding success criterion.

---

## 18. Subject/object parsing rule

Before any subject/object reversal experiment:

1. audit parsing over the eligible test set;
2. record success/failure/ambiguity counts;
3. verify reconstruction on a sample;
4. exclude uncertain examples;
5. store exclusions and reasons.

Do not rely on the historical generic split around `" is "` for a confirmatory counterfactual.

---

## 19. Prediction schema

Every new prediction row should contain at least:

```text
example_id
paired_parent_id
split
condition
intervention_axis
statement
original_statement
relation
relation_family
subject
object
ground_truth
expected_transformed_label
expected_prediction_behavior
prediction
correct
raw_output
model_id
model_revision
model_condition
adapter_path
adapter_hash
training_seed
prompt_version
parser_version
image_id
source_image_id
replacement_image_id
transformed_image_id
transform_name
transform_version
transform_metadata
shuffle_seed
generation_settings
run_id
git_commit
protocol_version
```

No result file should depend only on a timestamp for provenance.

---

## 20. Run metadata

Every run must store:

- git commit + branch;
- protocol version/hash;
- model ID/revision;
- adapter path/hash;
- dataset ID/revision/split;
- exact example IDs;
- condition/intervention version;
- all random seeds;
- prompt text/hash;
- parser version/hash;
- generation parameters;
- dtype and attention implementation;
- image preprocessing;
- package/environment snapshot;
- start/end timestamps;
- prediction artifact hash where practical.

Reuse the stronger SITE-style metadata discipline from the prior paper.

---

## 21. Prompt and decoding fairness

Within every base/tuned comparison:

- same prompt;
- same processor path;
- same image preprocessing;
- same generation limit;
- greedy decoding;
- same parser;
- same batch semantics where possible.

Cross-model implementation differences matter less than within-model fairness, but unnecessary differences should still be minimized.

The parser must have tests for:

- `True`;
- `False`;
- harmless wrappers;
- both words present;
- empty output;
- malformed output.

---

## 22. Anti-cherry-picking / change-control policy

Before each confirmatory full run, freeze:

- compared model conditions;
- eligible IDs;
- intervention definitions;
- transform validity map;
- shuffle seed/mapping;
- prompt/parser/generation parameters;
- primary metrics;
- primary statistical tests.

After full primary results are observed:

- new conditions are exploratory unless fixing a demonstrated bug;
- bug fixes must document affected examples and old/new behavior;
- no dropping conditions because they weaken the preferred story;
- no redefining a relation subset based on observed performance;
- no changing a shuffle seed after seeing results;
- no replacing an unfavorable primary metric with a newly invented one.

Protocol changes are recorded in `research/DECISION_LOG.md`.

---

## 23. What future research agents MAY change

They may:

- improve engineering efficiency without changing model inputs/semantics;
- add tests;
- fix verified bugs with a logged diff;
- add exploratory analyses clearly labeled as such;
- propose a controlled visual-counterfactual dataset design before it is frozen;
- refine figure/table presentation after metrics are fixed.

They may **not silently change**:

- the central `ΔA / ΔC / ΔG` question;
- the core 7B zero→General comparison;
- the General→HardNeg diagnostic role;
- the 2B replication role;
- the evidence hierarchy;
- semantic-vs-visual intervention separation;
- the primary correct-vs-shuffled evidence test;
- interpretation rules;
- confirmatory/exploratory labels after results are seen.

Any scientific redesign must be explicit and committed as a protocol revision before the affected full run.

---

## 24. Novelty target and literature guardrail

The intended contribution is **not** that consistency can be wrong, that VLMs sometimes ignore images, or that fine-tuning can overfit.

The intended contribution is:

> **A controlled adaptation-delta study testing whether spatial fine-tuning moves benchmark accuracy, relational coherence, and causal visual evidence sensitivity together or independently.**

The strongest framing is about **what the adaptation changed**, using the same model/checkpoints before and after training.

Before submission, run a fresh literature review focused specifically on:

- spatial fine-tuning + visual grounding;
- consistency training + evidence sensitivity;
- behavioral adaptation decomposition;
- visual counterfactual sensitivity after fine-tuning;
- spatial negative transfer.

Do not claim “first” without that final review.

---

## 25. Main paper table concept

| Model condition | VSR accuracy | Semantic consistency | Correct→shuffle gap | Visual-CF expected response | Visual-CF both-correct | Controlled OOD-CF |
|---|---:|---:|---:|---:|---:|---:|
| 7B zero-shot | ... | ... | ... | ... | ... | ... |
| 7B General | ... | ... | ... | ... | ... | ... |
| 7B HardNeg | ... | ... | ... | ... | ... | ... |
| 2B zero-shot | ... | ... | ... | ... | ... | ... |
| 2B General | ... | ... | ... | ... | ... | ... |

The paper should emphasize transitions (`ΔA`, `ΔC`, `ΔG`), not just absolute rows.

---

## 26. Main figure concept

A conceptual figure should place adaptation effects on three axes:

```text
              Accuracy ΔA
                  ^
                 / \
                /   \
               /     \
   Grounding ΔG ----- Consistency ΔC
```

Different adaptation transitions may occupy different parts of this space.

Additional figures:

1. normal vs shuffled/blank/text by model condition;
2. per-family `ΔG_shuffle`;
3. semantic consistency vs visual causal sensitivity;
4. visual-counterfactual both-correct rate;
5. controlled OOD counterfactual result if completed.

---

## 27. First milestone

The first milestone is complete when the **same VSR test examples** have been evaluated for:

```text
7B zero-shot
7B General LoRA
7B HardNeg LoRA
```

under:

```text
normal
shuffled image
blank image
text-only diagnostic
```

with:

- deterministic pairing metadata;
- standard accuracy/invalid rate;
- correct→shuffle gaps;
- `ΔG_shuffle` for zero→General and General→HardNeg;
- per-family breakdown;
- paired confidence intervals/tests;
- a frozen result report.

No new fine-tuning is required for this milestone.

---

## 28. Second milestone

Add validated semantic counterfactuals and visual counterfactuals, then compute for the same transitions:

```text
ΔA
ΔC
ΔG
```

The study becomes scientifically decisive when we can say whether those three quantities co-move or dissociate.

---

## 29. Success criteria

The project succeeds even under a null result if the protocol is correct and paired.

Scientifically useful outcomes include:

- accuracy rises while grounding does not;
- accuracy and grounding both rise;
- consistency rises while grounding does not;
- consistency rises and grounding also rises despite unchanged accuracy;
- strongly relation-dependent changes;
- model-size differences in how adaptation is absorbed.

Do not define success as obtaining a preferred direction.

---

## 30. Working titles

Primary:

> **What Does Spatial Fine-Tuning Actually Teach? Separating Accuracy, Consistency, and Visual Evidence Sensitivity in Vision-Language Models**

Alternatives:

- **Better, More Consistent, or More Grounded? Auditing Spatial Fine-Tuning in Vision-Language Models**
- **Seeing or Just Agreeing? Causal Tests of What Spatial Adaptation Changes in VLMs**
- **Do Spatial Fine-Tuning Gains Reflect Visual Grounding? A Paired Adaptation Audit**

Do not use a result-assuming title such as “Consistent but Not Grounded” before the data support it.

---

## 31. Current branch state and next action

At this plan revision:

- prior orientation research remains frozen/standalone;
- existing 2B/7B base and General checkpoints are available;
- existing 7B HardNeg checkpoint is available;
- existing logical-consistency results motivate the diagnostic comparison;
- systematic Tier-A grounding/evidence-dependence results have not yet been run;
- no new training is needed for the first milestone;
- the next bottleneck is **protocol-compliant evaluation implementation**.

**Next action:** implement/freeze the Tier-A protocol exactly as specified by `research/GROUNDING_PROTOCOL_FREEZE.md` and `configs/grounding_protocol.yaml`, then run 7B zero/General/HardNeg engineering smokes before the full paired audit.
