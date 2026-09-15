# VISAPP 2027 — Authoritative Revision and Submission Plan

Decision date: 2026-09-15
Decision owner: ChatGPT research audit for Paper 1 (`Beyond Spatial Accuracy...`)
Execution rule: the implementing agent should execute this plan and report deviations; it should not invent a different scientific story without new evidence.

## 1. Final venue decision

Target **VISAPP 2027 as a Regular Paper**, not the Abstracts Track.

Official current deadlines:
- Regular Paper, first stage: **September 29, 2026 (AOE, extended)**
- Position Paper / Regular Paper, second stage: **October 22, 2026 (AOE)**
- Abstracts Track: **December 3, 2026 (AOE)**

The Abstracts Track is a different publication route. Accepted abstracts are presented and appear in the conference program/book of abstracts, but are **not published in the proceedings and are not indexed**. A complementary PDF uploaded to an abstract submission does not convert it into a Regular Paper.

Submission settings:
- Type: **Regular Paper**
- Main area: **Foundations and Representation Learning**
- Primary topic: **Deep Learning for Visual Understanding**
- Secondary topics: **Machine Learning Technologies for Vision**; **Categorization and Scene Understanding**
- Add **Transfer Learning** only if the SITE transfer result remains a meaningful part of the final paper.

The current SCITEPRESS rules require a double-blind PDF with 10,000–50,000 characters excluding whitespace. Accepted Regular Papers may be classified as Full or Short Papers and are published in the proceedings.

## 2. Scientific decision

Do **not** submit the rejected TMLR paper with only a new abstract.

Do **not** submit the current retrospective VISAPP draft unchanged unless the September 29 experiment gate below fails and the paper is deliberately repositioned for the October 22 second stage.

The strongest practical VISAPP paper that can be completed without turning this into a new flagship project is:

> **What Do Orientation Errors Measure? Validating Spatial Diagnostics for Vision-Language Models**

Central question:

> When a VLM makes an object-orientation error, which conclusions remain valid after we independently verify the proposition labels and the semantic transformations used by the diagnostics?

This changes the paper from an intervention inventory into a focused evaluation-validity study with one new piece of evidence that directly repairs the largest weakness in the rejected version.

## 3. Why the TMLR version was vulnerable

The TMLR rejection email itself gives no technical reason, so the following are audit findings, not claims about the editor's reasoning.

### 3.1 Invalid representation target

The stored probe predicts the `relation` word from the VSR caption, including false captions. For a false statement such as “A is facing B,” the word `facing` is not a ground-truth visual relation. Therefore the old probe cannot support a claim that orientation information is absent or inaccessible from the representation.

Action: remove the old probe from the mechanistic argument. Preserve it only as a deprecated analysis with the target mismatch documented.

### 3.2 Invalid complement assumption

The old consistency analysis treats `facing` and `facing away` as exact Boolean complements. That is not generally true: a subject can face sideways relative to the reference, making both propositions false. Parallel/perpendicular can likewise have an oblique neither-state.

Action: do not report the previous 66.0%→77.7% as “logical coherence” until the transformed propositions are independently labeled or the transformation law is valid by construction.

### 3.3 Two-stage scorer mismatch

The legacy two-stage implementation compares its prediction to the control model's `correct` flag rather than to the control model's predicted verdict. That quantity is not model agreement.

Action: remove the old two-stage aggregate result.

### 3.4 Small and uncertain orientation effect

For the archived Qwen2-VL-7B base vs General-LoRA comparison:
- overall VSR: 1776/2195 → 1859/2195 (+3.78 pp)
- orientation: 87/137 → 90/137 (+2.19 pp)
- image-cluster 95% interval for the orientation change is approximately -8.8 to +13.1 pp

This does not establish a ceiling, saturation, or failure of adaptation. It is a small, imprecisely estimated change for one checkpoint pair.

Action: use effect sizes and clustered intervals; do not use “ceiling,” “irreducible bottleneck,” or “scaling fails.”

### 3.5 Stored annotation masks are not enough

The existing clean/ambiguous files change the evaluated population and their collection provenance needs explicit verification. They do not independently provide corrected proposition truth.

Action: add a new blind proposition-level adjudication for the existing orientation items.

## 4. One required new experiment for the September 29 submission

This is the highest-value addition. Do this instead of more GPU training.

### 4.1 Dataset to annotate

Annotate **all 137 VSR orientation statements**, not only prior failures.

