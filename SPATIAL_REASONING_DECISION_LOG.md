# SPATIAL_REASONING_DECISION_LOG

Chronological, append-only record of decisions made for the spatial-reasoning
research line. Entries are stamped exactly when the described decision is
made. "FROZEN BEFORE TRAINING" entries bind the artifact versions they cite.

---

## 2026-08-11 - Seed Campaign pre-registration (FROZEN BEFORE TRAINING)

**Decision.** Re-train the two general-VSR LoRA backbones
(Qwen2-VL-7B-Instruct, SmolVLM2-2.2B-Instruct) under three fresh random
seeds (A=101, B=202, C=303) with every training-run input identical to the
respective seed-0 runs EXCEPT the seed. Three user-approved choices:

1. **Battery**: implement + pre-register the full HEAVY battery (normal,
   with_sample 2px, with_shuffle, relcomp <0.3, facing, hflip, hflip_inv)
   under the uniform 392px evaluation contract, evaluated on all six
   checkpoints.
2. **Split frozen at 42**: keep the 95/5 train/val split mapping at
   seed=42 for all runs; only train-time RNG (LoRA init, DataLoader
   shuffle order, dropout) varies with the campaign seed.
3. **Scope**: full 3x2 campaign runs in background; results reported per
   stage.

**Frozen bound artifacts.**
- Full spec: `configs/seed_campaign/SEED_CAMPAIGN.json`
- Battery rationale + contract: `configs/seed_campaign/BATTERY_JUSTIFICATION.md`
- Training recipe sources (verbatim): `scripts/run_7b_pipeline.py` PHASE 2
  (master), `src/training/lora.py` + `src/training/collator.py` (master)
- Seed-0 reference artifacts: `checkpoints/general_lora/final` incl.
  `training_log.json` (2B; epoch losses 0.513/0.414; 6253s),
  `checkpoints/qwen2vl_7b_general_lora/final` (7B; master)
- Manifest (NOT rebuilt): `data/manifests/general_train.jsonl`

**Findings recorded at freeze time.**
- Seed-0 training runs were unseeded; the campaign adds explicit seeds.
- The battery existed only as a spec (aftertrain.md); no implementation
  existed in the repo (all branches searched).
- 2B micro-batch ambiguity (train() signature defaults 4/4 vs CLI defaults
  1/16) resolved to the CLI defaults the seed-0 run used (effective batch
  16 identical either way); verified against seed-0 training_log.json.
- Seed-0 2B reference loss: epoch1 0.513, epoch2 0.414 (adaptation-sanity
  target for new seeds).

**State at freeze: no campaign files existed before this entry**
(configs/seed_campaign/, scripts/run_seed_campaign.py, battery drivers,
results/seed_campaign/ all absent; git tree clean).

---

## 2026-08-11 - Machine closure / handoff (campaign interrupted mid-run)

The cloud device was closed while the seed campaign training queue was
running (7B seedA in training loop; no adapter saved yet). All campaign
artifacts were pushed to origin/research/spatial-grounding-audit along with
configs/seed_campaign/RUN_STATUS.md (full resumption checklist, machine
config notes, pending-work list). Battery drivers were implemented but not
runtime-validated; battery evals + analysis remain pending. Campaign spec,
recipes, seed semantics and progress state are unchanged (frozen entry above).

---

## 2026-08-11 - Local prep session + second handoff (Windows box; 2B seedA aborted)

A local Windows machine (RTX 3060 Ti, 8 GB) was used for authoring/prep work:
- Battery rows built + validated + committed (commit 43e0aa0): counts
  2195/2195/2195/666/103/103/103; fixes to src/evaluation/battery.py
  (frozen vsr_test_ids.json id loader; entries-dict eligible-ids shape).
- Local env brought up: CUDA torch 2.8.0+cu128 on the 3060 Ti, image cache
  (1874 unique images, 0 missing), SmolVLM2-2.2B cached, peft/num2words deps.
