# Spatial Grounding After Spatial LoRA — Research Plan

**Branch:** `research/spatial-grounding-audit`  
**Parent/frozen source:** `master` at `3c6bb351edd40b2155a7beac98aeea1cfc7de0ef`  
**Status:** PLANNED / NOT YET EXECUTED  
**Primary benchmark:** VSR (`cambridgeltl/vsr_random`)  
**Primary models:** SmolVLM2-2.2B-Instruct and Qwen2-VL-7B-Instruct  
**Primary intervention:** spatial LoRA trained on VSR  

---

## 1. One-sentence research question

> **When spatial LoRA improves VSR accuracy, did the model actually become more visually grounded?**

The key distinction is between **benchmark improvement** and **grounding improvement**.

A model can score higher on VSR after fine-tuning for several reasons:

- better use of the image's spatial evidence;
- stronger linguistic or label priors;
- better adaptation to VSR templates;
- improved task-format/calibration behavior;
- memorization of benchmark-specific regularities;
- improved logical consistency without improved perception;
- some combination of the above.

This study is designed to isolate whether the gain caused by spatial LoRA is accompanied by a stronger causal dependence on the **correct visual evidence**.

---

## 2. Scope boundary

This branch is a **new standalone research project**.

The previous orientation-focused study is considered frozen and complete as an independent paper direction. Its results are useful motivation, but this study must not silently turn back into an orientation-only project.

### Previous study

Main question:

> Why does orientation remain a stubborn spatial-reasoning bottleneck?

It studied scaling, prompting, LM LoRA, hard negatives, projector/vision adaptation, representation probes, logical consistency, two-stage reasoning, clean-label robustness, and SITE transfer.

### This study

Main question:

> When explicit spatial task adaptation raises benchmark accuracy, what kind of capability changed?

The unit of analysis is therefore **the before-vs-after capability change caused by spatial LoRA**, measured behaviorally under controlled visual and semantic interventions.

---

## 3. Core experimental design

For each model size, compare the **same base model** before and after spatial LoRA on the **same evaluation examples**.

```text
                  SAME VSR TEST EXAMPLES
                          |
             +------------+------------+
             |                         |
          BASE MODEL                LoRA MODEL
             |                         |
             +------------+------------+
                          |
              IDENTICAL AUDIT CONDITIONS
                          |
       +------------------+------------------+
       |        |         |        |         |
     normal   text     blank    shuffled   counterfactuals
```

Primary treatment/control pairs:

### 2B pair

- Base: `HuggingFaceTB/SmolVLM2-2.2B-Instruct`
- Tuned: existing **2B General LoRA** checkpoint

Current standard VSR test result:

- base: ~73.99%
- General LoRA: ~76.63%
- benchmark gain: ~+2.64 percentage points

### 7B pair

- Base: `Qwen/Qwen2-VL-7B-Instruct`
- Tuned: existing **7B General LoRA** checkpoint

Current standard VSR test result:

- base: ~80.91%
- General LoRA: ~84.69%
- benchmark gain: ~+3.78 percentage points

These existing checkpoints are sufficient for the **first grounding audit**. Do not retrain before establishing whether the effect exists.

---

## 4. Primary research questions

### RQ1 — Benchmark learning

How much does spatial LoRA improve ordinary held-out VSR accuracy?

This is already partially answered by the existing standard evaluations.

### RQ2 — Visual grounding learning

Does spatial LoRA increase the model's dependence on the correct visual evidence?

Operationally, this means the tuned model should lose more of its advantage when the correct visual information is removed or corrupted, and should respond appropriately when the image geometry changes.

### RQ3 — Counterfactual geometric sensitivity

Does LoRA improve paired consistency when the relation semantics or image geometry are deliberately changed?

### RQ4 — Transfer

Does any learned grounding improvement transfer outside the exact VSR distribution?

### RQ5 — Scale

Does the relationship between benchmark gain and grounding gain differ between ~2B and ~7B models?

This is a secondary question. The paper should not become a broad scaling study.

---

## 5. Main hypotheses