Also annotate every transformed facing/facing-away item used by the old paired-consistency analysis. The expected set is roughly 103 transformed facing-family statements; use the exact frozen IDs from the archived script/output rather than regenerating ad hoc.

### 4.2 Annotation protocol

Use **two independent human annotators**, blind to:
- model outputs,
- base-vs-LoRA condition,
- original correctness,
- previous audit labels.

Use an adjudicator for disagreements. The author can be the adjudicator if they did not produce both initial labels.

For each item record:
- stable example ID and image ID/hash
- subject identity
- reference-object identity
- predicate (`facing`, `facing away`, `parallel`, `perpendicular`)
- reference frame
- predicate applicability: applicable / not applicable / uncertain
- visual judgeability: decidable / indeterminate
- proposition truth: true / false / indeterminate
- for transformed items: transformation type and whether the assumed semantic law is valid
- annotator IDs/pseudonyms and adjudication status

Do not force a binary label when the object's intrinsic front is undefined, occluded, or visually ambiguous.

### 4.3 Primary new measurements

1. **Benchmark-label validity**
   - agreement between original VSR label and adjudicated label on decidable items
   - support and coverage, including indeterminate items

2. **Transformation validity**
   - among the old facing/facing-away transformed pairs, fraction for which the assumed XOR/complement law is actually valid
   - separately count cases where both propositions are false, indeterminate, or otherwise not complements

3. **Matched model accuracy under adjudicated labels**
   - Base and General-LoRA accuracy on the same adjudicated decidable subset
   - paired transitions and image-cluster confidence intervals

4. **Joint correctness instead of raw opposite-answer frequency**
   - for independently labeled proposition pairs, report whether both model answers are correct
   - report complement compliance only on pairs for which a complement law is semantically valid

5. **Annotation agreement**
   - report raw agreement and an appropriate chance-corrected statistic for the human ratings
   - keep truth agreement and judgeability agreement separate

### 4.4 Statistical rules

- Use stable IDs, never row order.
- Cluster uncertainty by image when multiple statements share an image.
- Report numerator/denominator and coverage for every headline percentage.
- Do not treat indeterminate labels as False.
- Keep seed uncertainty separate from example uncertainty.
- Do not call a nonsignificant result equivalence unless a justified equivalence margin was preregistered.
- Do not compare “significant overall” vs “nonsignificant orientation” as evidence that the effects differ; use the direct subgroup contrast if needed.

## 5. Experiments not required for this VISAPP paper

Do not spend the next two weeks on:
- new LoRA variants
- larger model sweeps
- a new 400-image benchmark
- new representation probes
- vision-tower adaptation
- a new mechanistic architecture
- a broad “capability audit ladder” framework

Those directions add scope without fixing the construct-validity problem that currently dominates the paper.

Optional only if trivial after provenance reconciliation:
- report verified existing multi-seed results as secondary context
- retain SITE as one small transfer subsection

## 6. Final paper story after the annotation experiment

The paper should have exactly one story:

1. VSR orientation performance looked unusually resistant in an archived evaluation.
2. Several diagnostics used to explain that pattern were measuring the wrong construct or using unverified semantic assumptions.
3. We independently re-label the orientation propositions and transformed pairs.
4. We quantify how much the scientific conclusion changes when the evaluation is made semantically valid.
5. We provide a small set of reusable rules for orientation evaluation: proposition truth, applicability/judgeability, valid transformation laws, joint correctness, clustered uncertainty.

Do not claim:
- first discovery that VLMs struggle with orientation
- a universal orientation bottleneck
- a representation bottleneck
- a scaling law
- a new general-purpose benchmark unless a new benchmark is actually built
- a new consistency method

## 7. Proposed manuscript structure

### Title
Preferred after successful annotation:

**What Do Orientation Errors Measure? Validating Spatial Diagnostics for Vision-Language Models**

Fallback if only retrospective audit is completed:

**What Do Orientation Errors Measure? A Retrospective Audit of Vision-Language Evaluation**

### Sections
1. Introduction
2. Related Work
3. Why Orientation Evaluation Is Semantically Fragile
4. Audited VSR Orientation Set
5. Reanalysis of Base vs General LoRA
6. Validating Paired Orientation Transformations
7. Secondary Cross-Dataset Transfer (SITE)
8. Discussion and Evaluation Recommendations
9. Limitations
10. Conclusion

Move implementation-deprecation details (old probe/two-stage bugs) to a compact audit subsection or appendix. They support the motivation but should not dominate the paper.

## 8. Abstract logic