- 2B seedA (seed=101) training was STARTED locally and ABORTED at ~2h
  (no checkpoint saved; driver saves first at step 100/238). Reason: 3060 Ti
  throughput >65 s/step (est. 5-8 h/seed) vs 26 s/step on the A6000; running
  all campaign seeds on one machine also keeps the seed-0 (A6000) comparison
  free of a hardware confound. Decision: ALL training/eval moves to the GPU
  cloud box (A6000); local box is prep/analysis only.
- Handoff: handoff.md (full resume checklist + exact commands). Aborted run
  logs committed for audit (results/seed_campaign/runs/smolvlm2_2b_seedA.log).

---

## 2026-08-11 - Protocol correction: drifted battery retracted, frozen legacy Tier-A/B/C battery reinstated (FROZEN BEFORE EVALUATION)

**Discovery (code audit).** The battery committed for the seed campaign
(`results/seed_campaign/rows/*.jsonl`, `src/evaluation/battery.py`,
`scripts/eval_seed_battery.py`, plus `shuffle_mapping.json` in
`results/seed_campaign/`) drifts from the frozen Paper-2 protocol despite the
labeling in `configs/seed_campaign/SEED_CAMPAIGN.json`:

1. The condition labeled `with_sample` applies a **wrong-image** substitution
   (2px-shifted off-by-one image indices) instead of the frozen Paper-2
   WITH_SAMPLE mask sampling.
2. The shuffles were **re-hashed** with a different seed/domain than the
   frozen protocol permutation (`results/grounding/protocol/shuffle_mapping
   .json`, verified at load by `src/grounding/shuffle.py`), so
   `with_shuffle` rows do not implement the protocol's wrong_image_shuffle.
3. The uniform **392px evaluation cap** is not part of the frozen protocol
   (G1: same-size no-rescale; G2: 2x upscale; hflip: no-rescale), and the
   heavy-battery extras (with_sample, with_shuffle) are not protocol
   conditions.

**Decision.** Retract the drifted battery from any reportable result. No
fresh-seed output was produced by it (nothing farther than engineering
counts), so nothing needs to be deleted: the drifted files are preserved
verbatim as audit history (no deletion, no rewrite; `--allow-drifted` escape
hatch only). The corrected battery is the **already-committed legacy
Tier-A/B/C protocol**, reused unmodified:

- Tier-A: `normal` (2195) + wrong_image_shuffle via the legacy shuffle
  derangement (frozen `shuffle_mapping.json`, verified on load).
- Tier-B: `relcomp` (strict complement pairs, 0 < semantic dist < 0.3, run
  with its eligible-id inclusion) and `facingcomp` (facing-antonym pairs,
  must run alone per its freeze).
- Tier-C: `hflip_flip` (reflection; image+language flip, L/R truth flips)
  and `hflip_invariant` (reflection; vertical/depth truth stable), via the
  PIL FLIP_LEFT_RIGHT lane with language held.

Configuration pins (from committed run metadata): batch-size 8 for both
families; attn **eager** for 7B; attn **sdpa** for 2B (amendment recorded
above in this log; probe verified 0/32 outputs differ eager vs sdpa).

**Regression mandate.** `scripts/grounding/regress_seed_battery.py` reruns
the corrected battery on the existing adapters (7B: zero_shot /
general_lora / hardneg_lora; 2B: zero_shot / general_lora) and must
reproduce the already-committed legacy Tier-A/B/C metric files before any
fresh-seed battery evaluation. The corrected battery is then frozen in a new
commit, and ONLY afterwards are the campaign(checkpoint x condition) cells
evaluated.

**Frozen bound artifacts (all already committed).** the legacy drivers
(`scripts/grounding/run_tier_{a,b,c}.py`, `analyze_tier_{a,b,c}.py`),
`src/grounding/{shuffle,semantic,visual,eligibility,config}.py`, `results/
grounding/protocol/` IDs + shuffle permutation, `results/grounding/analysis/
tier_*_metrics_*.json` regression targets, this entry + deprecation marks.

