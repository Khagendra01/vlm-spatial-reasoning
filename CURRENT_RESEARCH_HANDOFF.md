# CURRENT RESEARCH HANDOFF REPORT

Audit date: 2026-08-10 (UTC). Auditor: autonomous agent inspecting the live repo.
IMPORTANT CONTEXT: at audit time, a SITE zero-shot evaluation is RUNNING on the
GPU (image subset, ~75% through). Everything below reflects the live state.

---

## 1. EXECUTIVE STATUS

The repository is a VLM spatial-reasoning research project that has drifted
from its originally planned paper scope (2B + 7B base-vs-LoRA behavioral
grounding audit) into a deeper, 7B-only orientation causal-decomposition
program, now culminating in external validation on SITE (ICCV 2025).

- **IMPLEMENTED + TESTED**: SmolVLM2-2.2B zero-shot baseline; structured-prompt
  variant; 2B General/Targeted LoRA train+eval; Qwen2-VL-7B zero-shot; 7B
  General/Targeted/Hard-negative/Projector/Vision+Projector LoRA trains+evals;
  orientation failure annotation/audit; representation probes (global, patch,
  object-grounded); two-stage explicit reasoning; logical-consistency
  (complement-flip) analysis; SITE loader + inspection + preregistered
  evaluation protocol.
- **VERIFIED**: dataset statistics (train 7,680 / dev 1,097 / test 2,195;
  64 relations; near-balanced labels); VSR image loading works; all checkpoint
  adapters load (used in evals); SITE media (8,086 files) downloaded; SITE
  eval script smoke-tested and currently running.
- **NOT IMPLEMENTED**: nearly all of the PLANNED PAPER's grounding-audit
  conditions (text-only, blank image, shuffled image, relation inversion,
  subject/object reversal, horizontal reflection); VSR zero-shot/config-shift
  split (does not exist in the dataset and no loader support); controlled OOD
  audit; MiMo integration; paired base-vs-tuned grounding metrics; seed
  variation (single seed everywhere); 2B→7B paired transfer analysis.
- **PARTIAL**: the planned "2B + 7B" paper is partially covered (both models
  have baselines and LoRAs on VSR test) but the intended behavioral
  decomposition (before-vs-after grounding gain) is absent.
- **BROKEN / UNVERIFIED**: `scripts/fetch_site_ranges.py` (superseded,
  contains known ZIP64/multipart limitations); flash-attn install (failed on
  CUDA 13); `datasets` v5 API change ("dev" split no longer exists — it is
  "validation"); no test suite exists at all.
- **IMMEDIATE NEXT EXPERIMENT (running)**: SITE 7B zero-shot image-subset
  evaluation (preregistered protocol) → then report metrics and decide
  whether the VSR-trained 7B LoRA is justified on SITE.

---

## 2. REPOSITORY STRUCTURE

Root: `/home/ubuntu/vlm-spatial-reasoning` (git repo, branch `master`).

```
├── README.md                     # Stub README (structure only, no usage)
├── requirements.txt              # Dependencies (stale: python3.10/conda-era)
├── .gitignore                    # python/dataset/media exclusions
├── .intro.md.un~, intro.md~      # editor droppings
├── aftertrain.md, leadfromhere.md, transferfromgp.md   # 200-600KB context dumps
├── configs/└── README.md         # empty stub (no real configs anywhere)
├── notebooks/exploratory_analysis.ipynb
├── paper/└── README.md           # empty stub
├── figures/                      # empty
├── data/
│   ├── image_cache/              # 703MB cached VSR images (md5(url).jpg)
│   ├── site_media/               # 43GB SITE media (extracted, gitignored)
│   └── manifests/                # general/targeted/hardneg_train.jsonl (2000 rows each)
├── src/
│   ├── datasets/vsr.py           # VSR loader + stats helpers (4274 B)
│   ├── datasets/site.py          # SITE (ICCV 2025) loader + orientation heuristic
│   ├── evaluation/parser.py      # True/False output parser (96 lines)
│   ├── models/smolvlm.py         # SmolVLM2-2.2B wrapper (ONLY model wrapper)
│   ├── training/lora.py          # SmolVLM2 LoRA training (2B)
│   ├── training/collator.py      # VSR collator (loss on answer tokens only)
│   └── training/build_train_sets.py  # builds 2000-ex manifests from VSR train
├── scripts/                      # 40+ scripts (see §30/§31 for key ones)
├── results/                      # all experiment outputs (see §12)
└── checkpoints/                  # 2B + 7B LoRA adapters (see §18)
```

Note: `tests/` does not exist. No formal experiment configs; hyperparameters
live in script defaults/CLI flags.

---

## 3. GIT STATE

- Branch: `master`; HEAD: `b8336bb8d73ebc77c0eff73c336ffc8b2a65c455`
- Working tree: NOT clean — `results/site/zeroshot_7b_predictions.csv` is
  modified (the running SITE eval appends to it; expected).
- No other untracked/modified files (site_media + image_cache gitignored).
- Recent commits (oldest→newest): `2d732cd` orientation deep-dive per-relation;
  `4b83729` 48-failure annotation taxonomy; `9fc694f` hard-negative LoRA
  ablation; `9d9c50c` representation probe; `fa9d0be` object-grounded probe;
  `a0d50ca` clear-subset label-noise check; `f1bc14f` vision-side LoRAs;
  `1e83604` two-stage reasoning; `6bf8b84` logical consistency; `10494bf`
  SITE loader; `8d7f173` SITE preregistration; `b8336bb` SITE eval protocol
  update (current HEAD).
