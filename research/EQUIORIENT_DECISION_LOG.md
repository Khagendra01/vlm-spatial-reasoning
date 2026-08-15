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

---
## 2026-08-14 — Gate 1 executed: transformation algebra + protocol amendment (CPU work, no GPU)

results already seen? no (no model outputs exist yet)

decision: execute Amendment A (MUTATE target) in protocol authority + YAML,
and build the transformation algebra as executable, unit-tested data.

- research/EQUIORIENT_PROTOCOL_FREEZE.md: appended Amendment A (mutated
  target: answer-path z; rho never receives true relation; H/V seen, V o H
  held out; facing excluded from Phase 1; wrong-geometry control mandatory;
  composition = primary test; gate order A6).
- configs/equiorient_protocol.yaml: status -> mutated_target_amended_gate1_in_progress;
  added wrong_geometry_control_required, composition_is_primary_test,
  holdout_transform=V_composition_H, rho_relation_label_conditioned=false,
  z_on_answer_path_required, facing_excluded_phase1; pilot relations ->
  horizontal_left_right, vertical_above_below, parallel_perpendicular.
- src/equiorient/transforms.py: typed state (z_h/z_v/z_d/z_pose/z_orient),
  predeclared geometry-derived rho(T) for I/H/V/VoH/HoH, expected_after()
  relation algebra (component-driven: a transform flips a relation iff it
  flips the relation's typed component).
- tests/test_equiorient_transforms.py: 21 tests covering identity, inverse,
  composition rho(VoH)=rho(V)rho(H) (state + relations), geometry-derived
  actions (H flips only z_h etc.), depth/orientation invariance, no
  contradictions, determinism, wrong-geometry-control reachability. ALL PASS.
- Full shared suite: 142 passed (incl. merged protocol manifests from
  master 8be6b05).
- Also fixed a shared-layer gap: results/grounding/protocol/ backfilled to
  master (was only on paper2; tests depend on it).

alternatives considered: parameterized rho_r(T) keyed on true relation
(rejected: violates A2.2 — leaks the answer into the action); invariance-only
constraint (rejected: anti-drift forbids replacing equivariance).

reason: novelty gate closed MUTATE on 2026-08-13; Gate 1 is the mandatory
first step before any GPU per the execution guide and Amendment A6.

affected frozen artifacts: PROTOCOL_FREEZE.md (amended, not rewritten),
equiorient_protocol.yaml (amended), NOVELTY_GATE.md (unchanged — still
authoritative for the mutated target).

confirmatory or exploratory: protocol/governance + CPU infrastructure; no
model training performed.

---
## 2026-08-14 (cont.) — Gates 2-3 executed (CPU work; still no GPU)

results already seen? no

Gate 2 (synthetic paired scenes):
- src/equiorient/datasets.py: plan-view synthetic generator (rects/circles/
  line segments with depth + direction), geometry-level transforms
  (H/V/VoH), margin-guaranteed strict relations, PIL rendering.
- tests/test_equiorient_synthetic.py: 8 tests PASS — algebra law holds for
  every pair x relation x transform; VH composition == sequential; no ties
  post-transform; pixel-level inverse/composition/determinism.
- Hostile-verified: injected renderer bug (V flips x instead of y) produced
  192 law violations -> gate is sensitive, not vacuous.
- Human-inspection pack committed: 51 side-by-side PNG pairs + manifest
  (4896 rows, all law_ok, stratified relation x transform) at
  results/equiorient/human_inspection/. HUMAN SPOT-CHECK STILL REQUIRED
  (50+ pairs) before pilot — see manifest.csv.

Gate 3 (representation feasibility): research/EQUIORIENT_REPRESENTATION_
FEASIBILITY.md — proposal: PairEncoder over pooled vision features of known
object boxes (synthetic scenes = exact grounding), typed z = [z_h|z_v|z_d|
z_orient]; relation head W_rel·z with FORCED relation decoding (no LM-side
bypass); answer gradient reaches z via W_rel^T; equivariance loss reaches
same z via shared PairEncoder weights on z(x) and z(Tx); bypass table with
mitigations (forced decoding, causal ablation mandatory, equivariance loss
as structural backstop). Open items frozen at pilot time (backbone, head
dims, lambda_eq selection rule predeclared). Verdict: FEASIBLE.

alternatives considered: auxiliary-branch z (rejected: model can ignore it —
gate requires answer-path); conditioning rho on relation label (rejected:
A2.2 leaks answer).

reason: execution-guide gate order (Gate 1 -> synthetic scenes -> feasibility
-> pilot); protocol Amendment A6.

affected frozen artifacts: none frozen changed; adds datasets.py,
test_equiorient_synthetic.py, FEASIBILITY.md, human_inspection pack.

confirmatory or exploratory: CPU infrastructure + design analysis; no model
training.

---
## 2026-08-14 (cont.) — Gate 2 human spot check: PASS (all clear)

results already seen? no (no model outputs; only synthetic renderings)

decision: human spot check of the 51 synthetic pairs completed by the
orchestrator with verbal sign-off "all clear" — 0 flags.

- Recorded as results/equiorient/human_inspection/spotcheck_verdict.json.
- Combined with machine verification (4,896 manifest rows all law_ok;
  hostile renderer-bug test detected 192 violations when corrupted) the
  synthetic-data layer is accepted.
- Gate 2 CLOSED. Next: pilot-freeze config (backbone choice, budgets,
  lambda_eq rule, arms) then GPU pilot under explicit unlock.

alternatives considered: none (spot check is protocol-mandated; no flag
required re-check).

reason: execution guide Gate 1 -> human spot check >= 50 pairs stratified
by relation x transform; Amendment A6.

affected frozen artifacts: none frozen changed; adds spotcheck_verdict.json.

confirmatory or exploratory: CPU verification; no model training.

---
## 2026-08-14 (cont.) — Pilot freeze config drafted (pre-GPU)

results already seen? no

decision: draft configs/equiorient_pilot_freeze.yaml encoding the full
predeclared pilot contract per Amendment A6: 6 matched arms, H/V seen with
V o H held out, 14 train / 3 holdout scenes from Gate-2 generator (seed
20260814), lambda_eq grid {0.1,1.0,10.0} chosen on fixed validation slice
before method comparison, forced-relation decoding, mandatory causal
ablation, stop conditions from protocol s12 + A5.

OPEN DECISION (not frozen yet): backbone — SmolVLM2-2B vs Qwen2-VL-7B
(max 1 per protocol). Both candidates listed with reasons; must be fixed
in the YAML before GPU.

GPU REMAINS OFF until: (a) backbone frozen in pilot YAML, (b) explicit
compute unlock from orchestrator.

affected frozen artifacts: none (draft only; freeze happens on next commit
after backbone decision).

confirmatory or exploratory: planning only; no model training.

---
## 2026-08-14 (cont.) — BACKBONE DECISION: Qwen3-VL-8B primary (prospective, pre-result)

results already seen? NO EquiOrient GPU/model results exist.

decision: Paper-3 primary pilot backbone = Qwen/Qwen3-VL-8B-Instruct.
- Qwen2-VL-7B: optional LATER replication backbone only.
- SmolVLM2-2B: engineering smoke tests only; never the scientific pilot.
- Selected PROSPECTIVELY (before any EquiOrient result) because Paper 3
  should use the newer backbone.
- Prior Gate-3 feasibility design was backbone-generic in concept but its
  concrete implementation assumptions referenced SmolVLM2/Qwen2 module
  names and visual-token layouts; Qwen3 requires a compatibility check
  (Gate 3b) BEFORE freeze.
- This is a pre-result protocol amendment, NOT result-driven model switching.

FROZEN AND UNCHANGED (do not reopen): Gate 1 algebra, Gate 2 synthetic
generator + 4896 machine law checks + 51-pair human audit, H/V seen with
V o H held out, six-arm matched comparison, wrong-geometry control,
primary stop conditions.

status: pilot YAML amended -> backbone_primary Qwen/Qwen3-VL-8B-Instruct,
backbone_status pending_qwen3_gate3b. Next: Gate 3b (Qwen3-specific
representation feasibility) then freeze + explicit GPU unlock.

confirmatory or exploratory: protocol amendment (pre-result); no training.

---
## 2026-08-14 (cont.) — Gate 3b executed: Qwen3-VL-8B feasibility (CPU only)

results already seen? no (no EquiOrient GPU results; smoke tests are
random-weight engineering checks, no scientific outputs produced/inspected)

decision: run Qwen3-specific feasibility per orchestrator Steps 2-4.

FINDINGS (source-verified from transformers 4.57.6 modeling_qwen3_vl.py):
1. transformers >= 4.57.0 required (local upgraded 4.56.2 -> 4.57.6).
2. Qwen3-VL vision stack emits DEEPSTACK features (deepstack_visual_indexes
   + deepstack mergers) in addition to merged image_embeds — richer
   mid-stream source for z(a,b) pooling; spatial layout intact.
3. Qwen3 vision attention uses FUSED self.qkv (nn.Linear(dim, dim*3)) —
   differs from Qwen2-VL separate q/k/v; LoRA target must be 'qkv'.
4. Box->grid mapping deterministic via image_grid_thw + patch(28)/merge(2);
   no detector needed (synthetic ground truth).
5. typed z = [z_h|z_v|z_d|z_orient] construction unchanged; forced relation
   decoding unchanged; causal ablation mandatory.
6. VRAM estimate 24-27 GB (bf16, LoRA, batch 8, grad checkpointing) ->
   fits A6000 48GB.

ARCHITECTURE CRITIQUE (Step 4): frozen-backbone + head-only WOULD invite
"classifier on pretrained encoder" criticism -> MUTATE_ARCHITECTURE (minor):
pool z from Qwen3 deepstack features + LoRA-train vision tower (fused qkv)
so gradients from BOTH objectives reach the backbone representation; forced
relation decoding + causal ablation unchanged. Pre-result amendment.

SMOKE TESTS (scripts/equiorient/qwen3_smoke_test.py, CPU, tiny random
Qwen3-VL): 13/13 PASS — preprocessing/tensor shapes, box->cell mapping,
pooled V_a/V_b shapes, typed z blocks, relation logits depend on z,
z-corruption changes logits, L_answer grad to PairEncoder, L_eq grad to
same PairEncoder, rho keyed on (T, component) only, six-arm matched
trainable counts (base arms share head-only budget; EquiOrient delta =
20,608 PairEncoder params reported explicitly).

affected frozen artifacts: none reopened (Gates 1-2 intact); adds
EQUIORIENT_QWEN3_FEASIBILITY.md, EQUIORIENT_ARCHITECTURE_CRITIQUE.md,
qwen3_smoke_test.py; local pip env upgraded transformers 4.57.6.

confirmatory or exploratory: engineering/CPU only; NO GPU, NO scientific run.

---
## 2026-08-14 (cont.) — FINAL PILOT FREEZE (Amendment B + corrected six-arm design)

results already seen? NO (no EquiOrient GPU results; smoke tests are
random-weight engineering checks only)

decision: final pre-result control correction per orchestrator:
1. ALL six arms use the identical Qwen3 answer-path architecture
   (deepstack -> pooling -> PairEncoder -> typed z -> forced relation head);
   PairEncoder + relation head trainable in EVERY arm.
2. Loss functions are pure functions (zero trainable params) — verified.
3. Init-equivalence test: one common state cloned into six arms,
   numerically identical pre-training; differences only in data/loss —
   PASS (smoke R2 12/12).
4. LoRA cleanup: Qwen3 fused vision qkv/proj/c_fc/c_proj (rank 16 alpha 32
   dropout 0.05); text backbone FROZEN; lm_head FROZEN (relation answer
   forced from z, so text LoRA not on primary answer path; identical in all
   arms).
5. Structural-loss fairness: same grid {0.1,1.0,10.0}, same validation
   slice (scene_0010-0013), same selection rule; wrong-geometry uses the
   same selected weight as EquiOrient; never select on held-out VoH.
6. Phase-1 scope declaration added to protocol (Amendment B1): one-seed
   falsification pilot, 10 train / 4 val / 3 holdout, NOT final-paper
   evidence; success authorizes multi-seed confirmatory.
7. Frozen PairEncoder spec (B6): input 8192, hidden 512, depth 2 GELU,
   z_total 512 (128x4), head Linear(256,4), default init.
8. Backbone pinned: Qwen/Qwen3-VL-8B-Instruct @ 0c351dd..., transformers
   ==4.57.6.

Trainable params per arm (smoke R2): 4,458,500 identical across all six
(common PairEncoder + head; vision LoRA; text/lm_head frozen).

FINAL FREEZE COMMIT: see commit message. GPU REMAINS OFF. No training
launched. Awaiting explicit orchestrator GPU unlock.

affected frozen artifacts: equiorient_pilot_freeze.yaml (final), protocol
Amendment B, qwen3_smoke_test.py (R2).

confirmatory or exploratory: pre-result freeze; no model training.

---
## 2026-08-14 (cont.) — Pre-GPU documentation/config consistency correction (zero compute)

results already seen? NO (no EquiOrient GPU results exist)

decision: single zero-compute freeze-correction commit per orchestrator:
- Phase-1 scope wording updated from "14-train / 3-held-out" to
  "10-train / 4-validation / 3-held-out" in configs/equiorient_pilot_freeze.yaml
  (scope_declaration) and research/EQUIORIENT_PROTOCOL_FREEZE.md (Amendment
  B1 quote).
- Structural-loss validation slice made unambiguous as scene_0010, scene_0011,
  scene_0012, scene_0013 in the YAML selection_rule and Protocol Amendment B3.
- NO changes to: model, architecture, losses, scene IDs, metrics, seeds,
  hyperparameters, stop conditions, or any scientific decision.
- Schema/config sanity checks only (YAML parse + scene-split consistency).
- This is a documentation consistency correction, logged pre-GPU.

confirmed frozen data split (unchanged): 10 train (scene_0000-0009),
4 validation (scene_0010-0013), 3 holdout (scene_0014-0016).

confirmatory or exploratory: documentation only; no training.

---
## 2026-08-15 — Engineering fix: Qwen3VLProcessor image_token=None (zero-compute, pre-training)

results already seen? NO (no EquiOrient scientific outputs; the pilot
crashed in PRE-FLIGHT on the box before any training step)

decision: fix a transformers-4.57.6 processor construction bug that the
CPU --tiny smoke could NOT catch (the tiny path bypasses the processor;
the real path crashed at the first AutoProcessor call):

- On the A6000 box, the full pilot crashed at:
  processing_qwen3_vl.py __call__ line 190: while self.image_token in
  text[i] -> TypeError: 'NoneType' is not iterable.
- Root cause: the frozen revision 0c351dd0's snapshot has an EMPTY
  processor_config.json, and its tokenizer sets the image_token attribute
  to None; Qwen3VLProcessor falls back to tokenizer.image_token only when
  the image_token kwarg is absent -> self.image_token = None.
- Fix (engineering only, no scientific parameter touched): construct the
  processor with explicit image_token/video_token kwargs:
    AutoProcessor.from_pretrained(bb["name"], revision=bb["revision"],
        image_token="<|image_pad|>", video_token="<|video_pad|>")
  token strings verified against the snapshot's added_tokens_decoder
  (ids 151655/151656).
- No changes to: backbone, revision, architecture, losses, data, seeds,
  metrics, hyperparameters, stop conditions, or any frozen protocol
  parameter.

affected frozen artifacts: scripts/equiorient/pilot_harness.py (bug fix
only; re-verified with a REAL-model processor forward before relaunch)

confirmatory or exploratory: engineering fix; no training, no results.

---
### 2026-08-15 (cont.) — Second root cause of the same crash: text=None -> [None]

On re-verification with the fix above, the same line still crashed: the
None was NOT self.image_token (now set) but text[i]: Qwen3VLProcessor
__call__ wraps missing text as [None] (text = [text] when not a list),
then iterates 'while self.image_token in text[i]' -> None is not
iterable. Engineering fix: harness now calls the processor with
text="" (the harness consumes only pixel_values + image_grid_thw; the
empty text is never used). Both fixes verified with a REAL-model forward
on the box (Qwen3-VL-8B @ 0c351dd0, bf16/sdpa, deepstack features
returned) before the pilot relaunch. Still zero scientific changes.

---
### 2026-08-15 (cont.) — Fix 2: bf16/float32 mismatch + Fix 3: vision-LoRA gradient flow

Real-model verification on the box surfaced two more implementation
deviations (tiny smoke cannot catch either):

Fix 2 (dtype): pre-flight crashed with
  RuntimeError: mat1 and mat2 must have the same dtype, but got BFloat16 and Float
  Root cause: deepstack features arrive bf16 (model bf16) but the frozen
  PairEncoder spec is default fp32 init. Fix: pooled() casts the pooled
  feature to float() (encoder/head remain frozen-spec fp32; no scientific
  parameter changed).

Fix 3 (gradient flow, deeper): image_features() computed vision features
under torch.no_grad(), so the vision LoRA (3,028,992 trainable params)
NEVER received gradients — violating the frozen Amendment B4 /
ARCHITECTURE_CRITIQUE requirement that gradients from BOTH objectives
reach the backbone representation. Fix: the real path now forwards
WITHOUT no_grad; eval_scenes explicitly wraps its loop in torch.no_grad()
so evaluation never builds autograd graphs.

Both fixes verified locally (py_compile + --tiny PASS) and must pass a
REAL-model training-step gradient check on the A6000 box before relaunch.
No changes to: backbone, revision, architecture spec, losses, data, seeds,
metrics, hyperparameters, stop conditions.

---
### 2026-08-15 (cont.) — Deepstack discovery + REAL-model grad-flow verification PASS

Verification on the box (Qwen3-VL-8B @ 0c351dd0, bf16/sdpa, one real
training step) established:
- Deepstack executes vision blocks 0-8 ONLY (the deep stack reuses them);
  LoRA adapters attached to blocks 9-26 are inert (never in the forward
  graph) — same in ALL six arms, so the matched comparison is unaffected;
  frozen target-module set (qkv/proj/c_fc/c_proj) kept EXACTLY as frozen,
  so the recorded init-equivalence numbers (4,458,500 per arm) remain the
  frozen contract.
- Gradient-flow check: all 36 executed-tower LoRA params receive
  gradients from L_answer, as do PairEncoder and relation head
  (TRAIN_STEP_GRAD_FLOW_OK). Fix 2 (dtype cast) and Fix 3 (no_grad
  removal) validated in a real training step, not just a forward.

Frozen contract unchanged; discovery documented for the pilot report.

---
## 2026-08-15 — PILOT RUN #1 INVALID: five implementation deviations found in result audit (run void)

results already seen? The first GPU run COMPLETED (62 min, all 12 runs) but
the result audit found the matrix scientifically VOID — the numbers are
correct as computed, the sentences they would support are not:

1. HELD-OUT LEAK (fatal): load_pilot_data did not filter v_after_h; the
   manifest contains V o H rows for all 17 scenes and they entered the
   training data of every arm except ordinary_sft (and validation). The
   frozen protocol requires transform_held_out v_after_h NEVER in training.
   This is why every arm hit ~1.0 — the held-out transform was seen.
2. equiorient arm ran with NO equivariance loss: run() passed
   structural='equiorient' but the loss branch keys on 'equivariance' —
   the primary method arm silently collapsed to augmentation_only.
3. wrong_geometry arm was NOT wrong: it ran latent_invariance (rho=I)
   instead of the frozen WRONG predeclared rho (e.g., rho_H acting on z_v).
4. Vision LoRA state carried over between arms (only enc/head were
   re-initialized) — arms did not start from the common init (Amendment B3).
5. Hold-out evaluation ran ONCE on the last arm only (wrong_geometry), not
   per causal-comparison arm at its selected lambda — the frozen primary
   metric (per-arm held_out_VoH_accuracy contrast) was never computed.

decision: fix all five in pilot_harness.py (filter V o H from train/val;
STRUCTURAL_OF map with fail-loud assert; WRONG_RHO_VEC with the frozen
example semantics — H acts on z_v, V acts on z_h, V o H misread as
identity; common-init LoRA snapshot restored at every train_run; selected-
lambda re-run of all five causal arms with a SINGLE hold-out V o H
evaluation each, after selection, never used for selection) and RE-RUN the
pilot. Run #1 numbers are void and must not be reported.

affected frozen artifacts: pilot_harness.py only (engineering); no change
to backbone/revision/losses/data/seeds/metrics/stop conditions.

confirmatory or exploratory: implementation correction; the re-run is the
first valid pilot execution.

---
## 2026-08-15 — Pilot run #2 (valid) COMPLETE: verdict MUTATE (ceiling), stop conditions 1+4 triggered

results already seen? YES (run #2 results seen; run #1 void)

run #2 (65 min, A6000, Qwen3-VL-8B @ 0c351dd0, freeze 91185d7, harness
cdc80b7): all six arms 0.9861 val; held-out V o H = 1.0000 for ALL five
causal arms incl. wrong_geometry; z-corrupted = 0.5 everywhere (causal
path PASS); lambda selection -> 0.1 for all three structural arms.

stop conditions: 1 TRIGGERED (equiorient does not beat augmentation/
output-consistency behaviorally); 2 NOT MEASURABLE (latent equivariance
error missing from harness — frozen metric gap); 3 PASS (ablation
1.0->0.5); 4 TRIGGERED (correct rho == wrong rho behaviorally).

verdict: MUTATE the held-out test — V o H composition is at ceiling for
every arm (closed answer-level algebra; augmentation alone composes it),
so the pilot has no discriminative power. This is a falsification of the
TEST DESIGN, not of EquiOrient. Candidate mutations (order recommended):
B first — implement frozen latent metrics (latent_equivariance_error_VoH,
paired_both_correct_VoH) and re-run same design (~1h GPU, zero protocol
change); then A — held-out depth relation family (head to 6 classes,
Amendment C) if B does not discriminate; C (unseen transform class)
reopens Gate-1 algebra — heaviest, last.

affected frozen artifacts: none changed; adds PILOT_REPORT.md + pilot_run
artifacts. Harness metric gap documented; harness to be completed before
any further GPU run.

confirmatory or exploratory: one-seed falsification pilot (Phase-1 scope
per Amendment B1); result is NOT final-paper evidence.

---
### 2026-08-15 (cont.) — Harness metric gap closed (Option B, zero protocol change)

The two missing frozen primary metrics are now implemented and verified
(local --tiny PASS): eval_voh_deep() computes, per causal arm, exactly
once after selection on the held-out V o H:
- paired_both_correct_VoH = P(normal-correct AND transformed obeys the
  law), joined per pair on the same object ids across identity and
  v_after_h images of the same holdout scene;
- latent_equivariance_error_VoH = mean || rho(V o H) z(x) - z(Tx) ||^2
  with the CORRECT predeclared rho (0 iff z obeys the algebra on the
  unseen composition).

Re-running the same pilot design (run #3) to obtain the complete frozen
metric matrix. Behavioral ceiling expected to persist; discrimination,
if any, must come from the latent/both-correct columns. No change to any
frozen scientific parameter.

---
## 2026-08-15 — Amendment C APPROVED (orchestrator): held-out relation-family test via depth probe

results already seen? run #2 results seen (ceiling verdict); run #3 (metric
completion) ABORTED mid-flight and superseded by run #4 — no partial
scientific output existed (matrix written only at completion).

amendment (pre-result, logged): the frozen behavioral primary test (held-
out V o H composition) is at ceiling and has no discriminative power; per
the Gate-4 MUTATE verdict and orchestrator approval, the held-out test is
EXTENDED (not replaced) by a representation-transfer test:
- depth probe: after each causal arm's selected-lambda training, fit a
  logistic-regression probe on z (concat of the four typed blocks) from
  VALIDATION-scene depth pairs (identity images; labels in_front_of/
  behind, 816 pairs available in the manifest); evaluate on HOLD-OUT-scene
  depth pairs. Depth labels never appear in training supervision.
- prediction: EquiOrient's rho keeps z_d invariant under H/V, so L_eq
  forces z_d to carry depth geometry -> probe transfers; controls without
  rho shaping stay near chance.
- NO change to: backbone, revision, PairEncoder/z spec, head, losses,
  training data, seeds, lambda rule, stop conditions. Purely additive
  evaluation (harness-only + scikit-learn added to provisioner).

affected frozen artifacts: none reopened; harness + provisioner gain the
probe; run #4 = same design as run #2 + latent metrics + depth probe.

confirmatory or exploratory: pre-result amendment to the pilot test
protocol; still Phase-1 one-seed falsification scope.

---
### 2026-08-15 (cont.) — Run #4 ABORTED (operational): stale provisioner on the box

run #4 (metric-complete + probe) aborted at the first depth-probe call:
ModuleNotFoundError: sklearn in the venv. Root cause: the box executed the
stale ~/setup_equiorient.sh (curl'd at staging, before scikit-learn was
added to the provisioner); my earlier box-side import check used the
system python, not the venv, and gave a false green. No matrix was
written -> no scientific output lost; partial logs archived as
pilot_run_run4_ABORTED. Fixed by re-curl'ing the provisioner (venv pip now
installs scikit-learn 1.9.0) and relaunching as run #5. Lesson encoded:
the on-box pre-flight must verify the VENV imports (python = /bin/
python), not system python.