### H1 — Benchmark improvement

Spatial LoRA increases ordinary VSR test accuracy for both model sizes.

### H2 — Benchmark gain and grounding gain are not necessarily equal

A model may improve on VSR without becoming equivalently more dependent on correct visual evidence.

### H3 — Some LoRA gains may survive visual ablation

If text-only, blank-image, or shuffled-image accuracy also rises strongly after LoRA, part of the benchmark gain is likely attributable to nonvisual task/dataset adaptation.

### H4 — Genuine grounding should improve paired geometric sensitivity

A visually grounded improvement should increase correctness/consistency under interventions whose truth value changes because the geometry changes.

### H5 — The effect will vary by relation family

Spatial relations differ substantially in whether they require object identity, object-intrinsic orientation, depth, topology, containment, or simple relative position. Grounding gains should therefore be analyzed per relation/family rather than only globally.

---

## 6. Audit conditions

The audit is split into two tiers.

## Tier A — Visual evidence ablations

These are the first experiments because they are cheap, broad, and directly diagnostic.

### A1. Normal

**Input:** correct image + original VSR statement.  
**Purpose:** standard benchmark performance.

This is the reference condition.

### A2. Text-only

**Input:** original statement with no meaningful image evidence.  
**Purpose:** estimate how much of the task can be solved from linguistic/template priors alone.

Implementation must preserve the model interface as fairly as possible. If a model architecture strictly requires a visual input, prefer a dedicated null-visual implementation rather than silently changing prompt format in a way that confounds the comparison.

Report both accuracy and invalid-output rate.

### A3. Blank image

**Input:** original statement + a constant blank image.  
**Purpose:** remove semantic visual evidence while keeping the multimodal pathway active.

The blank image must have fixed size/content across examples and models, with the exact generation rule stored in metadata.

### A4. Shuffled image

**Input:** original statement + a different VSR test image.  
**Purpose:** test whether the model requires the correct scene rather than merely any image.

Requirements:

- deterministic permutation;
- fixed seed;
- no example may receive its own image;
- same permutation for base and LoRA;
- ideally preserve split only; do not mix train/test;
- store `source_example_id` and `shuffled_image_example_id`.

A derangement is preferred over naive random sampling.

---

## Tier B — Paired semantic/geometric counterfactuals

These are implemented only after Tier A is validated.

### B1. Relation inversion

Replace a relation with a logically valid inverse/complement where the transformed truth value is known.

Examples of safe inverse/complement families may include:

- left ↔ right;
- above ↔ below;
- in front of ↔ behind;
- inside ↔ contains, when grammatical argument structure is handled correctly.

Do **not** assume every relation has a strict complement.

Particularly:

- `parallel` ↔ `perpendicular` is not a strict binary complement in arbitrary scenes;
- symmetric relations require different treatment;
- soft/ambiguous cases must be excluded from strict paired metrics.

Every transformation needs an explicit validity map and unit tests.

### B2. Subject/object reversal

Swap the two entities while retaining or appropriately transforming the relation.

Example:

```text
Original:    A is left of B.
Reversal:    B is left of A.
```

For asymmetric relations, truth should often flip. For symmetric relations it should not.

Create an explicit taxonomy:

- asymmetric;
- symmetric;
- inverse-pair;
- unsafe/ambiguous.

Do not rely on a generic string swap.

### B3. Horizontal image reflection

Horizontally mirror the image while keeping the text fixed.

This is a high-value visual intervention because the linguistic input is unchanged while image geometry changes.

For left/right-type relations, the truth value should change under valid reflection cases. For many other relations, it should remain invariant.

Requirements:

- explicit relation-specific expected label behavior;
- exclude relations where the expected effect is not logically guaranteed;
- preserve image dimensions and non-geometric content;
- store transformation metadata and paired-parent ID.

Do **not** globally flip all labels after mirroring.

---

## 7. Why these conditions answer the question

The central logic is causal/behavioral rather than purely correlational.

Suppose LoRA raises normal VSR accuracy.

### Pattern A — likely nonvisual/task adaptation