- Not yet committed: in-flight SITE predictions CSV; final SITE metrics (when
  the run finishes).

---

## 4. HARDWARE AND SYSTEM ENVIRONMENT

- GPU: 1× NVIDIA RTX A6000, 49,140 MiB VRAM (verified)
- GPU current: ~24 GiB used, 100% util (SITE eval running), ~296W/300W, 67°C
- Driver: NVIDIA-SMI 610.43.02, CUDA UMD 13.3
- CPU: Intel Xeon E5-2683 v4 @ 2.10GHz, 6 online vCPUs (0-5; 58 offline)
- RAM: 48 GiB (25 GiB free, 20 GiB buff/cache)
- OS: Ubuntu 24.04, kernel 6.17.0-35-generic; Python 3.12.13
- Disk: 200 GiB overlay, 124 GiB free (77 GiB used; 43 GiB = site_media)
- CWD: `/home/ubuntu/vlm-spatial-reasoning`

Matches the expected spec (A6000 48GB / 6 vCPU / 48GB RAM) — confirmed.

---

## 5. PYTHON / ML ENVIRONMENT

Key installed versions (pip, user site):

- torch 2.12.1+cu130, torchvision 0.27.1+cu130
- transformers 5.14.1 (very new; several 4.x APIs changed)
- datasets 5.0.1 ("dev" split no longer exists; it is "validation")
- peft 0.20.0, accelerate 1.14.0, safetensors 0.8.0
- numpy 2.5.0, pandas 3.0.3, scipy 1.18.0, pillow 12.2.0, pyarrow 25.0.0
- av 18.0.0 (video decoding; torchvision.io.read_video is BROKEN here)
- matplotlib 3.11.0, PyYAML 6.0.3, tqdm 4.70.0
- ABSENT: bitsandbytes, trl, flash-attn (install failed on CUDA 13), cv2, decord

Issues:
- `requirements.txt` is stale (conda/python3.10-era, outdated pins, lists
  opencv/timm/rouge/cider/wandb that the repo does not use).
- transformers 5.14.1: Qwen2VLProcessor has no `enable_grounding`; video
  loading defaults to torchcodec→torchvision (broken) — must pre-decode with
  `av` (as `scripts/eval_site_zeroshot.py` does).
- No lock files / pyproject / env YAML.

---

## 6. DATASET IMPLEMENTATION

`src/datasets/vsr.py` loads `cambridgeltl/vsr_random`. Split mapping caveat:
the wrapper maps "dev"/"validation"→"dev", which now RAISES under datasets 5.x
(actual HF split name is "validation"). Use split="validation" directly.

Verified stats (fresh load):
- train 7,680; validation 1,097; test 2,195
- train labels: 0→3,804, 1→3,876 (≈ balanced)
- 64 unique relations; top: touching 884, in front of 528, behind 498, under
  415, on 408, on top of 349, at the right side of 335, at the left side of 273
- Raw fields: image (filename), image_link (URL), caption, label (int),
  relation, annotator_id, vote_true/false_validator_id, reference_frame
- Wrapper returns: image (URL string), statement (=caption), label (bool),
  relation, subject, object
- Subject/object are PARSED by splitting the caption on " is " (heuristic;
  fails on plurals/"are" and non-standard templates)
- Images load via `data/image_cache` (md5(url).jpg); loading verified by evals
  (0 invalid outputs on 2B/7B full runs)
- No transforms; seeds: np.random.seed(42) in run_baseline.py only
- No zero-shot/config-shift split exists in this dataset

---

## 7. DATA LEAKAGE / SPLIT AUDIT

- Training manifests (general/targeted/hardneg) are built ONLY from the VSR
  **train** split (`src/training/build_train_sets.py` L243;
  `scripts/build_hardneg_manifest.py` reads manifests + train-split audit).
- All evaluation scripts load split="test" only (run_7b_pipeline.py L119/533,
  run_7b_hardneg_pipeline.py L316, eval_lora.py L115).
- Hard-negative flips: syntactically generated (relation flip + label flip)
  from train examples; audit "exclude" examples dropped from originals and
  negatives.
- Probes: train on audited-clean VSR train; eval val+test. Two-stage and
  consistency analyses: train on train, eval on test.
- RISK: low. No test data used for training decisions found. Nuance:
  hard-negative flipped statements share images with originals within the
  same training split (intentional).
- VSR zero-shot split: NOT SUPPORTED (dataset has none; no loader support).

---

## 8. MODEL IMPLEMENTATION

Only ONE wrapper exists: `src/models/smolvlm.py` → `SmolVLMClassifier`.

- 2B: `HuggingFaceTB/SmolVLM2-2.2B-Instruct` (confirmed in use)
  - ~2.2B params, bf16, eager attention, low_cpu_mem_usage, `.to("cuda")`
  - AutoProcessor + apply_chat_template, padding_side=left, padding=True
  - generation: do_sample=False, max_new_tokens=5 (default)
  - TESTED: zero-shot 10/50/200/2195, structured prompt, LoRA evals
