# EquiOrient — Protocol Authority

**Status:** PRE-EXPERIMENT GOVERNANCE.  
**Authority order:** `EQUIORIENT_PROTOCOL_FREEZE.md` > `configs/equiorient_protocol.yaml` > `EQUIORIENT_STUDY.md` > implementation convenience.

This file freezes the research logic that future agents must not silently change after observing results.

---

## 1. Frozen main question

> Can explicit relation-aware latent equivariance teach spatial representations that transform according to known geometry and generalize better to held-out transformations than matched ordinary fine-tuning, augmentation, or output-consistency training?

The paper is **not** a generic spatial benchmark paper and **not** a generic consistency paper.

---

## 2. Precondition: novelty gate

No confirmatory model training begins until `EQUIORIENT_NOVELTY_GATE.md` ends with `PROCEED` or an explicitly documented `MUTATE` decision.

If novelty gate outcome is `KILL`, stop this project.

---

## 3. Frozen comparison hierarchy

At minimum, the main controlled experiment must compare the same backbone and paired training data under:

1. ordinary spatial SFT/LoRA;
2. transformation data augmentation only;
3. output-consistency training;
4. latent invariance baseline where semantically meaningful;
5. relation-aware latent equivariance (EquiOrient).

A method claim is invalid if EquiOrient receives more paired data, more optimization steps, or privileged target labels unavailable to matched baselines without that difference being explicitly ablated.

---

## 4. Frozen evidence hierarchy

### Primary evidence

1. held-out transformation task performance;
2. both-correct paired accuracy / expected-change correctness;
3. held-out latent equivariance error;
4. multi-seed method-vs-baseline comparison.

### Secondary evidence

- seen-transform accuracy;
- relation-family breakdown;
- visual-dependence tests;
- external benchmark transfer;
- general-capability preservation.

### Exploratory evidence

- mechanistic probes;
- attention maps;
- newly invented transforms after primary results;
- post-hoc subgroup analyses.

Do not promote exploratory evidence after seeing favorable results.

---

## 5. Frozen transformation principles

Every transform must be assigned one of:

- `invariant_relation`;
- `relation_permutation`;
- `object_local_state_change`;
- `viewpoint_frame_change`;
- `unsafe`.

Every eligible relation/transform pair must have a predeclared expected action `rho_r(T)`.

No global rule may be applied across all relation families.

Unsafe/ambiguous examples are excluded before confirmatory evaluation IDs are frozen.

---

## 6. Required transform algebra checks

Before data generation is accepted:

- identity action test;
- inverse transform test where defined;
- composition test where defined;
- label/action consistency test;
- deterministic regeneration test;
- train/test scene leakage test;
- object-pair identity preservation test.

---

## 7. Primary methodological distinction

The central structural objective must act on a learned latent spatial state, not merely on final answers.

Required conceptual form:

```text
z(T(x), a, b) ~= rho_r(T) z(x, a, b)
```

If the final implementation reduces to `answer(T(x)) == transformed_answer` with no representation-level structural constraint, it is no longer EquiOrient and must be renamed/repositioned.

---

## 8. Pilot rule

Pilot is for falsification and implementation validation, not paper-number optimization.

Before pilot:

- freeze pilot scene IDs;
- freeze transform set;
- freeze relation set;
- freeze model revision;
- freeze baseline definitions;
- freeze metrics.

Pilot may use one seed. Confirmatory training must use multiple seeds for final method and strongest matched baselines.

---

## 9. Main protocol freeze point

After a valid pilot, create a dated protocol revision that freezes:

- backbone + revision;
- training data IDs;
- validation/test IDs;
- relation families;
- transformation classes and magnitudes;
- `rho_r(T)` definitions;
- architecture of pair representation;
- loss definitions;
- lambda selection rule;
- optimizer / steps / batch budget;
- seeds;
- primary metrics;
- primary statistical tests;
- baseline set;
- external evaluation set.

After that point, changes require an entry in `EQUIORIENT_DECISION_LOG.md` stating whether results had been seen and why the change is scientifically necessary.

---

## 10. Statistics

The main paper must distinguish:

- training-run variability across seeds;
- paired example-level uncertainty within a fixed checkpoint.

Do not use example-level McNemar alone to claim method robustness across training runs.

Predeclare a small confirmatory test family before full results.

---

## 11. Anti-drift rules

Future agents must not silently:

- replace equivariance with invariance;
- turn the paper into Paper 2's ΔA/ΔC/ΔG audit;
- add a new model because one result is weak;
- tune transformation definitions after observing test results;
- drop an unfavorable matched baseline;
- redefine held-out transformations after training;
- claim firstness without a new literature pass;
- move to 3D/4D world modeling unless a documented `MUTATE` decision explicitly changes the project.

---

## 12. Stop conditions

Stop and report before continuing if:

- transform labels/actions are uncertain;
- object grounding is unreliable enough to invalidate `z(a,b)`;
- prior work is discovered that threatens the novelty target;
- EquiOrient gains are fully explained by augmentation-only baseline;
- implementation requires changing a frozen confirmatory definition.
