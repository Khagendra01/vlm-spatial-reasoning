# EquiOrient — Decision Log

This file records why the project exists in its current form. Future agents should append decisions rather than rewrite history.

---

## 2026-08-10 — Create Paper 3 as a separate branch

**Decision:** create `research/equiorient` separately from the WACV diagnostic paper and the Paper-2 grounding-audit branch.

**Reason:** Paper 3 is a method/solution project. Combining it with Paper 2 would mix a behavioral learning audit with a new representation-learning intervention and would risk scientific drift and duplicated experiments.

---

## 2026-08-10 — Keep Paper 2 and EquiOrient distinct

**Paper 2 question:** when spatial fine-tuning changes performance, do accuracy (ΔA), consistency (ΔC), and dependence on correct visual evidence (ΔG) move together?

**Paper 3 question:** can we train the spatial representation itself to obey known transformation structure?

**Reason:** Paper 2 should diagnose what ordinary adaptation changes. Paper 3 should introduce a new structural learning principle informed by that diagnosis.

---

## 2026-08-10 — Reject naive “view consistency” framing

**Decision:** EquiOrient will not be framed as simply training on mirrored/warped views or rewarding consistent answers.

**Reason:** initial literature search found direct close work:

- SVQA-R1: view-consistent reward optimization with horizontal flips and 2D viewpoint transforms;
- SAGE: geometric/linguistic duality consistency;
- STAR-R1: multi-view spatial transformation reasoning;
- related perspective-aware and camera-guided methods.

A generic consistency claim would be weak or duplicative.

---

## 2026-08-10 — Make latent equivariance the provisional novelty target

**Decision:** center the method on a pair-conditioned latent `z(x,a,b)` and a relation-specific transformation action `rho_r(T)`.

**Reason:** this distinguishes predictable **representation change** from merely correct final-answer change.

This is still provisional until the full novelty gate is completed.

---

## 2026-08-10 — Distinguish equivariance from invariance

**Decision:** do not train one universal invariance objective.

**Reason:** some transforms preserve a relation, while others predictably permute or change the relation. A useful spatial representation must retain that distinction.

Examples:

- reflection can swap left/right;
- global rigid transforms can preserve parallel/perpendicular;
- object-local rotation can alter facing/facing-away while leaving pair position unchanged.

---

## 2026-08-10 — Controlled synthetic pairs first

**Decision:** use controlled paired scenes for the first method pilot.

**Reason:** causal transform supervision is only defensible when the expected relation/action is known exactly. Natural-image relabeling introduces ambiguity that could swamp the method signal.

Synthetic data are not the final proof; external transfer is required later if the method is to claim general spatial benefit.

---

## 2026-08-10 — Matched augmentation baseline is mandatory

**Decision:** EquiOrient must be compared with ordinary training on the exact same transformed data.

**Reason:** otherwise gains could come from simply seeing more transformed examples, not from the equivariance objective.

---

## 2026-08-10 — Output-consistency baseline is mandatory

**Decision:** compare against a final-answer consistency objective using the same paired data.

**Reason:** this directly tests whether representation-level structure adds value beyond the dominant 2026 consistency-training paradigm.

---

## 2026-08-10 — Held-out transformations are primary evidence

**Decision:** seen-transform accuracy alone cannot establish the method contribution.

**Reason:** a structural learning objective is valuable only if the learned rule generalizes beyond memorized transform-answer mappings.

At least one of held-out transform magnitudes, compositions, or types must be confirmatory.

---

## 2026-08-10 — Do not reuse Paper 1/Paper 2 experiments as Paper 3 contribution

**Decision:** prior results may motivate baselines, but Paper 3 must contain new training and new primary evidence.

**Reason:** avoid duplicate publication/salami slicing and preserve a clear thesis progression:

```text
Paper 1: diagnose the failure
Paper 2: audit what fine-tuning changes
Paper 3: introduce a structural solution
```

---

## 2026-08-13 — Close Gate 0 with `MUTATE`

**Results already seen?** No EquiOrient training results. Decision is literature- and design-driven.

**Decision:** close `EQUIORIENT_NOVELTY_GATE.md` with verdict `MUTATE`.

**Reason:** a deeper search found substantial overlap around the original broad formulation:

- VLM latent spatial shaping and causal intervention already exist;
- representation-level geometric supervision inside VLMs already exists;
- continuous / object-centric spatial latent tokens already exist;
- transformation/view-consistency spatial VLM training already exists;
- latent equivariance, group actions, and homomorphism/composition objectives are established representation-learning ideas.

No searched paper, however, was found to combine the full revised target: an answer-path object-pair state, predeclared heterogeneous geometry-derived actions that do not receive the true relation label, matched augmentation/output-consistency/invariance controls, a wrong-geometry control, and held-out transformation composition as the primary behavioral test.

**Mutation:** replace the provisional `rho_r(T)` framing with a typed spatial state and geometry-derived `rho(T)` action. The answer label / ground-truth relation must not be an input to the transformation operator. Make unseen composition the primary pilot test.

**Pilot redesign:**

- first relation behaviors: left/right, above/below, controlled parallel/perpendicular invariance;
- first transform generators: horizontal reflection `H`, vertical reflection `V`;
- train on `H` and `V` individually;
- hold out `V ∘ H` composition;
- matched conditions: ordinary SFT/LoRA, augmentation-only, output-consistency, latent-invariance, EquiOrient, wrong-geometry control;
- require answer-path participation of `z` and causal ablation/corruption evidence;
- do not include facing/facing-away until the simpler algebra passes.

**Affected frozen artifacts:**

- `research/EQUIORIENT_NOVELTY_GATE.md` — updated and gate closed;
- `research/EQUIORIENT_PROTOCOL_FREEZE.md` — **must be amended before GPU pilot**;
- `configs/equiorient_protocol.yaml` — **must be amended before GPU pilot**;
- `research/EQUIORIENT_STUDY.md` — may be synchronized after protocol authority is amended.

**Confirmatory status:** no GPU training is confirmatory until the protocol/config amendments are committed and the CPU algebra, synthetic-data, and representation-feasibility gates pass.

---

## Future decisions

Append entries with:

```text
date
results already seen? yes/no
decision
alternatives considered
reason
affected frozen artifacts
whether change is confirmatory or exploratory
```