---
## 2026-08-15 — FINAL: run #5 complete, Phase-1 pilot verdict = KILL as designed; compute CLOSED

results already seen? YES (run #5 = final complete matrix; runs #1-#4
void/aborted as logged)

run #5 (69 min; oc/lat λ=1.0, eq λ=10.0): all arms 0.9722 val; held-out
V o H 1.0000; z-corr 0.5 (causal path PASS); both_correct 0.9444-0.9722;
latent_eq_err_VoH equiorient 10.309 vs controls 10.370/10.384/10.392
(no meaningful drop -> stop 2 TRIGGERED); depth_probe_holdout 0.6111 for
ALL arms incl. wrong_geometry (stop 4 TRIGGERED, Amendment C probe does
NOT discriminate; the common 0.6111 = generic depth signal from answer-
path training, zero EquiOrient contribution).

verdict: KILL Phase-1 design as tested — no support on any frozen
criterion (stops 1, 2, 4 triggered; 3 is sanity-only). NO Gate-6
multi-seed, NO external validation on this design. Compute budget for
this account EXHAUSTED; instance deleted 06:10 UTC (billing stopped);
snapshot equiorient-pilot-provisioned-run5 retained. GPU stays OFF until
explicit orchestrator unlock + fresh budget.

open (zero-compute, for a future budget, NOT promised): a harder regime
(richer scenes / longer training / non-closed held-out structure) could
re-test EquiOrient; candidate paper stories per guide s12 are the
negative-result framings. No action taken.