Do not finalize the abstract before the annotation numbers exist.

The final abstract should contain five elements in this order:
1. known problem: orientation errors are often over-interpreted
2. audit finding: old auxiliary targets/transformations do not always identify the intended construct
3. new evidence: independently adjudicated orientation propositions and transformed pairs
4. main quantitative result: how labels/transformation validity alter model accuracy/joint correctness
5. contribution: a validated case study and concrete evaluation requirements

Template to fill only with real results:

> Object-relative orientation remains difficult for vision-language models, but an orientation error does not by itself identify a failure of visual representation or relational reasoning. We revisit a VSR evaluation of Qwen2-VL-7B and audit the measurements used to interpret its errors. We independently adjudicate [N] orientation propositions and [M] transformed orientation pairs, recording object identity, applicability, visual judgeability, proposition truth, and transformation validity. We find that [RESULT ON ORIGINAL LABEL VALIDITY] and that [RESULT ON COMPLEMENT/ANTONYM VALIDITY]. Re-scoring the archived base and LoRA predictions on the adjudicated decidable subset changes orientation accuracy from [A/B] to [C/D], while image-cluster uncertainty remains [INTERVAL/RESULT]. Paired analysis further shows [JOINT-CORRECTNESS RESULT], demonstrating that opposite-answer frequency and logical correctness are not interchangeable. These results do not establish a universal orientation bottleneck; instead, they show that orientation diagnostics require validated propositions, explicit semantic transformation laws, coverage reporting, and uncertainty estimates matched to shared visual inputs. We release the adjudication protocol, labels, and analysis code.

Never fill placeholders by extrapolation.

## 9. Submission decision gate

### Submit September 29 as Regular Paper if all are true

- two independent annotation passes are complete
- disagreements adjudicated
- labels and transformed-pair validity are frozen
- retained metrics regenerated from exact raw predictions
- checkpoint/input provenance is documented as far as possible
- the final PDF is anonymous and within the VISAPP character limit
- overlap with Paper 2 / any other active submission is explicitly checked
- AI-use disclosure follows VISAPP's current policy without breaking review anonymity

### Otherwise

Do **not** use the Abstracts Track as a substitute for the paper.

Use the **October 22 Regular/Position second stage** to finish the repair. If the work remains mostly methodological/prospective by then, Position Paper is acceptable; if the annotation study is completed, keep Regular Paper.

## 10. Submission-form guidance

The current page titled **“Abstract for VISAPP 2027”** with a 100–2000 character structured abstract and optional complementary PDF is the **Abstracts Track**.

For the proceedings paper, use VISAPP's **Submit Paper** route. In that route:
- upload the anonymous complete manuscript PDF
- enter the paper's ordinary abstract as metadata
- choose Regular Paper
- use the author fields for the real author list while keeping the review PDF anonymous

Do not upload the manuscript as “complementary material” to an Abstracts Track entry expecting it to become a proceedings paper.

## 11. Current recommended topics

Main area: **Foundations and Representation Learning**

Select:
- **Deep Learning for Visual Understanding**
- **Machine Learning Technologies for Vision**
- **Categorization and Scene Understanding**

Add **Transfer Learning** only if SITE remains in the main paper rather than the appendix.

## 12. Reproducibility and ethics checks

Before upload:
- rebuild every table from machine-readable outputs
- document model checkpoint revision, adapter, dataset split, prompt/parser, image preprocessing, seed, and hashes where available
- if provenance is missing, state that rather than reconstructing it from memory
- remove author-identifying repository URLs/paths from anonymous supplement
- do not silently overlap the same contribution with another active proceedings submission
- verify every reference from a primary source; remove placeholder authors
- VISAPP currently requires disclosure of AI-generated text/code/content and names the AI tool; follow the portal's review-version guidance because the same guidelines also require anonymous review manuscripts to omit acknowledgements

## 13. Timeline

- Sep 15–17: freeze exact 137-item and transformed-pair annotation sheets; verify image access and instructions
- Sep 17–21: two blind annotation passes
- Sep 21–22: adjudication and label freeze
- Sep 22–24: recompute accuracy, joint correctness, validity rates, agreement, intervals
- Sep 24–26: rewrite Results/Methods/Abstract around real findings
- Sep 26–28: overlap, references, provenance, anonymity, supplement, character-count checks
- Sep 29 AOE: submit Regular Paper

If annotation slips materially, move to the October 22 second stage rather than submitting an underpowered retrospective draft.