- 7B: `Qwen/Qwen2-VL-7B-Instruct` — SELECTED, DOWNLOADED, TESTED, INTEGRATED,
  LoRA-READY (in HF cache `models--Qwen--Qwen2-VL-7B-Instruct`).
  - 8.29B params total; ~16.6GB bf16 weights
  - No dedicated wrapper class; used via inline code in
    `scripts/run_7b_pipeline.py` (zero-shot/LoRA train/eval),
    `scripts/eval_lora.py` (with `--base-model Qwen/Qwen2-VL-7B-Instruct`),
    `scripts/eval_site_zeroshot.py`, probe scripts
  - eager attention, bf16, greedy (temperature 0 / do_sample=False)
  - VRAM observed: ~24GB at batch 1 image inference; ~38GB peaks with long
    multi-image sequences; 48GB fits at batch 8 only for short sequences

No 14B/30B models present. `eval_lora.py` defaults to the 2B model but works
for 7B via `--base-model`.

---

## 9. PROMPT CURRENTLY USED

Two prompt families:

1. Plain (used by 2B wrapper `SPATIAL_PROMPT`, `run_7b_pipeline.py`
   `TRAIN_PROMPT`, `eval_lora.py`, `eval_site_zeroshot.py` prompts are
   separate for SITE):
```
Look at the image carefully.

Statement: "{statement}"

Is this statement true or false?

Answer with exactly one word: True or False.
```
2. Structured decomposition (2B only, `STRUCTURED_PROMPT` in smolvlm.py):
   subject/ref identification → position/orientation steps → same True/False
   constraint.

Properties: no system prompt; no chain-of-thought requested; answer
constrained to one word True/False; deterministic greedy (do_sample=False,
temperature 0, top_p 1.0); max_new_tokens 5 (2B) / 128 (7B pipelines) / 16
(SITE eval, protocol-recorded change from 128, validated result-neutral).

Fairness flag: 2B and 7B use the same plain prompt, so base-vs-tuned
comparisons are internally consistent. The structured prompt (2B only) is a
separate experiment, not a condition of the planned paper.

---

## 10. OUTPUT PARSER

`src/evaluation/parser.py` → `parse_true_false(output) -> Optional[bool]`:

- Normalizes: strip, lower; strips prefixes "the answer is|answer:|response:
  |output:" and trailing punctuation/whitespace.
- TRUE patterns: ^true$, ^yes$, ^correct$, "the answer is true", "this
  statement is true", "it's true", "absolutely", "definitely", ... (regex
  anchored, case-insensitive)
- FALSE patterns: ^false$, ^no$, ^incorrect$, "the answer is false", "this
  statement is false", "not true", ...
- Fallback: if "true" in output and "false" not → True; if "false" in output
  and "true" not → False; both words present → None.
- Returns None (no guessing) on malformed output.