---
### 2026-08-15 (cont.) — Harness compute optimizations (Modal migration, zero protocol change)

Per orchestrator directive (don't waste pay-per-second compute on idle or
under-utilization), profiling run #5 (4146s) showed the hot spots:
~43% = per-pair vision forwards (each image forwarded ~12x, once per pair),
~9% = duplicate PIL/processor calls per pair, evals re-extracting
features per call. Three protocol-neutral fixes:
1. image_input(): processed pixel tensors are LoRA-independent -> cached
   for the whole run (kills ~12k duplicate processor calls).
2. train_run steps group pairs by image: ONE vision forward per unique
   image per step, shared autograd graph (vision-LoRA gradients still
   flow, Amendment B4 preserved); ~20% wall-time cut.
3. vision_features(requires_grad=False) + per-arm feature cache (reset at
   each train_run) -> all evals (val, holdout, corrupted, voh_deep, depth
   probe) reuse features: evals become near-free.
Expected: run time ~69 min -> ~45-50 min. Verified: py_compile + --tiny
PASS (tiny now exercises the gradient path on CPU, more faithful gate).
No change to any frozen scientific parameter, loss, data, or seed.

---
## 2026-08-15 — Amendment D APPROVED + IMPLEMENTED (harder regime, D1 only)

results already seen? YES (run #5 = definitive ceiling/pilot evidence that
motivates D)