```text
normal gain:      large
text-only gain:   large
blank gain:       large
shuffled gain:    large
mirror/inverse:   little improvement
```

Interpretation: benchmark performance improved, but much of the added capability survives when correct visual evidence is absent or wrong.

### Pattern B — stronger evidence of visual grounding

```text
normal gain:      positive
text-only gain:   small/none
blank gain:       small/none
shuffled gain:    small/none
paired geometric correctness: improves
```

Interpretation: the tuned model benefits specifically when valid scene information is available and is more sensitive to geometry-changing interventions.

### Pattern C — mixed learning

The most realistic outcome may be a mixture: some task adaptation plus some grounding improvement, varying by relation family.

The paper should support mixed conclusions rather than forcing a binary grounded/not-grounded label.

---

## 8. Primary metrics

Let:

- `A_base,c` = base accuracy under condition `c`
- `A_lora,c` = LoRA accuracy under condition `c`

### 8.1 Benchmark gain

```text
Delta_A = A_lora,normal - A_base,normal
```

### 8.2 Visual-ablation gaps

For each model:

```text
G_text     = A_normal - A_text
G_blank    = A_normal - A_blank
G_shuffle  = A_normal - A_shuffle
```

These quantify how much performance depends on the correct multimodal evidence.

### 8.3 Grounding-gain change after LoRA

For example:

```text
Delta_G_shuffle = G_shuffle,lora - G_shuffle,base
Delta_G_text    = G_text,lora    - G_text,base
Delta_G_blank   = G_blank,lora   - G_blank,base
```

A positive `Delta_G` means the tuned model has become more dependent on valid visual evidence by this operational measure.

### 8.4 Condition-specific LoRA gain

```text
Delta_A_condition = A_lora,condition - A_base,condition
```

Compare the normal gain against ablated gains.

### 8.5 Prediction flip rate

For paired counterfactuals, measure how often the prediction changes when the expected truth value changes.

Flip rate alone is not sufficient because a model can flip in the wrong direction.

### 8.6 Paired correctness

For each original/counterfactual pair, record:

- original correct;
- transformed correct;
- both correct;
- original-only correct;
- transformed-only correct;
- both wrong.

**Both-correct rate** is a stricter measure of geometric competence than marginal accuracy.

### 8.7 Expected-change consistency

For transforms with a known label flip:

- did the prediction change in the expected direction?

For invariant transforms:

- did the prediction remain semantically consistent?

### 8.8 Invalid-output rate

Always report malformed/unparseable output separately.

A lower invalid rate can improve benchmark accuracy without demonstrating improved reasoning.

---

## 9. Relation-family analysis

Do not rely only on aggregate VSR accuracy.

At minimum report:

- orientation;
- depth;
- horizontal;
- vertical;
- containment;
- topology/contact;
- proximity where sample size permits.

Also retain per-relation counts and accuracy.

Avoid strong conclusions for very small relations.

The existing family map can be reused, but this branch should centralize it rather than duplicating incompatible maps across scripts.

---

## 10. Statistical analysis

Because base and LoRA evaluate the **same examples**, use paired statistics.

### Required

- exact/paired McNemar test for paired binary correctness where applicable;
- paired bootstrap confidence intervals for accuracy differences;
- bootstrap confidence intervals for grounding-gap differences;
- report effect sizes, not p-values alone.

### Multiple seeds

Do not retrain immediately.

Phase 1 uses existing checkpoints to establish whether the phenomenon is meaningful.

If the main result is scientifically interesting, repeat the final General-LoRA condition with **3 training seeds** for both model sizes, or at minimum for the primary model if compute becomes limiting.

Report mean ± standard deviation across seeds and retain paired example-level analyses inside each seed.

### Multiple comparisons

If many relation-level significance tests are presented, apply an appropriate correction or clearly distinguish primary confirmatory tests from exploratory analyses.

---

## 11. Experimental order

## Phase 0 — Branch/reproducibility setup