Tested behavior from actual runs: 0 invalid outputs on full 2B/7B VSR evals.
Weakness: "both words appearing" → None (e.g. "The answer is true, not
false"). No unit tests exist. Do not modify without re-validating the
existing CSVs' parse paths.

## 11. BASELINE EVALUATOR

`scripts/run_baseline.py` (2B):
- Args: `--num-examples` (None=all), `--split` (train|dev|test; note dev now
  broken under datasets 5.x — use test), `--output-dir`, `--model`, `--resume`,
  `--batch-size` (default 8)
- Batch 8; incremental checkpointing (saves partial CSV every
  `checkpoint_interval`); parse via `parse_true_false`; metrics include
  global accuracy, per-relation accuracy + Wilson CIs, class breakdown,
  confusion matrix, prediction distribution; seeds np.random.seed(42)
- Actual commands used historically:
  - smoke: `python scripts/run_baseline.py --num-examples 10`
  - 200: `python scripts/run_baseline.py --num-examples 200`
  - full: `python scripts/run_baseline.py` (or with `--model` for variants)

7B equivalents:
- Zero-shot: `python scripts/run_7b_pipeline.py` phase 1 (whole pipeline runs
  zero-shot → LoRA train → eval → analysis; heavy)
- LoRA eval (any model): `python scripts/eval_lora.py --base-model Qwen/Qwen2-VL-7B-Instruct --lora-path checkpoints/qwen2vl_7b_general_lora/final --output-dir results --batch-size 8`

---

## 12. EXISTING EXPERIMENTAL RESULTS

All under `results/`. Verified key outputs (accuracy on VSR test n=2195):

| Experiment | File | Overall acc | Invalid |
|---|---|---|---|
| 2B SmolVLM2 zero-shot | smolvlm2_metrics_2195_20260808_214536.json | 73.99% | 0 |
| 2B structured prompt | smolvlm2_structured_metrics_2195_20260808_225009.json | 68.34% (True 91.3 / False 41.6) | 0 |
| 2B General LoRA | general_lora_metrics_20260809_054915.json | 76.63% | 0 |
| 2B Targeted LoRA | targeted_lora_metrics_20260809_061231.json | 76.54% | 0 |
| 7B zero-shot (A) | qwen2vl_7b_metrics_20260809_064919.json | 80.91% | n/a |
| 7B General LoRA | 7B_general_lora_metrics_20260809_094930.json | 84.69% (orientation 65.7%) | n/a |
| 7B Targeted LoRA | 7B_targeted_lora_metrics_20260809_095926.json | ~84% | n/a |
| 7B Hard-neg LoRA | 7B_hardneg_lora_metrics_20260809_164619.json | 84.33% | n/a |
| 7B Projector LoRA | qwen2vl_7b_projector_lora_metrics_20260809_221720.json | 82.87% | n/a |
| 7B Vision+Proj LoRA | qwen2vl_7b_vision_proj_lora_metrics_20260809_222845.json | 83.10% | n/a |

Orientation per-relation (test, 137 examples): facing 64 (7B zero 73.4 / gen
75.0), facing away 39 (48.7 / 59.0), parallel 22 (63.6 / 63.6), perpendicular
12 (58.3 / 41.7). Source: results/orientation_analysis.json +
hardneg_analysis_report.md.

Other outputs:
- `failure_cases_20260808_214536.csv/json`, `failure_annotations.csv`,
  `manual_annotations.csv`, `orientation_persistent_*.json` — failure audits
- `orientation_train_audit*.csv` — 428 train orientation examples audited
  (clean / original_only / exclude)
- `probe/*.npz/json`, `probe/*report.md` — probes (see §13)
- `two_stage_results.json/report.md` — two-stage experiment
- `consistency_*` — complement-flip consistency analysis
- `site/` — SITE inspection + protocol + run_metadata + in-flight predictions
- `comparison_structured_*.json` — 2B prompt-variant smoke comparisons
- `smolvlm2_zero_shot_10/50/200_*.csv` — smoke runs

Metadata gaps: most CSVs lack seed/prompt/config columns; timestamps exist in
filenames. Configuration must be reconstructed from code defaults.

---

## 13. CURRENT RESEARCH FINDINGS

### Confirmed observations (supported by actual outputs)
1. Orientation (facing/facing-away/parallel/perpendicular) is the weakest VSR
   family for both 2B and 7B (65.7% best 7B condition vs 85-93% easy
   families), and 2B→7B scaling barely moves it.
2. Frozen-feature probes (linear, MLP, patch-vote, object-grounded) extract
   orientation at/near chance from the 7B vision representation.
3. Vision-side adaptation (projector LoRA; vision blocks+projector LoRA) does
   not improve orientation and significantly lowers overall accuracy
   (McNemar p<0.02).
4. Explicit two-stage object-centric reasoning (geometry ± visual features)
   is significantly WORSE than the generative 7B control (58.3%/55.9% vs
   65.7% orientation; McNemar p≤0.004).
5. Zero-shot 7B is self-inconsistent on complementary statements (63%
   contradiction on facing pairs); LM-only LoRA repairs coherence
   (37→66%), hard-neg LoRA best (77.7%) with no accuracy change —
   coherence and accuracy are separable.
6. Hard-negative training produces a null global tradeoff (84.33% vs 84.69%).
7. Annotation noise is real (~10% questionable orientation labels) but does
   NOT explain the probe/accuracy nulls (clear-subset eval).

### Tentative observations
- 7B residual facing signal (~73-78%) exceeds all probes → some signal
  emerges via multimodal interaction / language priors (not cleanly
  decodable from frozen features).
- 2B structured prompt DECREASES accuracy (68.3% vs 74.0%) with a severe
  False-class regression (41.6%) — one run, one seed.

### Not tested yet
- Everything in the planned paper's audit conditions (§14), seed variation,
  OOD audit, MiMo, SITE results (in progress).

---

## 14. GROUNDING AUDIT IMPLEMENTATION STATUS

All seven planned conditions:

1. normal — IMPLEMENTED + TESTED (all baselines)
2. text-only — NOT IMPLEMENTED
3. blank image — NOT IMPLEMENTED
4. shuffled image — NOT IMPLEMENTED
5. relation inversion — PARTIAL: only `flip_relation()` inside
   `scripts/build_hardneg_manifest.py` (facing↔facing away,
   parallel↔perpendicular) used for TRAINING data, not as an eval condition;
   `scripts/eval_consistency_flips.py` implements complement flips as an
   EVALUATION condition (that one is IMPLEMENTED + TESTED — see §12 row 5)
6. subject/object reversal — NOT IMPLEMENTED
7. horizontal reflection — NOT IMPLEMENTED

Transformation/ground-truth handling exists only for the consistency flips
(statement-level complement with label flip; validated for the four
orientation relations on same-image object pairs).

---

## 15. INTERVENTION CORRECTNESS AUDIT

Relation mappings that exist today:

- `flip_relation()` in `scripts/build_hardneg_manifest.py`: facing ↔
  "facing away from", parallel to ↔ perpendicular to. Applied with label
  flip (not label = original label). Questionable mapping: parallel ↔
  perpendicular is a SOFT complement (objects may be neither); flipping
  label is not strictly correct for all scenes — this affected TRAINING
  data only, and examples were "audited clean".
- `COMPLEMENTS` in `scripts/eval_consistency_flips.py`: left↔right,
  at the left/right side of, in front of↔behind, at the back of→in front of,
  facing↔facing away from, parallel↔perpendicular. Used for the consistency
  analysis; parallel/perp treated separately as soft (both-True is the only
  genuine contradiction) — handled correctly in the analysis.

Not implemented: shuffled-image permutation logic, subject/object reversal
maps, horizontal-flip label transforms — so no correctness issues there yet,
but also nothing to validate. No deterministic-seed transforms exist (n/a).

---

## 16. METRICS CURRENTLY IMPLEMENTED

- Standard accuracy: YES (run_baseline.py, eval_lora.py, 7B pipeline)
- Accuracy counting invalids as wrong: YES (invalid counted wrong in 7B)
- Invalid-output rate: YES (2B metrics include invalid_rate)
- Per-relation accuracy: YES (2B by_relation + 7B by_family/per-relation)
- Relation counts: YES
- normal-vs-text gap: NOT IMPLEMENTED (no text-only condition)
- normal-vs-shuffled / normal-vs-blank gaps: NOT IMPLEMENTED
- Paired counterfactual correctness: PARTIAL (consistency analysis has
  per-pair both-correct/both-wrong, contradiction rates)
- Prediction flip rate: PARTIAL (derivable from consistency CSVs, not a
  standalone metric)
- Horizontal reflection consistency: NOT IMPLEMENTED
- Grounding gain before/after LoRA: NOT IMPLEMENTED (core planned metric)
- Benchmark gain before/after LoRA: PARTIAL (accuracy deltas reported;
  no paired significance except McNemar in 7B analyses)
- Confidence intervals: YES (Wilson CIs in metrics JSONs)
- Statistical significance: PARTIAL (McNemar exact/chi2 in 7B + consistency
  analyses; not on 2B results)

---

## 17. FINE-TUNING IMPLEMENTATION

Two independent LoRA implementations:

A) `src/training/lora.py` (2B SmolVLM2):
- r=8, alpha=16, dropout=0.05, targets q/k/v/o_proj, bias=none
- bf16, eager, gradient checkpointing, enable_input_require_grads
- micro_batch 4, grad_accum 4 → effective 16; lr 1e-4, AdamW wd 0.01,
  linear warmup 10%; 2 epochs; train_test_split(0.05, seed=42)