decision (orchestrator-approved, 2026-08-15): harder-regime re-test.
- D1 (IN SCOPE): scene recipe v2 — 5 objects (3 rects + 2 lines, size
  variance), seed 20260815, artifact results/equiorient/pilot_data_v2,
  20 ordered pairs/image vs 12; algebra law re-verified (10,880 checks,
  0 violations); scene split ids unchanged (10/4/3).
- D2 (DEFERRED): epochs 6 dropped — budget math (6 objects x 6 epochs ~
  5x v1 compute ~  pilot /  Gate 6) exceeds the /mo Modal
  credit and the continuous-run principle; D1 isolates the difficulty
  variable.
- Freeze artifact: configs/equiorient_pilot_freeze_v2.yaml (v1 contract
  byte-identical except data recipe/seed + decision-rule block).
- Harness: unchanged; local gates PASS (py_compile, law check, --tiny on
  v2 data, freeze v2 YAML parse).
- Compute platform: Modal (serverless, /mo credit) — scaffold
  modal/equiorient_modal.py clones the repo from origin at a PINNED
  commit inside the sandbox (no local mounts), L40S with A100-40GB
  fallback, HF cache + results Volumes, hf-token secret updated to the
  ROTATED HF token.
- Decision rules predeclared in the v2 YAML: PROCEED (EquiOrient beats
  controls on held-out V o H and/or depth probe >= +0.15) / KILL (flat).