- [x] Create dedicated research branch.
- [x] Add this study plan.
- [ ] Record branch parent commit.
- [ ] Add experiment config directory/files.
- [ ] Add tests before final runs.
- [ ] Freeze prompt/parser/generation settings for each model.

## Phase 1 — Refactor only what is necessary

Goal: avoid duplicating intervention logic separately for 2B and 7B.

Recommended interface:

```python
predict(image, statement)
predict_batch(images, statements)
```

Create or standardize:

```text
src/models/base.py
src/models/smolvlm.py
src/models/qwen2vl.py
src/evaluation/interventions.py
src/evaluation/grounding_metrics.py
src/evaluation/pairing.py
src/evaluation/statistics.py
```

Do not rewrite the full repository merely for style.

## Phase 2 — Tier-A implementation and tests

Implement:

- normal;
- text-only;
- blank image;
- deterministic shuffled image.

Required tests:

- shuffled mapping contains no self-pairs;
- shuffled mapping deterministic for fixed seed;
- blank image exactly reproducible;
- base and LoRA receive identical example IDs and transforms;
- parser behavior unchanged;
- metrics correct on toy examples.

## Phase 3 — 7B pilot

Run first on:

```text
7B base
7B General LoRA
```

Conditions:

```text
normal
text-only
blank
shuffled
```

Suggested execution order:

1. 10-example smoke;
2. 100–200-example paired smoke;
3. full VSR test.

Do not inspect and redesign transforms based on which version produces the preferred result.

## Phase 4 — First scientific decision point

Compute:

- normal LoRA gain;
- text/blank/shuffle gains;
- base visual-ablation gaps;
- LoRA visual-ablation gaps;
- `Delta_G` values;
- per-family differences;
- paired CIs/tests.

Decision:

### If clear signal exists

Proceed to Tier B counterfactuals.

### If null/mixed

Still report honestly; inspect relation-family heterogeneity before changing the hypothesis.

Do not train a new model simply because the first result is inconvenient.

## Phase 5 — Tier-B counterfactual implementation

Implement and validate:

- strict relation inversion;
- subject/object reversal;
- horizontal reflection.

Before full evaluation, produce an audit table with:

```text
relation
transform type
expected label behavior
symmetric/asymmetric
safe/unsafe
number of eligible examples
```

Manually inspect a stratified sample of transformed examples before running the full suite.

## Phase 6 — Full 7B grounding audit

Run base + General LoRA on all frozen valid conditions.

Generate paired prediction tables and canonical metrics.

## Phase 7 — 2B replication

Run the exact same frozen audit on:

```text
2B base
2B General LoRA
```

Do not change transformations, prompts, or metrics because of 7B results.

## Phase 8 — Seed replication

If the phenomenon survives both sizes and is worth publishing:

- retrain General LoRA with multiple seeds;
- rerun the final frozen audit;
- aggregate across seeds.

## Phase 9 — OOD transfer

Use a small controlled external audit rather than turning the project into a new benchmark-construction effort.

Potential components:

- simple synthetic scenes with balanced geometry;
- left/right, above/below, containment, overlap, near/far when unambiguous;
- balanced object identity/color/shape/background;
- identical textual templates across counterfactual image pairs.

SITE may be referenced as motivation from the prior project, but this study's main OOD test should be designed specifically to answer **grounding after LoRA**, not merely general external benchmark transfer.

## Phase 10 — Optional frozen strong-model reference

MiMo or another strong external model may be evaluated only after the protocol is frozen.

It is a reference condition, not a judge, and not necessary for the primary causal comparison.

No paid API calls should be made before the evaluation protocol and budget are explicitly frozen.

---

## 12. Data schema for prediction files

Every new prediction row should include at least:

```text
example_id
paired_parent_id
split
condition
statement
original_statement
relation
subject
object
ground_truth
expected_transformed_label
prediction
correct
raw_output
model_id
model_size
base_or_lora
adapter_path
seed
prompt_version
parser_version
image_id
source_image_id
transformed_image_id
transform_name
transform_metadata
shuffle_seed
generation_settings
run_id
git_commit
```

Do not rely on timestamps in filenames as the sole provenance mechanism.