- saves HF-Trainer-style checkpoints (checkpoints/general_lora/checkpoint-N)
- COMPLETED RUNS: yes (general + targeted 2B LoRAs exist + evals)

B) `scripts/run_7b_pipeline.py` `train_lora()` (7B Qwen2-VL) and
`scripts/train_vision_lora.py`:
- r=8, alpha=16, dropout=0.05
- 7B LM-only: targets q/k/v/o of the LLM; 2 epochs, batch_size=1 (effective
  1), lr 1e-4, warmup 10% of steps, grad clip 1.0, gradient checkpointing
- 7B projector: targets visual.merger.mlp.0/2 (152K trainable)
- 7B vision+projector: last 8 vision blocks (24-31) qkv/proj/fc1/fc2 +
  merger (1.46M trainable)
- COMPLETED RUNS: general, targeted, hardneg, projector, vision+projector
  (all with evaluations)
- Vision tower frozen in ALL conditions; only LoRA adapters trained
- Single seed (42 or default) everywhere — no seed variation yet

---

## 18. CHECKPOINTS

- `checkpoints/general_lora/` (2B, HF-Trainer style, 512MB with optimizer
  states; checkpoint-10..230 + final) — evaluated (76.63%)
- `checkpoints/targeted_lora/` (2B, same layout) — evaluated (76.54%)
- `checkpoints/qwen2vl_7b_general_lora/final` (7B LM LoRA, 19MB adapter) —
  evaluated (84.69%)
- `checkpoints/qwen2vl_7b_targeted_lora/final` (19MB) — evaluated (~84%)
- `checkpoints/qwen2vl_7b_hardneg_lora/final` (19MB) — evaluated (84.33%)
- `checkpoints/qwen2vl_7b_projector_lora/final` (0MB adapter — merger
  weights, ~152K params) — evaluated (82.87%)
- `checkpoints/qwen2vl_7b_vision_proj_lora/final` (5MB) — evaluated (83.10%)
- All loading VERIFIED (evaluations ran through PeftModel.from_pretrained);
  seeds: single default seed per run; checkpoint dates in filenames
- HF cache checkpoints (models--Qwen--Qwen2-VL-7B-Instruct) are NOT project
  checkpoints

---

## 19. REPRODUCIBILITY

Partially reproducible:
- git commit: YES (all code committed)
- dataset ID + split: YES
- model ID: YES
- LoRA config: YES (adapter_config.json committed)
- prompt version: YES (in code)
- seed: PARTIAL (seed=42 defaults exist; not recorded in results metadata)
- checkpoint: YES (paths in §18)
- transformation settings: N/A (no transforms implemented)
- run metadata: NO for VSR runs (timestamps only); YES for SITE
  (results/site/run_metadata.json with config hash)

Missing reproducibility fields: per-run seed, exact HF dataset revision,
environment snapshot, wandb/tensorboard logs (none exist).

---

## 20. TEST COVERAGE

- Unit tests: NONE (no tests/ dir, no test_*.py files)
- Parser: tested implicitly by full evals (0 invalid), no unit tests
- Dataset loader: smoke-tested via `scripts/inspect_vsr.py` and evals
- Model wrapper / LoRA loading / metrics / interventions: no tests
- SITE eval: smoke-tested manually (10-example runs + video path test)

---

## 21. PERFORMANCE / GPU OBSERVATIONS

- 2B eval: batch 8, ~4.2 ex/s (VSR), trivially fits
- 7B VSR eval: batch 8, ~4.2 ex/s, ~24-38GB
- 7B SITE image eval: batch 8 single-image ~15 ex/s; batch 1 multi-image
  ~3.4s/ex (long sequences, eager attention); GPU ~100% at ~24-38GB
- OOM observed: batch-8 multi-image SITE (fixed with batch 1 + progressive
  downscale); 16-frame 224px videos OOM (fixed: 128px frames)
- CPU bottleneck: image loading gaps between batches (GPU dips to ~4% during
  load at batch 1)