affected frozen artifacts: adds datasets.make_scene_v2/generate_pack_v2,
build_pilot_data.py --v2, freeze v2 YAML, pilot_data_v2, modal scaffold;
v1 frozen artifacts untouched.

confirmatory or exploratory: pre-result amendment; still Phase-1
one-seed falsification scope.

---
## 2026-08-15 — Amendment D pilot (Modal L40S, v2 harder regime) COMPLETE: verdict KILL (definitive)

results already seen? YES (Amendment D run = second valid regime, first
Modal run)

run (536 s on Modal L40S — ~20x faster than the A6000 runs thanks to the
harness optimizations; repo commit 6e1c91b): five objects/scene, 600
pairs/arm, epochs 2, all six arms + grid + selection + evals + depth
probe executed. Model = Qwen3-VL-8B @ 0c351dd0, verified in run.log.

results (selected-lambda):
- val: augmentation 0.9833, all others 0.9875; ordinary_sft 0.8917
- held-out V o H: 1.0000 for ALL five causal arms (ceiling persists)
- z-corrupted: 0.5000 everywhere (causal path PASS)
- both_correct_VoH: 1.0000 everywhere
- latent_eq_err_VoH: 20.05/20.17/20.27/20.17/19.96 (equiorient mid-pack;
  no meaningful drop -> stop 2 TRIGGERED)
