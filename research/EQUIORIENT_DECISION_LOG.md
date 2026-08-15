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