- flash-attn: NOT available (install failed on CUDA 13 build)

---

## 22. CLOUD / FILE PERSISTENCE

- Repo: /home/ubuntu/vlm-spatial-reasoning (git-tracked; pushed to remote)
- HF cache: ~/.cache/huggingface (datasets, models — regenerable)
- Results: results/ (committed except in-flight CSV + site_media-adjacent)
- Checkpoints: checkpoints/ (committed — LoRA adapters only, small)
- Local-only / at risk if instance stops: data/image_cache (703MB,
  re-downloadable), data/site_media (43GB, re-downloadable via
  download_site_media_v2.py with the HF token), results/probe/patch_embeddings.pkl
  (8.2GB, regenerable via extract_patch_embeddings.py), in-flight SITE CSV
- All key artifacts are either committed or regenerable; nothing critical is
  only-local except the 3 large caches above.

---

## 23. SECRETS / API SETUP

- HF_TOKEN: configured (token file at ~/.cache/huggingface/token — value
  redacted; used for fast SITE media download)
- TNR_API_TOKEN: configured as environment variable (name only — value
  redacted; purpose not used by any repo code found)
- MiMo API: NOT configured
- WandB: NOT configured
- No .env files found in repo

---

## 24. MIMO STATUS

NOT IMPLEMENTED. No MiMo wrapper, no API config, no interface integration,
no retry/rate-limit logic, no result saving. (Planned as a frozen
strong-model external comparison later in the paper — nothing exists yet.)

---

## 25. 7B MODEL STATUS

- SELECTED: Qwen/Qwen2-VL-7B-Instruct
- DOWNLOADED: yes (HF cache)
- TESTED: extensively (zero-shot, 5 LoRA conditions, probes, consistency,
  two-stage, SITE)
- INTEGRATED: yes (inline in scripts; no dedicated wrapper class)
- LoRA-READY: yes (peft works; 5 trained conditions)
- No candidate ambiguity: this is the final selection, actively used.

---

## 26. KNOWN BUGS / TECHNICAL DEBT

### Critical
- None found that invalidates existing results. (The SITE video handling
  would OOM/skip at 224px frames — fixed in code to 128px but video eval not
  yet run.)

### High
- `src/datasets/vsr.py` split_map breaks under datasets 5.x ("dev"→"dev"
  raises; must use "validation") — affects any dev/validation evaluation.
- SITE eval's previous resume bug (incremental saves dropped pre-resumed
  rows) — FIXED in b8336bb but earlier partial CSVs were overwritten (the
  original 125 rows were regenerated; bit-equivalent, verified).
- No run metadata for VSR experiments (seed/prompt not recorded per run).

### Medium
- `scripts/fetch_site_ranges.py` is dead code with known ZIP64/multipart
  issues (superseded by download_site_media_v2.py).
- `requirements.txt` is stale and misleading.
- Structured-prompt result (2B, 68.3%) is single-run, single-seed.

### Low
- Editor droppings (.intro.md.un~, intro.md~, 200-600KB *.md context dumps)
  in repo root.
- Empty stubs (configs/, paper/, figures/, results/README.md).
- wandb/tensorboard dependencies listed but unused.

---

## 27. RESEARCH-METHODOLOGY RISKS FOUND IN CODE

1. parallel↔perpendicular treated as strict complement in hard-negative
   TRAINING flips (soft complement in reality) — mitigated by audited-clean
   filtering, but the label-flip assumption is not strictly valid for all
   scenes.
2. Planned paper conditions (text-only/blank/shuffled/inversion/reversal/
   reflection) are entirely absent — the paper's core contribution
   (before-vs-after grounding decomposition) cannot yet be written.
3. Single seed everywhere — no seed variance reported.
4. No paired statistical tests on 2B results (only 7B has McNemar).
5. 2B structured prompt regression (False-class collapse to 41.6%) is
   single-run; could be prompt-artifact.
6. Probe conclusions rest on model-generated grounding boxes (Qwen2-VL
   self-grounding) — a detection-model cross-check was never run
   (ground_objects_owl.py exists but unverified).
7. SITE secondary (orientation heuristic) subset is keyword-derived — must
   stay labeled non-official (already handled in protocol).
8. 2B vs 7B comparisons use different wrappers/eval scripts — prompt and
   max_new_tokens differ (5 vs 128/16), though base-vs-tuned within model is
   consistent.
9. VSR subject/object parsing is heuristic; relation-inversion audits built
   on parsed pairs inherit its failure modes (plurals).
10. image_cache pre-download could silently miss images on other machines
    (no integrity check in evaluators; evals just skip missing → would
    change n).

---

## 28. WHAT IS MISSING RELATIVE TO THE PLANNED PAPER

