# EquiOrient — Transformation-Equivariant Spatial Representation Learning for VLMs

**Branch:** `research/equiorient`  
**Status:** PLANNED / NOT YET EXECUTED  
**Parent:** WACV submission-candidate state at `344c5ca7739d775274f13ae7aedf6d31f34675f2`  
**Paper role:** Method / solution paper following the diagnostic paper and the spatial-grounding audit paper  

---

## 1. Research program position

This branch is intentionally separate from:

1. **Paper 1 — diagnosis:** persistent orientation weakness, intervention ladder, representation probes, logical consistency, and cross-dataset transfer.
2. **Paper 2 — learning audit:** whether spatial fine-tuning changes accuracy (ΔA), logical consistency (ΔC), and dependence on correct visual evidence (ΔG) together or separately.

**Paper 3 asks a different question:**

> **Can a VLM be trained so that its internal spatial representation changes according to the known geometry of a scene transformation, instead of merely learning more question-answer pairs or output-consistency rules?**

This is a method paper. It must not collapse into another benchmark audit or another generic consistency-training study.

---

## 2. Working thesis

> **Reliable spatial reasoning requires representations that transform predictably when the visual world transforms. We hypothesize that explicitly enforcing relation-aware latent equivariance improves generalization to unseen spatial transformations and viewpoints beyond ordinary supervised fine-tuning or answer-consistency objectives.**

The key word is **equivariance**, not invariance.

If an input transformation changes the underlying spatial state, the learned representation should change in a predictable way. If the transformation preserves the relation, the relevant relational state should remain invariant.

---

## 3. Why the naive version is not novel enough

As of 2026-08-10, close work already covers several obvious variants:

- **SVQA-R1** uses horizontal flips and 2D viewpoint perturbations with view-consistent reward optimization.
- **SAGE** enforces geometric / linguistic duality consistency during GRPO training.
- **GASP** uses correspondence-based 2D view-invariance and depth-consistency supervision to inject geometric priors.
- **STAR-R1** targets multi-view spatial transformation reasoning with SFT + RL.
- **SpaceMind** uses camera-guided spatial fusion.
- **Perspective-Aware Reasoning via Mental Imagery Simulation** explicitly reasons under perspective changes.
- **SymPL** reformulates allocentric reasoning with projective layouts.

Therefore this paper must **not** claim novelty for:

- training on flipped views;
- enforcing answer consistency across views;
- generic camera conditioning;
- generic multi-view reasoning;
- generic geometric priors;
- generic spatial RL.

The novelty target is narrower and stronger:

> **Learn a relation-conditioned latent spatial state whose transformation under a known intervention is explicitly supervised by a relation-specific group/action map, then test whether this structural constraint transfers to unseen transformations, relations, and datasets.**

This novelty target is provisional until the dedicated novelty gate is completed.

---

## 4. Core conceptual distinction

### Output consistency

A standard consistency objective can encourage:

```text
answer(T(x), transformed_question) == expected_answer
```

A model may satisfy this by learning answer policies without learning a structured spatial representation.

### Latent equivariance

EquiOrient instead aims for:

```text
z(T(x), a, b) ≈ ρ_r(T) z(x, a, b)
```

where:

- `x` = image / scene,
- `a,b` = grounded object pair,
- `z` = learned spatial latent for that pair,
- `T` = known visual transformation or controlled scene intervention,
- `r` = relation family / spatial coordinate semantics,
- `ρ_r(T)` = the expected action of transformation `T` on the latent spatial state.

The method should not assume one universal transform law for every relation.

Examples:

- horizontal reflection swaps left/right state;
- vertical reflection swaps above/below state;
- object rotation can change facing/facing-away while leaving object positions unchanged;
- global scene reflection can preserve parallel/perpendicular;
- global camera/viewpoint changes may preserve intrinsic pair relations while changing egocentric coordinate relations.

---

## 5. Primary research questions

### RQ1 — Structural learning

Can an explicit latent-equivariance objective reduce transformation error in spatial representations compared with ordinary spatial SFT / LoRA?

### RQ2 — Generalization

Does latent equivariance improve accuracy and paired correctness on **unseen transformations or viewpoints**, rather than only trained transforms?

