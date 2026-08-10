# Research Execution Guide — Spatial Grounding After LoRA

This file is for any future researcher/agent continuing work on `research/spatial-grounding-audit`.

## Read order before changing anything

1. `research/GROUNDING_PROTOCOL_FREEZE.md` — operational authority.
2. `configs/grounding_protocol.yaml` — machine-readable protocol constants/status.
3. `research/SPATIAL_GROUNDING_LORA_STUDY.md` — scientific rationale and full design.
4. `research/DECISION_LOG.md` — why the current design differs from earlier versions.
5. prior frozen orientation results only as background/motivation, not as permission to change this study.

If two documents disagree, follow the protocol freeze, then the machine-readable config, then the broader study plan.

## Central question

> When spatial fine-tuning improves accuracy or relational consistency, does it also increase causal sensitivity to the visual evidence that determines the spatial relation?

Do not silently revert to a two-way “accuracy vs grounding” study or an orientation-only study.

## Core decomposition

- `ΔA`: benchmark accuracy change.
- `ΔC`: semantic/logical consistency change.
- `ΔG`: visual grounding / evidence-sensitivity change.
- `ΔT`: optional controlled transfer change.

The goal is to test whether these co-move or dissociate.

## Core model roles

- P1 primary: 7B zero-shot → 7B General LoRA.
- D1 diagnostic: 7B General → 7B HardNeg.
- R1 replication: 2B zero-shot → 2B General.

Do not promote Targeted/Projector/Vision-Projector conditions into confirmatory status after seeing results unless a new pre-result protocol version is created before the affected full evaluation.

## First work package

Implement and validate one reusable evaluation path for:

- normal;
- deterministic shuffled image;
- blank image;
- text-only diagnostic.

Run first on:

- 7B zero-shot;
- 7B General;
- 7B HardNeg.

No new training is required.

## Evidence hierarchy

Strongest to weakest for grounding claims:

1. correct vs deterministic wrong/shuffled image under same multimodal interface;
2. visual counterfactual response with text fixed and known truth effect;
3. original + visual-counterfactual both-correct;
4. blank-image gap;
5. text-only behavior.

Do not make text-only the headline grounding result.

## Semantic vs visual interventions

Never merge these analytically.

### Semantic (`S`)

- pixels fixed;
- language changes;
- measures relational/logical consistency (`C`).

Examples: strict complement/inverse, validated subject/object reversal.

### Visual (`V`)

- text fixed;
- pixels/world change;
- measures visual causal sensitivity (`G`).

Examples: validated horizontal reflection, controlled geometry-changing scene pairs.

### Evidence ablation (`E`)

- text fixed;
- correct visual evidence removed/replaced.

Examples: shuffle, blank, text-only diagnostic.

## Required implementation constraints

- same example IDs across compared model conditions;
- same shuffle mapping across all model conditions;
- deterministic fixed mapping;
- no self-pairs;
- same prompt/parser/generation parameters within each backbone transition;
- every transformed row stores parent ID and transform metadata;
- every run stores protocol version/hash and git commit;
- no global label flip rules across heterogeneous relations;
- no generic subject/object string swap without parser audit.

## Required tests before any full run

- deterministic derangement test;
- no-self-pair test;
- parser unit tests;
- pairing unit tests;
- metric toy tests;
- blank-image reproducibility test;
- exact ID equality across model conditions;
- manual stratified validation for semantic and visual transforms.

A run without these checks is an engineering run, not a confirmatory result.

## Pilot policy

Allowed:

- 10-example smoke;
- ~200-example engineering pilot.

Pilot purpose is only to detect bugs, OOMs, parser failures, and runtime issues.

Forbidden:

- choosing the best-looking shuffle seed;
- redefining a subset because results are weak;
- changing primary metrics based on pilot direction;
- adding adapters because the preferred effect is absent.

## Required artifacts before first full Tier-A run

Create and commit:

```text
results/grounding/protocol/vsr_test_ids.json
results/grounding/protocol/shuffle_mapping.json
results/grounding/protocol/blank_image_spec.json
results/grounding/protocol/run_config_snapshot.json
```

Also ensure the code/config commit hash is recorded before launching the full run.

## Required outputs for first milestone

For each of 7B zero, General, HardNeg:

- normal predictions;
- shuffled predictions;
- blank predictions;
- text-only predictions;
- run metadata;
- artifact hashes where practical.

Then produce:

- canonical accuracy table;
- invalid-output table;
- `G_shuffle`, `G_blank`, `G_text`;
- `ΔG_shuffle` for P1 and D1;
- per-family breakdown;
- paired confidence intervals/tests;
- a frozen Tier-A result report.

## Tier-B/C prerequisites

Before semantic transforms:

- relation transform validity table;
- eligible ID list;
- parser audit for subject/object reversal;
- manual spot check.

Before visual transforms:

- expected truth/stability behavior table;
- eligible ID list;
- manual spot check;
- exact image transformation version/hash.

## Interpretation rules

Allowed conclusions are behavioral and calibrated.

Examples:

- “greater dependence on the correct image”;
- “semantic consistency improved more than visual causal sensitivity”;
- “benchmark gain was not matched by a comparable grounding-gap increase”;
- “grounding changes were relation-dependent.”

Avoid:

- “the model learned geometry internally” from behavior alone;
- “text-only proves memorization”;
- “shuffle failure proves visual reasoning”;
- “consistency proves grounding.”

## When to retrain

Do not retrain before the first decomposition result.

Retraining is justified when:

- the final primary protocol is stable;
- an effect or null is scientifically worth making seed-robust;
- multi-seed evidence would materially strengthen the main claim.

Primary seed target if needed: 3 General-LoRA seeds on 7B. Replicate 2B if compute permits. HardNeg seeds only if D1 becomes central.

## When to add a controlled counterfactual scene set

Only if VSR-native interventions leave ambiguity about visual causal sensitivity.

The controlled set should be small, exact, balanced, and paired. It should not become a separate benchmark-construction project.

Include nuisance/irrelevant-edit controls so mere sensitivity to pixel changes cannot masquerade as grounding.

## Change-control procedure

Any material scientific change requires an entry in `research/DECISION_LOG.md`.

Record:

- old rule;
- new rule;
- reason;
- whether results were already seen;
- confirmatory/exploratory status;
- commit/files affected.

If results were already seen, default status is exploratory unless it is a verified bug fix.

## Definition of done

The study is ready for paper synthesis when we have reproducible paired estimates of:

```text
ΔA
ΔC
ΔG
```

for P1, D1, and R1 (at minimum P1 + R1 for the core adaptation claim), with visual counterfactual evidence strong enough to distinguish correct-scene dependence from generic perturbation sensitivity.

A null or mixed result still counts as success if the protocol is valid and the interpretation remains faithful to the evidence.