| Item | Status |
|---|---|
| ~2B base baseline | DONE |
| ~2B spatial-LoRA (×3 seeds) | PARTIAL (1 seed) |
| ~7B base baseline | DONE |
| ~7B spatial-LoRA (×3 seeds) | PARTIAL (1 seed) |
| Standard VSR eval | DONE |
| Text-only | NOT STARTED |
| Blank image | NOT STARTED |
| Shuffled image | NOT STARTED |
| Relation inversion | PARTIAL (hardneg flips + consistency flips only) |
| Subject/object reversal | NOT STARTED |
| Horizontal reflection | NOT STARTED |
| VSR zero-shot/config-shift | NOT STARTED (split doesn't exist) |
| Controlled OOD audit | NOT STARTED |
| Paired base-vs-tuned metrics | NOT STARTED |
| Statistical CIs/significance | PARTIAL (7B only) |
| MiMo frozen reference | NOT STARTED |

## 29. EXACT NEXT STEPS

1. Finish the running SITE image eval; produce metrics (overall, primary,
   secondary, CAA, Wilson CIs, single-vs-multi-image, source breakdown) via
   `scripts/eval_site_zeroshot.py` output + a small metrics script. Cheap;
   GPU running now. Success: metrics JSON + report committed.
2. Decide (with the user) whether SITE video subset + VSR-trained 7B LoRA on
   SITE are justified; if yes, run eval with `--max-new-tokens 16` and
   video frames at 128px. Medium cost (~2-3h GPU).
3. Implement the text-only condition (prompt with image removed / image
   token omitted) for 2B + 7B base and LoRAs. Cheap (eval only). Files:
   new script or flag in run_baseline/eval_lora. Success: CSV + gap metrics.
4. Implement blank-image and shuffled-image conditions with deterministic
   seeded transforms and correct ground-truth semantics. Medium. Files:
   `src/evaluation/` new module + eval wrappers.
5. Implement relation-inversion eval maps (explicit valid inverse mapping per
   relation — only orientation pairs have valid inverses; document which
   relations are excluded) and subject/object reversal eval. Medium.
6. Implement horizontal-reflection transforms + label-change logic (only for
   relations whose truth should flip; e.g., left/right flip, facing does
   NOT necessarily flip). Medium.
7. Add per-run metadata (seed, prompt hash, dataset revision) + paired
   McNemar + CI to 2B eval outputs. Cheap.
8. Add unit tests for parser, VSR loader, flip/inversion maps. Cheap.
9. After audits: seed-varied LoRA training (3 seeds) for the final
   conditions. Expensive (GPU, hours per run).
10. MiMo integration (API wrapper + results saving + rate-limit handling).
    Cheap-medium; needs API key.

---

## 30. COMMAND CHEAT SHEET

(All from repo root; environment is the system python — no venv/conda in use.)

- Inspect dataset:
  `python scripts/inspect_vsr.py`
- Run tests: none exist (no tests/)
- 2B smoke (10): `python scripts/run_baseline.py --num-examples 10`
- 2B 200: `python scripts/run_baseline.py --num-examples 200`
- 2B full: `python scripts/run_baseline.py`
- 7B zero-shot + LoRA pipeline: `python scripts/run_7b_pipeline.py` (full
  pipeline; heavy)
- Evaluate any LoRA: `python scripts/eval_lora.py --base-model Qwen/Qwen2-VL-7B-Instruct --lora-path checkpoints/qwen2vl_7b_general_lora/final --output-dir results --batch-size 8`
- Train 7B vision-side LoRA: `python scripts/train_vision_lora.py --target projector|vision_proj`
- SITE eval (running): `python scripts/eval_site_zeroshot.py --out results/site/zeroshot_7b_predictions.csv --max-new-tokens 16 --images-only`
- SITE inspect: `python scripts/inspect_site.py`
- Consistency flips: `python scripts/eval_consistency_flips.py --condition LM_only_LoRA`
- Probes: `python scripts/run_probe.py` ; `python scripts/run_patch_probe.py` ; `python scripts/run_grounded_probe.py`
- Two-stage: `python scripts/two_stage_reasoning.py`
- SITE media download: `python scripts/download_site_media_v2.py`
- Summarize a results CSV: metrics JSONs already contain summaries; no
  dedicated summarize CLI exists.

---

## 31. FILES THE NEXT AI SHOULD READ FIRST

1. `results/hardneg_analysis_report.md` — the cleanest summary of the 7B
   LoRA program + orientation numbers.
2. `results/orientation_deep_dive_report.md` — 48 annotated failures,
   failure-mode taxonomy, the motivation for everything after.
3. `results/probe_analysis_report.md` + `results/grounded_probe_report.md` —
   probe methodology and conclusions.
4. `results/two_stage_report.md` — explicit-reasoning null result.
5. `results/consistency_report.md` — coherence finding.
6. `results/vision_side_report.md` — vision-adaptation null result.
7. `results/site/site_protocol.md` + `site_dataset_report.md` — SITE
   preregistration + subsets.
8. `scripts/run_7b_pipeline.py` — the 7B train/eval machinery (32KB; read
   phase functions).
9. `scripts/eval_lora.py` — generic LoRA evaluator.
10. `scripts/run_baseline.py` — 2B evaluator.
11. `src/datasets/vsr.py` + `src/datasets/site.py` — loaders.
12. `src/models/smolvlm.py` — the only model wrapper.
13. `src/evaluation/parser.py` — output parser.
14. `src/training/lora.py` + `src/training/collator.py` — 2B training.
15. `scripts/build_hardneg_manifest.py` — flip/inversion logic.
16. `scripts/eval_site_zeroshot.py` — current SITE eval (running).
17. `scripts/eval_consistency_flips.py` — complement-flip analysis code.
18. `checkpoints/*/final/adapter_config.json` — LoRA configs (r=8, alpha=16).
19. `results/site/run_metadata.json` — SITE protocol/frozen config hash.
20. `README.md` + `requirements.txt` — context (stale; trust code over README).

---

## 32. FULL CONTENT OF CRITICAL SMALL FILES

### `src/evaluation/parser.py` (96 lines — full behavior described in §10;
key logic: normalized = strip().lower(); prefix strip
`^(the answer is|answer:|response:|output:)`; anchored pattern lists; then
substring fallback true/false; else None.)