---

## 13. Run metadata

Every run should save a machine-readable metadata file containing:

- git commit hash;
- branch;
- model ID/revision;
- adapter ID/path/hash;
- dataset ID/revision;
- split;
- exact example IDs;
- condition;
- transformation version;
- random seed;
- prompt text/hash;
- parser version/hash;
- generation parameters;
- dtype;
- attention implementation;
- image preprocessing settings;
- package/environment snapshot;
- start/end timestamps;
- output file hashes where practical.

Follow the stronger SITE-style reproducibility pattern already established in the previous project.

---

## 14. Parser and generation controls

The task is binary True/False.

The primary comparison should not be contaminated by different decoding policies between base and LoRA.

For each model pair:

- same prompt;
- same processor path;
- same image preprocessing;
- same `max_new_tokens`;
- same greedy decoding;
- same parser;
- same batch semantics where possible.

Cross-model 2B-vs-7B differences are less important than within-model base-vs-LoRA fairness, but unnecessary differences should still be minimized.

The parser must be unit-tested against:

- `True`;
- `False`;
- common harmless wrappers;
- outputs containing both words;
- malformed output;
- empty output.

---

## 15. Subject/object parsing warning

The existing VSR loader historically derives subject/object fields using a simple caption split around `" is "`.

That is insufficiently trustworthy for a subject/object reversal experiment without validation.

Before B2:

1. audit parsing over the full eligible test set;
2. record success/failure/ambiguous counts;
3. verify round-trip statement reconstruction where possible;
4. exclude uncertain examples rather than guessing;
5. keep an exclusion log.

No counterfactual claim should depend on silently incorrect entity parsing.

---

## 16. Transformation validity principles

The study's credibility depends more on intervention correctness than on the number of conditions.

Rules:

1. A transformation must have a clearly specified expected truth behavior.
2. If the expected label is ambiguous, exclude the example from the strict metric.
3. Never apply one global label-flip rule to all relations.
4. Symmetric and asymmetric relations must be handled separately.
5. Image transforms and text transforms must be independently logged.
6. All pairings must be deterministic and reproducible.
7. Base and LoRA must receive exactly the same transformed examples.
8. Transformation code must have unit tests and manual spot checks.

---

## 17. Main analysis table concept

The central table should eventually resemble:

| Model | Condition | Base acc | LoRA acc | LoRA gain | Base visual gap | LoRA visual gap | Grounding-gap change |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2B | normal | ... | ... | ... | — | — | — |
| 2B | text-only | ... | ... | ... | ... | ... | ... |
| 2B | blank | ... | ... | ... | ... | ... | ... |
| 2B | shuffled | ... | ... | ... | ... | ... | ... |
| 7B | normal | ... | ... | ... | — | — | — |
| 7B | text-only | ... | ... | ... | ... | ... | ... |
| 7B | blank | ... | ... | ... | ... | ... | ... |
| 7B | shuffled | ... | ... | ... | ... | ... | ... |

Counterfactual results should be a separate paired table rather than forced into the same format.

---

## 18. Main figures concept

Potential publication figures:

### Figure 1 — Benchmark gain vs grounding gain

For each model size, show normal LoRA gain beside `Delta_G_text`, `Delta_G_blank`, and `Delta_G_shuffle`.

### Figure 2 — Accuracy by visual condition

Base and LoRA across normal/text/blank/shuffled.

### Figure 3 — Relation-family grounding change

Per-family `Delta_G` with confidence intervals.

### Figure 4 — Paired counterfactual correctness

Base vs LoRA on relation inversion, object reversal, and horizontal reflection.

### Figure 5 — OOD transfer

Only if the controlled OOD audit is completed cleanly.

---

## 19. Interpretation framework

Do not claim internal mechanisms from behavior alone.

Use cautious language such as:

### Evidence consistent with stronger visual grounding

- normal accuracy increases;
- shuffled/blank/text-only gains remain small;
- normal-vs-ablation gap increases;
- paired geometric counterfactual correctness improves;
- OOD geometric sensitivity improves.

