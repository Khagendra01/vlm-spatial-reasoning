# Grounding Audit Protocol Freeze

**Branch:** `research/spatial-grounding-audit`  
**Protocol version:** `v0.1`  
**Status:** PRE-RESULT FREEZE — governs confirmatory runs  
**Parent research plan:** `research/SPATIAL_GROUNDING_LORA_STUDY.md`

This file is the operational source of truth for confirmatory experiments. It exists to prevent post-result drift.

## 1. Confirmatory scientific target

We measure whether spatial adaptation changes three quantities together or separately:

- `ΔA`: ordinary VSR accuracy change;
- `ΔC`: semantic/logical consistency change;
- `ΔG`: causal dependence on correct visual evidence / visual counterfactual sensitivity change.

Primary question:

> When spatial fine-tuning improves accuracy or relational consistency, does it also improve causal sensitivity to the visual evidence that determines the spatial relation?

## 2. Confirmatory model comparisons

### P1 — primary

`Qwen/Qwen2-VL-7B-Instruct` zero-shot → existing 7B General LoRA.

### D1 — key diagnostic

existing 7B General LoRA → existing 7B HardNeg LoRA.

Interpretation constraint: prior pooled strict-family General-vs-HardNeg consistency comparison was not significant (`p=0.29`), so D1 is a diagnostic contrast, not proof of a globally significant consistency-training effect.

### R1 — replication

`HuggingFaceTB/SmolVLM2-2.2B-Instruct` zero-shot → existing 2B General LoRA.

Targeted/projector/vision-projector adapters are exploratory unless explicitly promoted by a pre-result protocol revision.

## 3. Evaluation split

- VSR held-out test only.
- Exact example IDs must be frozen before the first full confirmatory run.
- Base and tuned conditions must receive identical IDs and intervention mappings.
- No training or validation examples may enter the confirmatory test audit.

## 4. Tier-A evidence conditions

Confirmatory order and status:

1. `normal` — reference.
2. `shuffle` — PRIMARY evidence-ablation condition.
3. `blank` — SECONDARY.
4. `text_only` — EXPLORATORY/diagnostic.

An optional `matched_shuffle` may be added only if its matching algorithm, fallback behavior, exact mappings, and eligibility are committed before the first full Tier-A result is inspected.

### Shuffled-image requirements

- deterministic derangement;
- fixed seed from machine-readable config;
- no self-pairs;
- replacement drawn from held-out test split;
- same mapping for all compared model conditions;
- mappings saved to disk and hashed;
- no seed/mapping regeneration after results.

## 5. Semantic intervention axis (`S`)

These change language while pixels remain fixed and measure `C`.

Confirmatory candidates:

- strict relation complement/inversion;
- validated subject/object reversal.

Before any full semantic run, commit a transform-validity table containing relation, transform, strict/soft/unsafe status, expected truth behavior, eligible IDs, and exclusions.

Never use `parallel ↔ perpendicular` as a universal strict complement.

## 6. Visual intervention axis (`V`)

These keep language fixed while pixels/world change and measure `G`.

### V1 — horizontal reflection

Confirmatory only for relation families/examples with logically guaranteed expected behavior. Left/right-style relations are the primary use. Do not globally flip labels.

### V2 — controlled visual counterfactual scenes

Optional high-value extension after the VSR pilot. If created, the dataset design must be frozen before evaluation and should include relation-changing pairs plus irrelevant/nuisance controls.

## 7. Evidence hierarchy

For claims of stronger visual grounding, weight evidence in this order:

1. correct image vs deterministic wrong/shuffled image under same multimodal interface;
2. visual counterfactual expected-response behavior with text fixed;
3. original+visual-counterfactual both-correct rate;
4. blank-image gap;
5. text-only behavior.

Do not use text-only as the strongest grounding evidence.

## 8. Primary metrics

### Accuracy

`A(m,c)` = accuracy for model condition `m` in evaluation condition `c`.

`ΔA(u→v) = A(v,normal) - A(u,normal)`.

### Correct-scene dependence

`G_shuffle(m) = A(m,normal) - A(m,shuffle)`.

Secondary:

- `G_blank(m)`;
- `G_text(m)`.

Primary grounding-gap change:

`ΔG_shuffle(u→v) = G_shuffle(v) - G_shuffle(u)`.