### RQ3 — Relation transfer

Does training transformation structure on one subset of relation families transfer to held-out spatial relations whose transformation laws share structure?

### RQ4 — Grounding

Do gains survive tests that require the correct visual evidence, rather than only semantic complement rules?

### RQ5 — Capability preservation

Can the method improve spatial reasoning without materially degrading unrelated VLM capabilities?

### RQ6 — Mechanism evidence

Do latent representations become more predictably transformable under controlled interventions after EquiOrient training?

This is evidence about the trained representation under tested readouts, not proof of a unique internal mechanism.

---

## 6. Main hypotheses

### H1

Ordinary spatial SFT / LoRA improves answer accuracy more than it improves latent transformation fidelity.

### H2

EquiOrient improves latent transformation fidelity beyond an accuracy-matched SFT baseline.

### H3

EquiOrient improves **both-correct paired performance** on held-out transformations more than answer-consistency training alone.

### H4

EquiOrient gains are largest on relations whose semantics require tracking orientation or reference-frame transformations.

### H5

A purely invariant objective will underperform a relation-aware equivariant objective when the correct spatial state should change under `T`.

---

## 7. Method skeleton

Start from a strong open VLM suitable for PEFT and hidden-state extraction. Final backbone is not frozen until the novelty/feasibility gate.

### 7.1 Object-pair spatial state

Given image `x` and subject/reference objects `(a,b)`, construct a pair-conditioned representation:

```text
h_a = subject visual feature
h_b = reference visual feature
h_global = global visual context
h_cam = optional camera/view transform metadata where available

z = f_pair(h_a, h_b, h_global [, h_cam])
```

Possible `f_pair` implementations to compare:

- lightweight MLP / projector head;
- cross-attention pair token;
- learned spatial token(s) inserted into the language backbone;
- low-rank adapter readout from post-merger visual tokens.

Do not begin with an unnecessarily large architecture.

### 7.2 Relation prediction objective

Standard task objective:

```text
L_task = answer / relation loss
```

### 7.3 Equivariance objective

For paired transformed examples `(x, T(x))`:

```text
L_equiv = d(z(T(x)), ρ_r(T) z(x))
```

Potential distances:

- cosine / L2 in normalized latent space;
- contrastive objective;
- class-conditional transformation prediction;
- structured permutation / rotation action on subspaces.

The exact form must be selected by pilot evidence, not aesthetics.

### 7.4 Optional transformation prediction auxiliary task

Predict `T` or the induced relation-state change from `(z(x), z(T(x)))`.

This is auxiliary only; it must not become the primary claim unless it materially explains performance.

### 7.5 Total objective

Provisional:

```text
L = L_task + λ_equiv L_equiv + λ_aux L_aux
```

No tuning sweep until a minimal protocol is frozen.

---

## 8. Transformation taxonomy

The paper must explicitly distinguish transformation classes.

### A. Semantic-preserving global transforms

Examples where the relation should remain the same:

- parallel/perpendicular under many global reflections/rotations;
- intrinsic facing relation under a global rigid scene transform, if all objects move together and semantics are preserved.

### B. Relation-permuting global transforms

Examples:

- horizontal reflection: left ↔ right;
- vertical reflection: above ↔ below;
- selected viewpoint-coordinate relations under controlled camera transforms.

### C. Object-local transforms

Examples:

- rotate only subject object: facing ↔ facing-away where ground truth is controlled;
- rotate only reference object when relation semantics require it.

These are especially important because they separate **intrinsic orientation** from whole-image symmetry.

### D. Viewpoint transforms

Known camera rotations/translations with scene geometry fixed.

These require careful definition of egocentric vs allocentric labels.

### E. Unsafe / ambiguous transforms

Natural-image transforms for which the expected label is not guaranteed must be excluded from confirmatory metrics.

---

## 9. Data strategy

Use three levels, in this order.

### Level 1 — controlled synthetic paired scenes

Purpose: exact transformation ground truth and cheap falsification.

Requirements:

- balanced relation labels;
- balanced object identities/colors/shapes;
- explicit object poses;
- known camera parameters;
- exact transformation metadata;
- paired original/transformed scene IDs;
- train/val/test splits separated by scene seed and, where possible, object-template composition.