### Evidence consistent with linguistic/task adaptation

- LoRA improves text-only strongly;
- blank/shuffled gains approach the normal gain;
- geometry-changing interventions remain weak;
- improvements concentrate in template-heavy relations.

### Evidence consistent with output/calibration learning

- invalid-output rate falls substantially;
- gains occur uniformly even where information content is unchanged;
- prediction distribution becomes better matched to dataset priors.

### Evidence consistent with benchmark specialization

- strong in-distribution improvement;
- weak controlled-OOD transfer;
- little increase in sensitivity to valid visual interventions.

These categories are behavioral interpretations, not claims about exact internal circuits.

---

## 20. What would make the paper interesting?

The study is interesting under more than one outcome.

### Outcome 1 — Accuracy rises but grounding does not

This supports a cautionary result:

> Fine-tuning can improve spatial benchmark scores without proportionally improving visual-spatial grounding.

### Outcome 2 — Accuracy and grounding both rise

This supports a positive result:

> Spatial LoRA can teach genuinely more visually grounded spatial behavior, and the audit identifies where that improvement occurs.

### Outcome 3 — Mixed relation-dependent result

Potentially the most informative outcome:

> Spatial fine-tuning teaches different things for different relation families; aggregate accuracy hides heterogeneous changes in visual dependence.

### Outcome 4 — Model-size interaction

If 2B and 7B differ materially:

> Model scale changes whether spatial adaptation is absorbed as task-specific behavior or as visually grounded capability.

This should remain secondary unless the effect is large and robust.

---

## 21. What we must NOT claim

Do not claim:

- that benchmark accuracy directly equals grounding;
- that text-only success proves memorization;
- that shuffled-image failure alone proves geometric reasoning;
- that behavior identifies the exact internal mechanism;
- that every relation has a valid binary complement;
- that horizontal reflection flips every spatial label;
- that this is the first grounding-ablation study without a final literature re-check;
- that one training seed establishes a robust fine-tuning effect;
- that SITE from the previous project directly answers this new grounding question.

Before submission, perform a fresh targeted literature review because this research area is moving rapidly.

---

## 22. Novelty target

The intended contribution is **not** merely:

- another VSR benchmark result;
- another spatial fine-tuning method;
- another blank-image ablation;
- another counterfactual benchmark;
- another orientation study.

The intended contribution is the **paired behavioral decomposition of the capability change caused by explicit spatial-task fine-tuning**:

> Given the same VLM before and after spatial LoRA, how much of the benchmark gain corresponds to increased dependence on correct visual evidence and transferable geometric sensitivity?

The contribution should be framed around the delta caused by adaptation:

```text
benchmark change:  Delta_A
visual-grounding change: Delta_G
counterfactual sensitivity change: Delta_C
OOD transfer change: Delta_T
```

The scientific question is whether these deltas move together.

---

## 23. Reproducibility and anti-cherry-picking policy

Before full runs:

- freeze the evaluation conditions;
- freeze transformation maps;
- freeze excluded relations/examples and reasons;
- freeze prompt/parser/generation parameters;
- freeze seeds;
- save exact eligible IDs;
- commit the protocol.

After seeing full primary results:

- do not redefine conditions to improve the story;
- new analyses must be labeled exploratory;
- bug fixes must document old/new outputs and affected examples;
- no silent reruns replacing unfavorable results.

A small protocol Markdown/JSON should be committed before the first full Tier-A 7B run.

---

## 24. Suggested branch file structure

```text
research/
└── SPATIAL_GROUNDING_LORA_STUDY.md

configs/
├── grounding_audit_2b.yaml
├── grounding_audit_7b.yaml
└── grounding_protocol.yaml

src/
├── models/
│   ├── base.py
│   ├── smolvlm.py
│   └── qwen2vl.py
└── evaluation/
    ├── interventions.py
    ├── grounding_metrics.py
    ├── pairing.py
    └── statistics.py

scripts/
├── run_grounding_audit.py
├── validate_interventions.py
├── summarize_grounding_results.py
└── make_grounding_figures.py

results/
└── grounding/
    ├── protocol/
    ├── predictions/
    ├── metrics/
    ├── tables/
    └── figures/

tests/
├── test_interventions.py
├── test_pairing.py
├── test_parser.py
└── test_grounding_metrics.py
```