**Status at this entry (untouched by evaluation):**
- Training pipeline continues (2B seedA final; seedB training in progress;
  seeds C + 7B A/B/C queued) with all hyperparameters inputs unchanged.
- No fresh-seed battery evaluation has been run or inspected.

At commit: ff51ab55 (research/spatial-grounding-audit).

---

## 2026-08-12 - Training incident: 2B seedB deadlock at first backward (root cause still open)

**Symptom.** Every `run_seed_campaign.py` 2B invocation after seedA (seedB,
3 attempts + 1 launcher-variant attempt, all with seed=202) freezes at the
FIRST `loss.backward()`: all 54 threads futex-waiting, 0% GPU, zero IO,
log frozen after the first autocast FutureWarning. seedA (same driver,
same seeds contract, ran 18:59-21:04 UTC) completed normally.

**Proven facts.**
- SIGUSR1 faulthandler stack dump (env PYTHONPATH=/tmp/opencode registers
  sitecustomize.py): main thread stuck in
  `torch/autograd/graph.py:_engine_run_backward` while a second thread is
  inside `torch/utils/checkpoint.py:backward` — circular wait between the
  autograd engine and the gradient-checkpointing recompute worker.
  Deadlock is at lora.py:189 `loss.backward()`, i.e. NOT collate/forward/
  data/network (all 2000 cache images verified present, hub mirror flaky
  period ruled out).
- Negative results: wedge reproduces with GPU free, with GPU shared, with
  `PYTHONPATH`/`PYTHONUNBUFFERED`/nohup/foreground, with a module-level-
  import launcher variant (scripts/run_seed_campaign_launcher.py, kept as
  diagnostic artifact: import order is NOT the cause).
- 8/8 probe-shaped training runs passed (n16/n64/n256/n512/n1024/n2000 and
  env/bg variants), including the FULL 2000-row manifest with the exact
  seeds/recipe (epochs=1). 5/5 driver-shaped runs failed. The only untested
  structural delta at the failing point was epochs=2 (+eval_every=100),
  which cannot mechanistically affect a first backward; investigation
  stopped here pending a box reboot + driver/stack re-check.

**Status / next steps (not yet executed).** Reboot the box, re-test
{epochs=2, n64}; if the trigger persists, test with gradient checkpointing
disabled (mathematically identical outputs, but a recipe deviation that
requires approval) and/or upgrade/downgrade torch. 7B legs never ran
post-fix (queued seedA/B/C failed rc=1 with TypeError before ff51ab5).

**Untouched by this incident:** battery correction + regression harness
(frozen, commit 88f5da2), control/eligibility files, and all seed-0
artifacts. No training inputs/recipe changed; no fresh-seed battery
evaluation has been run.

---

## 2026-08-14 - R1 seed campaign COMPLETE: all 5 training runs + both gates + both batteries + Qwen3-VL extension

**Compute executed (3x A6000, Thunder Compute; instances since deleted):**
- Training: 7B seedA/B/C (101/202/303) + 2B seedB/seedC — all 5 completed.
  2B seedB deadlock (2026-08-12 entry) did NOT recur on the fresh box:
  full 3800-step 2B runs completed with the identical driver.
- Regression gate: PASSED for both families (0 mismatches vs committed
  legacy outputs; qwen2vl + smolvlm2) — corrected battery verified.
- Fresh-seed batteries: qwen2vl (6 ckpts x 6 conds) + smolvlm2 (5 ckpts x 6
  conds) completed; all analysis artifacts committed under
  results/grounding/analysis (r1_campaign tags).
- Post-confirmatory extension: Qwen3-VL-8B-Instruct general LoRA trained
  (3800 steps, r=8/a=16, split seed=42) + evaluated on normal/shuffle/
  hflip_flip/hflip_invariant/relcomp. Labeled exploratory architecture
  extension, NOT preregistered (orchestrator guidance 2026-08-13).