- depth_probe_holdout: 0.5667/0.5833/0.6000/0.5833/0.5833 (all within
  binomial noise of chance; no arm exceeds controls by >= 0.15; stop 4
  TRIGGERED; equiorient 0.5833 == wrong_geometry 0.5833)

verdict per the predeclared Amendment D rules: KILL. The harder visual
regime did NOT break the behavioral ceiling and did NOT create any
discrimination: EquiOrient == controls on every metric in a SECOND
regime (v1 algebra-closed + v2 harder scenes + Amendment C depth probe).
Phase-1 falsification is now definitive across regimes.

consequences: NO Gate-6 multi-seed, NO external validation. GPU work for
EquiOrient is CLOSED. Modal billing ended with the sandbox (pay-per-
second); total compute spend this Amendment D run < .50, well within
the  credit. Volumes retained (model cache ~free); nothing running.

affected frozen artifacts: none changed by the result; artifacts added
(pilot_run_v2_modal/). Harness, v2 freeze, scaffold unchanged.

confirmatory or exploratory: Phase-1 one-seed falsification (Amendment
B1 scope); definitive negative for the tested design.

---
## 2026-08-15 — CRITICAL: manipulation-check failure — ALL structural losses were identically zero; prior pilots VOID as tests of the equivariance hypothesis