This is a target structure; adapt the existing repository incrementally rather than forcing a wholesale rewrite.

---

## 25. Compute strategy

Current RTX A6000 48 GB is sufficient for the core study.

Use it for:

- 2B/7B inference;
- existing LoRA checkpoint evaluation;
- eventual 3-seed LoRA replication;
- counterfactual audits.

Do not move to a larger GPU merely for convenience.

A larger GPU becomes scientifically justified only if the study later adds a larger model as a distinct scaling experiment.

Primary priority is paired methodology and reproducibility, not model count.

---

## 26. Immediate next actions

1. Create/freeze a Tier-A protocol file.
2. Inspect/refactor the 7B evaluator into a reusable wrapper only as much as needed.
3. Implement text-only, blank-image, and deterministic shuffled-image conditions.
4. Add unit tests for transformations and pairing.
5. Run 10-example 7B base/LoRA smoke tests.
6. Run ~200-example paired pilot.
7. Freeze any bug fixes before full evaluation.
8. Run full 7B base vs General-LoRA Tier-A audit.
9. Compute `Delta_A`, `G_text`, `G_blank`, `G_shuffle`, and `Delta_G` with paired CIs.
10. Decide whether to proceed to Tier-B counterfactuals based on scientific informativeness, not whether the result matches the preferred hypothesis.
11. Implement and validate relation inversion, subject/object reversal, and horizontal reflection.
12. Run full 7B Tier-B audit.
13. Replicate the frozen audit on 2B.
14. Only then perform multi-seed LoRA replication.
15. Add controlled OOD evaluation if it directly sharpens the grounding claim.
16. Perform a fresh literature/novelty review before paper drafting.

---

## 27. First milestone definition

The first milestone is complete when we have, for the **7B base and 7B General LoRA on the exact same VSR test examples**:

- normal predictions;
- text-only predictions;
- blank-image predictions;
- shuffled-image predictions;
- deterministic pairing metadata;
- standard accuracy and invalid rate;
- visual-ablation gaps;
- LoRA gains by condition;
- grounding-gap changes;
- paired confidence intervals/tests;
- per-family breakdown;
- a short frozen result report.

No new fine-tuning is required to reach this milestone.

---

## 28. Final study success criterion

The project succeeds scientifically if it can answer, with paired and reproducible evidence:

> **Did the spatial capability improvement produced by LoRA correspond to a stronger causal dependence on correct visual-spatial evidence, and if so, for which model sizes and relation families?**

A null answer is still a valid result if the interventions are correct, the comparisons are paired, and the analysis is rigorous.

---

## 29. Locked working title candidates

Primary working title:

> **What Does Spatial Fine-Tuning Actually Teach Vision-Language Models? Disentangling Benchmark Gains from Visual-Spatial Grounding**

Alternatives:

- **Better at the Benchmark, Better at Seeing? Auditing Visual Grounding After Spatial Fine-Tuning**
- **Do Spatial LoRA Gains Reflect Visual Grounding? A Paired Behavioral Audit of Vision-Language Models**
- **From Spatial Benchmark Gains to Visual Grounding: What Changes After LoRA?**

Do not lock the final title until results are known.

---

## 30. Current project state at branch creation

At the moment this branch is created:

- the prior orientation research is treated as frozen/standalone;
- both 2B and 7B standard base results exist;
- both 2B and 7B General-LoRA checkpoints/results exist;
- the expensive training prerequisite for the first experiment is already complete;
- Tier-A grounding conditions have not yet been executed as a systematic paired base-vs-LoRA audit;
- Tier-B transformations require careful implementation/validation;
- multi-seed replication is deferred until the primary effect is established;
- the next scientific bottleneck is **evaluation design**, not model training.

This document is the working source of truth for the new research branch unless a later committed protocol explicitly supersedes a section.