**Key results (full tables in results/seed_campaign/ANALYSIS.md):**
- dA: +5.4 pts (7B seed-0), +4.6..5.5 (7B seeds), +2.9..3.2 (2B), +3.2
  (Qwen3-VL) — benchmark gain replicates across every seed/backbone.
- dG (correct-image dependence, normal-shuffle gap): widens under tuning in
  all families (7B 0.352 seed-0 / 0.344-0.354 seeds; 2B 0.298 / 0.296-0.301;
  Qwen3-VL +0.036).
- Visual response (hflip_flip flip-rate): monotonic improvement across fresh
  2B seeds (0.298 -> 0.306/0.314/0.322), tight replication in 7B (0.657
  seed-0 vs 0.649/0.657/0.645), +0.045 in Qwen3-VL.
- dC (relcomp C_pair): seeds cluster tightly around seed-0 in both families
  (7B 0.655-0.665 vs 0.677; 2B 0.498-0.511 vs 0.502).
- All checkpoints + training logs pushed to origin/research/
  spatial-grounding-audit (commit 2ef4f3c); raw battery artifacts archived
  locally in results/seed_campaign/cloud_artifacts/.

**Framing decisions (per orchestrator literature review 2026-08-13):**
- Novelty claim = three-way training-effect decomposition (dA/dG/dC under
  ordinary spatial fine-tuning, multi-seed, cross-backbone) — NOT the
  normal-vs-shuffle gap itself (Beyond Accuracy 2026 defines VRS
  identically).
- hflip metrics reported as collapse-style paired answer-update metrics
  following VisualFLIP (Zhu et al. 2026); explicitly NOT the VisualFLIP
  protocol (global reflection vs minimal local edit). VisualFLIP official
  dataset gated; re-check before deadline.
- facingcomp contributes to dC (semantic), never sold as visual
  counterfactual.
- Qwen3-VL-8B labeled post-confirmatory external validation, motivated by
  reviewer/relevance concerns (VisualFLIP Table 1 provides the published
  zero-shot reference row).

### 2026-08-14 (cont.) - Reporting correction (no compute, no reruns)

Orchestrator audit caught a numerical/labeling inconsistency in the initial
ANALYSIS.md: the 2B synthesis quoted both_correct values (0.298->0.306/
0.314/0.322) while calling them flip-rates, and the tier-c tables labeled
direction_by_checkpoint["C"] (== A_transform) as C_pair. Corrected in
commit: tier-c tables now read summary_by_checkpoint["C_pair"] (true paired
metric); synthesis distinguishes A_transform (flip rate) from both_correct,
and G (normal-minus-shuffle gap) from dG (= G_tuned - G_zero_shot)
throughout. All numbers re-derived from raw prediction artifacts by
scripts/grounding/analyze_seed_campaign.py.

### 2026-08-14 (cont.) - Terminology correction (zero-GPU bookkeeping)

Orchestrator audit: the reporting layer still inverted the frozen metric
semantics in prose. Corrected (analyze_seed_campaign.py regenerates
ANALYSIS.md from raw artifacts):
- A_transform = P(transformed prediction == expected transformed label):
  TRANSFORMED-ANSWER ACCURACY (never "flip rate").
- C_pair = P(pair consistency): linked-answer law compliance; hflip_flip =
  P(mirrored != normal) (response flip / answer-update rate); hflip_invariant
  = P(mirrored == normal) (response-stability rate). (frozen definitions in
  analyze_tier_c.py docstring.)
- both_correct = P(normal-correct AND transformed obeys the law).
- Removed "monotonic across seeds" (seeds are independent draws, not ordered
  stages); fresh-seed statements now report ranges.
- Qwen3-VL extension scoped to A_transform only (C_pair NOT computed for the
  extension; no response-law-compliance claim made). The +0.0449 is a
  transformed-accuracy gain.
Story unchanged: dA and dG remain the seed-robust headline; Tier C reports
three separate transformation-behavior quantities.