### Semantic consistency

For strict semantic pairs, `C(m)` = proportion obeying the expected linked-answer law.

`ΔC(u→v) = C(v) - C(u)`.

Always report pair both-correct separately from consistency.

### Visual causal sensitivity

For visual transformations with expected label change:

- expected prediction flip rate;
- wrong-direction flip rate;
- transformed accuracy;
- both-correct rate.

For expected-invariant controls:

- expected stability rate;
- both-correct rate.

### Invalid outputs

Always report malformed/unparseable output rates separately.

## 9. Primary statistical plan

- paired example-level comparisons;
- exact McNemar where binary correctness is paired;
- paired/bootstrap confidence intervals for accuracy differences;
- bootstrap confidence intervals for `ΔG` and other difference-in-differences;
- effect sizes alongside p-values.

Primary comparison order:

1. P1: 7B zero → General;
2. D1: 7B General → HardNeg;
3. R1: 2B zero → General.

Relation-level inferential tests are secondary unless separately predeclared. Correct for multiplicity if many are promoted to claims.

## 10. Run fairness

Within every compared transition:

- identical prompt;
- identical processor path;
- identical preprocessing;
- identical generation settings;
- greedy decoding;
- identical parser;
- identical examples/interventions.

Any necessary model-specific difference must be documented in run metadata and must not differ between base and adapter versions of the same backbone.

## 11. Required metadata

Each run must record at minimum:

- protocol version/hash;
- git commit;
- model ID/revision;
- adapter path/hash;
- dataset ID/revision/split;
- exact example IDs;
- intervention condition/version;
- transform mapping hash;
- seeds;
- prompt/parser hash;
- generation config;
- preprocessing config;
- environment snapshot;
- artifact/output hashes when practical.

## 12. Required engineering validation before full run

- unit test shuffled mapping is a derangement;
- deterministic mapping test;
- blank image reproducibility test;
- parser tests;
- pairing tests;
- metric toy-case tests;
- exact ID equality across compared conditions;
- manual inspection of semantic/visual transforms before full Tier-B/C runs.

## 13. Pilot rule

Engineering pilots may use 10 examples and then roughly 200 examples.

Pilots may reveal implementation bugs and runtime problems. They must **not** be used to choose the best-looking shuffle seed, transform subset, metric definition, or model condition.

## 14. Change-control rule

After a full confirmatory result is inspected, changes to model matrix, IDs, interventions, seeds, primary metrics, or primary tests are exploratory unless they fix a verified implementation bug.

All changes must be logged in `research/DECISION_LOG.md` with:

- date;
- old rule;
- new rule;
- reason;
- whether any results were already seen;
- confirmatory vs exploratory status.

## 15. Stopping / escalation rules

No new fine-tuning is required before completing Tier A for 7B zero/General/HardNeg.

Proceed to semantic/visual counterfactuals regardless of whether Tier A is positive, null, or mixed if implementation is valid, because the axes answer different questions.

Do not add more adapters solely because the primary result is unfavorable.

Multi-seed training is deferred until a final primary protocol and scientifically meaningful effect are identified.

A controlled visual-counterfactual scene set is justified only if it directly resolves ambiguity left by VSR-native interventions.

## 16. Interpretation guardrails

Allowed language:

- evidence consistent with stronger visual grounding;
- greater dependence on correct visual evidence;
- improved semantic coherence;
- benchmark/task-policy adaptation;
- relation-dependent dissociation.

Do not infer exact internal mechanisms from these behavioral results.

Do not claim:

- shuffled-image failure alone proves geometric reasoning;
- text-only success proves memorization;
- consistency alone proves grounding;
- visual sensitivity to any pixel perturbation proves grounding;
- a single seed establishes a robust training effect.

## 17. First confirmatory milestone

Full VSR test predictions for:

- 7B zero-shot;
- 7B General LoRA;
- 7B HardNeg LoRA;

under:

- normal;
- deterministic shuffle;
- blank;
- text-only diagnostic.

Output must include canonical paired metrics, per-family breakdown, CIs/tests, metadata, and a frozen result report.

## 18. Protocol amendment policy

This is `v0.1`. A future protocol version is allowed if new information or a real bug requires it, but it must not silently overwrite history. Amendments should create an explicit versioned record in the decision log and, if material, a new protocol file/version/hash.