Relations to prioritize:

- left/right;
- above/below;
- front/behind;
- facing/facing-away;
- parallel/perpendicular;
- containment only if transformations have unambiguous expected semantics.

### Level 2 — controlled real / rendered benchmark pairs

Potential reuse of existing benchmarks only where transformations and labels are trustworthy.

Do not silently relabel natural images from geometry assumptions.

### Level 3 — external spatial benchmarks

Evaluate transfer on existing public benchmarks selected after novelty audit.

Paper 1 VSR and Paper 2 grounding-audit results may be used as prior baselines, but Paper 3 must have **new training and new primary evidence**.

---

## 10. Baselines

Minimum baseline families:

1. zero-shot base model;
2. ordinary spatial SFT / LoRA with matched data and compute;
3. transformed-data augmentation without latent loss;
4. output-consistency objective only;
5. invariant latent objective where applicable;
6. EquiOrient relation-aware latent-equivariance objective;
7. strongest practically reproducible close prior method if code/data permit.

The critical ablation is:

```text
same paired training data
same backbone
same optimizer / steps

augmentation only
vs output consistency
vs latent invariance
vs relation-aware latent equivariance
```

Otherwise any gain cannot be attributed to the structural objective.

---

## 11. Primary metrics

### Task metrics

- standard accuracy;
- relation-family accuracy;
- both-correct rate on paired examples;
- expected-change consistency;
- invariant-transform consistency where label should remain unchanged.

### Representation metrics

Define **equivariance error** on held-out pairs:

```text
E_equiv = d(z(T(x)), ρ_r(T) z(x))
```

Report on:

- seen transforms;
- unseen transform magnitudes;
- unseen transform classes where feasible;
- held-out relation families.

### Grounding metrics

Use correct-vs-shuffled or controlled visual counterfactual tests only as supporting evidence; Paper 2 owns the main ΔG story.

### Preservation metrics

Evaluate a small frozen general-capability suite to detect catastrophic specialization.

---

## 12. Experimental phases

### Phase 0 — novelty gate

Before model code:

- search arXiv, OpenReview, CVF, PMLR, ACL Anthology and relevant robotics venues;
- build a closest-work matrix;
- explicitly compare against SVQA-R1, SAGE, GASP, STAR-R1, SpaceMind, APC, SymPL and any newer work;
- kill or mutate the project if exact latent relation-aware equivariance is already established.

### Phase 1 — synthetic data generator / validator

Build only enough paired scenes to test the transformation algebra.

Required unit tests:

- transformed labels are correct;
- inverse transforms compose correctly;
- identity transform yields identity action;
- pair IDs and metadata are deterministic;
- unsafe cases are excluded.

### Phase 2 — representation readout pilot

Before training, test whether the chosen hidden state supports a stable pair representation at all.

If object-pair localization is unreliable, fix grounding/data design before training.

### Phase 3 — tiny 24–48 h pilot

One backbone, 2–3 relation families, small paired dataset.

Compare:

- SFT/LoRA;
- augmentation only;
- output consistency;
- EquiOrient.

Success criterion is not SOTA. It is a reproducible reduction in held-out equivariance error plus a directional improvement in paired task correctness.

### Phase 4 — frozen main protocol

Only after pilot validity:

- freeze model revision;
- freeze train/val/test scene IDs;
- freeze transform taxonomy;
- freeze `ρ_r(T)` maps;
- freeze primary metrics;
- freeze seeds and compute budget;
- freeze baselines.

### Phase 5 — main training

Run multiple seeds for the final method and strongest matched baselines.

### Phase 6 — unseen-transformation generalization

Evaluate transforms not used in training:

- held-out angles/magnitudes;
- held-out transform composition;
- ideally at least one held-out transformation type.

### Phase 7 — relation transfer

Train structural objective on selected relation families and test held-out families where the expected transformation algebra is related but not identical.

### Phase 8 — external transfer

Use established spatial benchmarks without retraining on target where possible.

### Phase 9 — hostile review

Independent agents audit:

- novelty;
- transform validity;
- leakage;
- representation-action definition;
- statistical claims;
- comparison fairness;
- seed sensitivity;
- whether gains are simply data augmentation.