### `src/models/smolvlm.py` (176 lines — §8/§9. Key: SPATIAL_PROMPT and
STRUCTURED_PROMPT templates; predict/predict_batch via apply_chat_template,
padding_side=left, do_sample=False, max_new_tokens=5; _extract_answer strips
"Assistant:" prefix or takes last non-empty line.)

### `src/datasets/vsr.py` (146 lines — §6. Key functions: load_vsr (split_map,
fields image/statement/label/relation/subject/object; subject/object parsed
by splitting on " is "), load_vsr_splits, get_relation_frequency.)

### LoRA config (from adapter_config.json, all conditions):
`r=8, lora_alpha=16, lora_dropout=0.05, target_modules=[q_proj,v_proj,k_proj,o_proj]`
(7B vision variants: merger mlp.0/2; vision+proj adds blocks 24-31
attn.qkv/attn.proj/mlp.fc1/mlp.fc2).

### `src/training/lora.py` (2B, ~280 lines — §17; key defaults: epochs=2,
lr=1e-4, micro_batch=4, grad_accum=4, warmup 10%, r=8 α=16 dropout 0.05,
seed 42, train_test_split 0.05, saves HF-Trainer checkpoints every 100
steps + final.)

### `src/training/collator.py` — labels masked to answer tokens only
(encode " True"/" False", -100 on prompt tokens).

### `configs/`: only README.md stub — no configs exist.

---

## 33. FINAL HANDOFF SNAPSHOT

## Current milestone

7B orientation causal-decomposition program complete (probes, vision-side
LoRAs, two-stage, consistency); SITE external-validation zero-shot image
eval RUNNING (~75% through, resumable, protocol preregistered and frozen);
planned paper's grounding-audit conditions not yet built.

## Working 2B model

HuggingFaceTB/SmolVLM2-2.2B-Instruct — zero-shot 73.99%, General LoRA
76.63%, Targeted LoRA 76.54%, structured prompt 68.34% (all VSR test n=2195,
invalid rate 0).

## Planned/working 7B model

Qwen/Qwen2-VL-7B-Instruct — selected, downloaded, tested, LoRA-ready.
Zero-shot 80.91%; General LoRA 84.69%; Targeted ~84%; Hard-neg 84.33%;
Projector 82.87%; Vision+Projector 83.10%. Orientation family stuck ~65.7%.

## Dataset state

VSR: train 7,680 / validation 1,097 / test 2,195, 64 relations, balanced
labels; images cached locally; no zero-shot split exists. SITE (external):
8,068 examples, two official test configs, media cached (43GB), protocol
frozen (primary 1,721 / secondary heuristic 3,272 / exploratory 1,103).

## Baseline result

2B 73.99% / 7B 80.91% zero-shot on VSR test; orientation per-relation weak
(facing-away 48.7%→59.0% with 7B LoRA).

## Grounding audit state

NOT IMPLEMENTED (text-only/blank/shuffled/inversion/reversal/reflection all
absent); complement-flip consistency analysis DONE (7B).

## Fine-tuning state

LoRA r=8 α=16 on q/k/v/o (LM) for 2B and 7B; 5 7B conditions + 2 2B
conditions trained and evaluated; vision tower frozen; single seed; recipe
documented (lr 1e-4, 2 epochs, warmup 10%).

## Existing checkpoints

2B general/targeted (HF-Trainer style, 512MB dirs); 7B general, targeted,
hardneg, projector, vision+projector adapters (19MB/0MB/5MB) — all verified
loadable and evaluated.

## Compute

1× RTX A6000 48GB (full spec verified); 6 vCPU; 48GB RAM; 200GB disk
(124GB free); torch 2.12.1+cu130, transformers 5.14.1, datasets 5.0.1, peft
0.20.0; flash-attn unavailable.

## Biggest methodological risk

The planned paper's core contribution — before-vs-after spatial
fine-tuning grounding decomposition (text-only/blank/shuffled/inversion/
reversal/reflection conditions, paired metrics, seed variation) — does not
exist in the repo yet; the existing strong negative results are on a
different (orientation-causality) question and must not be conflated with
the planned paper's claims.

## Biggest technical blocker

transformers 5.14.1 / datasets 5.x API drift (validation split naming,
Qwen2-VL grounding/video processor changes) plus no test suite and no run
metadata for VSR experiments; SITE media requires the HF token to
re-download (43GB, gitignored).

## Immediate next experiment

Finish SITE 7B zero-shot image eval → report preregistered metrics →
decide whether 7B VSR-LoRA on SITE and the SITE video subset are justified.

## Files I should send/read first

results/hardneg_analysis_report.md, results/orientation_deep_dive_report.md,
results/probe_analysis_report.md, results/two_stage_report.md,
results/consistency_report.md, results/vision_side_report.md,
results/site/site_protocol.md, scripts/run_7b_pipeline.py,
scripts/eval_lora.py, scripts/run_baseline.py, src/datasets/vsr.py,
src/models/smolvlm.py, src/evaluation/parser.py, src/training/lora.py,
scripts/build_hardneg_manifest.py, scripts/eval_site_zeroshot.py,
scripts/eval_consistency_flips.py, results/site/run_metadata.json,
checkpoints/*/final/adapter_config.json, this file.


