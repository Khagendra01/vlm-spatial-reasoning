# EquiOrient — Execution Guide for Research Agents

This guide exists so later agents do not inherit only a title and start inventing a different paper.

---

## 1. Read order

Before making any change, read in this order:

1. `research/EQUIORIENT_PROTOCOL_FREEZE.md`
2. `research/EQUIORIENT_NOVELTY_GATE.md`
3. `configs/equiorient_protocol.yaml`
4. `research/EQUIORIENT_DECISION_LOG.md`
5. `research/EQUIORIENT_STUDY.md`

Authority is determined by that order.

---

## 2. What agents may do before novelty gate closure

Allowed:

- literature search and bibliography verification;
- populate the novelty matrix;
- inspect candidate datasets/models;
- write transformation-algebra specifications;
- write unit-test plans;
- estimate compute;
- prototype synthetic scene generation on CPU;
- inspect hidden-state interfaces without training.

Not allowed as confirmatory research:

- full GPU training;
- large hyperparameter sweeps;
- declaring the final novelty claim;
- selecting results to define the transform set.

---

## 3. Gate 0 — novelty

Required output:

- ≥20 close papers;
- top-5 threat matrix;
- final `PROCEED/MUTATE/KILL` verdict;
- exact allowed claim.

If the verdict is not `PROCEED`, update the decision log before coding.

---

## 4. Gate 1 — transformation algebra

Create a machine-readable table with at least:

```text
relation
transform_name
transform_class
expected_relation_before
expected_relation_after
rho_action
is_confirmatory
is_safe
reason
```

Required tests:

- identity;
- inverse;
- composition where defined;
- no contradictory action maps;
- no ambiguous relation/transform pairs in confirmatory set.

Human spot-check at least 50 generated pairs stratified by relation and transform before training.

---

## 5. Gate 2 — dataset generator

Build the smallest controlled paired dataset that can falsify the hypothesis.

Recommended pilot families:

- left/right;
- facing/facing-away;
- parallel/perpendicular.

Reason: these give three distinct transformation behaviors — relation permutation, object-local orientation change, and relation invariance under selected global transforms.

Do not add many families until the algebra is validated.

Dataset metadata must include:

```text
scene_id
pair_id
subject_id
reference_id
camera_pose
object_poses
relation
transform_name
transform_parameters
expected_relation
split
generator_version
seed
```

Split by underlying scene seed, not by individual rendered image.

---

## 6. Gate 3 — representation feasibility

Before training EquiOrient, verify the chosen backbone exposes a practical pair-conditioned feature path.

Questions:

- Can subject/reference regions be identified reliably?
- Which hidden state is actually consumed by the language model?
- Can `z(a,b)` be extracted without changing the backbone architecture drastically?
- Does the pair encoder have enough capacity to express the intended transformation action?

Do not claim a failure of equivariance if grounding/pair extraction is broken.

---

## 7. Gate 4 — 24–48 hour pilot

Use one backbone and one seed.

Train four matched conditions on the same paired data:

```text
A. ordinary spatial SFT/LoRA
B. augmentation-only
C. output-consistency
D. EquiOrient latent equivariance
```

Optional invariant-latent baseline only if it is well-defined for the pilot transform set.

Pilot report must contain:

- seen-transform accuracy;
- held-out-transform accuracy;
- both-correct paired accuracy;
- expected-change consistency;
- latent equivariance error;
- data/compute parity table;
- training stability;
- qualitative failures.

Stop after the pilot and decide `PROCEED/MUTATE/KILL` before scaling.

---

## 8. Gate 5 — confirmatory protocol freeze

If pilot survives, freeze:

- backbone/revision;
- train/val/test IDs;
- transform classes;
- held-out transforms;
- relation families;
- pair encoder;
- rho maps;
- loss functions;
- lambda selection rule;
- training budget;
- seeds;
- baselines;
- primary metrics;
- confirmatory statistical family.

No test-set-driven tuning after this point.

---

## 9. Gate 6 — main runs

Use multiple training seeds for EquiOrient and strongest matched baselines.

Save per run:

```text
model revision
adapter/config hash
seed
training IDs
validation IDs
test IDs
transform spec hash
rho-map hash
prompt/parser versions
optimizer settings
steps/tokens
GPU type
package snapshot
prediction file hash
latent file hash
```

Do not overwrite failed/unfavorable runs.

---

## 10. Gate 7 — external validation

Only after the internal controlled result is frozen.

Goals:

- test whether structural gains leave synthetic distribution;
- evaluate at least one natural-image or established spatial benchmark;
- avoid target fine-tuning where possible;
- report failures to transfer honestly.

Do not call synthetic success “general spatial intelligence.”

---

## 11. Gate 8 — hostile review

Commission independent review agents with distinct roles:

- novelty reviewer;
- geometry/transform validity reviewer;
- statistical reviewer;
- implementation leakage reviewer;
- method-fairness reviewer;
- paper-claim reviewer.

Agents should search for rejection reasons, not polish wording.

---

## 12. Paper writing rule

Write the paper around the final evidence, not the planned title.

Allowed high-level stories include:

- successful latent-equivariance method;
- structural objective helps only specific relation classes;
- answer consistency does not imply representation equivariance;
- equivariance improves representation fidelity but not downstream behavior (negative/mechanistic paper).

Do not force a positive method claim if the data support a more useful negative result.

---

## 13. Compute discipline

Start small. Scale only after falsifiable evidence.

Order:

```text
CPU algebra/tests
→ tiny synthetic rendering
→ one-model pilot
→ protocol freeze
→ multi-seed main runs
→ external validation
```

Do not add larger models for prestige. Add a second model only if it tests a scientifically necessary generalization claim.

---

## 14. Handoff format

Every agent ending a substantial session must append or create a handoff containing:

```text
current branch SHA
protocol status
novelty gate status
what was changed
what results were seen
what remains frozen
bugs / unresolved risks
next single action
```

No undocumented result-driven protocol changes.