---

## 13. Statistics

Primary comparisons must include training-seed variability.

Use:

- mean ± SD / confidence interval across seeds;
- paired example-level tests within each checkpoint where appropriate;
- bootstrap CIs for both-correct and equivariance-error differences;
- multiplicity control for pre-declared confirmatory families;
- effect sizes, not p-values alone.

Do not treat McNemar across examples as evidence about training-run variability.

---

## 14. Failure criteria / kill conditions

Stop or substantially redesign if any of these occur:

1. dedicated novelty search finds an existing method matching the core latent-equivariance contribution;
2. EquiOrient only improves trained transformations but not held-out transformations;
3. gains disappear when augmentation-only baseline is compute/data matched;
4. latent equivariance error improves but task behavior does not, with no useful explanatory finding;
5. gains require transformation labels unavailable outside synthetic data and do not transfer;
6. grounding noise dominates the effect;
7. method materially degrades general capabilities without a compelling tradeoff.

A null result may still be scientifically useful, but it should not be forced into a method-success paper.

---

## 15. Strong result patterns

### Strong positive method result

```text
EquiOrient:
  task accuracy                  ↑
  held-out both-correct          ↑
  unseen-transform generalization ↑
  latent equivariance error      ↓
  general capability             ≈
```

with gains beyond augmentation and output-consistency baselines.

### Strong negative / diagnostic result

If output consistency improves but latent transformation fidelity and unseen-view correctness do not, this directly connects to the Paper 2 thesis that behavioral metrics can dissociate.

### Mixed result

If equivariance helps only certain relation families, characterize the structural boundary instead of averaging it away.

---

## 16. Paper-level contribution target

A successful Paper 3 should be able to claim something of the form:

> **We introduce a relation-aware latent equivariance objective for spatial VLM adaptation. Unlike answer-consistency training, the method explicitly supervises how pairwise spatial representations should change under known visual transformations. Under matched data and compute, it improves transformation fidelity and generalization to held-out spatial interventions while preserving ordinary multimodal capability.**

This wording is a target, not an allowed claim before results.

---

## 17. What this paper must NOT become

Do not drift into:

- another VSR orientation audit;
- another ΔA/ΔC/ΔG paper;
- another generic horizontal-flip augmentation paper;
- another consistency-RL paper;
- another multi-view benchmark with no method;
- another scene-graph / box pipeline;
- a 3D world-model paper unless evidence forces that redesign.

Paper 2 should inform Paper 3, but Paper 3 must have a genuinely new intervention and new experimental evidence.

---

## 18. Initial implementation layout

```text
research/
  EQUIORIENT_STUDY.md
  EQUIORIENT_NOVELTY_GATE.md
  EQUIORIENT_PROTOCOL_FREEZE.md
  EQUIORIENT_DECISION_LOG.md
  EQUIORIENT_EXECUTION_GUIDE.md

configs/
  equiorient_protocol.yaml

src/equiorient/
  transforms.py
  relation_actions.py
  pair_encoder.py
  losses.py
  datasets.py
  evaluation.py

scripts/
  build_equiorient_pairs.py
  validate_equiorient_pairs.py
  run_equiorient_pilot.py
  train_equiorient.py
  evaluate_equiorient.py
  summarize_equiorient.py

tests/
  test_equiorient_transforms.py
  test_relation_actions.py
  test_equivariance_metrics.py
```

Do not create implementation files until the novelty gate is signed off.

---

## 19. Immediate next action

**Do not run GPU experiments yet.**

The next action for this branch is the dedicated novelty gate and exact transformation-algebra specification. Only after those are accepted should a tiny synthetic generator and pilot be implemented.

---

## 20. Working title candidates

Primary:

> **EquiOrient: Relation-Aware Transformation-Equivariant Spatial Representations for Vision–Language Models**

Alternatives:

- **Learning How Space Transforms: Equivariant Spatial Representations for Vision–Language Models**
- **Beyond View Consistency: Relation-Aware Latent Equivariance for Spatial VLMs**
- **From Consistent Answers to Equivariant Representations in Spatial Vision–Language Models**

Do not lock the final title until the novelty gate and pilot results are complete.
