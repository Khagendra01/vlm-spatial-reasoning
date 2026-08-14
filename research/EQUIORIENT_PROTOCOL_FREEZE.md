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

---

# AMENDMENT A — MUTATED TARGET (2026-08-14, authority: EQUIORIENT_NOVELTY_GATE.md MUTATE verdict)

The novelty gate closed with **MUTATE**. The pre-amendment sections above remain
the general governance frame; this amendment narrows the confirmatory target.
Where this amendment conflicts with sections 1-12, THIS amendment wins until a
new decision-log entry supersedes it.

## A1. Mutated research question (replaces section 1)

> Can an **answer-path object-pair spatial state** be trained to obey a
> **predeclared, heterogeneous, geometry-derived transformation algebra**, such
> that the learned structure **generalizes compositionally to held-out
> transformations** beyond matched augmentation, output-consistency, invariance,
> and wrong-geometry controls?

Abandoned: "pair-conditioned latent with a relation-dependent equivariance
loss under transformed views" — not sufficiently distinctive (latent spatial
shaping, representation-level geometric supervision, view-consistency training,
and latent group-action learning all exist).

## A2. Hard design constraints (non-negotiable)

1. **z is on the answer path.** The structural objective acts on the same
   learned spatial state that the answer head consumes. Architecture:
   ision features -> object-pair spatial state z(a,b) -> answer pathway ->
   relation prediction / language answer, with the equivariance loss acting on
   that same z. An auxiliary probe that the model can ignore is NOT EquiOrient.
2. **rho(T) never receives the true relation label.** rho is predeclared and
   derived from the geometry/coordinate semantics of T, with typed block actions:
   z = [z_h, z_v, z_d, z_pose, ...]; horizontal reflection acts on z_h,
   vertical reflection on z_v, provably-orthogonal components stay invariant.
   No form of ho(T, true_relation) is permitted.
3. **Composition is the primary test.** Train on H and V individually; hold out
   V o H; the decisive test is ho(V o H) ~= rho(V) rho(H) behaviorally AND
   in latent equivariance error, on the unseen composition.

## A3. Amended pilot design (replaces pilot relation/transform lists)

- Relations: **left/right** (horizontal), **above/below** (vertical),
  **parallel/perpendicular** (controlled invariance only).
- Transforms: **H (horizontal reflection)**, **V (vertical reflection)**.
- **Hold out: V o H composition** (never seen in training data).
- **facing/facing-away are EXCLUDED from Phase 1** (intrinsic pose, camera
  viewpoint, grounding ambiguity — Paper-1 mess). Only after the clean algebra
  passes may facing enter as a scientifically meaningful extension.
- Matched controls (same scenes, transforms, steps, model, parameter budget):
  1. ordinary spatial SFT/LoRA;
  2. transformation augmentation only;
  3. output-consistency training;
  4. latent invariance baseline;
  5. relation-aware latent equivariance (EquiOrient);
  6. **wrong-geometry EquiOrient (mandatory)** — same loss machinery with an
     incorrect rho (e.g., rho_H acting on z_v). If correct rho > wrong rho on
     the held-out composition, the geometry matters; otherwise the claim dies.

## A4. Amended primary evidence (adds to section 4)

1. held-out V o H task accuracy (primary);
2. latent equivariance error on held-out V o H;
3. paired both-correct on held-out composition;
4. correct-rho vs wrong-rho contrast on held-out composition;
5. multi-seed method-vs-baseline comparison.

## A5. Amended stop condition (adds to section 12)

- **If EquiOrient does not beat augmentation-only AND output-consistency on the
  held-out V o H composition (same data/budget), STOP.** The protocol already
  names gains-explained-by-augmentation as a kill condition; the mutation makes
  held-out composition the decisive axis.

## A6. Gate order (mandatory before any GPU)

1. Gate 1: executable transformation algebra (this file's section 6 checks,
   implemented as unit tests on a machine-readable table).
2. Synthetic paired scenes CPU-side; 50 human-inspected pairs stratified by
   relation x transform.
3. Representation-feasibility gate: where z lives, how the answer head consumes
   it, gradient reachability from answer objective AND equivariance objective,
   no bypass path.
4. GPU pilot (one seed, falsification-first, 48h target).

# AMENDMENT B — Phase-1 falsification scope + final arm/architecture freeze
# (2026-08-14, authority: orchestrator pre-freeze control correction)

## B1. Phase-1 scope declaration (explicit, must appear in paper)

> "Phase-1 is a one-seed falsification pilot. The 14-train / 3-held-out-scene
> design is not final-paper evidence. Success only authorizes a larger
> multi-seed, larger-independent-scene confirmatory experiment."

(Note: the corrected freeze uses 10 train / 4 validation / 3 holdout scenes;
the scope declaration above retains the published protocol wording.)

## B2. All six arms share the IDENTICAL answer-path architecture

Qwen3 deepstack features -> object-region pooling -> PairEncoder -> typed
z(a,b) -> forced relation head. PairEncoder and relation head exist and are
trainable in EVERY arm (baselines included). Arm differences exist ONLY in
data treatment / loss computation.

- ordinary_sft_lora: original-only data, answer loss only (data difference
  explicitly labeled; optimization budget matched).
- augmentation_only: H/V paired data, answer loss only.
- output_consistency: H/V data + output-law consistency loss.
- latent_invariance: H/V data + latent rho=I loss.
- equiorient: H/V data + correct geometry-derived rho(T).
- wrong_geometry_equiorient: bit-for-bit same structure as EquiOrient,
  differing ONLY in the predeclared wrong rho.

The critical causal comparison (augmentation <-> output-consistency <->
latent-invariance <-> EquiOrient <-> wrong-geometry) uses EXACTLY the same
transformed H/V examples.

## B3. Structural-loss hyperparameter fairness

output_consistency, latent_invariance, equiorient, wrong_geometry all use
the SAME predeclared weight grid {0.1, 1.0, 10.0}, the SAME fixed validation
slice (scene_0010..0013), and the SAME selection rule. NEVER select using
held-out V o H. Wrong-geometry uses the same selected weight as EquiOrient
(not tuned independently to make it worse).

## B4. Loss functions introduce ZERO trainable parameters

All structural losses are pure functions of (logits, z, rho); verified by
smoke test (check 2).

## B5. Initialization equivalence (mandatory pre-training check)

One common Qwen3 + PairEncoder + head state is cloned into all six arms;
before training, common parameters must be numerically identical; arm
differences exist only in data/loss. Executable: scripts/equiorient/
qwen3_smoke_test.py check 3. Status at freeze: PASS.

## B6. Frozen PairEncoder spec (do not change after pilot results)

- input: concat [V_a(4096) ; V_b(4096)] = 8192 (Qwen3 deepstack features)
- hidden: 512, depth 2 (Linear -> GELU -> Linear), activation GELU
- z_total: 512, blocks z_h=z_v=z_d=z_orient=128
- init: default nn.Linear init
- relation head: Linear(256, 4) over [z_h ; z_v]; FORCED decoding

## B7. Backbone freeze (Qwen3)

Qwen/Qwen3-VL-8B-Instruct @ 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b,
transformers==4.57.6. LoRA: vision qkv/proj/c_fc/c_proj (fused qkv — Qwen3
naming), rank 16 alpha 32 dropout 0.05. Text backbone FROZEN; lm_head
FROZEN (relation answer is forced from z, text LoRA does not participate in
the primary answer path). All arms identical.