results already seen? YES (all prior runs; discovered during the Gate-8
hostile review, statistics/leakage reviewer)

finding (verified against pilot_harness.py at both cdc80b7 and the
Amendment D tip): train_run computed ztx = rho o z from the SAME z
(no transformed-image features ever forwarded), so:
- equivariance: sum((rho_i z_i - rho_i z_i)^2) = 0 identically
- wrong_geometry: same construction = 0
- latent_invariance: ztx = z -> (z - z)^2 = 0
- output_consistency: mse(logits, logits.detach()) = 0 (same values)
The intended laws require the pair state on the TRANSFORMED image
z(Tx); the harness never computed it. All four structural arms trained
as clones of augmentation-only (modulo fp noise). The lambda grid, the
flat latent errors, and the flat depth probes are all consistent with
five identical runs, not five manipulated conditions.

also confirmed: rel_label assigns left/right before above/below and every
ordered pair carries an x-relation -> the 4-class head is effectively
binary (0 above/below labels in either manifest); the held-out V o H
composition is answer-identical to the seen H transform for left/right
labels, so the behavioral composition test is degenerate by construction;
and the causal ablation's 0.5000 is the head's bias-only decode on
balanced binary labels (NOT chance for a 4-class head).

decision:
1. All GPU runs to date are VOID as tests of the equivariance hypothesis
   (runs #2, #5, Amendment D). They remain valid only as (a) evidence
   that augmentation-only saturates the binary task, and (b) causal-path
   plumbing evidence. No scientific claim about EquiOrient may be made
   from them. The earlier 'KILL' verdicts are withdrawn and replaced by
   'treatment never administered'.
2. Harness corrected (2026-08-15, same commit stream): structural losses
   now use the paired formulation — z(x) from the scene's IDENTITY image
   and z(Tx) from the transform image (identity features grouped per
   scene per step, gradients preserved, Amendment B4):
   - equivariance: ||rho(tr) z(x) - z(Tx)||^2
   - wrong_geometry: ||wrho(tr) z(x) - z(Tx)||^2
   - latent_invariance: ||z(x) - z(Tx)||^2
   - output_consistency: mse(logits_Tx, law_perm(logits_x).detach()),
     law_perm from expected_after on the head classes
3. MANIPULATION CHECK added (the failure class that escaped every prior
   gate): per-epoch mean structural loss is logged and ASSERTED > 1e-6
   whenever lam > 0 (tiny gate now catches zero-loss implementations).
   Per-epoch answer/structural loss curves recorded in the matrix.
4. Depth probe extended: full-z AND z_d-block-only probes (the
   invariance structure claim needs the z_d component specifically).
5. Re-run required: corrected pilot (Modal L40S, ~10-12 min, <).
6. Paper: rewritten AFTER the corrected run; binary-task disclosure,
   honest ablation language (bias decode), step-budget disclosure,
   n + binomial CIs, per-lambda table, loss curves, corrected
   bibliography (unverifiable entries dropped, HAE/SAGE added).

affected frozen artifacts: none frozen changed by the finding; harness +
paper to be corrected; v1/v2 freeze YAMLs remain the protocol contract
(the losses are now IMPLEMENTED as the contract specifies).

confirmatory or exploratory: implementation-correction; the corrected run
is the first VALID test of the equivariance hypothesis.

---
## 2026-08-15 — Corrected write-up COMPLETE: paper (v2) + Regime A replication + hostile-review resolution

results already seen? YES (corrected runs)

corrected pilots (Modal L40S, harness with paired x/Tx structural losses +
manipulation check):
- v2 regime (5-object scenes, 704 s): manipulation PASS (equiorient struct
  loss 0.0156 -> 0.0132; answer loss 7.46 -> 1.24). Latent algebra
  compliance: rho_H 0.033 / rho_V 0.006 / held-out rho_VH 0.045 vs
  augmentation 14.9/12.0/14.7 (325x); correct-vs-wrong contrast sharp
  (equiorient wrong-H 4.89 vs wrong_geometry wrong-H 0.020); wrong_geometry
  obeys ITS law per-transform; composed wrong law == correct on V o H
  (0.026) as predicted by axis-symmetry. No downstream: depth probes flat
  (0.53-0.55 full, 0.52-0.55 z_d), behavioral ceiling (binary task).
- v1 regime (4-object scenes): replication — equiorient rho_H 0.120 /
  rho_V 0.105 / rho_VH 0.172 vs augmentation 10.36 (60x); wrong_geometry
  own-law 0.112; probes flat (0.50-0.61).

hostile review (Gate 8, three independent reviewers) resolved: numbers
machine-verified; the zero-structural-loss class voided prior runs (logged
above); bibliography corrected per the gate records (HAE keurti2023hae,
GASP yeh2026gasp per gate, SAGE 2605.18162, Consistent Yet Wrong
2606.02742; unverifiable entries dropped); binary-task disclosure added;
causal ablation reframed as bias-decode plumbing check; per-lambda and
step-budget caveats disclosed; n + binomial CIs stated; per-transform and
per-block(z_d) metrics added.

paper: paper/main.tex -> main.pdf (tectonic, WACV style, anonymous);
all numbers machine-generated from committed matrices
(paper/extract_numbers.py -> numbers.tex; 178 macros).

scientific position (final): representation-level algebra compliance is
achievable, specific (correct-vs-wrong), and replicable across two scene
regimes, but it did not transfer to behavior (algebra-closed binary task
ceiling) or to a held-out relation family (depth probe flat). Mechanistic
negative per the execution guide's allowed story.

compute ledger (Modal): 3 GPU runs (corrected v2, corrected v1, plus the
voided zero-loss runs earlier) ~35 min L40S total, <  of the  credit.

---
