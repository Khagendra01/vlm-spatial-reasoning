# New session - 2026-08-22T05:11:27.873Z

**Session ID:** ses_fd81e747fffey16zO59Xh0VoM8
**Created:** 8/22/2026, 1:11:27 AM
**Updated:** 8/22/2026, 1:26:37 AM

---

## User

explain this repo, what is done and what is going on

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 14.1s)

_Thinking:_

Let me explore the repo.

**Tool: read**

**Input:**
```json
{
  "filePath": "/Users/kgensupertramp/Desktop/vlm-spatial-reasoning",
  "command": "git log --oneline -15 && git status",
  "description": "Shows recent commits and working tree status"
}
```

**Output:**
```
<path>/Users/kgensupertramp/Desktop/vlm-spatial-reasoning</path>
<type>directory</type>
<entries>
.git/
.gitignore
.intro.md.un~
aftertrain.md
BRANCH_MAP.md
checkpoints/
configs/
CURRENT_RESEARCH_HANDOFF.md
data/
docs/
figures/
intro.md
intro.md~
leadfromhere.md
notebooks/
paper/
README.md
requirements.txt
research/
results/
scripts/
src/
tests/
transferfromgp.md

(24 entries)
</entries>
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 11.6s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/README.md"
}
```

**Output:**
```
<path>/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/README.md</path>
<type>file</type>
<content>
1: # VLM Spatial Reasoning
2: 
3: A research project exploring spatial reasoning capabilities of Vision-Language Models (VLMs).
4: 
5: ## Project Structure
6: 
7: ```
8: vlm-spatial-reasoning/
9: ├── README.md
10: ├── configs/           # Configuration files for experiments
11: ├── data/              # Datasets and data processing scripts
12: ├── src/
13: │   ├── models/        # Model implementations
14: │   ├── datasets/      # Dataset loaders and processors
15: │   ├── evaluation/    # Evaluation metrics and scripts
16: │   └── training/      # Training loops and utilities
17: ├── scripts/           # Utility and automation scripts
18: ├── notebooks/         # Jupyter notebooks for analysis
19: │   └── exploratory_analysis.ipynb
20: ├── results/           # Experiment results and logs
21: ├── figures/           # Generated figures and visualizations
22: ├── paper/             # LaTeX source and figures for the paper
23: └── requirements.txt   # Python dependencies
24: ```
25: 
26: ## Getting Started
27: 
28: ### Installation
29: 
30: ```bash
31: pip install -r requirements.txt
32: ```
33: 
34: ### Usage
35: 
36: [Add usage instructions here]
37: 
38: ## SITE External Validation
39: 
40: SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025) is used as an
41: evaluation-only external-validation benchmark for our VSR orientation
42: finding. Key documents:
43: 
44: - `results/site/site_protocol.md` — preregistered protocol (subsets, metrics, decision rule)
45: - `results/site/site_protocol.json` — frozen subset definitions incl. example IDs
46: - `results/site/orientation_subset_definition.md` — the heuristic orientation
47:   subset: why it exists (official release has no orientation tag), the exact
48:   keyword list, frozen IDs, and its known limitations (non-official, supporting only)
49: - `results/site/zeroshot_image_report.md` — step-1 results (7B zero-shot, images)
50: - `results/site/site_dataset_report.md` — dataset inspection
51: - `results/site/site_eval_run_notes.md` — engineering issues and fixes
52: 
53: ## Techniques & conventions
54: 
55: `docs/TECHNIQUES.md` documents the empirically-derived conventions used
56: across the project: Qwen2-VL grounding coordinate space (per-axis [0,1000]),
57: one-box-per-query grounding, patch-grid region pooling, the `max_pixels`
58: regression and the 392 px resolution cap, pyav video frame sampling, and
59: OOM-safe batched generation.
60: 
61: ## License
62: 
63: [Add license here]

(End of file - total 63 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/CURRENT_RESEARCH_HANDOFF.md"
}
```

**Output:**
```
<path>/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/CURRENT_RESEARCH_HANDOFF.md</path>
<type>file</type>
<content>
1: # CURRENT RESEARCH HANDOFF REPORT
2: 
3: Audit date: 2026-08-10 (UTC). Auditor: autonomous agent inspecting the live repo.
4: IMPORTANT CONTEXT: at audit time, a SITE zero-shot evaluation is RUNNING on the
5: GPU (image subset, ~75% through). Everything below reflects the live state.
6: 
7: ---
8: 
9: ## 1. EXECUTIVE STATUS
10: 
11: The repository is a VLM spatial-reasoning research project that has drifted
12: from its originally planned paper scope (2B + 7B base-vs-LoRA behavioral
13: grounding audit) into a deeper, 7B-only orientation causal-decomposition
14: program, now culminating in external validation on SITE (ICCV 2025).
15: 
16: - **IMPLEMENTED + TESTED**: SmolVLM2-2.2B zero-shot baseline; structured-prompt
17:   variant; 2B General/Targeted LoRA train+eval; Qwen2-VL-7B zero-shot; 7B
18:   General/Targeted/Hard-negative/Projector/Vision+Projector LoRA trains+evals;
19:   orientation failure annotation/audit; representation probes (global, patch,
20:   object-grounded); two-stage explicit reasoning; logical-consistency
21:   (complement-flip) analysis; SITE loader + inspection + preregistered
22:   evaluation protocol.
23: - **VERIFIED**: dataset statistics (train 7,680 / dev 1,097 / test 2,195;
24:   64 relations; near-balanced labels); VSR image loading works; all checkpoint
25:   adapters load (used in evals); SITE media (8,086 files) downloaded; SITE
26:   eval script smoke-tested and currently running.
27: - **NOT IMPLEMENTED**: nearly all of the PLANNED PAPER's grounding-audit
28:   conditions (text-only, blank image, shuffled image, relation inversion,
29:   subject/object reversal, horizontal reflection); VSR zero-shot/config-shift
30:   split (does not exist in the dataset and no loader support); controlled OOD
31:   audit; MiMo integration; paired base-vs-tuned grounding metrics; seed
32:   variation (single seed everywhere); 2B→7B paired transfer analysis.
33: - **PARTIAL**: the planned "2B + 7B" paper is partially covered (both models
34:   have baselines and LoRAs on VSR test) but the intended behavioral
35:   decomposition (before-vs-after grounding gain) is absent.
36: - **BROKEN / UNVERIFIED**: `scripts/fetch_site_ranges.py` (superseded,
37:   contains known ZIP64/multipart limitations); flash-attn install (failed on
38:   CUDA 13); `datasets` v5 API change ("dev" split no longer exists — it is
39:   "validation"); no test suite exists at all.
40: - **IMMEDIATE NEXT EXPERIMENT (running)**: SITE 7B zero-shot image-subset
41:   evaluation (preregistered protocol) → then report metrics and decide
42:   whether the VSR-trained 7B LoRA is justified on SITE.
43: 
44: ---
45: 
46: ## 2. REPOSITORY STRUCTURE
47: 
48: Root: `/home/ubuntu/vlm-spatial-reasoning` (git repo, branch `master`).
49: 
50: ```
51: ├── README.md                     # Stub README (structure only, no usage)
52: ├── requirements.txt              # Dependencies (stale: python3.10/conda-era)
53: ├── .gitignore                    # python/dataset/media exclusions
54: ├── .intro.md.un~, intro.md~      # editor droppings
55: ├── aftertrain.md, leadfromhere.md, transferfromgp.md   # 200-600KB context dumps
56: ├── configs/└── README.md         # empty stub (no real configs anywhere)
57: ├── notebooks/exploratory_analysis.ipynb
58: ├── paper/└── README.md           # empty stub
59: ├── figures/                      # empty
60: ├── data/
61: │   ├── image_cache/              # 703MB cached VSR images (md5(url).jpg)
62: │   ├── site_media/               # 43GB SITE media (extracted, gitignored)
63: │   └── manifests/                # general/targeted/hardneg_train.jsonl (2000 rows each)
64: ├── src/
65: │   ├── datasets/vsr.py           # VSR loader + stats helpers (4274 B)
66: │   ├── datasets/site.py          # SITE (ICCV 2025) loader + orientation heuristic
67: │   ├── evaluation/parser.py      # True/False output parser (96 lines)
68: │   ├── models/smolvlm.py         # SmolVLM2-2.2B wrapper (ONLY model wrapper)
69: │   ├── training/lora.py          # SmolVLM2 LoRA training (2B)
70: │   ├── training/collator.py      # VSR collator (loss on answer tokens only)
71: │   └── training/build_train_sets.py  # builds 2000-ex manifests from VSR train
72: ├── scripts/                      # 40+ scripts (see §30/§31 for key ones)
73: ├── results/                      # all experiment outputs (see §12)
74: └── checkpoints/                  # 2B + 7B LoRA adapters (see §18)
75: ```
76: 
77: Note: `tests/` does not exist. No formal experiment configs; hyperparameters
78: live in script defaults/CLI flags.
79: 
80: ---
81: 
82: ## 3. GIT STATE
83: 
84: - Branch: `master`; HEAD: `b8336bb8d73ebc77c0eff73c336ffc8b2a65c455`
85: - Working tree: NOT clean — `results/site/zeroshot_7b_predictions.csv` is
86:   modified (the running SITE eval appends to it; expected).
87: - No other untracked/modified files (site_media + image_cache gitignored).
88: - Recent commits (oldest→newest): `2d732cd` orientation deep-dive per-relation;
89:   `4b83729` 48-failure annotation taxonomy; `9fc694f` hard-negative LoRA
90:   ablation; `9d9c50c` representation probe; `fa9d0be` object-grounded probe;
91:   `a0d50ca` clear-subset label-noise check; `f1bc14f` vision-side LoRAs;
92:   `1e83604` two-stage reasoning; `6bf8b84` logical consistency; `10494bf`
93:   SITE loader; `8d7f173` SITE preregistration; `b8336bb` SITE eval protocol
94:   update (current HEAD).
95: - Not yet committed: in-flight SITE predictions CSV; final SITE metrics (when
96:   the run finishes).
97: 
98: ---
99: 
100: ## 4. HARDWARE AND SYSTEM ENVIRONMENT
101: 
102: - GPU: 1× NVIDIA RTX A6000, 49,140 MiB VRAM (verified)
103: - GPU current: ~24 GiB used, 100% util (SITE eval running), ~296W/300W, 67°C
104: - Driver: NVIDIA-SMI 610.43.02, CUDA UMD 13.3
105: - CPU: Intel Xeon E5-2683 v4 @ 2.10GHz, 6 online vCPUs (0-5; 58 offline)
106: - RAM: 48 GiB (25 GiB free, 20 GiB buff/cache)
107: - OS: Ubuntu 24.04, kernel 6.17.0-35-generic; Python 3.12.13
108: - Disk: 200 GiB overlay, 124 GiB free (77 GiB used; 43 GiB = site_media)
109: - CWD: `/home/ubuntu/vlm-spatial-reasoning`
110: 
111: Matches the expected spec (A6000 48GB / 6 vCPU / 48GB RAM) — confirmed.
112: 
113: ---
114: 
115: ## 5. PYTHON / ML ENVIRONMENT
116: 
117: Key installed versions (pip, user site):
118: 
119: - torch 2.12.1+cu130, torchvision 0.27.1+cu130
120: - transformers 5.14.1 (very new; several 4.x APIs changed)
121: - datasets 5.0.1 ("dev" split no longer exists; it is "validation")
122: - peft 0.20.0, accelerate 1.14.0, safetensors 0.8.0
123: - numpy 2.5.0, pandas 3.0.3, scipy 1.18.0, pillow 12.2.0, pyarrow 25.0.0
124: - av 18.0.0 (video decoding; torchvision.io.read_video is BROKEN here)
125: - matplotlib 3.11.0, PyYAML 6.0.3, tqdm 4.70.0
126: - ABSENT: bitsandbytes, trl, flash-attn (install failed on CUDA 13), cv2, decord
127: 
128: Issues:
129: - `requirements.txt` is stale (conda/python3.10-era, outdated pins, lists
130:   opencv/timm/rouge/cider/wandb that the repo does not use).
131: - transformers 5.14.1: Qwen2VLProcessor has no `enable_grounding`; video
132:   loading defaults to torchcodec→torchvision (broken) — must pre-decode with
133:   `av` (as `scripts/eval_site_zeroshot.py` does).
134: - No lock files / pyproject / env YAML.
135: 
136: ---
137: 
138: ## 6. DATASET IMPLEMENTATION
139: 
140: `src/datasets/vsr.py` loads `cambridgeltl/vsr_random`. Split mapping caveat:
141: the wrapper maps "dev"/"validation"→"dev", which now RAISES under datasets 5.x
142: (actual HF split name is "validation"). Use split="validation" directly.
143: 
144: Verified stats (fresh load):
145: - train 7,680; validation 1,097; test 2,195
146: - train labels: 0→3,804, 1→3,876 (≈ balanced)
147: - 64 unique relations; top: touching 884, in front of 528, behind 498, under
148:   415, on 408, on top of 349, at the right side of 335, at the left side of 273
149: - Raw fields: image (filename), image_link (URL), caption, label (int),
150:   relation, annotator_id, vote_true/false_validator_id, reference_frame
151: - Wrapper returns: image (URL string), statement (=caption), label (bool),
152:   relation, subject, object
153: - Subject/object are PARSED by splitting the caption on " is " (heuristic;
154:   fails on plurals/"are" and non-standard templates)
155: - Images load via `data/image_cache` (md5(url).jpg); loading verified by evals
156:   (0 invalid outputs on 2B/7B full runs)
157: - No transforms; seeds: np.random.seed(42) in run_baseline.py only
158: - No zero-shot/config-shift split exists in this dataset
159: 
160: ---
161: 
162: ## 7. DATA LEAKAGE / SPLIT AUDIT
163: 
164: - Training manifests (general/targeted/hardneg) are built ONLY from the VSR
165:   **train** split (`src/training/build_train_sets.py` L243;
166:   `scripts/build_hardneg_manifest.py` reads manifests + train-split audit).
167: - All evaluation scripts load split="test" only (run_7b_pipeline.py L119/533,
168:   run_7b_hardneg_pipeline.py L316, eval_lora.py L115).
169: - Hard-negative flips: syntactically generated (relation flip + label flip)
170:   from train examples; audit "exclude" examples dropped from originals and
171:   negatives.
172: - Probes: train on audited-clean VSR train; eval val+test. Two-stage and
173:   consistency analyses: train on train, eval on test.
174: - RISK: low. No test data used for training decisions found. Nuance:
175:   hard-negative flipped statements share images with originals within the
176:   same training split (intentional).
177: - VSR zero-shot split: NOT SUPPORTED (dataset has none; no loader support).
178: 
179: ---
180: 
181: ## 8. MODEL IMPLEMENTATION
182: 
183: Only ONE wrapper exists: `src/models/smolvlm.py` → `SmolVLMClassifier`.
184: 
185: - 2B: `HuggingFaceTB/SmolVLM2-2.2B-Instruct` (confirmed in use)
186:   - ~2.2B params, bf16, eager attention, low_cpu_mem_usage, `.to("cuda")`
187:   - AutoProcessor + apply_chat_template, padding_side=left, padding=True
188:   - generation: do_sample=False, max_new_tokens=5 (default)
189:   - TESTED: zero-shot 10/50/200/2195, structured prompt, LoRA evals
190: - 7B: `Qwen/Qwen2-VL-7B-Instruct` — SELECTED, DOWNLOADED, TESTED, INTEGRATED,
191:   LoRA-READY (in HF cache `models--Qwen--Qwen2-VL-7B-Instruct`).
192:   - 8.29B params total; ~16.6GB bf16 weights
193:   - No dedicated wrapper class; used via inline code in
194:     `scripts/run_7b_pipeline.py` (zero-shot/LoRA train/eval),
195:     `scripts/eval_lora.py` (with `--base-model Qwen/Qwen2-VL-7B-Instruct`),
196:     `scripts/eval_site_zeroshot.py`, probe scripts
197:   - eager attention, bf16, greedy (temperature 0 / do_sample=False)
198:   - VRAM observed: ~24GB at batch 1 image inference; ~38GB peaks with long
199:     multi-image sequences; 48GB fits at batch 8 only for short sequences
200: 
201: No 14B/30B models present. `eval_lora.py` defaults to the 2B model but works
202: for 7B via `--base-model`.
203: 
204: ---
205: 
206: ## 9. PROMPT CURRENTLY USED
207: 
208: Two prompt families:
209: 
210: 1. Plain (used by 2B wrapper `SPATIAL_PROMPT`, `run_7b_pipeline.py`
211:    `TRAIN_PROMPT`, `eval_lora.py`, `eval_site_zeroshot.py` prompts are
212:    separate for SITE):
213: ```
214: Look at the image carefully.
215: 
216: Statement: "{statement}"
217: 
218: Is this statement true or false?
219: 
220: Answer with exactly one word: True or False.
221: ```
222: 2. Structured decomposition (2B only, `STRUCTURED_PROMPT` in smolvlm.py):
223:    subject/ref identification → position/orientation steps → same True/False
224:    constraint.
225: 
226: Properties: no system prompt; no chain-of-thought requested; answer
227: constrained to one word True/False; deterministic greedy (do_sample=False,
228: temperature 0, top_p 1.0); max_new_tokens 5 (2B) / 128 (7B pipelines) / 16
229: (SITE eval, protocol-recorded change from 128, validated result-neutral).
230: 
231: Fairness flag: 2B and 7B use the same plain prompt, so base-vs-tuned
232: comparisons are internally consistent. The structured prompt (2B only) is a
233: separate experiment, not a condition of the planned paper.
234: 
235: ---
236: 
237: ## 10. OUTPUT PARSER
238: 
239: `src/evaluation/parser.py` → `parse_true_false(output) -> Optional[bool]`:
240: 
241: - Normalizes: strip, lower; strips prefixes "the answer is|answer:|response:
242:   |output:" and trailing punctuation/whitespace.
243: - TRUE patterns: ^true$, ^yes$, ^correct$, "the answer is true", "this
244:   statement is true", "it's true", "absolutely", "definitely", ... (regex
245:   anchored, case-insensitive)
246: - FALSE patterns: ^false$, ^no$, ^incorrect$, "the answer is false", "this
247:   statement is false", "not true", ...
248: - Fallback: if "true" in output and "false" not → True; if "false" in output
249:   and "true" not → False; both words present → None.
250: - Returns None (no guessing) on malformed output.
251: 
252: Tested behavior from actual runs: 0 invalid outputs on full 2B/7B VSR evals.
253: Weakness: "both words appearing" → None (e.g. "The answer is true, not
254: false"). No unit tests exist. Do not modify without re-validating the
255: existing CSVs' parse paths.
256: 
257: ## 11. BASELINE EVALUATOR
258: 
259: `scripts/run_baseline.py` (2B):
260: - Args: `--num-examples` (None=all), `--split` (train|dev|test; note dev now
261:   broken under datasets 5.x — use test), `--output-dir`, `--model`, `--resume`,
262:   `--batch-size` (default 8)
263: - Batch 8; incremental checkpointing (saves partial CSV every
264:   `checkpoint_interval`); parse via `parse_true_false`; metrics include
265:   global accuracy, per-relation accuracy + Wilson CIs, class breakdown,
266:   confusion matrix, prediction distribution; seeds np.random.seed(42)
267: - Actual commands used historically:
268:   - smoke: `python scripts/run_baseline.py --num-examples 10`
269:   - 200: `python scripts/run_baseline.py --num-examples 200`
270:   - full: `python scripts/run_baseline.py` (or with `--model` for variants)
271: 
272: 7B equivalents:
273: - Zero-shot: `python scripts/run_7b_pipeline.py` phase 1 (whole pipeline runs
274:   zero-shot → LoRA train → eval → analysis; heavy)
275: - LoRA eval (any model): `python scripts/eval_lora.py --base-model Qwen/Qwen2-VL-7B-Instruct --lora-path checkpoints/qwen2vl_7b_general_lora/final --output-dir results --batch-size 8`
276: 
277: ---
278: 
279: ## 12. EXISTING EXPERIMENTAL RESULTS
280: 
281: All under `results/`. Verified key outputs (accuracy on VSR test n=2195):
282: 
283: | Experiment | File | Overall acc | Invalid |
284: |---|---|---|---|
285: | 2B SmolVLM2 zero-shot | smolvlm2_metrics_2195_20260808_214536.json | 73.99% | 0 |
286: | 2B structured prompt | smolvlm2_structured_metrics_2195_20260808_225009.json | 68.34% (True 91.3 / False 41.6) | 0 |
287: | 2B General LoRA | general_lora_metrics_20260809_054915.json | 76.63% | 0 |
288: | 2B Targeted LoRA | targeted_lora_metrics_20260809_061231.json | 76.54% | 0 |
289: | 7B zero-shot (A) | qwen2vl_7b_metrics_20260809_064919.json | 80.91% | n/a |
290: | 7B General LoRA | 7B_general_lora_metrics_20260809_094930.json | 84.69% (orientation 65.7%) | n/a |
291: | 7B Targeted LoRA | 7B_targeted_lora_metrics_20260809_095926.json | ~84% | n/a |
292: | 7B Hard-neg LoRA | 7B_hardneg_lora_metrics_20260809_164619.json | 84.33% | n/a |
293: | 7B Projector LoRA | qwen2vl_7b_projector_lora_metrics_20260809_221720.json | 82.87% | n/a |
294: | 7B Vision+Proj LoRA | qwen2vl_7b_vision_proj_lora_metrics_20260809_222845.json | 83.10% | n/a |
295: 
296: Orientation per-relation (test, 137 examples): facing 64 (7B zero 73.4 / gen
297: 75.0), facing away 39 (48.7 / 59.0), parallel 22 (63.6 / 63.6), perpendicular
298: 12 (58.3 / 41.7). Source: results/orientation_analysis.json +
299: hardneg_analysis_report.md.
300: 
301: Other outputs:
302: - `failure_cases_20260808_214536.csv/json`, `failure_annotations.csv`,
303:   `manual_annotations.csv`, `orientation_persistent_*.json` — failure audits
304: - `orientation_train_audit*.csv` — 428 train orientation examples audited
305:   (clean / original_only / exclude)
306: - `probe/*.npz/json`, `probe/*report.md` — probes (see §13)
307: - `two_stage_results.json/report.md` — two-stage experiment
308: - `consistency_*` — complement-flip consistency analysis
309: - `site/` — SITE inspection + protocol + run_metadata + in-flight predictions
310: - `comparison_structured_*.json` — 2B prompt-variant smoke comparisons
311: - `smolvlm2_zero_shot_10/50/200_*.csv` — smoke runs
312: 
313: Metadata gaps: most CSVs lack seed/prompt/config columns; timestamps exist in
314: filenames. Configuration must be reconstructed from code defaults.
315: 
316: ---
317: 
318: ## 13. CURRENT RESEARCH FINDINGS
319: 
320: ### Confirmed observations (supported by actual outputs)
321: 1. Orientation (facing/facing-away/parallel/perpendicular) is the weakest VSR
322:    family for both 2B and 7B (65.7% best 7B condition vs 85-93% easy
323:    families), and 2B→7B scaling barely moves it.
324: 2. Frozen-feature probes (linear, MLP, patch-vote, object-grounded) extract
325:    orientation at/near chance from the 7B vision representation.
326: 3. Vision-side adaptation (projector LoRA; vision blocks+projector LoRA) does
327:    not improve orientation and significantly lowers overall accuracy
328:    (McNemar p<0.02).
329: 4. Explicit two-stage object-centric reasoning (geometry ± visual features)
330:    is significantly WORSE than the generative 7B control (58.3%/55.9% vs
331:    65.7% orientation; McNemar p≤0.004).
332: 5. Zero-shot 7B is self-inconsistent on complementary statements (63%
333:    contradiction on facing pairs); LM-only LoRA repairs coherence
334:    (37→66%), hard-neg LoRA best (77.7%) with no accuracy change —
335:    coherence and accuracy are separable.
336: 6. Hard-negative training produces a null global tradeoff (84.33% vs 84.69%).
337: 7. Annotation noise is real (~10% questionable orientation labels) but does
338:    NOT explain the probe/accuracy nulls (clear-subset eval).
339: 
340: ### Tentative observations
341: - 7B residual facing signal (~73-78%) exceeds all probes → some signal
342:   emerges via multimodal interaction / language priors (not cleanly
343:   decodable from frozen features).
344: - 2B structured prompt DECREASES accuracy (68.3% vs 74.0%) with a severe
345:   False-class regression (41.6%) — one run, one seed.
346: 
347: ### Not tested yet
348: - Everything in the planned paper's audit conditions (§14), seed variation,
349:   OOD audit, MiMo, SITE results (in progress).
350: 
351: ---
352: 
353: ## 14. GROUNDING AUDIT IMPLEMENTATION STATUS
354: 
355: All seven planned conditions:
356: 
357: 1. normal — IMPLEMENTED + TESTED (all baselines)
358: 2. text-only — NOT IMPLEMENTED
359: 3. blank image — NOT IMPLEMENTED
360: 4. shuffled image — NOT IMPLEMENTED
361: 5. relation inversion — PARTIAL: only `flip_relation()` inside
362:    `scripts/build_hardneg_manifest.py` (facing↔facing away,
363:    parallel↔perpendicular) used for TRAINING data, not as an eval condition;
364:    `scripts/eval_consistency_flips.py` implements complement flips as an
365:    EVALUATION condition (that one is IMPLEMENTED + TESTED — see §12 row 5)
366: 6. subject/object reversal — NOT IMPLEMENTED
367: 7. horizontal reflection — NOT IMPLEMENTED
368: 
369: Transformation/ground-truth handling exists only for the consistency flips
370: (statement-level complement with label flip; validated for the four
371: orientation relations on same-image object pairs).
372: 
373: ---
374: 
375: ## 15. INTERVENTION CORRECTNESS AUDIT
376: 
377: Relation mappings that exist today:
378: 
379: - `flip_relation()` in `scripts/build_hardneg_manifest.py`: facing ↔
380:   "facing away from", parallel to ↔ perpendicular to. Applied with label
381:   flip (not label = original label). Questionable mapping: parallel ↔
382:   perpendicular is a SOFT complement (objects may be neither); flipping
383:   label is not strictly correct for all scenes — this affected TRAINING
384:   data only, and examples were "audited clean".
385: - `COMPLEMENTS` in `scripts/eval_consistency_flips.py`: left↔right,
386:   at the left/right side of, in front of↔behind, at the back of→in front of,
387:   facing↔facing away from, parallel↔perpendicular. Used for the consistency
388:   analysis; parallel/perp treated separately as soft (both-True is the only
389:   genuine contradiction) — handled correctly in the analysis.
390: 
391: Not implemented: shuffled-image permutation logic, subject/object reversal
392: maps, horizontal-flip label transforms — so no correctness issues there yet,
393: but also nothing to validate. No deterministic-seed transforms exist (n/a).
394: 
395: ---
396: 
397: ## 16. METRICS CURRENTLY IMPLEMENTED
398: 
399: - Standard accuracy: YES (run_baseline.py, eval_lora.py, 7B pipeline)
400: - Accuracy counting invalids as wrong: YES (invalid counted wrong in 7B)
401: - Invalid-output rate: YES (2B metrics include invalid_rate)
402: - Per-relation accuracy: YES (2B by_relation + 7B by_family/per-relation)
403: - Relation counts: YES
404: - normal-vs-text gap: NOT IMPLEMENTED (no text-only condition)
405: - normal-vs-shuffled / normal-vs-blank gaps: NOT IMPLEMENTED
406: - Paired counterfactual correctness: PARTIAL (consistency analysis has
407:   per-pair both-correct/both-wrong, contradiction rates)
408: - Prediction flip rate: PARTIAL (derivable from consistency CSVs, not a
409:   standalone metric)
410: - Horizontal reflection consistency: NOT IMPLEMENTED
411: - Grounding gain before/after LoRA: NOT IMPLEMENTED (core planned metric)
412: - Benchmark gain before/after LoRA: PARTIAL (accuracy deltas reported;
413:   no paired significance except McNemar in 7B analyses)
414: - Confidence intervals: YES (Wilson CIs in metrics JSONs)
415: - Statistical significance: PARTIAL (McNemar exact/chi2 in 7B + consistency
416:   analyses; not on 2B results)
417: 
418: ---
419: 
420: ## 17. FINE-TUNING IMPLEMENTATION
421: 
422: Two independent LoRA implementations:
423: 
424: A) `src/training/lora.py` (2B SmolVLM2):
425: - r=8, alpha=16, dropout=0.05, targets q/k/v/o_proj, bias=none
426: - bf16, eager, gradient checkpointing, enable_input_require_grads
427: - micro_batch 4, grad_accum 4 → effective 16; lr 1e-4, AdamW wd 0.01,
428:   linear warmup 10%; 2 epochs; train_test_split(0.05, seed=42)
429: - saves HF-Trainer-style checkpoints (checkpoints/general_lora/checkpoint-N)
430: - COMPLETED RUNS: yes (general + targeted 2B LoRAs exist + evals)
431: 
432: B) `scripts/run_7b_pipeline.py` `train_lora()` (7B Qwen2-VL) and
433: `scripts/train_vision_lora.py`:
434: - r=8, alpha=16, dropout=0.05
435: - 7B LM-only: targets q/k/v/o of the LLM; 2 epochs, batch_size=1 (effective
436:   1), lr 1e-4, warmup 10% of steps, grad clip 1.0, gradient checkpointing
437: - 7B projector: targets visual.merger.mlp.0/2 (152K trainable)
438: - 7B vision+projector: last 8 vision blocks (24-31) qkv/proj/fc1/fc2 +
439:   merger (1.46M trainable)
440: - COMPLETED RUNS: general, targeted, hardneg, projector, vision+projector
441:   (all with evaluations)
442: - Vision tower frozen in ALL conditions; only LoRA adapters trained
443: - Single seed (42 or default) everywhere — no seed variation yet
444: 
445: ---
446: 
447: ## 18. CHECKPOINTS
448: 
449: - `checkpoints/general_lora/` (2B, HF-Trainer style, 512MB with optimizer
450:   states; checkpoint-10..230 + final) — evaluated (76.63%)
451: - `checkpoints/targeted_lora/` (2B, same layout) — evaluated (76.54%)
452: - `checkpoints/qwen2vl_7b_general_lora/final` (7B LM LoRA, 19MB adapter) —
453:   evaluated (84.69%)
454: - `checkpoints/qwen2vl_7b_targeted_lora/final` (19MB) — evaluated (~84%)
455: - `checkpoints/qwen2vl_7b_hardneg_lora/final` (19MB) — evaluated (84.33%)
456: - `checkpoints/qwen2vl_7b_projector_lora/final` (0MB adapter — merger
457:   weights, ~152K params) — evaluated (82.87%)
458: - `checkpoints/qwen2vl_7b_vision_proj_lora/final` (5MB) — evaluated (83.10%)
459: - All loading VERIFIED (evaluations ran through PeftModel.from_pretrained);
460:   seeds: single default seed per run; checkpoint dates in filenames
461: - HF cache checkpoints (models--Qwen--Qwen2-VL-7B-Instruct) are NOT project
462:   checkpoints
463: 
464: ---
465: 
466: ## 19. REPRODUCIBILITY
467: 
468: Partially reproducible:
469: - git commit: YES (all code committed)
470: - dataset ID + split: YES
471: - model ID: YES
472: - LoRA config: YES (adapter_config.json committed)
473: - prompt version: YES (in code)
474: - seed: PARTIAL (seed=42 defaults exist; not recorded in results metadata)
475: - checkpoint: YES (paths in §18)
476: - transformation settings: N/A (no transforms implemented)
477: - run metadata: NO for VSR runs (timestamps only); YES for SITE
478:   (results/site/run_metadata.json with config hash)
479: 
480: Missing reproducibility fields: per-run seed, exact HF dataset revision,
481: environment snapshot, wandb/tensorboard logs (none exist).
482: 
483: ---
484: 
485: ## 20. TEST COVERAGE
486: 
487: - Unit tests: NONE (no tests/ dir, no test_*.py files)
488: - Parser: tested implicitly by full evals (0 invalid), no unit tests
489: - Dataset loader: smoke-tested via `scripts/inspect_vsr.py` and evals
490: - Model wrapper / LoRA loading / metrics / interventions: no tests
491: - SITE eval: smoke-tested manually (10-example runs + video path test)
492: 
493: ---
494: 
495: ## 21. PERFORMANCE / GPU OBSERVATIONS
496: 
497: - 2B eval: batch 8, ~4.2 ex/s (VSR), trivially fits
498: - 7B VSR eval: batch 8, ~4.2 ex/s, ~24-38GB
499: - 7B SITE image eval: batch 8 single-image ~15 ex/s; batch 1 multi-image
500:   ~3.4s/ex (long sequences, eager attention); GPU ~100% at ~24-38GB
501: - OOM observed: batch-8 multi-image SITE (fixed with batch 1 + progressive
502:   downscale); 16-frame 224px videos OOM (fixed: 128px frames)
503: - CPU bottleneck: image loading gaps between batches (GPU dips to ~4% during
504:   load at batch 1)
505: - flash-attn: NOT available (install failed on CUDA 13 build)
506: 
507: ---
508: 
509: ## 22. CLOUD / FILE PERSISTENCE
510: 
511: - Repo: /home/ubuntu/vlm-spatial-reasoning (git-tracked; pushed to remote)
512: - HF cache: ~/.cache/huggingface (datasets, models — regenerable)
513: - Results: results/ (committed except in-flight CSV + site_media-adjacent)
514: - Checkpoints: checkpoints/ (committed — LoRA adapters only, small)
515: - Local-only / at risk if instance stops: data/image_cache (703MB,
516:   re-downloadable), data/site_media (43GB, re-downloadable via
517:   download_site_media_v2.py with the HF token), results/probe/patch_embeddings.pkl
518:   (8.2GB, regenerable via extract_patch_embeddings.py), in-flight SITE CSV
519: - All key artifacts are either committed or regenerable; nothing critical is
520:   only-local except the 3 large caches above.
521: 
522: ---
523: 
524: ## 23. SECRETS / API SETUP
525: 
526: - HF_TOKEN: configured (token file at ~/.cache/huggingface/token — value
527:   redacted; used for fast SITE media download)
528: - TNR_API_TOKEN: configured as environment variable (name only — value
529:   redacted; purpose not used by any repo code found)
530: - MiMo API: NOT configured
531: - WandB: NOT configured
532: - No .env files found in repo
533: 
534: ---
535: 
536: ## 24. MIMO STATUS
537: 
538: NOT IMPLEMENTED. No MiMo wrapper, no API config, no interface integration,
539: no retry/rate-limit logic, no result saving. (Planned as a frozen
540: strong-model external comparison later in the paper — nothing exists yet.)
541: 
542: ---
543: 
544: ## 25. 7B MODEL STATUS
545: 
546: - SELECTED: Qwen/Qwen2-VL-7B-Instruct
547: - DOWNLOADED: yes (HF cache)
548: - TESTED: extensively (zero-shot, 5 LoRA conditions, probes, consistency,
549:   two-stage, SITE)
550: - INTEGRATED: yes (inline in scripts; no dedicated wrapper class)
551: - LoRA-READY: yes (peft works; 5 trained conditions)
552: - No candidate ambiguity: this is the final selection, actively used.
553: 
554: ---
555: 
556: ## 26. KNOWN BUGS / TECHNICAL DEBT
557: 
558: ### Critical
559: - None found that invalidates existing results. (The SITE video handling
560:   would OOM/skip at 224px frames — fixed in code to 128px but video eval not
561:   yet run.)
562: 
563: ### High
564: - `src/datasets/vsr.py` split_map breaks under datasets 5.x ("dev"→"dev"
565:   raises; must use "validation") — affects any dev/validation evaluation.
566: - SITE eval's previous resume bug (incremental saves dropped pre-resumed
567:   rows) — FIXED in b8336bb but earlier partial CSVs were overwritten (the
568:   original 125 rows were regenerated; bit-equivalent, verified).
569: - No run metadata for VSR experiments (seed/prompt not recorded per run).
570: 
571: ### Medium
572: - `scripts/fetch_site_ranges.py` is dead code with known ZIP64/multipart
573:   issues (superseded by download_site_media_v2.py).
574: - `requirements.txt` is stale and misleading.
575: - Structured-prompt result (2B, 68.3%) is single-run, single-seed.
576: 
577: ### Low
578: - Editor droppings (.intro.md.un~, intro.md~, 200-600KB *.md context dumps)
579:   in repo root.
580: - Empty stubs (configs/, paper/, figures/, results/README.md).
581: - wandb/tensorboard dependencies listed but unused.
582: 
583: ---
584: 
585: ## 27. RESEARCH-METHODOLOGY RISKS FOUND IN CODE
586: 
587: 1. parallel↔perpendicular treated as strict complement in hard-negative
588:    TRAINING flips (soft complement in reality) — mitigated by audited-clean
589:    filtering, but the label-flip assumption is not strictly valid for all
590:    scenes.
591: 2. Planned paper conditions (text-only/blank/shuffled/inversion/reversal/
592:    reflection) are entirely absent — the paper's core contribution
593:    (before-vs-after grounding decomposition) cannot yet be written.
594: 3. Single seed everywhere — no seed variance reported.
595: 4. No paired statistical tests on 2B results (only 7B has McNemar).
596: 5. 2B structured prompt regression (False-class collapse to 41.6%) is
597:    single-run; could be prompt-artifact.
598: 6. Probe conclusions rest on model-generated grounding boxes (Qwen2-VL
599:    self-grounding) — a detection-model cross-check was never run
600:    (ground_objects_owl.py exists but unverified).
601: 7. SITE secondary (orientation heuristic) subset is keyword-derived — must
602:    stay labeled non-official (already handled in protocol).
603: 8. 2B vs 7B comparisons use different wrappers/eval scripts — prompt and
604:    max_new_tokens differ (5 vs 128/16), though base-vs-tuned within model is
605:    consistent.
606: 9. VSR subject/object parsing is heuristic; relation-inversion audits built
607:    on parsed pairs inherit its failure modes (plurals).
608: 10. image_cache pre-download could silently miss images on other machines
609:     (no integrity check in evaluators; evals just skip missing → would
610:     change n).
611: 
612: ---
613: 
614: ## 28. WHAT IS MISSING RELATIVE TO THE PLANNED PAPER
615: 
616: | Item | Status |
617: |---|---|
618: | ~2B base baseline | DONE |
619: | ~2B spatial-LoRA (×3 seeds) | PARTIAL (1 seed) |
620: | ~7B base baseline | DONE |
621: | ~7B spatial-LoRA (×3 seeds) | PARTIAL (1 seed) |
622: | Standard VSR eval | DONE |
623: | Text-only | NOT STARTED |
624: | Blank image | NOT STARTED |
625: | Shuffled image | NOT STARTED |
626: | Relation inversion | PARTIAL (hardneg flips + consistency flips only) |
627: | Subject/object reversal | NOT STARTED |
628: | Horizontal reflection | NOT STARTED |
629: | VSR zero-shot/config-shift | NOT STARTED (split doesn't exist) |
630: | Controlled OOD audit | NOT STARTED |
631: | Paired base-vs-tuned metrics | NOT STARTED |
632: | Statistical CIs/significance | PARTIAL (7B only) |
633: | MiMo frozen reference | NOT STARTED |
634: 
635: ## 29. EXACT NEXT STEPS
636: 
637: 1. Finish the running SITE image eval; produce metrics (overall, primary,
638:    secondary, CAA, Wilson CIs, single-vs-multi-image, source breakdown) via
639:    `scripts/eval_site_zeroshot.py` output + a small metrics script. Cheap;
640:    GPU running now. Success: metrics JSON + report committed.
641: 2. Decide (with the user) whether SITE video subset + VSR-trained 7B LoRA on
642:    SITE are justified; if yes, run eval with `--max-new-tokens 16` and
643:    video frames at 128px. Medium cost (~2-3h GPU).
644: 3. Implement the text-only condition (prompt with image removed / image
645:    token omitted) for 2B + 7B base and LoRAs. Cheap (eval only). Files:
646:    new script or flag in run_baseline/eval_lora. Success: CSV + gap metrics.
647: 4. Implement blank-image and shuffled-image conditions with deterministic
648:    seeded transforms and correct ground-truth semantics. Medium. Files:
649:    `src/evaluation/` new module + eval wrappers.
650: 5. Implement relation-inversion eval maps (explicit valid inverse mapping per
651:    relation — only orientation pairs have valid inverses; document which
652:    relations are excluded) and subject/object reversal eval. Medium.
653: 6. Implement horizontal-reflection transforms + label-change logic (only for
654:    relations whose truth should flip; e.g., left/right flip, facing does
655:    NOT necessarily flip). Medium.
656: 7. Add per-run metadata (seed, prompt hash, dataset revision) + paired
657:    McNemar + CI to 2B eval outputs. Cheap.
658: 8. Add unit tests for parser, VSR loader, flip/inversion maps. Cheap.
659: 9. After audits: seed-varied LoRA training (3 seeds) for the final
660:    conditions. Expensive (GPU, hours per run).
661: 10. MiMo integration (API wrapper + results saving + rate-limit handling).
662:     Cheap-medium; needs API key.
663: 
664: ---
665: 
666: ## 30. COMMAND CHEAT SHEET
667: 
668: (All from repo root; environment is the system python — no venv/conda in use.)
669: 
670: - Inspect dataset:
671:   `python scripts/inspect_vsr.py`
672: - Run tests: none exist (no tests/)
673: - 2B smoke (10): `python scripts/run_baseline.py --num-examples 10`
674: - 2B 200: `python scripts/run_baseline.py --num-examples 200`
675: - 2B full: `python scripts/run_baseline.py`
676: - 7B zero-shot + LoRA pipeline: `python scripts/run_7b_pipeline.py` (full
677:   pipeline; heavy)
678: - Evaluate any LoRA: `python scripts/eval_lora.py --base-model Qwen/Qwen2-VL-7B-Instruct --lora-path checkpoints/qwen2vl_7b_general_lora/final --output-dir results --batch-size 8`
679: - Train 7B vision-side LoRA: `python scripts/train_vision_lora.py --target projector|vision_proj`
680: - SITE eval (running): `python scripts/eval_site_zeroshot.py --out results/site/zeroshot_7b_predictions.csv --max-new-tokens 16 --images-only`
681: - SITE inspect: `python scripts/inspect_site.py`
682: - Consistency flips: `python scripts/eval_consistency_flips.py --condition LM_only_LoRA`
683: - Probes: `python scripts/run_probe.py` ; `python scripts/run_patch_probe.py` ; `python scripts/run_grounded_probe.py`
684: - Two-stage: `python scripts/two_stage_reasoning.py`
685: - SITE media download: `python scripts/download_site_media_v2.py`
686: - Summarize a results CSV: metrics JSONs already contain summaries; no
687:   dedicated summarize CLI exists.
688: 
689: ---
690: 
691: ## 31. FILES THE NEXT AI SHOULD READ FIRST
692: 
693: 1. `results/hardneg_analysis_report.md` — the cleanest summary of the 7B
694:    LoRA program + orientation numbers.
695: 2. `results/orientation_deep_dive_report.md` — 48 annotated failures,
696:    failure-mode taxonomy, the motivation for everything after.
697: 3. `results/probe_analysis_report.md` + `results/grounded_probe_report.md` —
698:    probe methodology and conclusions.
699: 4. `results/two_stage_report.md` — explicit-reasoning null result.
700: 5. `results/consistency_report.md` — coherence finding.
701: 6. `results/vision_side_report.md` — vision-adaptation null result.
702: 7. `results/site/site_protocol.md` + `site_dataset_report.md` — SITE
703:    preregistration + subsets.
704: 8. `scripts/run_7b_pipeline.py` — the 7B train/eval machinery (32KB; read
705:    phase functions).
706: 9. `scripts/eval_lora.py` — generic LoRA evaluator.
707: 10. `scripts/run_baseline.py` — 2B evaluator.
708: 11. `src/datasets/vsr.py` + `src/datasets/site.py` — loaders.
709: 12. `src/models/smolvlm.py` — the only model wrapper.
710: 13. `src/evaluation/parser.py` — output parser.
711: 14. `src/training/lora.py` + `src/training/collator.py` — 2B training.
712: 15. `scripts/build_hardneg_manifest.py` — flip/inversion logic.
713: 16. `scripts/eval_site_zeroshot.py` — current SITE eval (running).
714: 17. `scripts/eval_consistency_flips.py` — complement-flip analysis code.
715: 18. `checkpoints/*/final/adapter_config.json` — LoRA configs (r=8, alpha=16).
716: 19. `results/site/run_metadata.json` — SITE protocol/frozen config hash.
717: 20. `README.md` + `requirements.txt` — context (stale; trust code over README).
718: 
719: ---
720: 
721: ## 32. FULL CONTENT OF CRITICAL SMALL FILES
722: 
723: ### `src/evaluation/parser.py` (96 lines — full behavior described in §10;
724: key logic: normalized = strip().lower(); prefix strip
725: `^(the answer is|answer:|response:|output:)`; anchored pattern lists; then
726: substring fallback true/false; else None.)
727: 
728: ### `src/models/smolvlm.py` (176 lines — §8/§9. Key: SPATIAL_PROMPT and
729: STRUCTURED_PROMPT templates; predict/predict_batch via apply_chat_template,
730: padding_side=left, do_sample=False, max_new_tokens=5; _extract_answer strips
731: "Assistant:" prefix or takes last non-empty line.)
732: 
733: ### `src/datasets/vsr.py` (146 lines — §6. Key functions: load_vsr (split_map,
734: fields image/statement/label/relation/subject/object; subject/object parsed
735: by splitting on " is "), load_vsr_splits, get_relation_frequency.)
736: 
737: ### LoRA config (from adapter_config.json, all conditions):
738: `r=8, lora_alpha=16, lora_dropout=0.05, target_modules=[q_proj,v_proj,k_proj,o_proj]`
739: (7B vision variants: merger mlp.0/2; vision+proj adds blocks 24-31
740: attn.qkv/attn.proj/mlp.fc1/mlp.fc2).
741: 
742: ### `src/training/lora.py` (2B, ~280 lines — §17; key defaults: epochs=2,
743: lr=1e-4, micro_batch=4, grad_accum=4, warmup 10%, r=8 α=16 dropout 0.05,
744: seed 42, train_test_split 0.05, saves HF-Trainer checkpoints every 100
745: steps + final.)
746: 
747: ### `src/training/collator.py` — labels masked to answer tokens only
748: (encode " True"/" False", -100 on prompt tokens).
749: 
750: ### `configs/`: only README.md stub — no configs exist.
751: 
752: ---
753: 
754: ## 33. FINAL HANDOFF SNAPSHOT
755: 
756: ## Current milestone
757: 
758: 7B orientation causal-decomposition program complete (probes, vision-side
759: LoRAs, two-stage, consistency); SITE external-validation zero-shot image
760: eval RUNNING (~75% through, resumable, protocol preregistered and frozen);
761: planned paper's grounding-audit conditions not yet built.
762: 
763: ## Working 2B model
764: 
765: HuggingFaceTB/SmolVLM2-2.2B-Instruct — zero-shot 73.99%, General LoRA
766: 76.63%, Targeted LoRA 76.54%, structured prompt 68.34% (all VSR test n=2195,
767: invalid rate 0).
768: 
769: ## Planned/working 7B model
770: 
771: Qwen/Qwen2-VL-7B-Instruct — selected, downloaded, tested, LoRA-ready.
772: Zero-shot 80.91%; General LoRA 84.69%; Targeted ~84%; Hard-neg 84.33%;
773: Projector 82.87%; Vision+Projector 83.10%. Orientation family stuck ~65.7%.
774: 
775: ## Dataset state
776: 
777: VSR: train 7,680 / validation 1,097 / test 2,195, 64 relations, balanced
778: labels; images cached locally; no zero-shot split exists. SITE (external):
779: 8,068 examples, two official test configs, media cached (43GB), protocol
780: frozen (primary 1,721 / secondary heuristic 3,272 / exploratory 1,103).
781: 
782: ## Baseline result
783: 
784: 2B 73.99% / 7B 80.91% zero-shot on VSR test; orientation per-relation weak
785: (facing-away 48.7%→59.0% with 7B LoRA).
786: 
787: ## Grounding audit state
788: 
789: NOT IMPLEMENTED (text-only/blank/shuffled/inversion/reversal/reflection all
790: absent); complement-flip consistency analysis DONE (7B).
791: 
792: ## Fine-tuning state
793: 
794: LoRA r=8 α=16 on q/k/v/o (LM) for 2B and 7B; 5 7B conditions + 2 2B
795: conditions trained and evaluated; vision tower frozen; single seed; recipe
796: documented (lr 1e-4, 2 epochs, warmup 10%).
797: 
798: ## Existing checkpoints
799: 
800: 2B general/targeted (HF-Trainer style, 512MB dirs); 7B general, targeted,
801: hardneg, projector, vision+projector adapters (19MB/0MB/5MB) — all verified
802: loadable and evaluated.
803: 
804: ## Compute
805: 
806: 1× RTX A6000 48GB (full spec verified); 6 vCPU; 48GB RAM; 200GB disk
807: (124GB free); torch 2.12.1+cu130, transformers 5.14.1, datasets 5.0.1, peft
808: 0.20.0; flash-attn unavailable.
809: 
810: ## Biggest methodological risk
811: 
812: The planned paper's core contribution — before-vs-after spatial
813: fine-tuning grounding decomposition (text-only/blank/shuffled/inversion/
814: reversal/reflection conditions, paired metrics, seed variation) — does not
815: exist in the repo yet; the existing strong negative results are on a
816: different (orientation-causality) question and must not be conflated with
817: the planned paper's claims.
818: 
819: ## Biggest technical blocker
820: 
821: transformers 5.14.1 / datasets 5.x API drift (validation split naming,
822: Qwen2-VL grounding/video processor changes) plus no test suite and no run
823: metadata for VSR experiments; SITE media requires the HF token to
824: re-download (43GB, gitignored).
825: 
826: ## Immediate next experiment
827: 
828: Finish SITE 7B zero-shot image eval → report preregistered metrics →
829: decide whether 7B VSR-LoRA on SITE and the SITE video subset are justified.
830: 
831: ## Files I should send/read first
832: 
833: results/hardneg_analysis_report.md, results/orientation_deep_dive_report.md,
834: results/probe_analysis_report.md, results/two_stage_report.md,
835: results/consistency_report.md, results/vision_side_report.md,
836: results/site/site_protocol.md, scripts/run_7b_pipeline.py,
837: scripts/eval_lora.py, scripts/run_baseline.py, src/datasets/vsr.py,
838: src/models/smolvlm.py, src/evaluation/parser.py, src/training/lora.py,
839: scripts/build_hardneg_manifest.py, scripts/eval_site_zeroshot.py,
840: scripts/eval_consistency_flips.py, results/site/run_metadata.json,
841: checkpoints/*/final/adapter_config.json, this file.
842: 
843: 

(End of file - total 843 lines)
</content>
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 8.3s)

_Thinking:_

There's a comprehensive handoff doc. Let me check what's changed since (results/site status, BRANCH_MAP, leadfromhere) briefly to say "what is going on" now.

**Tool: bash**

**Input:**
```json
{
  "command": "ls results/site/ && git log --oneline -3 --all | head -5",
  "description": "Lists SITE results and recent commits"
}
```

**Output:**
```
needed_media.txt
orientation_subset_definition.md
run_metadata.json
site_dataset_report.md
site_eval_run_notes.md
site_inspection.json
site_protocol.json
site_protocol.md
vsr_lora_predictions.csv
vsr_lora_transfer_report.md
vsr_lora_vs_zeroshot.json
zeroshot_7b_metrics_20260810_054124.json
zeroshot_7b_predictions.csv
zeroshot_image_metrics.json
zeroshot_image_report.md
b024525 diagnostics: latent collapse data + v2 easyA result + dev log update
544a05f fix: increment n_processed for shape probe
c7e7c8f fix: track actual processed scenes in probe for correct train/test split

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 10.3s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/results/site/zeroshot_image_report.md"
}
```

**Output:**
```
<path>/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/results/site/zeroshot_image_report.md</path>
<type>file</type>
<content>
1: # SITE External Validation — 7B Zero-Shot Image Results (Preregistered Step 1)
2: 
3: **Status: IMAGE SUBSET COMPLETE.** Videos and the 7B VSR-LoRA condition are
4: NOT run (deferred per protocol until this review).
5: 
6: ## Protocol reference
7: 
8: - Frozen subsets: `results/site/site_protocol.json` (config hash
9:   `28f4cc09887477af` in `results/site/run_metadata.json`)
10: - Model: Qwen2-VL-7B-Instruct, frozen, zero-shot, greedy
11: - Format: SITE native multiple-choice; official prompt + parsing
12: - Efficiency changes (protocol-neutral, recorded): max_new_tokens 16
13:   (validated 125/125 identical parses), 392px image cap (constant; this
14:   transformers build ignores max_pixels), sdpa backend
15: - Images only: single-image 1,368 + multi-image 1,223 = 2,591 examples
16: 
17: ## Results
18: 
19: | Subset | n | Raw acc | 95% Wilson CI | CAA |
20: |---|---|---|---|---|
21: | **All images** | 2,591 | 54.2% | [52.3, 56.1] | 31.1% |
22: | **Primary: spatial relationship reasoning** (official) | 993 | 75.1% | [72.3, 77.7] | **59.2%** |
23: | **Secondary: orientation heuristic** (non-official) | 1,824 | 47.3% | [45.0, 49.6] | **22.6%** |
24: 
25: CAA (chance-adjusted accuracy) = Σ(score − 1/n_opts) / Σ(1 − 1/n_opts),
26: official SITE metric.
27: 
28: ### By modality (all images)
29: 
30: | Modality | n | Raw acc | CAA |
31: |---|---|---|---|
32: | single-image | 1,368 | 61.3% | 37.4% |
33: | multi-image | 1,223 | 46.4% | 25.0% |
34: 
35: ### By source dataset (n ≥ 30)
36: 
37: | Source | n | Raw | CAA | | Source | n | Raw | CAA |
38: |---|---|---|---|---|---|---|---|---|
39: | CLEVR | 108 | 92.6% | 88.3% | | MMTBench | 251 | 51.4% | 33.4% |
40: | IconQA | 141 | 91.5% | 86.8% | | SpatialEval | 100 | 53.0% | 29.3% |
41: | VSR (in SITE) | 71 | 85.9% | 71.8% | | SPEC | 133 | 51.1% | 34.8% |
42: | GQA | 61 | 82.0% | 66.7% | | SAT | 183 | 46.5% | −7.1% |
43: | MME | 46 | 82.6% | 65.2% | | VStarBench | 39 | 46.2% | −7.7% |
44: | VQA | 105 | 80.0% | 68.1% | | MuirBench | 69 | 37.7% | 18.1% |
45: | CVBench | 35 | 77.1% | 54.3% | | exoego4d | 316 | 36.4% | 15.2% |
46: | MMVP | 61 | 72.1% | 44.3% | | egoexo4d | 288 | 34.7% | 13.0% |
47: | ThreeDSRBench | 141 | 63.1% | 31.8% | | MMIU | 152 | 34.2% | 4.4% |
48: | SeedBench | 89 | 61.8% | 49.1% | | MMERealWorld | 89 | 32.6% | 15.7% |
49: | Blink | 51 | 60.8% | 23.8% | | LogicVista | 37 | 18.9% | −7.0% |
50: 
51: ## Decision-rule outcome (preregistered)
52: 
53: 1. **Primary subset (official spatial relationship reasoning): NOT broadly
54:    weak.** CAA 59.2% — comparable to or above published open-source results
55:    on this category (e.g., Qwen2.5-VL-7B 51.5% CAA per the SITE leaderboard).
56: 2. **Orientation heuristic subset: weak.** CAA 22.6% vs 31.1% overall and
57:    59.2% primary — a large, consistent drop, driven by orientation/
58:    direction-vocabulary questions (facing, direction, view, rotation,
59:    left/right, parallel/perpendicular...).
60: 
61: **Conclusion (matches decision-rule branch 2):** the VSR orientation finding
62: **generalizes to SITE**, but specifically for **object/direction-related
63: orientation** — not spatial relationship reasoning broadly. The claim is
64: narrowed accordingly: *VLMs show a persistent, benchmark-independent weakness
65: in object-intrinsic orientation (facing/direction), while general spatial
66: relationship reasoning is comparatively strong.*
67: 
68: ## Caveats
69: 
70: - The orientation subset is keyword-derived (non-official tag); labeled as
71:   such; supporting analysis, not the headline.
72: - 392px input cap (constant protocol parameter) may under-serve fine
73:   orientation cues; effect should be uniform across subsets, and the
74:   orientation deficit is large enough that it cannot be explained by
75:   resolution alone (high-resolution multi-image subsets like CLEVR do fine).
76: - Videos deferred; movement/navigation orientation in video is a separate
77:   extension.
78: 
79: ## Next steps (per protocol, awaiting decision)
80: 
81: - If the primary-subset weakness claim is desired at higher fidelity: rerun
82:   the primary subset at native resolution (max_pixels regression documented).
83: - 7B VSR-LoRA on SITE: only if justified after this review.
84: - Video subset: secondary extension, deferred.
85: 
86: ## Files
87: 
88: - Predictions: `results/site/zeroshot_7b_predictions.csv` (2,591 rows)
89: - Metrics: `results/site/zeroshot_image_metrics.json`
90: - Run metadata + config hash: `results/site/run_metadata.json`

(End of file - total 90 lines)
</content>
```

**Tool: bash**

**Input:**
```json
{
  "command": "git log --oneline -20 master",
  "description": "Shows last 20 commits on master"
}
```

**Output:**
```
8be6b05 master: backfill frozen protocol manifests from paper2/wacv2027 (results/grounding/protocol/) — vsr_test_ids, visual/semantic/facing eligible IDs, shuffle mapping, blank-image spec, validity tables, visual spot checks; required by shared tests (test_visual/test_semantic/test_shuffle/test_facing); prediction/analysis outputs intentionally stay on paper branches
f62cfdd repo: BRANCH_MAP.md — equiorient governance: Paper-3 line pulls shared code from master (d76c1e6), Paper-1-era artifacts cleaned (6124eab), status = MUTATE verdict pending protocol amendment
41b7307 repo: BRANCH_MAP.md — add governance model (master = shared trunk; paper branches = paper-specific only; merge shared code back to master; branch fresh from master)
4408735 master: backfill shared research layer from paper2/wacv2027 — grounding pipeline (src/grounding, src/evaluation/battery.py), scripts/grounding (tier analyzers, seed battery, q3vl extension), audit scripts (independent audit, hostile reviewer, claim hierarchy, figures), configs (grounding_protocol.yaml, seed_campaign), tests (parser/metrics/interventions/shuffle/facing/visual/statistics), research docs (protocol freeze, execution guide, decision log). All 60 files are pure additions vs master base (0 modifications/0 deletions) — no history rewrite; paper-2-specific artifacts (submission kit, seed_campaign outputs, decision log, checkpoints) intentionally stay on paper2 branch
98fed02 repo: BRANCH_MAP.md — kit ownership corrected (Paper-1 kit on paper1/wacv2027, Paper-2 kit on paper2/wacv2027; duplicate paper2_source hash-verified and dropped)
cd365f6 repo: add BRANCH_MAP.md documenting canonical branch scheme (master / paper1/wacv2027 / paper2/wacv2027 / research/equiorient) + archive tags + rename history + submission state
592e6bb Merge remote-tracking branch 'origin/master'
0fe1ed3 paper: CVPR 2026 manuscript from committed artifacts — 8pp main (official author kit) + 6pp hardened supplementary; every headline number traced to results CSVs/JSONs (numerical audit + make_paper_figures.py recompute script); SITE secondary subset discrepancy resolved to CSV+protocol-canonical n=2,024 (48.3%/CAA 24.0), documented in paper
9be69a2 Fix four-way probe baseline terminology
4aebb9e Correct clean-label table strict subset header to n=107
288a3cd Fix clean-label strict subset header count (107, not 114)
9b6f0d8 Fix claim precision in paper summary (reviewer-safe wording)
3c6bb35 Freeze experimental phase: canonical tables, clean-label robustness, 5 publication figures, paper summary
828e072 SITE LoRA cross-dataset transfer: VSR-trained adapter does not transfer, hurts official category
04cf63a Document orientation heuristic subset + technical conventions
46e3b49 SITE image-subset zero-shot results: orientation weakness generalizes, spatial-relationship reasoning strong
8c9c4a6 Add SITE evaluation engineering run notes (issues + fixes)
1ca57c0 Add current research handoff audit report; update in-flight SITE eval predictions
b8336bb SITE eval: protocol update (max_new_tokens 16), batch-8 single-image, resume + incremental saves
8d7f173 Preregister SITE external-validation protocol (frozen subsets, metrics, decision rule)

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 6.1s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/BRANCH_MAP.md"
}
```

**Output:**
```
<path>/Users/kgensupertramp/Desktop/vlm-spatial-reasoning/BRANCH_MAP.md</path>
<type>file</type>
<content>
1: # Repository Branch Map
2: 
3: Last updated: 2026-08-14 (branch reorganization + master backfill)
4: 
5: ## Governance model (how the repo grows)
6: 
7: ```
8: master  ← TRUNK: single source of truth for ALL shared research code,
9:            protocol definitions, configs, tests, and shared docs.
10:            (src/, scripts/, configs/, tests/, research/ live ONLY here.)
11:    │
12:    ├── paper1/wacv2027   ← Paper-1-specific: manuscript, external-eval CSVs,
13:    │                        submission kit FINAL_WACV2027_SUBMISSION/
14:    ├── paper2/wacv2027   ← Paper-2-specific: seed-campaign outputs,
15:    │                        submission kit FINAL_WACV2027_SUBMISSION_PAPER2/
16:    └── (future papers branch from master, same pattern)
17: ```
18: 
19: **Rules:**
20: 1. New shared research code (scripts, src, configs, tests, protocol docs)
21:    → developed on a branch → **merged back to master when stable**.
22: 2. Paper branches hold ONLY paper-specific artifacts: manuscripts,
23:    per-paper analysis outputs, submission kits. Never duplicated shared code.
24: 3. Before starting any new paper: branch fresh from **master** (pulls all
25:    shared code), not from an older paper branch.
26: 4. Pull master into a paper branch when shared code updates are needed
27:    (rare mid-paper; the frozen submission layer never syncs mid-deadline).
28: 5. `research/equiorient` = Paper-3 research line (EquiOrient): pulls shared
29:    code from master (merged 2026-08-14, `d76c1e6`), pushes stable infra back
30:    to master, and carries NO paper-specific artifacts (Paper-1-era leftovers
31:    removed `6124eab`; canonical copies on paper1/wacv2027).
32: 
33: ## Branch contents
34: 
35: | Branch | What it is | Workspace clone |
36: |---|---|---|
37: | `master` | Trunk. Default branch on GitHub. Shared code + protocol + tests + shared docs. | both |
38: | `paper1/wacv2027` | **Paper 1**: "Beyond Spatial Accuracy..." (WACV 2027 Datasets Track). Manuscript at `submission/wacv2027/source/`, external flagship eval CSVs, Paper-1 submission kit `FINAL_WACV2027_SUBMISSION/`. | `Desktop\VLM-Spatial-Reasoning` |
39: | `paper2/wacv2027` | **Paper 2**: "What Spatial Fine-Tuning Actually Changes" (WACV 2027 Datasets Track). Seed campaign outputs, audit artifacts, Paper-2 submission kit `FINAL_WACV2027_SUBMISSION_PAPER2/`. | `Documents\vlm-spatial-reasoning` |
40: | `research/equiorient` | **Paper 3** (EquiOrient): method paper on transformation-equivariant spatial representation learning. Status: novelty gate CLOSED (MUTATE verdict); protocol/config amendment + transformation algebra pending before GPU. Own docs under `research/EQUIORIENT_*` + `configs/equiorient_protocol.yaml` + shared layer from master. | — |
41: 
42: ## Kit ownership
43: 
44: - Paper-1 kit `FINAL_WACV2027_SUBMISSION/` lives on **`paper1/wacv2027`** (moved verbatim from the Paper-2 line; commits `00d85b8` on paper1, `44df918` on paper2).
45: - Paper-2 kit `FINAL_WACV2027_SUBMISSION_PAPER2/` lives on **`paper2/wacv2027`**.
46: - The old `FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/paper2_source/` copy was a byte-identical duplicate (hash-verified); deleted, zero loss.
47: 
48: ## Master backfill (2026-08-14, commit `4408735`)
49: 
50: Master was stale relative to the shared research layer built on the Paper-2
51: line. Backfilled with 60 files that were **pure additions** vs the master
52: base (verified: 0 modifications, 0 deletions — no conflicts, no history
53: rewrite): `src/grounding/`, `src/evaluation/battery.py`, `scripts/grounding/`,
54: audit scripts, `configs/` (grounding protocol + seed campaign), `tests/`,
55: `research/` docs. Paper-2-specific artifacts intentionally left on paper2.
56: 
57: ## Archive tags (old branch names, preserved forever)
58: 
59: | Tag | Points at |
60: |---|---|
61: | `archive/paper-draft-v1` | former Paper-1 branch tip `e3bd95b` |
62: | `archive/research-spatial-grounding-audit` | former Paper-2 branch tip `586ad24` |
63: | `archive/external-eval-flagship-v1` | former external-eval branch tip `dd8517a` |
64: | `archive/research-equiorient` | former equiorient tip `1161b24` |
65: 
66: ## Renaming history (2026-08-14)
67: 
68: - `paper-draft-v1` → `paper1/wacv2027` (Paper 1)
69: - `research/spatial-grounding-audit` → `paper2/wacv2027` (Paper 2)
70: - `external-eval/flagship-v1` → `paper1/external-eval` → **deleted** (fully merged into `paper1/wacv2027`; raw provenance CSVs live at repo root on that branch and canonical copies under `results/iaa/`; archive tag preserved)
71: - `research/equiorient` → kept unchanged
72: - Open DRAFT PR #1 ("Start conference-style paper draft", head `paper-draft-v1`) auto-closed by branch deletion; its content is fully in `paper1/wacv2027`.
73: 
74: ## Submission state (2026-08-14)
75: 
76: Both papers target WACV 2027 (Datasets Track), same deadline card:
77: 
78: | Date (AoE) | Action |
79: |---|---|
80: | Aug 21 | OpenReview enrollment (paste title/abstract, final author list) |
81: | Aug 28 | Upload main.pdf |
82: | Aug 30 | Upload supplementary.pdf + code zip |
83: 
84: - Paper 1 kit: `FINAL_WACV2027_SUBMISSION/` (PDFs, checklists, hashes in `03_DOCS_CHECKLISTS/`)
85: - Paper 2 kit: `FINAL_WACV2027_SUBMISSION_PAPER2/` (same layout; compiled main.pdf 5pp + supplementary.pdf 1p + wacv2027_code.zip, SHA-256s in checklist)
86: - GPU compute: OFF for both.

(End of file - total 86 lines)
</content>
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 23.3s)

_Thinking:_

I have a comprehensive picture now. Summarize concisely but with enough detail — user asked "explain this repo, what is done and what is going on". This warrants a moderately detailed answer despite the brevity instruction (user asks for explanation/detail).

## What this repo is

A research program studying **spatial reasoning in Vision-Language Models**, centered on the VSR benchmark (`cambridgeltl/vsr_random`, True/False spatial captions) and the finding that **orientation relations (facing / facing away / parallel / perpendicular) are a persistent, benchmark-independent weakness** of VLMs. Models: SmolVLM2-2.2B and Qwen2-VL-7B-Instruct, fine-tuned with LoRA (r=8, α=16).

## What's been done

**Experiments & results** (all on VSR test, n=2195):
- Zero-shot: 2B 74.0%, 7B 80.9% → LoRA-tuned 7B reaches 84.7% overall, but orientation stays stuck ~65.7%
- Causal decomposition of the orientation failure:
  - Linear/patch/object-grounded probes on frozen features ≈ chance
  - Vision-side LoRA (projector, vision+projector) doesn't help and hurts accuracy
  - Explicit two-stage reasoning is worse than generative control
  - Complement-flip consistency: zero-shot contradicts itself on facing pairs 63%; hard-negative LoRA fixes coherence (→77.7%) *without* changing accuracy — coherence and accuracy are separable
- **SITE (ICCV 2025) external validation** (preregistered protocol): orientation weakness generalizes — primary spatial-reasoning subset CAA 59.2% (strong), keyword-derived orientation subset CAA only 22.6%. VSR-trained LoRA does **not** transfer to SITE.
- A CVPR-style paper draft was compiled from committed artifacts; the claim narrowed to: *"VLMs have a persistent weakness in object-intrinsic orientation while general spatial relationship reasoning is comparatively strong."*

## What's going on right now

The repo was reorganized into a **multi-paper pipeline** (see `BRANCH_MAP.md`, updated 2026-08-14):
- `master` = shared trunk (code, protocols, tests, grounding battery backfilled from Paper-2)
- `paper1/wacv2027` — "Beyond Spatial Accuracy..." submission kit done
- `paper2/wacv2027` — "What Spatial Fine-Tuning Actually Changes" (the grounding audit originally planned here got built there: text-only/blank/shuffled/inversion/reflection conditions, seed campaign)
- `research/equiorient` — **Paper 3**: transformation-equivariant spatial representation learning; novelty gate closed with a **MUTATE verdict**; latest commit (`b024525`) shows active work: latent-collapse diagnostics + a "v2 easyA" result

Both WACV 2027 submissions are due Aug 28–30; enrollment was due Aug 21.

## Known gaps / debt

- Stale `requirements.txt`, no unit tests until the recent master backfill, single-seed results in places, datasets 5.x breaks `"dev"` split naming, flash-attn unavailable on CUDA 13.
- `CURRENT_RESEARCH_HANDOFF.md` (2026-08-10 audit) is the authoritative deep-dive if you want per-file detail.

---

## User

do u have acess to all 3 latest papers

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 8.8s)

_Thinking:_

The user asks whether I have access to all 3 latest papers. The papers live on branches: paper1/wacv2027, paper2/wacv2027, research/equiorient. Let me check what's available locally.

**Tool: bash**

**Input:**
```json
{
  "command": "git branch -a && git log --oneline -3 paper1/wacv2027 paper2/wacv2027 research/equiorient 2>/dev/null",
  "description": "Lists local and remote branches"
}
```

**Output:**
```
* master
  remotes/origin/HEAD -> origin/master
  remotes/origin/clean-confirmatory
  remotes/origin/master
  remotes/origin/paper1/wacv2027
  remotes/origin/paper2/wacv2027
  remotes/origin/research/equiorient
  remotes/origin/research/equiorient-no-box
  remotes/origin/research/equiorient-phase2

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 5.7s)

**Tool: bash**

**Input:**
```json
{
  "command": "git log --oneline -3 origin/paper1/wacv2027; echo ---; git log --oneline -3 origin/paper2/wacv2027; echo ---; git log --oneline -3 origin/research/equiorient",
  "description": "Shows latest commits on each paper branch"
}
```

**Output:**
```
5195640 docs: Thunder Compute startup runbook — one-by-one instance procedure distilled from session-ses_008a (create → stage → queue/supervisor → monitor → collect → snapshot/teardown), failure playbook + gotchas; GPU freeze status noted from ses_006f
41ecc78 repo: BRANCH_MAP.md — equiorient governance update
e5bf4e4 repo: BRANCH_MAP.md — add governance model (master = shared trunk; paper branches = paper-specific only; merge shared code back to master; branch fresh from master)
---
44df918 paper2: drop stray Paper-1 submission kit (FINAL_WACV2027_SUBMISSION) — moved verbatim to paper1/wacv2027 (commit 00d85b8); paper2_source subdir inside it was a byte-identical duplicate of FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source (hash-verified, zero loss)
5e39746 paper2: record branch reorganization (paper2/wacv2027 scheme, archive tags, PR1 closed) in decision log
b868461 paper2: remaining tasks — LaTeX compiled (MiKTeX pdflatex 26.5): main.pdf 5pp + suppl.pdf 1p, 0 undefined citations, 0 overfull boxes (tabcolsep fixes in 4_results.tex; suppl.tex macro-definition + nested-math \dG + \allowbreak fixes; stale commit hash 0db0fff->95b66bc); FINAL_WACV2027_SUBMISSION_PAPER2 kit built mirroring Paper-1 convention: 01_UPLOAD_THIS (main.pdf D6AF008E, supplementary.pdf A4A55543, wacv2027_code.zip 9ABAE8E3 - 39 entries incl. seed-campaign scripts/results/protocol manifests), 02_OPENREVIEW_ENROLLMENT (paste-ready title/abstract), 03_DOCS_CHECKLISTS (SHA-256s, anonymity, reproducibility), set_paper_id.py adapted to MiKTeX (hostile-tested end-to-end with ID 1234, reverted to anonymous; fixed re.sub \d escape + suppl build-name mapping); decision log updated; GPU stays OFF; remaining steps are calendar actions (enroll Aug 21, main.pdf Aug 28, suppl+code Aug 30)
---
ee669cf submission: Paper-3 supplementary compiled (suppl.pdf, 2 pages) — full matrices both regimes, per-transform correct/wrong rho tables, per-epoch loss curves, depth-probe n/CI details, algebra verification counts, compute ledger + voided-run provenance, reproducibility summary; OpenReview checklist updated
73e849c submission: WACV 2027 R2 E&D OpenReview kit — title + abstract (extract_openreview.py resolves macros to plain text, 1585 chars), track/keywords guidance, deadline table (reg Aug 21 / paper Aug 28 / suppl Aug 30 AoE), files + pre-enrollment action checklist
cd4eda6 paper: orchestrator verdict edits — title -> 'EquiOrient: Latent Transformation Equivariance without Measurable Downstream Transfer'; abstract: drop duplicate 'a', bug-history sentence compressed to manipulation-verified implementation phrasing; intro 'first valid test' -> 'valid controlled test'; contribution 2 'first valid measurement' -> 'controlled measurement'; contribution 4 de-emphasizes Modal/cost (protocol, harness, matrices, reproducible pipeline); SAGE sentence 'exactly' -> 'provides a SAGE-style output-level consistency control'; conclusion + abstract + section headers aligned to 'measurable downstream transfer'; 5 pages, compiles clean

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 12.4s)

_Thinking:_

All three branches exist as remote-tracking branches locally, so yes I can access them. Let me verify the paper manuscripts (PDFs/LaTeX) exist. Quick check of key paths.

**Tool: bash**

**Input:**
```json
{
  "command": "git ls-tree -r --name-only origin/paper1/wacv2027 | grep -iE '\\.(pdf|tex)$' | head; echo ---; git ls-tree -r --name-only origin/paper2/wacv2027 | grep -iE 'main\\.(pdf|tex)$|suppl.*\\.pdf$' | head; echo ---; git ls-tree -r --name-only origin/research/equiorient | grep -iE '\\.pdf$' | head",
  "description": "Checks for manuscript files on each branch"
}
```

**Output:**
```
FINAL_WACV2027_SUBMISSION/01_UPLOAD_THIS/main.pdf
FINAL_WACV2027_SUBMISSION/01_UPLOAD_THIS/supplementary.pdf
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/fig/consistency_facing.pdf
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/fig/orientation_per_relation.pdf
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/fig/site_validation.pdf
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/main.tex
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/preamble.tex
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/sec/A_appendix.tex
FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/suppl.tex
paper/fig/consistency_facing.pdf
---
FINAL_WACV2027_SUBMISSION_PAPER2/01_UPLOAD_THIS/main.pdf
FINAL_WACV2027_SUBMISSION_PAPER2/01_UPLOAD_THIS/supplementary.pdf
FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source/main.pdf
FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source/main.tex
FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source/suppl.pdf
paper/main.tex
---
paper/main.pdf
paper/suppl.pdf

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 21.3s)

Yes — all three paper branches exist as local remote-tracking refs (`origin/paper1/wacv2027`, `origin/paper2/wacv2027`, `origin/research/equiorient`), and each has the full manuscript:

| Paper | Branch | Manuscript | Status (latest commit) |
|---|---|---|---|
| 1 — "Beyond Spatial Accuracy..." | `paper1/wacv2027` | `FINAL_WACV2027_SUBMISSION/01_UPLOAD_THIS/main.pdf` + LaTeX source | Complete kit; latest commit adds Thunder Compute runbook |
| 2 — "What Spatial Fine-Tuning Actually Changes" | `paper2/wacv2027` | `FINAL_WACV2027_SUBMISSION_PAPER2/01_UPLOAD_THIS/main.pdf` (5pp) + suppl + code zip | Kit built, SHA-256s recorded; only calendar actions remain |
| 3 — "EquiOrient: Latent Transformation Equivariance without Measurable Downstream Transfer" | `research/equiorient` | `paper/main.pdf` (5pp) + `paper/suppl.pdf` (2pp) | Compiled; OpenReview kit ready |

Note they're remote-tracking refs — I can read any file from them via git, but I'm currently checked out on `master`. Want me to read any of them (e.g., extract a paper's abstract or check submission-readiness)?

---

## User

ok look can u do web fetch and get all information and tell me which can be the best paper to submit

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 10.7s)

_Thinking:_

The user wants me to web fetch to get info and tell which paper is best to submit. They're targeting WACV 2027 Datasets Track (deadline Aug 28/30, 2026). Let me:

1. Read the three papers' abstracts from the branches
2. Web search WACV 2027 deadlines/review criteria
3. Compare and recommend

Let me first extract abstracts/titles from each branch, then do web research on WACV 2027.

**Tool: bash**

**Input:**
```json
{
  "command": "git show origin/paper1/wacv2027:FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/wacv2027_source/main.tex | grep -A 30 -iE 'begin\\{abstract\\}' | head -45",
  "description": "Extracts Paper 1 abstract"
}
```

**Output:**
```
\begin{abstract}
Aggregate spatial accuracy can hide sharply different capabilities within vision--language models (VLMs). We study object-relative orientation as a diagnostic case. On Visual Spatial Reasoning (VSR), moving from a compact 2.2B model to a larger 7B VLM substantially improves overall, depth, horizontal, and containment accuracy, but orientation changes only modestly. Except for structured prompting, which degrades performance, trained conditions on both models remain in a narrow 62--66\% orientation band. We test structured prompting, general and targeted LoRA, hard negatives, visual/projector adaptation, frozen and object-grounded representation probes, and object-centric decomposition; none of the tested configurations reliably closes the gap, and a single-annotator clean-label sensitivity analysis shows that the pattern persists after excluding examples flagged as ambiguous.

Accuracy also fails to capture relational coherence. LM-side adaptation significantly improves consistency over zero-shot, while hard-negative training raises facing/facing-away consistency from 66.0\% to 77.7\% with facing accuracy unchanged at 68.9\%; the additional pooled consistency gain over LM-only is not significant. Cross-dataset evaluation on SITE shows that VSR-trained adaptation does not transfer cleanly: it is neutral overall and significantly harms official spatial-relationship reasoning (75.1\%$\rightarrow$71.6\%, $p=0.004$). A pre-specified orientation-vocabulary slice, frozen before SITE evaluation, is analyzed as exploratory evidence rather than as direct replication of the VSR construct. The results point to a persistent orientation bottleneck in which orientation is not robustly decodable by the tested frozen-feature readouts and relational decisions are not always propagated coherently, while also showing that task-specific spatial adaptation can transfer poorly.
\end{abstract}

\section{Introduction}
Spatial reasoning is central to multimodal systems that must interact with physical environments. A useful VLM should not only recognize objects, but determine whether one object is in front of another, whether it is facing another, whether two objects are parallel, and whether equivalent or complementary formulations yield logically compatible answers. These abilities matter for robotics, embodied agents, navigation, and scene understanding.

Existing work already shows that spatial relations are difficult for vision--language systems. VSR was designed as a controlled natural-image probe and reported particularly poor performance on object-orientation relations in earlier VLMs~\cite{liu2023vsr}. More recent controlled benchmarks likewise find that strong VLMs can fail on basic left/right and other grounded relations~\cite{kamath2023whatsup,rajabi2024gsrbench}, while broader evaluations continue to identify spatial orientation as a difficult factor~\cite{wang2025site}. Our question is therefore not whether spatial reasoning can fail, but whether the orientation weakness persists in modern generative VLMs of different sizes and after targeted intervention, and what the failure signature reveals about representation, reasoning, and transfer.

In our VSR experiments, the distinction between relation families is striking. Moving from \modelsmall{} to the larger \modellarge{} increases zero-shot overall accuracy from 74.0\% to 80.9\%. Horizontal reasoning rises from 70.2\% to 84.8\%, depth from 68.9\% to 75.2\%, and containment from 83.4\% to 89.3\%. Orientation, by contrast, moves only from 62.8\% to 63.5\%. We then evaluate interventions spanning prompting, language-side adaptation, targeted data construction, visual-side adaptation, representation probing, and explicit object-centric decomposition. Structured prompting significantly hurts performance; general and targeted LoRA improve aggregate accuracy but do not remove the orientation ceiling; hard negatives improve targeted relational coherence without a significant overall orientation-accuracy gain; and the tested visual-side LoRA configurations do not outperform the language-side control.

As a sensitivity analysis, removing examples flagged by a single-annotator audit raises orientation accuracy (65.7\%$\rightarrow$78.5\% for 7B General LoRA, 66.4\%$\rightarrow$76.6\% for hard-negative LoRA on the strictest 107-example subset) but does not eliminate error (2B structured shows no gain). Because the removed examples were drawn from persistent failures, part of this gain is expected by construction.

A second failure mode emerges from logical consistency. The zero-shot 7B model is consistent on only 36.9\% of complementary facing/facing-away pairs. LM-side LoRA substantially improves coherence, and hard-negative training raises facing consistency to 77.7\% while facing accuracy remains unchanged at 68.9\%. The extra hard-negative gain is not significant in the pooled strict-family comparison, yet accuracy stays unchanged while consistency moves: the two metrics capture different behavior.

Finally, we test cross-dataset transfer. The 7B model is strong on SITE's official spatial-relationship-reasoning category (75.1\% raw; 59.2\% chance-adjusted accuracy), yet the VSR-trained adapter does not generalize cleanly: it is statistically neutral overall (54.2\%$\rightarrow$53.8\%, $p=0.66$) and significantly degrades the official category (75.1\%$\rightarrow$71.6\%, $p=0.004$). A pre-specified, non-official orientation-vocabulary slice is much weaker in the aggregate (48.3\% raw; 24.0\% chance-adjusted) and shows no positive transfer, but---as we detail below---its composition limits what it can establish, and we therefore do not treat SITE as independent confirmation of the VSR orientation construct.

Our contributions are fourfold:
\begin{itemize}[leftmargin=*]
    \item \textbf{Fine-grained diagnosis across two differently sized VLMs.} Across ten VSR conditions and two differently sized models, several spatial families improve substantially while object-relative orientation remains unusually resistant.
    \item \textbf{Robustness and mechanism analysis.} A single-annotator clean-label sensitivity analysis, frozen/object-grounded probes, visual-side adaptation, and object-centric decomposition constrain purely annotation-based or single-component explanations.
    \item \textbf{VSR-specific accuracy--coherence separation.} Complementary-relation tests on VSR's strict relation pairs show that, for the tested conditions, relational consistency can change substantially while task accuracy remains fixed.
    \item \textbf{Cross-dataset transfer analysis.} SITE shows strong official spatial-relationship performance, while VSR-trained LoRA transfers poorly and significantly harms the official SITE category; the orientation-vocabulary slice is analyzed as exploratory evidence.
\end{itemize}

\section{Related Work}
\label{sec:related}
\paragraph{Spatial reasoning benchmarks.}
VSR introduced a controlled natural-image benchmark of more than 10k image--text pairs spanning 66 spatial relations and explicitly highlighted orientation relations such as \emph{facing} and \emph{parallel} as difficult for the VLMs studied at the time~\cite{liu2023vsr}. Our work should therefore be read as a modern diagnostic extension rather than the first observation of an orientation weakness. What'sUp isolates basic spatial relations by holding object identities fixed while varying configurations, and found large gaps between humans and tested vision--language models~\cite{kamath2023whatsup}. GSR-Bench extends controlled grounded spatial evaluation across a larger set of multimodal models and model scales~\cite{rajabi2024gsrbench}. SITE broadens evaluation to single-image, multi-image, and video inputs and organizes tasks using cognitive-science dimensions including spatial visualization/orientation, intrinsic/extrinsic relations, and static/dynamic settings; its authors report spatial orientation as a persistent challenge~\cite{wang2025site}. Recent broad evaluations such as SpatialScore similarly argue that spatial intelligence remains fragmented across tasks and modalities~\cite{wu2026spatialscore}, and Mind the Gap isolates spatial reasoning from detection and semantic comprehension in contemporary VLMs~\cite{stogiannidis2025mindgap}.

```

**Tool: bash**

**Input:**
```json
{
  "command": "git show origin/paper2/wacv2027:FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source/main.tex | grep -B2 -A 25 -iE 'abstract' | head -50",
  "description": "Extracts Paper 2 abstract"
}
```

**Output:**
```
\maketitle

\begin{abstract}
Fine-tuning a vision--language model (VLM) on a spatial reasoning task usually improves benchmark accuracy. But ``better accuracy'' is not a single capability: the same adaptation may change how much the model depends on the correct image, how coherently it applies relational semantics, and how it responds to a causal image transformation, in different directions and at different rates. We treat ordinary LoRA fine-tuning on the Visual Spatial Reasoning (VSR) task as a controlled intervention and measure, per training seed and across two backbone families, a vector of capability changes: benchmark gain \dA{}, correct-image dependence \dG{} (the normal-minus-shuffle accuracy gap, relative to zero-shot), and semantic pair consistency \dC{} (relcomp/facing-antonym flip-law compliance), together with Tier-C transformation behavior under global horizontal reflection (transformed accuracy, pair consistency, joint correctness). Across 3 fresh training seeds per family (plus the committed seed-0), \dA{} is positive for every seed on both backbones (7B: $+0.0506\pm0.0046$; 2B: $+0.0316\pm0.0009$) and \dG{} is positive for every seed (7B: $+0.0440\pm0.0054$; 2B: $+0.0316\pm0.0026$). Fresh-seed semantic pair consistency stays within 0.05 of the legacy General checkpoint in both families, and all fresh 2B answer-update rates exceed the 2B zero-shot rate. A post-confirmatory extension on the contemporary \qwennew{} backbone reproduces the primary \dA{}/\dG{} pattern ($+0.032$/$+0.036$) and the transformed-accuracy gain ($+0.045$). We conclude that ordinary spatial fine-tuning is not a scalar capability update: benchmark accuracy, correct-image dependence, and semantic consistency can be described---and must be reported---as a jointly measured vector whose components replicate across seeds and families.
\end{abstract}

\section{Introduction}
\input{sec/1_intro.tex}
\section{Related Work}
\input{sec/2_related.tex}
\section{Protocol}
\input{sec/3_protocol.tex}
\section{Results}
\input{sec/4_results.tex}
\section{Discussion and Limitations}
\input{sec/5_discussion.tex}
\section{Conclusion}
\input{sec/6_conclusion.tex}

\bibliographystyle{ieeenat_fullname}
\bibliography{references}

\end{document}

```

**Tool: bash**

**Input:**
```json
{
  "command": "git ls-tree -r --name-only origin/research/equiorient | grep -iE 'paper.*\\.tex$|main\\.tex$'; git show origin/research/equiorient:paper/main.tex 2>/dev/null | grep -A 20 -iE 'begin\\{abstract\\}' | head -30",
  "description": "Extracts Paper 3 abstract"
}
```

**Output:**
```
paper/main.tex
paper/numbers.tex
paper/preamble.tex
paper/suppl.tex
\begin{abstract}
Can training an answer-relevant object-pair spatial state in a
vision--language model (VLM) to obey a predeclared, geometry-derived
transformation algebra deliver measurable downstream transfer beyond matched
augmentation, output-consistency, and invariance controls? We test this
with a one-seed falsification pilot on synthetic plan-view scenes rendered
for Qwen3-VL-8B-Instruct. We use a manipulation-verified implementation
with per-epoch structural-loss logging and a nonzero-loss assertion, and
compare six matched arms sharing the same answer path while differing only
in data or structural objective. The result is a
clean separation. When the loss is actually applied, the latent
\emph{complies} with the predeclared algebra: on a held-out transform
composition never seen in training, EquiOrient's equivariance error is
\eqnVTwoCRhoVHEq\ vs.\ \eqnVTwoCRhoVHAug\ for augmentation-only (a
$\approx$\eqnVTwoCRatio$\times$ reduction), and the
per-transform correct-vs-wrong contrast discriminates sharply
(\eqnVTwoCRhoHEq\ vs.\ \eqnVTwoCWHEq\ on the horizontal reflection), with
a wrong-geometry control that obeys \emph{its own} (incorrect) law
per-transform. Yet no measurable downstream transfer appears: the behavioral
composition test is uninformative by construction (the task reduces to a
binary left/right axis on which the answer algebra is closed, so every

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 8.2s)

_Thinking:_

Now let me get the full Paper 3 abstract ending and check WACV 2027 deadlines/tracks via web search to ground the recommendation.

**Tool: bash**

**Input:**
```json
{
  "command": "git show origin/research/equiorient:paper/main.tex | grep -A 45 'begin{abstract}' | tail -25",
  "description": "Gets rest of Paper 3 abstract"
}
```

**Output:**
```
arm reaches ceiling), and a held-out relation-family probe (depth) is
flat across arms (0.53--0.55). The paper is a mechanistic negative:
representation-level algebra compliance is achievable and measurable,
but it did not transfer to behavior or to an unseen relation family
within Phase-1 scope.
\end{abstract}

\section{Introduction}
Answer-level consistency laws are a standard diagnostic: a model that
flips its answer when an image is mirrored is ``using'' the visual
evidence~\cite{liu2023vsr}. But a model can obey an answer law while its
\emph{representation} transforms arbitrarily, and vice versa. EquiOrient
tests the stronger object: can a typed, answer-relevant spatial latent be
trained to obey a predeclared, geometry-derived transformation algebra, and
does that compliance pay off behaviorally or in transfer to unseen
structure?

This paper's central contribution is the honest answer to both parts,
obtained with a discipline that the first attempt lacked. Our first
implementation---and, unknowingly, every GPU run built on it---had
identically zero structural losses: the equivariance term fabricated
$\rhoop(T)\zblk$ from the same $\zblk$ instead of coupling $\zblk(x)$ and
$\zblk(Tx)$ from the original and transformed images. A hostile review
found it; the runs were voided and the harness corrected with a
manipulation check (per-epoch loss logging and a nonzero-loss assertion)

```

**Tool: websearch**

**Input:**
```json
{
  "numResults": 6,
  "query": "WACV 2027 datasets track evaluation criteria submission deadline OpenReview"
}
```

**Output:**
```
{
  "search_id": "search_62da3892f964a1a59e63eabdbb6f907f",
  "results": [
    {
      "url": "https://openreview.net/group?id=thecvf.com/WACV/2027/Conference_Round_1",
      "title": "WACV 2027 Conference Round 1 | OpenReview",
      "publish_date": null,
      "excerpts": [
        "Submission Start: Jun 05 2026 12:00PM UTC-0, Abstract Registration: Jun 20 2026 11:59AM UTC-0, Submission Deadline: Jun 27 2026 11:59AM UTC-0. No recent activity to display. OpenReview is a long-term project to advance science through improved peer review with legal nonprofit status."
      ]
    },
    {
      "url": "https://wacv.thecvf.com/Conferences/2027/CallForPapers",
      "title": "WACV 2027 Call for Papers",
      "publish_date": null,
      "excerpts": [
        "* Adversarial learning, adversarial attack, and defense methods\n* Biometrics, face, gesture, and body pose\n* Computational photography\n* Generative models for image, video, 3D, etc.\n* Explainable, fair, accountable, privacy-preserving, and ethical computer vision\n* Image recognition and understanding (object detection, categorization, segmentation, scene modeling, visual reasoning)\n* Low-level and physics-based vision\n* Machine learning architectures, formulations, and algorithms (including transfer, low-shot, semi-, self-, and unsupervised learning)\n* Video recognition and understanding (tracking, action recognition, etc.)\n* Vision + language and/or other modalities\n* Foundation models for downstream vision tasks\n\n## Evaluations & Datasets Track\n\nAuthors are also encouraged to submit papers to the Evaluations & Datasets (E&D) Track.\nThese submissions must advance the science and practice of evaluation in computer vision including the development and use of datasets and other resources. Topics of interest include, but are not limited to:\n\n* Analysis of strengths, limitations, or failure modes of existing benchmarks or evaluation practices\n* Study benchmark saturation or overfitting and their impact on scientific conclusions\n* Compare evaluation designs and demonstrate how different assumptions lead to different results or conclusions\n* Provide rigorous reproduction, auditing, and stress-testing of prior evaluations\n* Propose new evaluation protocols, practices, or methodologies\n* Conduct human- or interaction-centered evaluations (e.g., user studies, red-teaming)\n* Introduce datasets and clearly explain their scope, assumptions, limitations, and how they are intended to support or shape evaluative claims across the computer vision lifecycle\n* Contribute tools, analyses, or frameworks that improve how evaluative claims are constructed or interpreted\n* Present negative results, critical analyses, and use-case-inspired evaluations\n* New datasets and dataset collections\n* Audits of existing datasets\n* Benchmarks on new or existing datasets, benchmarking tools, and methodologies\n* Systematic analyses of systems on novel datasets\n\n* * *\n\nAll submissions will be handled electronically through OpenReview: [https://openreview.net/group?id=thecvf.com/WACV/2027/Conference\\_Round\\_1](https://openreview.net/group?id=thecvf.com/WACV/2027/Conference_Round_1)\n\nPapers can be submitted to either the Evaluation & Datasets, Applications, or Algorithms tracks, which will have different review criteria. Applications papers will be evaluated on systems-level innovation, novelty of the domain and comparative assessment.\nAlgorithms papers will be evaluated according to the standard conference criteria including algorithmic novelty and quantified evaluation against current, alternative approaches.\n\nAuthors should follow the Author Guidelines and use the WACV 2027 Author Kit (Templates to be provided), when preparing their papers for review.\n\nThe Author Guidelines contains additional information on submission, ethics, plagiarism, the review process, the publishing process, and use of LLMs.\n\n## Deadlines\n\n_(All deadline dates are Anywhere on Earth)_\n\n#### Round 1\n\n* **Paper enrollment:** June 19th, 2026\n* **Paper submission:** June 26th, 2026\n* **Supplementary material submission:** June 28th, 2026\n* **Reviews and Decisions released to authors:** August 7th, 2026\n* **Rebuttal and Revision submission:** August 28th, 2026\n* **Final Decisions released to authors:** October 9th, 2026\n\n#### Round 2\n\n* **New paper enrollment:** August 21st, 2026\n* **Paper submission:** August 28th, 2026\n* **Supplementary material submission:** August 30th, 2026\n* **Reviews and Final Decisions released to authors:** October 9th, 2026\n\n#### Both Rounds\n\n* **Camera ready submission:** November 2nd, 2026\n\nFor additional questions, contact the WACV 2027 Program Chairs through the WACV Help Desk. Please make sure to include your OpenReview ID in any communication.\n\nSuccessful Page Load  \n### Contact Us\n\n[WACV Help Desk](https://support.conferences.computer.org/wacv/help-desk/)\n\nPlease contact us with questions\nabout the following topics:\n\nAuthor - Paper Submission,\nAuthor - Open Review Issues,\nAuthor - Camera-Ready Paper,\nRegistration - General,\nRegistration - Cancellation,\nChildcare/Guests,\nExpo/Guests,\nLodging,\nVisa Letter,\nReviewer - Open Review Issues,\nReviewer - General Issues,\nArea Chair Issues,\n\n###### Useful links\n\n* * *\n\n* [WACV Proceedings](https://www.computer.org/csdl/proceedings/1000040)\n* Code of Conduct\n\n* * *\n\n|IEEE Logo |[IEEE Computer Society](https://www.computer.org/) |"
      ]
    },
    {
      "url": "https://www.computer.org/conferences/cfp-ieee-cvf-wacv",
      "title": "Call for Submissions: IEEE WACV 2027 - computer.org",
      "publish_date": "2026-07-14",
      "excerpts": [
        "Call for Submissions: IEEE WACV 2027 - computer.org\nIn addition to submitting your paper to IEEE WACV 2027, you are also encouraged to upload the data related to your paper to IEEE DataPort. IEEE DataPort is IEEE’s data platform that supports the storage and publishing of datasets while also providing access to thousands of research datasets."
      ]
    },
    {
      "url": "https://wacv.thecvf.com/Conferences/2027/ReviewerGuidelines",
      "title": "WACV 2027 Reviewer Guidelines - The Computer Vision Foundation",
      "publish_date": null,
      "excerpts": [
        "This document explains what is expected of all members of the Reviewing Committee for WACV 2027.\n\n## **The WACV 2027 Reviewing Timeline**\n\n**Round 1**\n\nPaper submission deadline: June 26, 2026\n\nPapers assigned to reviewers: July 3, 2026\n\nReviews due: July 24, 2026\n\nDecisions released to authors: August 7, 2026\n\n**Round 2**\n\nPaper and supplementary submission deadline: August 28, 2026\n\nPapers assigned to reviewers: September 4, 2026\n\nReviews due: September 25, 2026\n\nDecisions released to authors: October 9, 2026\n\n## **What’s New for Reviewers at WACV 2027?**\n\nTo improve the review process and uphold the conference’s high standards, WACV will strictly enforce a Responsible Reviewing Policy and a Reviewing Deadline Policy. Any reviewer whose review fail to comply with these policies may will face a possible desk rejection of all papers on which they are an author per the discretion of the PCs.\n\n...\n\nHistorically, previous WACV conferences (and CVPR, ICCV, ECCV and NeurIPS, amongst others) faced challenges with some reviewers failing to meet the review submission deadlines. It came to be accepted that there was an unofficial grace period after the reviewing deadline. In some cases, reviewers failed to respond to multiple reminders and did not submit their reviews at all. This necessitated Area Chairs (ACs) to follow up diligently with late reviewers, as well as assign emergency reviewers to ensure each paper received the minimum of three reviews. Over the years, this has added to the already large workload and stress of the conference organizers. To improve the review process and uphold the conference’s high standards, WACV will strictly enforce the reviewing deadline. This policy aims to ensure fairness and accountability across the reviewing process while reducing the burden on ACs and other conference organizers.\nThere will be multiple emails sent out to all reviewers as a reminder to submit reviews in a timely manner.\n\n### **Application vs Algorithms vs Evaluations & Datasets**\n\nWACV papers can either be “application” or “algorithms” papers, and have different reviewing criteria. Please read these instructions carefully and apply the appropriate criteria based on the paper type indicated in the submission.\n\nApplication papers must be evaluated on systems-level innovation, novelty of the domain and comparative assessment . They should not be evaluated solely on the basis of algorithmic novelty (i.e, it is okay to have algorithmic novelty, but it is also okay not to have it). Examples of systems-level innovation are: 1) A new task, i.e., does this paper deliver an interesting application of computer vision that the community has never seen before? 2) A new formulation of an existing application; 3) A new way of benchmarking performance of existing methods.\nRecent examples of WACV application-track papers:\n\n* [CharacterGAN: Few-Shot Keypoint Character Animation and Reposing](https://openaccess.thecvf.com/content/WACV2022/papers/Hinz_CharacterGAN_Few-Shot_Keypoint_Character_Animation_and_Reposing_WACV_2022_paper.pdf)\n* [DeepCSR: A 3D Deep Learning Approach For Cortical Surface Reconstruction](https://openaccess.thecvf.com/content/WACV2021/papers/Santa_Cruz_DeepCSR_A_3D_Deep_Learning_Approach_for_Cortical_Surface_Reconstruction_WACV_2021_paper.pdf)\n* [OpenFace: An open source facial behavior analysis toolkit](https://www.cl.cam.ac.uk/research/rainbow/projects/openface/wacv2016.pdf)\n* [FuturePose - Mixed Reality Martial Arts Training Using Real-Time 3D Human Pose Forecasting With a RGB Camera](https://ieeexplore.ieee.org/document/8658594)\n\nAlgorithms papers must be evaluated according to the standard conference criteria including algorithmic novelty and quantified evaluation against current, alternative approaches .\nThey should not be evaluated solely on the basis of systems-level innovation (i.e, it is okay to have systems-level novelty, but it is also okay not to have it). Algorithms papers will be similar in style to other major computer vision conferences (e.g., CVPR, ICCV, ECCV). Recent examples include:\n\n* [Hole-robust wireframe Detection](https://openaccess.thecvf.com/content/WACV2022/papers/Kong_Hole-Robust_Wireframe_Detection_WACV_2022_paper.pdf)\n* [Agree to Disagree: When Deep Learning Models With Identical Architectures Produce Distinct Explanations](https://openaccess.thecvf.com/content/WACV2022/papers/Watson_Agree_To_Disagree_When_Deep_Learning_Models_With_Identical_Architectures_WACV_2022_paper.pdf)\n* [Understanding Convolution for Semantic Segmentation](https://cseweb.ucsd.edu/~gary/pubs/panqu-wacv-2018.pdf)\n\nEvaluation & Dataset track papers must be evaluated similarly to NeurIPS Evaluations & Dataset Track.\nPapers in this category should propose tools, datasets, benchmarks, and practices for testing, stress-testing, auditing, comparing, and interpreting AI/ML systems throughout their lifecycle. The reviewers should ask whether this dataset will meaningfully advance any particular sub-areas in Computer Vision, and if the proposed dataset and benchmarking efforts are scientifically correct. While this is the 1st time WACV is introducing the Evaluation & Dataset Track, the following recent papers published in WACV are examples of this track:\n\n* [MEVID: Multi-view Extended Videos with Identities for Video Person Re-Identification](https://openaccess.thecvf.com/content/WACV2023/papers/Davila_MEVID_Multi-View_Extended_Videos_With_Identities_for_Video_Person_Re-Identification_WACV_2023_paper.pdf)\n* [WildlifeDatasets: An open-source toolkit for animal re-identification](https://openaccess.thecvf.\n\n...\n\nIRB reviews for the US or the appropriate local ethics approvals are typically required for new datasets in most countries. It is the dataset creators' responsibility to obtain them. If the authors use an existing, published dataset, we encourage, but do not require them to check how data was collected and whether consent was obtained. Our goal is to raise awareness of possible issues that might be ingrained in our community. Thus, we would like to encourage dataset creators to provide this information to the public.\n\nIn this regard, if a paper uses an existing public dataset that is released by other researchers/research organizations, we encourage, but not require them to include a discussion of IRB related issues in the paper. Reviewers hence should not penalize a paper if such a discussion is NOT included.\n\n### **Be Specific**\n\nPlease be specific and detailed in your reviews. Your main critique of the paper should be written in terms of a list of strengths and weaknesses.\n\n...\n\narXiv papers are often corrected and modified; the site is set up to support this scientific process of revision.\n\n_Q. May the authors build a project website related to their arXiv paper?_\n\nA. Yes, the authors may, as long as the project website itself does not contain any information that would otherwise link it to your WACV submission.\n\n_Q. A paper is using a withdrawn dataset, such as DukeMTMC-ReID or MS-Celeb-1M. How should I handle this?_\n\nA. Reviewers are advised that the choice to use a withdrawn dataset, while not in itself grounds for rejection, should invite very close scrutiny. Reviewers should flag such cases in the review form for further consideration by ACs and PCs. Consider questions such as: Do the authors explain why they had to do this? Is this explanation compelling? Is there really no alternative dataset that could have been used? Remember, authors might simply not know the dataset had been withdrawn.\nIf you believe the paper could be accepted without the authors’ use of a withdrawn dataset, then it is natural to advise the authors to remove the experiments associated with this dataset.\n\n_Q. If a paper did not evaluate on a withdrawn dataset, can I request authors that they do?_\n\nA. It is a violation of policy for a reviewer or area chair to require comparison on a dataset that has been withdrawn without a detailed consultation with PCs.\n\nSuccessful Page Load\n\n  \n### Contact Us\n\n[WACV Help Desk](https://support.conferences.computer.org/wacv/help-desk/)\n\nPlease contact us with questions\nabout the following topics:\n\nAuthor - Paper Submission,\nAuthor - Open Review Issues,\nAuthor - Camera-Ready Paper,\nRegistration - General,\nRegistration - "
      ]
    },
    {
      "url": "https://github.com/467718584/dino-cascade-crack-seg/blob/main/WACV_2027_OpenReview_submission_checklist.md",
      "title": "dino-cascade-crack-seg/WACV_2027_OpenReview_submission ...",
      "publish_date": null,
      "excerpts": [
        "Paper: Conditional Cascade Trigger for Crack Segmentation on DINOv3 BackbonesVenue: IEEE/CVF WACV 2027 (Jan 4-8, 2027, Disney Springs, Buena Vista, FL) Track: Applications — Structural Engineering + Embedded Sensing + Real-Time Submission date target: 2026-07-28 (Round 2 paper) + 2026-07-30 (supplementary) Round: 2 (Round 1 deadline passed"
      ]
    },
    {
      "url": "https://openreview.net/group?id=thecvf.com/WACV/2027/Conference",
      "title": "WACV 2027 Conference | OpenReview",
      "publish_date": "2026-08-21",
      "excerpts": [
        "OpenReview is a long-term project to advance science through improved peer review with legal nonprofit status. We gratefully acknowledge the support of the OpenReview Sponsors. © 2026 OpenReview."
      ]
    },
    {
      "url": "https://wacv2024.thecvf.com/submissions",
      "title": "Submission – WACV 2024",
      "publish_date": null,
      "excerpts": [
        "* Virtual and augmented reality\n* Visualization\n\nAuthors are also encouraged to submit more traditional computer vision algorithms papers. Topics of interest include, but are not limited to:\n\n* 3D computer vision\n* Adversarial learning, adversarial attack, and defense methods\n* Biometrics, face, gesture, and body pose\n* Computational photography\n* Generative models for image, video, 3D, etc.\n* Datasets and evaluations\n* Explainable, fair, accountable, privacy-preserving, and ethical computer vision\n* Image recognition and understanding (object detection, categorization, segmentation, scene modeling, visual reasoning)\n* Low-level and physics-based vision\n* Machine learning architectures, formulations, and algorithms (including transfer, low-shot, semi-, self-, and unsupervised learning)\n* Video recognition and understanding (tracking, action recognition, etc.)\n* Vision + language and/or other modalities\n\nAll submissions will be handled electronically through CMT: <https://cmt3.research.\nmicrosoft.com/WACV2024>\n\nPapers can be submitted to either the applications or the algorithms tracks, which will have different review criteria. Applications papers will be evaluated on systems-level innovation, novelty of the domain and comparative assessment. Algorithms papers will be evaluated according to the standard conference criteria including algorithmic novelty and quantified evaluation against current, alternative approaches.\n\n# **Deadlines** **(\\*\\*note that all PT timezone deadlines are AM not PM)** **:**\n\n**Round 1:**\n\n* Paper registration: **June 21st, 2023** **11:59 AM PT** (June 21st, 2023 06:59 PM GMT)\n* Submission: **June 28th, 2023** **11:59 AM PT** (June 28th, 2023 06:59 PM GMT)\n* Supplementary material deadline: **June 30th, 11:59 AM PT** (June 30th, 2023 06:59 PM GMT)\n* Reviews and Decisions released to authors: **~~Aug 11th, 2023~~ Aug 14th, 2023**\n* Rebuttal and Revision submission: **Aug. 30th, 2023** **11:59 AM PT** (Aug. 30th, 2023 06:59 PM GMT)\n* Final Decisions released to authors: **Oct 20th, 2023**\n* Camera ready deadline: **November 7 th , 11:59 PM, PT**\n* Author Registration deadline: **November 7 th , 11:59 PM, PT**\n\n**Round 2:**\n\n* Paper registration: **Aug 23rd, 2023** **11:59 AM PT** (Aug. 23th, 2023 06:59 PM GMT)\n* Submission: **Aug. 30th, 2023** **11:59 AM PT** (Aug. 30th, 2023 06:59 PM GMT)\n* Supplementary material deadline: **September 1st, 11:59 AM PT** (September 1st, 2023 06:59 PM GMT)\n* Reviews and Final Decisions released to authors: **Oct 20th, 2023**\n* Camera ready deadline: **November 7 th , 11:59 PM, PT**\n* Author Registration deadline: **November 7 th , 11:59 PM, PT**\n* Camera ready submission instructions are here: [https://docs.google.com/document/d/1UrN19rmmotCk10FajE1y0Zh0W4ruL3uGQHU\\_oEzK5pY/](https://docs.google.com/document/d/1UrN19rmmotCk10FajE1y0Zh0W4ruL3uGQHU_oEzK5pY/)\n\nAs in previous years, WACV 2024 will employ a two-round review process."
      ]
    },
    {
      "url": "https://www.getpaperpilot.com/deadlines/wacv-2027.html",
      "title": "WACV 2027 Deadline & Important Dates | PaperPilot",
      "publish_date": "2026-07-28",
      "excerpts": [
        "PaperPilot PaperPilot\n\nBack to all deadlines Get PaperPilot\n\n# WACV 2027 Call for Papers\n\nOfficial deadlines & important dates\n\nIEEE/CVF Winter Conference on Applications of Computer Vision\n\nICORE A CCF N AI\n\nPaper deadline countdown\n\n—\n\n## When is the WACV 2027 deadline?\n\nPaper deadline TBD (AoE)\n\nConference dates January 2027\n\nLocation TBD\n\nWebsite <https://wacv.thecvf.com/>\n\nData last updated: Jul 28, 2026\n\n.ics export Google Calendar [DBLP](https://dblp.org/db/conf/wacv) [Official website](https://wacv.thecvf.com/)\n\n## Track this and 1200+ more conferences\n\nLive countdowns, field and rank filters, .ics export, ICORE 2026 rankings — all free.\n\nBrowse all deadlines\n\n## WACV deadlines from other years\n\nWACV 2026 deadline was Sep 19, 2025 WACV 2025 deadline was Sep 9, 2024\n\n## About WACV 2027\n\nWACV 2027 (IEEE/CVF Winter Conference on Applications of Computer Vision) is a leading conference focused on artificial intelligence, machine learning, and natural language processing.\nIt is ranked as an A-ranked venue in the ICORE 2026 rankings, representing a highly respected publication outlet. This edition takes place in TBD (January 2027). Researchers can track the WACV 2027 deadline with live countdowns, export to Google Calendar, and manage their submission workflow using PaperPilot.\n\n## Other Artificial Intelligence conferences\n\n← All Artificial Intelligence conference deadlines\n\nAAAI 2027 A\\* AAAI Conference on Artificial Intelligence ICRA 2026 A\\* IEEE International Conference on Robotics and Automation COLING 2025 B INTERNATIONNAL CONFERENCE ON COMPUTATIONAL LINGUISTICS ALT 2026 B International Conference on Algorithmic Learning Theory ICLR 2026 A\\* International Conference on Learning Representations\n\n## Frequently asked questions\n\n### When is the WACV 2027 paper submission deadline?\n\nThe WACV 2027 paper submission deadline is TBD (AoE). This page tracks it with a live countdown and lets you add it to your calendar in one click (.ics or Google Calendar).\n\n...\n\n### What are the WACV 2027 important dates?\n\nWACV 2027 key dates: paper submission deadline TBD (AoE); conference dates January 2027. The deadline is Anywhere on Earth (AoE), i.e. UTC-12, so it has not passed until the time has elapsed in every time zone on the planet — practically, you have until the end of that calendar day in the very last location on Earth, which buys a little buffer over your own local clock. Dates can change as the program is finalized, so confirm against the [official WACV 2027 call for papers](https://wacv.thecvf.com/) before you rely on them. You can export every date on this page to .ics or Google Calendar in one click.\n\n### How is WACV 2027 ranked?\n\nWACV 2027 is rated ICORE A, CCF N. ICORE/CORE (the CORE Conference Ranking, 2026 edition) grades venues from A\\* (flagship) through A, B and C; CCF is the China Computer Federation's parallel A/B/C rating."
      ]
    },
    {
      "url": "https://www.myhuiban.com/conference/517",
      "title": "WACV 2027 (ICORE A): IEEE/CVF Winter Conference on Applic... - Conference Partner",
      "publish_date": "2026-07-06",
      "excerpts": [
        "1. Home\n2. Conferences\n3. WACV\n\n* Track It 32\n* Attend It 2\n* Claim this conference\n\n## **Conference Information**\n\n# **WACV 2027: IEEE/CVF Winter Conference on Applications of Computer Vision**\n\n**Please  to view website of conference**\n\nFree account: view official websites, track deadlines, and get email reminders.\n\n \n\nEmbed deadline badge\n\nWACV\n\nGet this via API\n\nSearch and ranking lists need no credentials at all; full detail for this page needs a free API key. See the developer guide .\n\nSubmission Date:\n\n2026-08-28 Due in 7 days\n\nNotification Date:\n\n2026-10-09\n\nConference Date:\n\n2027-01-04\n\nLocation:\n\nBuena Vista, Florida, USA\n\nYears:\n\nView past editions (1)\n\nICORE: A QUALIS: B1 Viewed: 41622 Tracked: 32 Attend: 2\n\n## Never miss the WACV deadline\n\nCreate a free account and we will email you 30, 14, 7, 3, 1 days before the submission deadline.  \nYour first reminder would be sent on 2026-08-21.\n\nFree account. At most one email a day, and every email has a one-click unsubscribe link.\n## **Call For Papers**\n\nWACV 2027 (IEEE/CVF Winter Conference on Applications of Computer Vision) is a ICORE A / QUALIS B1 conference held in Buena Vista, Florida, USA on 2027-01-04. The paper submission deadline is 2026-08-28. Acceptance notifications are sent on 2026-10-09.\n\nIEEE/CVF Winter Conference on Applications of Computer Vision (WACV) provides a forum for computer vision researchers working on practical applications and innovative algorithms to share their latest developments.\nApplications Track\nWACV 2027 solicits high-quality, original submissions describing research in computer vision, with a particular emphasis on systems and applications with significant, interesting vision components.\nApplication areas include, but are not limited to:\nAgriculture\nAnimals and Insects\nArts, games, and social media\nAutonomous driving\nBiomedical, healthcare, and medicine\nCommercial and retail\nEducation\nEmbedded sensing and real-time techniques\n\n...\n\nVideo recognition and understanding (tracking, action recognition, etc.)\nVision + language and/or other modalities\nFoundation models for downstream vision tasks\nEvaluations &amp; Datasets Track\nAuthors are also encouraged to submit papers to the Evaluations &amp; Datasets (E&amp;D) Track. These submissions must advance the science and practice of evaluation in computer vision including the development and use of datasets and other resources. Topics of interest include, but are not limited to:\nAnalysis of strengths, limitations, or failure modes of existing benchmarks or evaluation practices\nStudy benchmark saturation or overfitting and their impact on scientific conclusions\nCompare evaluation designs and demonstrate how different assumptions lead to different results or conclusions\nProvide rigorous reproduction, auditing, and stress-testing of prior evaluations\nPropose new evaluation protocols, practices, or methodologies\nConduct human- or interaction-centered evaluations (e.g.\n, user studies, red-teaming)\nIntroduce datasets and clearly explain their scope, assumptions, limitations, and how they are intended to support or shape evaluative claims across the computer vision lifecycle\nContribute tools, analyses, or frameworks that improve how evaluative claims are constructed or interpreted\nPresent negative results, critical analyses, and use-case-inspired evaluations\nNew datasets and dataset collections\nAudits of existing datasets\nBenchmarks on new or existing datasets, benchmarking tools, and methodologies\nSystematic analyses of systems on novel datasets\n\nLast updated by Admin Agent on 2026-07-06\n\n## **People who viewed this also viewed**\n\n|CCF |ICORE |Short |Full Name |Submission |Notification |Conference |\n| --- | --- | --- | --- | --- | --- | --- |\n|C |A |ECIR |European Conference on Information Retrieval |2026-09-21 |2026-12-07 |2027-03-21 |\n| |B |ICAART |International Conference on Agents and Artificial Intelligence |2026-09-15 |2026-11-13 |2027-02-23 |"
      ]
    },
    {
      "url": "https://wacv2025.thecvf.com/submissions",
      "title": "Submissions – WACV 2025",
      "publish_date": null,
      "excerpts": [
        "* Biomedical, healthcare, and medicine\n* Commercial and retail\n* Education\n* Embedded sensing and real-time techniques\n* Environmental monitoring, climate change, and ecology\n* Food science and nutrition\n* Psychology and cognitive science\n* Remote sensing\n* Robotics\n* Smartphones and end-user devices\n* Social good\n* Structural engineering and civil engineering\n* Virtual and augmented reality\n* Visualization\n\nAuthors are also encouraged to submit more traditional computer vision algorithms papers. Topics of interest include, but are not limited to:\n\n* 3D computer vision\n* Adversarial learning, adversarial attack, and defense methods\n* Biometrics, face, gesture, and body pose\n* Computational photography\n* Generative models for image, video, 3D, etc.\n* Datasets and evaluations\n* Explainable, fair, accountable, privacy-preserving, and ethical computer vision\n* Image recognition and understanding (object detection, categorization, segmentation, scene modeling, visual reasoning)\n* Low-level and physics-based vision\n* Machine learning architectures, formulations, and algorithms (including transfer, low-shot, semi-, self-, and unsupervised learning)\n* Video recognition and understanding (tracking, action recognition, etc.)\n* Vision + language and/or other modalities\n\nAll submissions will be handled electronically through CMT: [https://cmt3.research.microsoft.com/WACV2025](https://cmt3.research.microsoft.com/WACV2024)\n\nPapers can be submitted to either the applications or the algorithms tracks, which will have different review criteria. Applications papers will be evaluated on systems-level innovation, novelty of the domain and comparative assessment. Algorithms papers will be evaluated according to the standard conference criteria including algorithmic novelty and quantified evaluation against current, alternative approaches.\n\nAuthors should follow the Author Guidelines and use the WACV 2025 Author Kit ( [Overleaf template](https://www.overleaf."
      ]
    }
  ],
  "warnings": null,
  "usage": [
    {
      "name": "sku_search",
      "count": 1
    }
  ],
  "session_id": "ses_fd81e747fffey16zO59Xh0VoM8"
}
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 45.3s)

_Thinking:_

Now I have all three abstracts and the WACV 2027 E&D track criteria. Let me give a recommendation.

Paper 1: "Beyond Spatial Accuracy" — diagnostic of orientation bottleneck, negative results, SITE transfer. E&D fit: analysis of failure modes, stress-testing — good fit.

Paper 2: "What Spatial Fine-Tuning Actually Changes" — seed-replicated causal decomposition (ΔA/ΔG/ΔC vector), multi-seed, two backbones + replication on newer backbone. Very strong methodological rigor: preregistration, seeds, controls, transformation battery. Fits "propose new evaluation protocols/practices", "compare evaluation designs". This is arguably the strongest: replicated across seeds and backbones, quantitative positive findings (not just nulls), clear novel evaluation framework.

Paper 3: EquiOrient — mechanistic negative result on synthetic data, one-seed falsification pilot. Riskiest for reviewers: synthetic-only, single seed, negative result; though honest and rigorous.

Recommendation: Paper 2 as strongest submission candidate, with reasoning. Also note all three are kits ready; deadlines Aug 28/30. Also note potential overlap concern if submitting multiple papers to same venue (salami-slicing risk) — worth flagging.

Keep answer reasonably concise but this warrants detail.

I pulled the full abstracts from all three branches plus the official WACV 2027 CFP and reviewer guidelines. Here's the comparison against the **Evaluations & Datasets Track** criteria (Round 2 deadline: Aug 28 paper / Aug 30 suppl):

## The three papers

| | Paper 1 | Paper 2 | Paper 3 |
|---|---|---|---|
| **Title** | Beyond Spatial Accuracy… | What Spatial Fine-Tuning Actually Changes | EquiOrient |
| **Core claim** | Orientation is a persistent bottleneck in VLMs; probes/adaptation/prompting don't close it; LoRA transfers poorly to SITE | LoRA fine-tuning is not a scalar update — benchmark gain ΔA, image-dependence ΔG, consistency ΔC move independently; measured across **3 fresh seeds × 2 backbones** + replication on Qwen3-VL | Latent can be trained to obey a transformation algebra (~40× equivariance-error reduction) but it does **not** transfer to behavior or unseen relations |
| **Evidence strength** | Strong but largely null results; single-seed; clean-label caveat acknowledged in-paper | Strongest: seed-variance stats, paired controls, preregistered protocol, cross-family replication, positive + replicable effects | Rigorous falsification design, but **one seed**, synthetic-only scenes, negative result |

## Recommendation: **Paper 2**

1. **Best fit to the E&D review criteria.** The track explicitly asks for "new evaluation protocols/practices," "compare evaluation designs," and NeurIPS-E&D-style rigor. Paper 2's ΔA/ΔG/ΔC capability-vector protocol *is* a new evaluative practice, demonstrated with a controlled intervention.
2. **It's the only one with positive, replicable findings.** Reviewers punish pure-null papers hardest. Paper 2 has every-seed-consistent effects (+0.05/+0.044 on 7B, +0.032/+0.036 on both backbones) plus an out-of-sample replication on a newer backbone — exactly the "scientifically correct, will advance the sub-area" question reviewers must answer yes to.
3. **Paper 3 is the riskiest submit.** Single-seed pilot, synthetic plan-view scenes only, headline = "no measurable downstream transfer." Honest and well-executed, but a hostile reviewer reads it as "method doesn't work." Better suited for a later round or a workshop after more seeds/scenes.
4. **Paper 1 is solid but partially superseded**: its single-seed limitations are what Paper 2 was built to fix; its clean-label sensitivity analysis relies on a single annotator, which the paper itself flags.

## One caution

All three share models, benchmarks, and findings — submitting multiple to the **same venue/round** invites overlap/salami-slicing concerns from ACs. If you're set on submitting more than one, Paper 2 first (E&D track), and consider Paper 3 for Round 1 next cycle or a different venue once expanded beyond one seed.

Want me to do a final pre-submission check on the Paper-2 kit (PDF hashes, anonymity, checklist) before the Aug 28 deadline?

---

## User

wait i think there are latest effort going on for paper 3??? is that true?? and if that get completed is that more better to have

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 10.5s)

_Thinking:_

User asks: is there ongoing latest effort on Paper 3 (research/equiorient), and if completed, would it be better? Let me check the latest commits and state on research/equiorient branch — recent commits showed "submission: Paper-3 supplementary compiled" etc. But also there were branches research/equiorient-phase2, equiorient-no-box. And master's latest commit b024525 mentioned "diagnostics: latent collapse data + v2 easyA result + dev log update". Let me investigate what's actively going on.

**Tool: bash**

**Input:**
```json
{
  "command": "git log --oneline -15 origin/research/equiorient; echo ===; git log --oneline -10 origin/research/equiorient-phase2 2>/dev/null; echo ===; git log --oneline -10 origin/research/equiorient-no-box 2>/dev/null",
  "description": "Shows recent activity on all equiorient branches"
}
```

**Output:**
```
ee669cf submission: Paper-3 supplementary compiled (suppl.pdf, 2 pages) — full matrices both regimes, per-transform correct/wrong rho tables, per-epoch loss curves, depth-probe n/CI details, algebra verification counts, compute ledger + voided-run provenance, reproducibility summary; OpenReview checklist updated
73e849c submission: WACV 2027 R2 E&D OpenReview kit — title + abstract (extract_openreview.py resolves macros to plain text, 1585 chars), track/keywords guidance, deadline table (reg Aug 21 / paper Aug 28 / suppl Aug 30 AoE), files + pre-enrollment action checklist
cd4eda6 paper: orchestrator verdict edits — title -> 'EquiOrient: Latent Transformation Equivariance without Measurable Downstream Transfer'; abstract: drop duplicate 'a', bug-history sentence compressed to manipulation-verified implementation phrasing; intro 'first valid test' -> 'valid controlled test'; contribution 2 'first valid measurement' -> 'controlled measurement'; contribution 4 de-emphasizes Modal/cost (protocol, harness, matrices, reproducible pipeline); SAGE sentence 'exactly' -> 'provides a SAGE-style output-level consistency control'; conclusion + abstract + section headers aligned to 'measurable downstream transfer'; 5 pages, compiles clean
4342311 paper: final submission-ready pass — round-2 hostile review resolved (no CRITICALs): real author records for all bib entries (arXiv-verified SAGE/CYW/CoSaT/GeoWorld; gate-record GASP/3DThinker); runtime corrected via macro (1357s); control-range sentence scoped (latent-invariance 3.1-5.6); Regime-A probe language honest (n=36, eq 0.5000 vs aug 0.6111); structural-loss sentence qualified (lat-inv rises); conclusion 'below controls' scoped; repo_commit recorded in matrices; contributions list, behavioral Table 2, lambda-sensitivity sentence, computed ratio macros (324x/60x), fig1 caption + fig3 title fixed, tables span columns, overfull-hbox eliminated, stale figures removed; 5 pages, compiles clean
f9a7c54 results: record repo commit provenance in the voided Amendment-D matrix (zero-loss run, logged as void)
9398609 research: CORRECTED manuscript complete — main.tex/main.pdf (WACV style, anonymous, machine-generated numbers only): mechanistic negative with two-regime replication (v1: rhoVH 0.172 vs 10.36, 60x; v2: 0.045 vs 14.65, 325x), correct-vs-wrong specificity, axis-symmetry insight, flat depth probes, honest binary-task + bias-decode + n/CI disclosures; hostile-review findings resolved (bib per gate records, per-transform + z_d metrics, loss curves, manipulation check); decision log updated; matrices committed
c3d312d research: FINAL corrected pilot (v2, Modal L40S) — manipulation verified (loss curves), latent algebra compliance: equiorient rho_H 0.033 / rho_V 0.006 / held-out rho_VH 0.045 vs augmentation 14.9/12.0/14.7 (325x); wrong_geometry obeys ITS law per-transform (0.020/0.005) but violates correct (3.18/3.31) — clean specificity; composed wrong law == correct on VH (0.026) confirms axis-symmetry; depth probe flat (0.53-0.55 all arms) — no downstream transfer; behavioral ceiling (binary task); prior KILL verdicts withdrawn as zero-loss artifacts
65c6c1c research: add eval_rho_per_transform — per-transform latent equivariance error under correct AND wrong rho (the composition metric cannot separate axis-swapped wrong laws; per-transform can); wired into selected-lambda results (rho_H/rho_V/rho_VH + wrong_H); tiny PASS
a646959 research: CRITICAL correction — structural losses were identically zero in ALL prior runs (manipulation-check failure found in Gate-8 review); harness now computes paired z(x)/z(Tx) laws (identity+transform image features per scene per step, grads preserved), output-consistency via LAW_PERM soft targets, per-epoch loss curves + MANIPULATION CHECK assert (>1e-6), z_d-block-only depth probe; prior KILL verdicts withdrawn (treatment never administered); tiny gate PASS with nonzero structural losses; corrected pilot required
2ed6245 research: PILOT_REPORT addendum — Amendment D KILL verdict (second-regime definitive negative)
521b529 research: Amendment D pilot (Modal L40S, v2) COMPLETE — verdict KILL (definitive, second regime): held-out VoH 1.0 all arms (ceiling persists with 5 objects), latent error flat (20.0-20.3), depth probe flat (0.57-0.60, binomial noise; equiorient == wrong_geometry 0.5833); stop 2+4 triggered, causal path PASS; no Gate 6, GPU work closed, spend <\.50 of the \ credit; artifacts committed (pilot_run_v2_modal/)
6e1c91b cloud: pin is optional (empty by default) + record actual cloned commit in the result matrix; fix orphaned freeze var
48e1f6c cloud: bump pin to 969f367
969f367 cloud: pin via HEAD assert (shallow clones can't fetch arbitrary SHAs) — clone branch tip, require HEAD == pinned release
54e5137 cloud: cone-mode sparse-checkout accepts directories only — drop requirements.txt from cone
zsh:1: == not found

```

**Tool: bash**

**Input:**
```json
{
  "command": "git show origin/master --stat | head -30; git log -1 --format='%ci %s' origin/research/equiorient origin/master origin/paper1/wacv2027 origin/paper2/wacv2027 2>/dev/null",
  "description": "Shows dates of latest commits per branch"
}
```

**Output:**
```
commit 8be6b05ee8e50d70a9f9692f8b5b7677f4eb4612
Author: khagendra01 <khagendrakhatri365@gmail.com>
Date:   Fri Aug 14 16:31:58 2026 -0400

    master: backfill frozen protocol manifests from paper2/wacv2027 (results/grounding/protocol/) — vsr_test_ids, visual/semantic/facing eligible IDs, shuffle mapping, blank-image spec, validity tables, visual spot checks; required by shared tests (test_visual/test_semantic/test_shuffle/test_facing); prediction/analysis outputs intentionally stay on paper branches

 results/grounding/protocol/blank_image.png         |   Bin 0 -> 1540 bytes
 results/grounding/protocol/blank_image_spec.json   |    20 +
 .../grounding/protocol/facing_eligible_ids.json    |  1049 +
 .../protocol/facing_transform_validity.csv         |    62 +
 .../grounding/protocol/run_config_snapshot.json    |    48 +
 .../grounding/protocol/semantic_eligible_ids.json  | 14411 ++++++++++
 .../protocol/semantic_transform_validity.csv       |   184 +
 results/grounding/protocol/shuffle_mapping.json    |  2207 ++
 .../grounding/protocol/visual_eligible_ids.json    |  4686 +++
 .../protocol/visual_spot/vsr_test_0009_flip.png    |   Bin 0 -> 239407 bytes
 .../protocol/visual_spot/vsr_test_0009_orig.png    |   Bin 0 -> 239538 bytes
 .../protocol/visual_spot/vsr_test_0118_flip.png    |   Bin 0 -> 167736 bytes
 .../protocol/visual_spot/vsr_test_0118_orig.png    |   Bin 0 -> 168138 bytes
 .../protocol/visual_spot/vsr_test_0821_flip.png    |   Bin 0 -> 239092 bytes
 .../protocol/visual_spot/vsr_test_0821_orig.png    |   Bin 0 -> 238583 bytes
 .../protocol/visual_spot/vsr_test_1001_flip.png    |   Bin 0 -> 134758 bytes
 .../protocol/visual_spot/vsr_test_1001_orig.png    |   Bin 0 -> 136319 bytes
 .../protocol/visual_spot/vsr_test_1306_flip.png    |   Bin 0 -> 133760 bytes
 .../protocol/visual_spot/vsr_test_1306_orig.png    |   Bin 0 -> 133031 bytes
 .../protocol/visual_spot/vsr_test_2162_flip.png    |   Bin 0 -> 163865 bytes
 .../protocol/visual_spot/vsr_test_2162_orig.png    |   Bin 0 -> 164462 bytes
 .../protocol/visual_transform_validity.csv         |   123 +
 results/grounding/protocol/vsr_test_ids.json       | 28546 +++++++++++++++++++
 23 files changed, 51336 insertions(+)
2026-08-15 16:44:17 -0400 submission: Paper-3 supplementary compiled (suppl.pdf, 2 pages) — full matrices both regimes, per-transform correct/wrong rho tables, per-epoch loss curves, depth-probe n/CI details, algebra verification counts, compute ledger + voided-run provenance, reproducibility summary; OpenReview checklist updated

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 6.6s)

**Tool: bash**

**Input:**
```json
{
  "command": "git log --oneline -8 origin/research/equiorient-phase2; echo ===; git log --oneline -8 origin/research/equiorient-no-box; echo ===; git log -1 --format='%ci' origin/research/equiorient-phase2; git log -1 --format='%ci' origin/research/equiorient-no-box",
  "description": "Checks phase2 and no-box branch activity"
}
```

**Output:**
```
e48054b submission preflight: soften to law-consistent compliance, fix stale 10-seed numbers, sync OpenReview abstract, add 15-seed supplement table
1b3e77c FINAL 15-seed canonical: Eq-Aug -0.93pp n.s., Eq-Wrong +0.68pp p<0.0001 15/15; paper updated (15 seeds, law-sensitivity framing)
c62f90f FINAL: paper updated with clean deterministic N=128 (10 matched seeds) — Eq-Aug -1.4pp n.s., Eq-Wrong +0.76pp p<0.001; mixed-outcome story
623bd81 clean N=128: 10 matched deterministic seeds — Eq-Aug -1.40pp (n.s.), Eq-Wrong +0.76pp (p<0.001, 10/10); exploratory +2.1pp was seeding artifact
8138313 scaffold pulls research/equiorient-phase2 (has determinism fixes)
e7fec42 clean-confirmatory: Modal scaffold -> clean branch, N=128 15-seed clean launcher
714c3f5 FIX determinism: seed before model init (torch/numpy/random/cuda) + SHA-256 noise seed (replaces randomized hash()) + provenance in result JSONs
4b69ead phase2: paper updated with scaling results — N=128 eq=0.956 vs aug=0.936 (+2.1pp)
zsh:1: == not found

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 10.1s)

**Tool: bash**

**Input:**
```json
{
  "command": "git log -1 --format='%ci %s' origin/research/equiorient-phase2; git log -1 --format='%ci %s' origin/research/equiorient-no-box; git log --oneline -5 origin/clean-confirmatory 2>/dev/null; git log -1 --format='%ci' origin/clean-confirmatory",
  "description": "Gets dates and clean-confirmatory branch state"
}
```

**Output:**
```
2026-08-18 19:36:32 -0400 submission preflight: soften to law-consistent compliance, fix stale 10-seed numbers, sync OpenReview abstract, add 15-seed supplement table
2026-08-19 19:23:31 -0400 diagnostics: latent collapse data + v2 easyA result + dev log update
4b69ead phase2: paper updated with scaling results — N=128 eq=0.956 vs aug=0.936 (+2.1pp)
c095c82 phase2: ALL scale experiments complete — N=128 20/20, N=2048 20/20
a9d8bd9 FIX: force L40S only (no A100 fallback) + batch=6 (Modal task limit=10)
9e503c9 phase2: add Qwen2-VL-7B backbone support + data-scale launcher
75dd383 phase2: supplementary material — full tables, bootstrap, identifiability audit, dataset stats, compute ledger
2026-08-17 21:35:09 -0400

```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 58.2s)

_Thinking:_

So yes — Paper 3 has active, very recent work:

- `research/equiorient` (Aug 15): submission-ready kit for WACV 2027 R2
- `research/equiorient-phase2` (Aug 18): 15-seed canonical results — Eq-Aug -0.93pp n.s., Eq-Wrong +0.68pp p<0.0001 15/15; "law-sensitivity framing"; preflight softened claims
- `clean-confirmatory` (Aug 19): latest — "diagnostics: latent collapse data + v2 easyA result + dev log update"

Wait — clean-confirmatory's last commit message "diagnostics: latent collapse data + v2 easyA result" matches master's b024525? Earlier I saw master tip b024525 "diagnostics: latent collapse data + v2 easyA result + dev log update". Let me check: earlier `git log --oneline -3 --all` showed b024525 as top. The no-box branch last commit is 2026-08-19 with that message. Actually the output shows clean-confirmatory log = 4b69ead etc. Hmm, the third block printed clean-confirmatory commits? Let me parse: first command showed phase2 log ending at 4b69ead... then "===" failed because zsh error "== not found"? Actually output shows zsh:1: == not found in previous calls too. In this last call: git log -1 phase2 → Aug 18; no-box → Aug 19 "diagnostics: latent collapse data + v2 easyA result". Then `git log --oneline -5 origin/clean-confirmatory` printed c095c82, a9d8bd9, 9e503c9, 75dd383... wait no.

Actually the output ordering: 
- Line1: phase2 date Aug 18 preflight
- Line2: no-box date Aug 19 diagnostics latent collapse
- Then clean-confirmatory log: 4b69ead? No — it shows "4b69ead phase2: paper updated..." Hmm confusing. It seems clean-confirmatory shares history: its log shows 4b69ead, c095c82 (ALL scale experiments complete), a9d8bd9, 9e503c9, 75dd383. So clean-confirmatory is a branch off phase2 with scale experiments. Date 2026-08-17.

Anyway key answer: YES, Paper 3 has ongoing effort beyond the submitted-kit state:
- Phase-2 line: scaling experiments (N=128→2048 scenes), Qwen2-VL-7B backbone support, determinism fixes, and a final **15-seed canonical run** showing Eq-Aug null but **Eq-Wrong +0.68pp p<0.0001 in 15/15 seeds** — i.e., equiorient training makes the model *more consistent with a wrong law* — reframed as "law-sensitivity".
- Latest branch (no-box / master-tip b024525, Aug 19): latent collapse diagnostics + "v2 easyA result".

Would completed Paper 3 be better than Paper 2? My assessment: The new 15-seed result changes the story from one-seed negative to a multi-seed finding ("training representation to obey an algebra yields law-consistency but transfers to a wrong law too — sensitivity without specificity"). That's more rigorous than before. But compared to Paper 2:
- Paper 3 still synthetic-only (N=128/2048 plan-view scenes), narrow task (binary left/right axis ceiling), mechanistic negative/mixed outcome.
- Paper 2 has real benchmarks (VSR), two real backbones + replication on Qwen3-VL, preregistered protocol.

So even completed, Paper 2 remains the stronger E&D-track submission. But the improved Paper 3 could be a viable second submission or better targeted at a different venue/round after expansion. Also note deadline pressure: today is Aug 22, paper due Aug 28 — phase2 preflight was Aug 18, kit nearly ready.

Also flag: submitting both P2 and P3 same round → overlap risk moderate (different questions though: P2 behavioral fine-tuning decomposition vs P3 representation algebra). They're actually fairly distinct.

Answer concisely with evidence.

Yes — that's true. I checked all the EquiOrient branches, and there's been substantial work **after** the submission-ready kit was frozen (Aug 15):

## What's happened since (newest first)

| Date | Branch | What |
|---|---|---|
| **Aug 19** | `research/equiorient-no-box` (+ merged to master, `b024525`) | Latent-collapse diagnostics + "v2 easyA" experiment + dev log |
| **Aug 18** | `research/equiorient-phase2` | Submission preflight: claims softened to "law-consistent compliance," stale numbers fixed, **15-seed supplement table added**, OpenReview abstract synced |
| Aug 17–18 | `research/equiorient-phase2` | **FINAL 15-seed canonical run**: Eq-Aug −0.93pp (n.s.), **Eq-Wrong +0.68pp p<0.0001 in 15/15 seeds**; also N=128→2048 scene scaling (20/20 runs) and Qwen2-VL-7B backbone support |
| Aug 17 | `clean-confirmatory` | Determinism fixes (seed-before-init, SHA-256 noise seed) after an exploratory +2.1pp result turned out to be a seeding artifact |

## Does the upgraded Paper 3 beat Paper 2?

It materially improves Paper 3 — the story moved from *"one-seed mechanistic negative"* to *"15-seed law-sensitivity finding"*: forcing the latent to obey an algebra produces compliance, but the model obeys a **wrong** law just as readily (Eq-Wrong significant in every seed). That's a cleaner, statistically robust, honest mixed result.

But **it still doesn't overtake Paper 2** as your best E&D-track submission:

1. **Synthetic-only evidence.** All Paper 3 results are on rendered plan-view binary left/right scenes (behavioral task hits ceiling by construction). Paper 2 measures real VLMs on VSR with SITE-grade protocol.
2. **The headline is still a cautionary null.** "Representation complies but transfers nothing behaviorally, and can't distinguish right law from wrong law" is a good workshop/negative-results paper; reviewers scoring NeurIPS-E&D-style criteria favor Paper 2's replicable capability-vector methodology.
3. **Deadline risk.** Paper 2's kit is fully frozen with SHA-256s; Paper 3's phase-2 line was still doing diagnostics *today-minus-3-days* — integrating the 15-seed story into a coherent 5pp paper by Aug 28 is doable but tight.

**Practical suggestion:** submit Paper 2 now (deadline Aug 28), and let Paper 3 ride the phase-2 upgrade into Round 1 of the next cycle (or a different venue) once the easyA/latent-collapse diagnostics settle — the two papers ask different enough questions that venue overlap isn't an issue if they're sequenced.

---

## User

but isnt that not novel enough?? how about u fetch reddit and other website for more actual people talk about

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 79.5s)

_Thinking:_

The user is questioning novelty — presumably of Paper 2 (and/or Paper 3), and wants me to fetch Reddit and other sites for real people's discussions about spatial reasoning in VLMs / VSR benchmark / orientation weakness, to gauge whether this is novel or already-known.

Let me do several web searches: reddit discussions on VLM spatial reasoning, VSR benchmark, orientation facing weakness, SITE benchmark, "VLMs can't tell left from right", fine-tuning spatial reasoning LoRA.

**Tool: websearch**

**Input:**
```json
{
  "numResults": 6,
  "query": "\"Visual Spatial Reasoning\" VSR benchmark orientation relations weakness paper 2025 2026"
}
```

**Output:**
```
{
  "search_id": "search_a42497a0b7901132db9dbffe9515b1b6",
  "results": [
    {
      "url": "https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00566/116470/Visual-Spatial-Reasoning",
      "title": "Visual Spatial Reasoning",
      "publish_date": null,
      "excerpts": [
        "Visual Spatial Reasoning\nby F Liu · 2023 · Cited by 501 — In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in"
      ]
    },
    {
      "url": "https://aclanthology.org/2023.tacl-1.37/",
      "title": "Visual Spatial Reasoning - ACL Anthology",
      "publish_date": "2026-08-21",
      "excerpts": [
        "for underline , <sc>...</sc> for small-caps , <tt>...<tt> for typewriter text , <url>...</url> for URLs, <a href=...> for hyperlinks, and <par/> for paragraph breaks.\n\nVerification against PDF Ensure that the new title/authors match the snapshot below. (If there\nis no snapshot or it is too small, consult the PDF .)\n\nAuthors concatenated from the text boxes above:\n\nALL author names match the snapshot above—including\nmiddle initials, hyphens, and accents.\n\nCreate GitHub issue for staff review\n\n* * *\n\n##### Abstract\n\nSpatial relations are a basic part of human cognition. However, they are expressed in natural language in a variety of ways, and previous work has suggested that current vision-and-language models (VLMs) struggle to capture relational information. In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (e.g., under, in front of, facing).\n\n...\n\nvolume = \"11\",\n    year = \"2023\",\n    address = \"Cambridge, MA\",\n    publisher = \"MIT Press\",\n    url = \"https://aclanthology.org/2023.tacl-1.37/\",\n    doi = \"10.1162/tacl_a_00566\",\n    pages = \"635--651\",\n    abstract = \"Spatial relations are a basic part of human cognition. However, they are expressed in natural language in a variety of ways, and previous work has suggested that current vision-and-language models (VLMs) struggle to capture relational information. In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (e.g., under, in front of, facing). While using a seemingly simple annotation format, we show how the dataset includes challenging linguistic phenomena, such as varying reference frames. We demonstrate a large gap between human and model performance: The human ceiling is above 95{\\%}, while state-of-the-art models only achieve around 70{\\%}.\n\n...\n\nHowever, they are expressed in natural language in a variety of ways, and previous work has suggested that current vision-and-language models (VLMs) struggle to capture relational information. In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (e.g., under, in front of, facing). While using a seemingly simple annotation format, we show how the dataset includes challenging linguistic phenomena, such as varying reference frames. We demonstrate a large gap between human and model performance: The human ceiling is above 95%, while state-of-the-art models only achieve around 70%. We observe that VLMs’ by-relation performances have little correlation with the number of training examples and the tested models are in general incapable of recognising relations concerning the orientations of objects.1</abstract>\n    <identifier type=\"citekey\">liu-etal-2023-visual</identifier>\n\n...\n\nIn this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (e.g., under, in front of, facing). While using a seemingly simple annotation format, we show how the dataset includes challenging linguistic phenomena, such as varying reference frames. We demonstrate a large gap between human and model performance: The human ceiling is above 95%, while state-of-the-art models only achieve around 70%. We observe that VLMs’ by-relation performances have little correlation with the number of training examples and the tested models are in general incapable of recognising relations concerning the orientations of objects.1\n%R 10.1162/tacl_a_00566\n%U https://aclanthology.org/2023.tacl-1.37/\n%U https://doi.org/10.1162/tacl_a_00566\n%P 635-651\n```\n\nDownload as\nFile Copy to Clipboard\n\n##### Markdown (Informal)\n\n[Visual Spatial Reasoning](https://aclanthology.org/2023.tacl-1.37/) (Liu et al."
      ]
    },
    {
      "url": "https://www.alphaxiv.org/abs/2510.03441",
      "title": "Spatial-ViLT: Enhancing Visual Spatial Reasoning through Multi-Task Learning | alphaXiv",
      "publish_date": "2025-10-03",
      "excerpts": [
        "Recent work like SpatialVLM [5] and [22] has attempted to address this shortcoming by creating large-scale datasets focused on spatial reasoning, and ⋆ These authors contributed equally. arXiv:2510.03441v1 [cs.CV] 3 Oct 2025\n\n2 Islam et al. The airplane is perpendicular to the truck The bus is away from the cup The cake consists of the dog The potted plant is touching the teddy bear The cat is inside the vase The bed is on the left side of the bench Fig. 1: Challenging spatial reasoning examples from the VSR dataset that high- light current limitations in vision-language models. These cases demonstrate failures in orientation understanding (airplane-truck), proximity detection in complex scenes (bus-cup), topological reasoning (cat-vase), semantic consistency (cake-dog), contact detection (plant-teddy bear), and precise spatial positioning (bed-bench). fine-tuning VLMs explicitly on spatial relation understanding tasks respectively.\n\n...\n\nTable 1 presents the meta-categories and their associated relations used in the VSR dataset. Adapted from the summarized table in [20], we have included the spatial features required for each meta-category based on detailed study. This table categorizes spatial relations and identifies essential spatial features nec- essary for accurate interpretation. Research highlights the importance of these features: depth maps are crucial for understanding adjacency and projective re- lations [23], 3D coordinates facilitate orientation and spatial positioning [21], and edge detection is vital for identifying boundaries and topological relationships [3]. Directional relations benefit from motion vectors and trajectory analysis [27], while pose estimation and orientation detection are critical for accurately interpreting orientation [6]. Distance measurement tools enhance proximity un- derstanding [8], and segmentation aids in recognizing topological relations [10]."
      ]
    },
    {
      "url": "http://export.arxiv.org/abs/2205.00363v1",
      "title": "[2205.00363v1] Visual Spatial Reasoning - export.arxiv.org",
      "publish_date": "2022-04-30",
      "excerpts": [
        "Abstract: Spatial relations are fundamental to human cognition and are the most basic knowledge for us to understand and communicate about our physical surroundings. In this paper, we ask the critical question: Are current vision-and-language models (VLMs) able to correctly understand spatial relations? To answer this question, we propose Visual Spatial Reasoning (VSR), a novel benchmark task"
      ]
    },
    {
      "url": "https://arxiv.org/abs/2205.00363",
      "title": "[2205.00363] Visual Spatial Reasoning - arXiv",
      "publish_date": null,
      "excerpts": [
        "In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (such as: under, in front of, and facing). While using a seemingly simple annotation format, we show how the dataset includes challenging linguistic phenomena, such as varying reference frames. We demonstrate a large gap between human and model performance: the human ceiling is above 95%, while state-of-the-art models only achieve around 70%. We observe that VLMs' by-relation performances have little correlation with the number of training examples and the tested models are in general incapable of recognising relations concerning the orientations of objects.\n\n|Comments: |TACL camera-ready version; code and data available at [this https URL](https://github.com/cambridgeltl/visual-spatial-reasoning) |\n| --- | --- |\n|Subjects: |Computation and Language (cs.CL) ; Artificial Intelligence (cs."
      ]
    },
    {
      "url": "https://arxiv.org/html/2510.13394",
      "title": "Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models",
      "publish_date": null,
      "excerpts": [
        "Our in-depth error analysis further reveals that these failures stem not from simple visual perception, but from fundamental deficits in cognitive processes like rule-based reasoning and mental simulation.\nOur key contributions include:\n\n* •\n  \n  A Cognitively Grounded Taxonomy: We adopt a cognitively grounded framework that, unlike previous task-oriented benchmarks, provides a unified taxonomy to classify any spatial task, revealing specific weaknesses like dynamic reasoning that are otherwise obscured.\n* •\n  \n  A Scalable and Verifiable Data Generation Pipeline: We design and implement a novel, automated pipeline using Blender to programmatically generate complex 3D spatial reasoning tasks. This methodology is a key contribution, offering a reusable tool for the community to overcome the data scarcity that has limited previous dynamic reasoning research. The pipeline ensures verifiability through seeded randomization and reproducible distractor generation strategies.\n* •\n\n...\n\nPrevious benchmarks offer a fragmented evaluation, lacking a unified cognitive framework. Benchmarks such as LEGO-Puzzles (Tang et al. , [2025](https://arxiv.org/html/2510.13394v3.bib44 \"LEGO-Puzzles: How Good Are MLLMs at Multi-Step Spatial Reasoning?\") ) , SAT (Ray et al. , [2024](https://arxiv.org/html/2510.13394v3.bib54 \"SAT: Dynamic Spatial Aptitude Training for Multimodal Language Models\") ) and VSI-Bench (Yang et al. , [2024](https://arxiv.org/html/2510.13394v3.bib57 \"Thinking in Space: How Multimodal Large Language Models See, Remember, and Recall Spaces\") ) are confined to narrow, specific tasks, preventing a holistic assessment of a model’s true spatial abilities. Spatial-DISE overcomes this by introducing a unified 2x2 cognitive taxonomy. This framework, rooted in cognitive science, enables a comprehensive and balanced evaluation, allowing for the precise diagnosis of model weaknesses.\n\nFurthermore, prior benchmarks have a disproportionate focus on static reasoning.\n\n...\n\nIn The IEEE Conference on Computer Vision and Pattern Recognition (CVPR) , Cited by: [§1](https://arxiv.org/html/2510.13394v3.p2.1 \"1 Introduction ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") , [Table 1](https://arxiv.org/html/2510.13394v3.T1.1.1.1.1.14.1 \"In 2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") , [§2](https://arxiv.org/html/2510.13394v3.p3.1 \"2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") .\n* M. Jia, Z. Qi, S. Zhang, W. Zhang, X. Yu, J. He, H. Wang, and L. Yi (2025) OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models . arXiv:2506.03135 . Cited by: [Table 1](https://arxiv.org/html/2510.13394v3.T1.1.1.1.1.18.1 \"In 2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") , [§2](https://arxiv.\n\n...\n\nYuan (2024) LLaVA-CoT: Let Vision Language Models Reason Step-by-Step . arXiv:2411.10440 . Cited by: [§4.1](https://arxiv.org/html/2510.13394v3.SS1.p1.1 \"4.1 Experiment Setting ‣ 4 Evaluation on Spatial-DISE Bench ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") .\n* W. Xu, D. Lyu, W. Wang, J. Feng, C. Gao, and Y. Li (2025) Defining and Evaluating Visual Language Models’ Basic Spatial Abilities: A Perspective from Psychometrics . In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) , W. Che, J. Nabende, E. Shutova, and M. T. Pilehvar (Eds.) , pp. 11571–11590 . External Links: ISBN 979-8-89176-251-0 Cited by: [Table 1](https://arxiv.org/html/2510.13394v3.T1.1.1.1.1.16.1 \"In 2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") , [§2](https://arxiv.org/html/2510.13394v3.p4.\n1 \"2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") .\n* J. Yang, S. Yang, A. W. Gupta, R. Han, L. Fei-Fei, and S. Xie (2024) Thinking in Space: How Multimodal Large Language Models See, Remember, and Recall Spaces . In CVPR 2025 , Cited by: [Table 1](https://arxiv.org/html/2510.13394v3.T1.1.1.1.1.10.1 \"In 2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") , [§2](https://arxiv.org/html/2510.13394v3.p2.1 \"2 Related Work ‣ Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models\") .\n* S. Yang, R. Xu, Y. Xie, S. Yang, M. Li, J. Lin, C. Zhu, X. Chen, H. Duan, X. Yue, D. Lin, T. Wang, and J. Pang (2025) MMSI-Bench: A Benchmark for Multi-Image Spatial Intelligence . arXiv:2505.23764 . Cited by: [§C.2](https://arxiv.org/html/2510.13394v3.SS2.p1.1 \"C.\n\n...\n\nTable 6: Each spatial task used in our study and its canonical source test. Spatial Perception (SP), Spatial Relation (SR), Spatial Orientation (SO), Mental Rotation (MR), and Spatial Visualization (SV)\n\nTask Original Test DISE Taxonomy Spatial Ability 3D Combination Differential Aptitude Tests (Bennett et al. , [1947](https://arxiv.org/html/2510.13394v3.bib8 \"Differential aptitude tests\") ) Extrinsic-Dynamic SV 2D Combination Minnesota Paper Form Board Test (Peter, [1974](https://arxiv.org/html/2510.13394v3.bib10 \"Minnesota paper form board test manual, series AA and BB.\") ) Extrinsic-Dynamic SV 3D Projection Purdue Spatial Visualization Test – Views (BODNER and GUAY, [1997](https://arxiv.org/html/2510.13394v3.bib9 \"The Purdue Visualization of Rotations Test\") ) Extrinsic-Static SP, SV Fold and Punch Paper Folding Test (VZ-2) (Pallrand and Seeber, [1984](https://arxiv.org/html/2510.13394v3."
      ]
    },
    {
      "url": "https://github.com/cambridgeltl/visual-spatial-reasoning",
      "title": "GitHub - cambridgeltl/visual-spatial-reasoning: [TACL'23] VSR: A probing benchmark for spatial undersranding of vision-language models. · GitHub",
      "publish_date": null,
      "excerpts": [
        "# cambridgeltl/visual-spatial-reasoning\n\n- Page: GitHub repository\n- URL: https://github.com/cambridgeltl/visual-spatial-reasoning\n- Description: [TACL'23] VSR: A probing benchmark for spatial undersranding of vision-language models. - cambridgeltl/visual-spatial-reasoning\n- Stars: 150\n- Forks: 14\n- License: Apache-2.0 license\n- Default branch: master\n- Created: 2022-05-01T14:03:59.000Z\n- Commits: 52\n\n## Top-level files\n\n- analysis_scripts/\n- data/\n- feature_extraction/\n- figures/\n- scripts/\n- src/\n- .gitignore\n- LICENSE\n- README.md\n- requirements.txt\n\n## README.md\n\n# 🔭 VSR: Visual Spatial Reasoning\n\n### A probing benchmark for spatial undersranding of vision-language models.\n\n[arxiv](https://arxiv.org/abs/2205.00363) · [dataset](https://github.com/cambridgeltl/visual-spatial-reasoning/tree/master/data) · [benchmark](https://paperswithcode.com/sota/visual-reasoning-on-vsr)\n\n* * *\n\n...\n\n_** The relations are sorted by frequencies from left to right. The VLMs' by-relation performances have little correlation with relation frequency, meaning that more training data do not necessarily lead to better performance.\n\n**_Understanding object orientation is hard._** After classifying spatial relations into meta-categories, we can clearly see that all models are at chance level for \"orientation\"-related relations (such as \"facing\", \"facing away from\", \"parallel to\", etc.).\n\nFor more findings and takeways including zero-shot split performance. check out our paper!\n\n### 2 The VSR dataset: Splits, statistics, and meta-data\n\nThe VSR corpus, after validation, contains 10,972 data points with high agreement. On top of these, we create two splits (1) random split and (2) zero-shot split. For random split, we randomly split all data points into train, development, and test sets. Zero-shot split makes sure that train, development and test sets have no overlap of concepts (i.e."
      ]
    },
    {
      "url": "https://www.researchgate.net/publication/371823714_Visual_Spatial_Reasoning",
      "title": "(PDF) Visual Spatial Reasoning - ResearchGate",
      "publish_date": "2023-06-20",
      "excerpts": [
        "In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial relations in English (e.g., under, in front of, facing)."
      ]
    },
    {
      "url": "https://www.researchgate.net/publication/360333079_Visual_Spatial_Reasoning",
      "title": "(PDF) Visual Spatial Reasoning - ResearchGate",
      "publish_date": "2022-04-30",
      "excerpts": [
        "net/publication/360333079_Visual_Spatial_Reasoning/fulltext/62709d94107cae29198419d0/Visual-Spatial-Reasoning.pdf)\n\nRead file\n\n[Download citation](https://www.researchgate.net/publication/360333079_Visual_Spatial_Reasoning/citation/download)\n\nCopy link Link copied\n\n* * *\n\nRead file [Download citation](https://www.researchgate.net/publication/360333079_Visual_Spatial_Reasoning/citation/download) Copy link Link copied\n\nCitations (2) References (33) Figures (12)\n\n## Abstract and Figures\n\nSpatial relations are fundamental to human cognition and are the most basic knowledge for us to understand and communicate about our physical surroundings. In this paper, we ask the critical question: Are current vision-and-language models (VLMs) able to correctly understand spatial relations? To answer this question, we propose Visual Spatial Reasoning (VSR), a novel benchmark task with human labelled dataset for investigating VLMs' capabilities in recognising 65 types of spatial relationships (e.g.\n, under, in front of, facing etc.) in natural text-image pairs. Specifically, given a caption and an image, the model needs to perform binary classification and decide if the caption accurately describes the spatial relationships of two objects presented in the image. While being seemingly simple and straightforward, the task shows a large gap between human and model performance (human ceiling on the VSR task is above 95% and models only achieve around 70%). With fine-grained categorisation and control on both concepts and relations, our VSR benchmark enables us to perform interesting probing analysis to pinpoint VLMs' failure cases and the reasons behind. We observe that VLMs' by-relation performances have little correlation with the number of training examples and the tested models are in general incapable of recognising relations that concern orientations of objects. Also, VLMs have poor zero-shot generalisation toward unseen concepts. The dataset and code are released at github.\n\n...\n\ncognition and are the most basic knowledge\n\nfor us to understand and communicate about\n\nour physical surroundings.In this paper, we\n\nask the critical question:Are current vision-\n\nand-language models (VLMs) able to correctly\n\nunderstand spatial relations?To answer this\n\nquestion, we propose Visual Spatial Reasoning\n\n(VSR), a novel benchmark task with human la-\n\nbelled dataset for investigating VLMs’ capabil-\n\nities in recognising 65 types of spatial relation-\n\nships (eg., under, in front of, facing etc.)in\n\nnatural text-image pairs.Speciﬁcally, given a\n\ncaption and an image, the model needs to per-\n\nform binary classiﬁcation and decide if the cap-\n\ntion accurately describes the spatial relation-\n\nships of two objects presented in the image.\n\nWhile being seemingly simple and straightfor-\n\nward, the task shows a large gap between hu-\n\nman and model performance (human ceiling\n\non the VSR task is above 95% and models only\n\nachieve around 70%).With ﬁne-grained cate-\ngorisation and control on both concepts and re-\n\nlations, our VSR benchmark enables us to per-\n\nform interesting probing analysis to pinpoint\n\nVLMs’ failure cases and the reasons behind.\n\nWe observe that VLMs’ by-relation perfor-\n\nmances have little correlation with number of\n\ntraining examples and the tested models are in\n\ngeneral incapable of recognising relations that\n\nconcern orientations of objects.Also, VLMs\n\nhave poor zero-shot generalisation towards un-\n\nseen concepts.The dataset and code are re-\n\nleased at github.com/cambridgeltl/\n\nvisual-spatial-reasoning .\n\n1 Introduction\n\nMulti-modal NLP research has been developing\n\nrapidly in the last couple of years with the intro-\n\nduction of a series of pre-trained vision-language\n\nmodels (VLMs) such as ViLBERT ( Lu et al. , 2019 ),\n\nVisualBERT ( Li et al. , 2019 ), LXMERT ( T an and\n\nBansal , 2019 ), UNITER ( Chen et al. , 2019 ), and\n\nFigure 1:Caption: The person is ahead of the cow .\n\nLabel: True .\n\n...\n\nguistic or cognitive properties, making it difﬁcult to\n\ncategorise and fully understand the model failures.\n\nAnother line of work generates synthetic datasets\n\nin a controlled manner to target speciﬁc relations\n\nand properties when testing VLMs (e.g., CLEVR\n\n( Liu et al. , 2019 )), but we will demonstrate later\n\nin our paper that synthetic datasets neglect many\n\nrealistic challenges presented in natural images.\n\nTo address the lack of probing evaluation bench-\n\nmarks in this ﬁeld,we present VSR (Visual\n\nSpatial Reasoning),a ﬁrst controlled probing\n\ntask/benchmark that explicitly tests VLM’s spa-\n\ntial reasoning. We choose spatial reasoning as the\n\ntask focus because it is one of the most fundamen-\n\ntal capabilities for both humans and VLMs. Such\n\nrelations are crucial to how humans organise the\n\nmental space and make sense of the physical world,\n\nand therefore fundamental for a grounded theory\n\nof semantics ( Levinson , 2003 ). However, spatial\n\n...\n\nand highlight that (1) positional encodings are ex-\n\ntremely important for the VSR task, (2) models’\n\nby-relation performance barely correlates with the\n\nnumber of training examples, (3) in fact, several\n\nspatial relations that concern orientation of objects\n\nare especially challenging for current VLMs, (4)\n\nVLMs have extremely poor generalisation on un-\n\nseen concepts.\n\n2Dataset Creation\n\nIn this section we detail how VSR is constructed.\n\nThe data collection process can generally be split-\n\nCaption: The cat (is) \\_\\_\\_\\_ the laptop.\n\nabovebeneathbehind ……\n\nThe completed caption is true for:\n\nimage 1image 2\n\n✅\n\n✅\n\nChoose a relation to complete the caption:\n\nFigure 3: An annotation example of concepts “cat” and\n\n“laptop” in the contrastive caption generation phase.\n\nThe example generates two data points for the VSR\n\nbenchmark:one “True” instance when the completed\n\ncaption is paired with image 2 (right) and one “False”\n\ninstance when paired with image 1 (left).\n\n...\n\nalso have the error-conﬂation problem. Also, the\n\nnumber of examples and types of relations are\n\nrestricted by COCO captions.\n\nThere has also been interests in probing models’\n\nspatial reasoning capability without visual input.\n\nE.g, Collell et al. ( 2018 ); Liu et al. ( 2022 ) probe\n\npretrained text-only models or VLMs’ spatial rea-\n\nsoning capabilities with text-only questions.Dif-\n\nferently, VSR focuses on the joint understanding\n\nof vision and language input.\n\n5Conclusion and Future Directions\n\nWe have proposed Visual Spatial Reasoning (VSR),\n\na controlled probing task for testing current vision-\n\nlanguage models (VLMs)’ capabilities of recognis-\n\ning and reasoning about spatial relations in natural\n\nimage and text pairs.On the VSR benchmark,\n\nwe tested three popular VLMs and found they lag\n\nbehind humans by more than 20%.On a more chal-\n\nlenging concept zero-shot split, the tested VLMs\n\nstruggle to reach 60% of accuracy and their per-\n\n...\n\n### Visual Spatial Reasoning\n\nJune 2023 · Transactions of the Association for Computational Linguistics\n\n* [Fangyu Liu](https://www.researchgate.net/profile/Fangyu-Liu-10)\n* [Guy Emerson](https://www.researchgate.net/scientific-contributions/Guy-Emerson-2220582889)\n* [Nigel Collier](https://www.researchgate.net/scientific-contributions/Nigel-Collier-39952245)\n\nSpatial relations are a basic part of human cognition. However, they are expressed in natural language in a variety of ways, and previous work has suggested that current vision-and-language models (VLMs) struggle to capture relational information. In this paper, we present Visual Spatial Reasoning (VSR), a dataset containing more than 10k natural text-image pairs with 66 types of spatial ... [Show full abstract] relations in English (e.g., under, in front of, facing). While using a seemingly simple annotation format, we show how the dataset includes challenging linguistic phenomena, such as varying reference frames."
      ]
    },
    {
      "url": "https://github.com/cambridgeltl/visual-spatial-reasoning/blob/master/README.md",
      "title": "visual-spatial-reasoning/README.md at master · cambridgeltl/visual-spatial-reasoning · GitHub",
      "publish_date": null,
      "excerpts": [
        "# cambridgeltl/visual-spatial-reasoning — README.md\n\n- Page: GitHub code file\n- URL: https://github.com/cambridgeltl/visual-spatial-reasoning/blob/master/README.md\n- Repository: cambridgeltl/visual-spatial-reasoning\n- Path: README.md\n- Ref: master\n- Lines: 124\n\n---\n\n<br />\n<p align=\"center\">\n  <h1 align=\"center\">🔭 VSR: Visual Spatial Reasoning</h1>\n  <h3 align=\"center\">A probing benchmark for spatial undersranding of vision-language models.</h3>\n  \n  <p align=\"center\">  \n    <a href=\"https://arxiv.org/abs/2205.00363\">arxiv</a>\n    ·\n    <a href=\"https://github.com/cambridgeltl/visual-spatial-reasoning/tree/master/data\">dataset</a>\n    ·\n    <a href=\"https://paperswithcode.com/sota/visual-reasoning-on-vsr\">benchmark</a>\n    \n  </p>\n</p>\n\n***\n**Update [Mar 22, 2023]**: We updated our arxiv preprint with the [camera-ready version](https://arxiv.org/abs/2205.00363)) and also the dataset in this repo to be consistent with the accepted paper.\n\n...\n\nExisting vision-language reasoning datasets are great but they compose multiple types of challenges and can thus conflate different sources of error.\nThe VSR corpus focuses specifically on spatial relations so we can have accurate diagnosis and maximum interpretability.\n\n#### 1.2 What have we found?\nBelow are baselines' by-relation performances on VSR (random split). \n!\n**_More data != better performance._** The relations are sorted by frequencies from left to right. The VLMs' by-relation performances have little correlation with relation frequency, meaning that more training data do not necessarily lead to better performance.\n\n<img align=\"right\" width=\"320\"  src=\"figures/performance_by_meta_cat_random_split_v4.png\"> \n\n**_Understanding object orientation is hard._** After classifying spatial relations into meta-categories, we can clearly see that all models are at chance level for \"orientation\"-related relations (such as \"facing\", \"facing away from\", \"parallel to\", etc.)."
      ]
    }
  ],
  "warnings": null,
  "usage": [
    {
      "name": "sku_search",
      "count": 1
    }
  ],
  "session_id": "ses_fd81e747fffey16zO59Xh0VoM8"
}
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 9.7s)

**Tool: websearch**

**Input:**
```json
{
  "numResults": 6,
  "query": "site:reddit.com VLM spatial reasoning \"left from right\" OR orientation OR facing failure multimodal"
}
```

**Output:**
```
{
  "search_id": "search_0d1b3e606b3dd7fe43ca220336178785",
  "results": [
    {
      "url": "https://huggingface.co/blog/KBayoud/spatial-reasoning-in-vlms",
      "title": "Seeing Isn’t Understanding: The Spatial Reasoning Gap in Vision-Language Models",
      "publish_date": "2025-07-13",
      "excerpts": [
        "This blog post explores one of the most persistent challenges in multimodal AI: spatial reasoning. We'll walk through what spatial reasoning actually means, why it’s so hard for VLMs, what researchers have tried to fix it, and what future directions and the benefits of a spatially-aware VLMs."
      ]
    },
    {
      "url": "https://cvpr.thecvf.com/virtual/2024/poster/31284",
      "title": "CVPR Poster SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities",
      "publish_date": "2026-04-16",
      "excerpts": [
        "We designate 38 different types of qualitative and quantitative spatial reasoning ... VLM is able to understand the quantitative spatial reasoning question."
      ]
    },
    {
      "url": "https://arxiv.org/html/2503.01773v2",
      "title": "Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective on Focus Areas",
      "publish_date": null,
      "excerpts": [
        "bib23) ) analyze VLM failures from a CLIP perspective, highlighting that the visual capabilities of recent VLMs still face systematic shortcomings, partly due to CLIP’s limitations in specific cases.\n\n#### C.3 Decoding Strategies for Reducing Hallucinations\n\nThis work is also connected to various decoding and tuning strategies aimed at mitigating hallucinations in VLMs. Leng et al. ( [2024](https://arxiv.org/html/2503.01773v2.bib13) ) introduce a contrastive decoding method that emphasizes certain image regions. Wang et al. ( [2024](https://arxiv.org/html/2503.01773v2.bib24) ) propose a data-augmentation approach to create image-intensive datasets, followed by preference tuning on this enhanced data. Furthermore, knowledge extraction techniques such as the method proposed by Chuang et al. ( [2023](https://arxiv.org/html/2503.01773v2.bib7) ) improve decoding by leveraging contrastive layers for better knowledge extraction. Similarly, Activation Decoding (Chen et al., [2024b](https://arxiv.\n\n...\n\nFor example, we hypothesize that the entropy of attention will be lower when the model encounters familiar cases.\n\n| |$E\\left(\\mathcal{A}_{n,j}^{(l,h)}\\right)=-\\sum_{j=1}^{t}\\tilde{P}\\left(\\mathcal%\n{A}_{n,j}^{(l,h)}\\right)\\log\\tilde{P}\\left(\\mathcal{A}_{n,j}^{(l,h)}\\right)$ | |(4) |\n| --- | --- | --- | --- |\n\nIn Equation [4](https://arxiv.org/html/2503.01773v2.E4 \"Equation 4 ‣ E.1 Other metrics to distinguish the distributions ‣ Appendix E Further Analysis ‣ Appendix ‣ Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective on Focus Areas\") , $\\mathcal{A}_{n,j}^{(l,h)}$ denotes the attention scores assigned by the $h$ \\-th head in the $l$ \\-th layer to the $j$ \\-th token in sequence $n$ . The summation runs over $j=1$ to $t$ , where $t$ is the total number of tokens considered for this attention distribution. $\\tilde{P}\\left(\\mathcal{A}_{n,j}^{(l,h)}\\right)$ is the normalized probability distribution of these attention scores.\n\n...\n\nA high skewness suggests that the attention is predominantly focused on a few positions, while a low skewness indicates a more balanced spread across multiple regions. By examining skewness, we aim to identify whether the attention is being disproportionately allocated to particular image features, which could provide additional insights into how familiarity is expressed through attention patterns.\nWe could see from Figure [14](https://arxiv.org/html/2503.01773v2.F14 \"Figure 14 ‣ E.1 Other metrics to distinguish the distributions ‣ Appendix E Further Analysis ‣ Appendix ‣ Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective on Focus Areas\") that Synthetic datasets show a higher skewness. However, it also related with the object distribution, which is not the real factor behinds the difference.\n\n| |$S\\left(\\mathcal{A}_{n,j}^{(l,h)}\\right)=\\frac{\\sum_{j=1}^{t}\\left(j-\\mu_{%\n\\mathcal{A}}\\right)^{3}\\tilde{P}_{j}}{\\sigma_{\\mathcal{A}}^{3}}$ | |(5) |\n\n...\n\nTo categorize six different spatial relationships, we check whether specific phrases appear in the “llava\\_v1\\_5\\_mix665k.json”, which is the training data of LLaVA and increment corresponding counters. For the left relationship, we look for phrases such as “left side,” “left of,” “to the left,” and “on the left.” Similarly, for the right relationship, we detect phrases like “right side,” “right of,” “to the right,” and “on the right.” The on relationship is identified using phrases like “are on the,” “is on the,” and “located on,” ensuring they do not co-occur with “on the left” or “on the right.” To detect the under relationship, we check for phrases such as “under the,” “beneath the,” or “below the.” For the front relationship, we look for phrases like “are in front of,” “is in front of,” and “locate in front of.” Finally, the behind relationship is identified by the phrase “behind the.”."
      ]
    },
    {
      "url": "https://arxiv.org/html/2607.17657v1",
      "title": "OrientSAM: Mitigating Camera-Centric Shortcut in Multimodal Spatial Reasoning via Orientation-Aware Spatial Alignment",
      "publish_date": null,
      "excerpts": [
        "Multimodal large language models (MLLMs) have achieved strong performance on a wide range of vision-language tasks ( 17 ; 36 ) , yet their spatial reasoning ability remains limited when the task requires perspective transformation rather than direct interpretation from the camera view. In many real-world scenarios, the correct answer is defined by the local viewpoint of a reference object rather than the image plane. For example, judging whether one person is on another person’s left or right depends not only on image-plane coordinates, but also on the reference person’s facing direction ( 16 ; 15 ; 18 ; 25 ) .\n\nThis limitation is fundamental for multimodal intelligence in the physical world ( 36 ) . Applications such as embodied interaction ( 27 ) , human-object collaboration ( 6 ) , and scene understanding ( 34 ; 1 ) often require reasoning from a reference object’s viewpoint rather than the camera’s.\n\n...\n\nBased on this aligned multimodal input, the model predicts the reference-centric answer $y^{\\text{ref}}$ using the standard next-token prediction objective:\n\n|$\\mathcal{L}_{\\text{NTP}}=-\\log p_{\\Theta}\\left(y^{\\text{ref}}\\mid\\mathcal{X}\\right),$ |(16) |\n| --- | --- |\n\nwhere $\\Theta$ denotes all trainable parameters.\nNotably, we do not explicitly introduce an auxiliary loss against the camera-centric answer. Instead, shortcut suppression is achieved implicitly through multimodal alignment: once the model is forced to condition its prediction on the aligned RGB-depth-orientation token structure, it becomes less likely to rely solely on image-plane cues and more capable of performing reference-centric reasoning. In this sense, orientation-aware alignment serves as the bridge between low-level geometric priors and high-level language reasoning.\n\n...\n\nwhere $\\hat{\\phi}_{i}$ is the predicted azimuth and $\\ell_{\\text{orient}}$ denotes the orientation supervision loss. This stage encourages the model to establish a stable mapping from regional appearance to semantic facing direction, thereby learning reliable orientation-aware embeddings.\n\n|Model |Comp. |Spatial-MM |ViewSpatial |3DSR |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n|Orient |CL |Cam |Non-Cam |P-Obj |P-Rel |Ori.-Dir. |\n|Base-VLM (Zero-shot) |$\\times$ |$\\times$ |77\\.15 |33\\.40 |32\\.13 |34\\.59 |41\\.21 |\n|Base-VLM (SFT) |$\\times$ |$\\times$ |87\\.65 |43\\.15 |44\\.30 |42\\.12 |50\\.35 |\n|OrientSAM (w/o CL) |$\\checkmark$ |$\\times$ |88\\.54 |76\\.29 |65\\.40 |74\\.32 |72\\.83 |\n|OrientSAM (Full) |$\\checkmark$ |$\\checkmark$ |89\\.40 |87\\.31 |73\\.49 |85\\.04 |81\\.83 |\n\nTable 4: Ablation results of orientation feature injection and curriculum learning (Accuracy, %). Comp.\n\n...\n\nIn this paper, we study perspective-aware spatial reasoning in multimodal large language models and show that current models still suffer from a strong camera-centric shortcut, especially when camera-centric and reference-centric answers conflict. Our analysis further reveals that this failure is closely related to the orientation of the reference object, suggesting that the lack of explicit orientation modeling is a key bottleneck for reference-centric reasoning.\nTo address this issue, we propose OrientSAM, an orientation-aware spatial alignment framework that explicitly injects object orientation into multimodal representations and aligns it with downstream spatial reasoning. By combining multi-expert spatial data construction, Fourier-based angle encoding, and curriculum learning, OrientSAM enables the model to better establish local reference frames and perform perspective-aware reasoning.\n\n...\n\nFollowing this framework, our main analysis is conducted on three left/right person-perspective benchmarks: Spatial-MM, ViewSpatial, and 3DSRBench. For all three datasets, each sample is converted into a unified format containing the image, the question, the reference-centric answer, the camera-centric answer derived from the image plane, the reference and query regions, and the estimated orientation of the reference object. This unified formulation allows the same diagnostic metrics to be applied across datasets.\n\nBeyond the consistent/conflict split, we also analyze how shortcut strength varies with the orientation of the reference object. Under the angle semantics adopted in our analysis, $0^{\\circ}$ corresponds to front-facing and $180^{\\circ}$ corresponds to back-facing relative to the camera. To measure the distance from the back-facing condition, we define\n\n|$\\theta_{\\mathrm{abs}}=\\mathrm{circ\\_dist}(\\theta_{\\mathrm{raw}},180^{\\circ}),$ |(25) |\n| --- | --- |\n\n...\n\nwhere $D_{\\mathrm{img}}\\in\\mathbb{R}^{H\\times W}$ is the dense depth map, $K\\in\\mathbb{R}^{3\\times 3}$ is the estimated camera intrinsic matrix, and $\\xi\\in SE(3)$ denotes the camera pose. Based on the segmentation mask of each instance, we further compute an instance-level depth representation. To reduce the influence of local noise and outliers, we use the median depth inside the mask as the depth of instance $O_{i}$ :\n\n|$z_{i}=\\mathrm{Median}\\left(\\left\\{D_{\\mathrm{img}}(u,v)\\mid(u,v)\\in m_{i}\\right\\}\\right).$ |(31) |\n| --- | --- |\n\nBesides depth, object orientation is another key attribute in our pipeline. For each instance region cropped from the image, we apply an orientation estimation model to obtain\n\n|$(\\hat{\\theta}_{i},\\hat{\\phi}_{i},\\hat{\\delta}_{i},c_{i})=F_{\\mathrm{ori}}(\\mathrm{Crop}(I,b_{i})),$ |(32) |\n| --- | --- |\n\n...\n\nUsing their image-plane positions, instance-level depth, and the orientation of the reference object, we derive the relative relation under the reference-centered local frame. Compared with standard camera-view labeling, this step explicitly introduces reference-frame transformation into the annotation process. Therefore, the generated supervision is not limited to image-plane left/right relations, but instead reflects the spatial relation from the viewpoint of the reference object.\n\nBased on the derived spatial attributes and relations, we construct spatial question-answer pairs for instruction tuning. These samples cover both basic orientation-related perception and more challenging perspective-aware reasoning under non-camera reference frames.\n\n...\n\nOur experiments focus on perspective-aware spatial reasoning under non-camera reference frames, where the model is required to infer spatial relations from the local viewpoint of a reference object rather than from the image plane.\n\nWe evaluate OrientSAM on three representative spatial reasoning benchmarks, namely Spatial-MM, ViewSpatial, and 3DSRBench. These benchmarks are all used to assess whether multimodal models can correctly perform reference-frame transformation in left/right spatial reasoning tasks. For analysis purposes, all samples are converted into a unified format containing the image, the question, the ground-truth reference-centric answer, the corresponding camera-centric answer derived from image-plane geometry, the reference and query regions, and the estimated orientation of the reference object. This unified formulation allows us to conduct consistent shortcut analysis across different datasets.\nFollowing the setting in the main paper, the evaluation mainly focuses on binary left/right reasoning under a reference object’s viewpoint. In addition to standard answer accuracy, we further analyze model behavior using the diagnostic framework introduced in Section 3. Specifically, for each sample, we compare the model prediction with both the reference-centric answer and the camera-centric answer, and divide the benchmark into consistent and conflict subsets according to whether these two answers agree. This protocol is used throughout our shortcut analysis and orientation-based analysis.\n\nFor model comparison, we consider both strong multimodal baselines and our orientation-aware model under the same evaluation setting. All compared models are prompted to answer the same spatial question without access to ground-truth orientation labels at test time.\nThe goal is to ensure that performance differences mainly reflect differences in spatial reasoning ability rather than differences in task formulation. During evaluation, the model output is mapped to the predefined answer space, and only the final left/right decision is used for scoring.\n\nFor training data construction, we use the multi-expert spatial pipeline described in the previous section to automatically generate orientation-aware supervision from large-scale images. The resulting data contain both basic orientation-related perception samples and more complex perspective-aware reasoning samples. These samples are then organized by the curriculum learning strategy in the main paper, so that the training process gradually shifts from easier orientation perception tasks to harder reference-frame transformation tasks.\n\nIn terms of implementation, the orientation signal is incorporated into the model through explicit orientation-aware tokens and Fourier-based angle encoding.\n\n...\n\nFirst, the overall framework still relies on the quality of external expert models in the data construction stage, including region grounding, monocular geometry estimation, and object orientation prediction. Errors from these components may propagate to the automatically generated supervision, which in turn affects the quality of the learned spatial reasoning behavior.\n\nSecond, the effectiveness of the proposed approach depends on whether the reference object has a stable and semantically meaningful front direction. In real images, some objects have ambiguous orientation, weak visual cues, or heavy occlusion, making their semantic facing direction difficult to estimate reliably. In such cases, even e"
      ]
    },
    {
      "url": "https://github.com/vulab-AI/Awesome-Spatial-VLMs",
      "title": "Awesome Spatial VLMs - GitHub",
      "publish_date": null,
      "excerpts": [
        "com/BAAI-DCAI/SpatialBot) [[checkpoint]](https://huggingface.co/RussRobin/SpatialBot-3B) ;\n* [NeurIPS2025] RoboRefer: Towards Spatial Referring with Reasoning in Vision-Language Models for Robotics ( _Beihang University_ ) [[paper]](https://arxiv.org/pdf/2506.04308) [[code]](https://github.com/Zhoues/RoboRefer) [[checkpoint]](https://huggingface.co/collections/Zhoues/roborefer-and-refspatial-6857c97848fab02271310b89) ;\n* [NeurIPS2025] SSR: Enhancing Depth Perception in Vision-Language Models via Rationale-Guided Spatial Reasoning ( _Westlake University_ ) [[paper]](https://arxiv.org/pdf/2505.12448) [[code]](https://github.com/yliu-cs/SSR) [[checkpoint]](https://huggingface.co/collections/yliu-cs/ssr-682d44496b64e4edd94092bb) ;\n* [NeurIPS2025] SD-VLM: Spatial Measuring and Understanding with Depth-Encoded Vision-Language Models ( _Zhejiang University_ ) [[paper]](https://arxiv.org/pdf/2509.17664) [[code]](https://github.com/cpystan/SD-VLM) [[checkpoint]](https://huggingface.\nco/cpystan/SD-VLM-7B) ;\n\n* [NeurIPS2025] SPATIALLM: Training Large Language Models for Structured Indoor Modeling ( _Manycore Tech Inc._ ) [[paper]](https://arxiv.org/pdf/2506.07491) [[code]](https://github.com/manycore-research/SpatialLM) [[checkpoint]](https://huggingface.co/manycore-research/SpatialLM1.1-Qwen-0.5B)\n\n* [Arxiv2025] 3D Aware Region Prompted Vision Language Model ( _UC San Diego_ ) [[paper]](https://arxiv.org/pdf/2509.13317) ;\n **Implicit 3D from Egocentric Views**\n\n* [arXiv2025] VLM-3R: Vision-Language Models Augmented with Instruction-Aligned 3D Reconstruction ( _UT Austin_ ) [[paper]](https://arxiv.org/pdf/2505.20279) [[code]](https://github.com/VITA-Group/VLM-3R) ;\n* [arXiv2025] Spatial-MLLM: Boosting MLLM Capabilities in Visual-based Spatial Intelligence ( _Tsinghua University_ ) [[paper]](https://arxiv.org/pdf/2505.23747) [[code]](https://github.com/diankun-wu/Spatial-MLLM) ;\n\n...\n\n**Manifesting Spatial Priors in 3D and Synthetic Worlds**\n\n* [CVPR2024] SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities ( _Google DeepMind_ ) [[paper]](https://arxiv.org/pdf/2401.12168) [[code]](https://spatial-vlm.github.io/) [[checkpoint]](https://github.com/remyxai/VQASynth?tab=readme-ov-file) ;\n* [NeurIPS2024] Multi-modal Situated Reasoning in 3D Scenes ( _BIGAI_ ) [[paper]](https://arxiv.org/pdf/2409.02389) [[code]](https://github.com/MSR3D/MSR3D) ;\n* [arXiv2025] Multi-SpatialMLLM: Multi-Frame Spatial Understanding with MultiModal Large Language Models ( _Meta FAIR_ ) [[paper]](https://arxiv.org/pdf/2505.17015) [[code]](https://github.com/facebookresearch/Multi-SpatialMLLM?tab=readme-ov-file) ;\n* [arXiv2025] Sparkle: Mastering Basic Spatial Capabilities in Vision Language Models Elicits Generalization to Spatial Reasoning ( _Massachusetts Institute of Technology_ ) [[paper]](https://arxiv.org/pdf/2410.16162) ;\n\n...\n\n* [NeurIPS2025] Actial: Activate Spatial Reasoning Ability of Multimodal Large Language Models ( _Nanjing University_ ) [[paper]](https://openreview.net/pdf?id=jquTBzt3Av) [[code]](https://github.com/warmsnow-sh/Actial) [[checkpoint]](https://huggingface.co/Osilly/Acital-Qwen-2.5VL-7B) ;\n\n## 📚 Datasets and Benchmarks\n\n> A comprehensive list of datasets for training and evaluation.\n> \n> \n\n### Spatially-Oriented Training Corpora\n\n[Dataset](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Dataset_SVQA.md)\n\n### Evaluation Benchmarks\n\n[Benchmark](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Benchmark_SVQA.md)\n\n## 🏆 Spatial VLM Leaderboard & Evaluation Toolkit\n\n### 🏅 Main Leaderboard\n\nThe table below presents the main results from our survey, comparing [38 VLMs](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/evaluation/README.md) across 9 benchmarks . Scores are QA Accuracy (%).\nBenchmarks are grouped by our Cognitive Hierarchy.\n\n[Leaderboard](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/samples/leaderboard.jpg)\n\nWe invite the community to benchmark new models using our suite. Please to add your model's results!\n\n### 🧑‍🔬 How to Evaluate Your Model\n\n1. **Selected Benchmarks for the Leaderboard**  \n   We collect existing spatial benchmarks used in the literature and standardize their usage for evaluation in the hugging face repo [Hugging Face](https://huggingface.co/datasets/LLDDSS/Awesome_Spatial_VQA_Benchmarks) .  \n   The table below summarizes the key datasets used to benchmark spatial VLMs on our leaderboard.\n   \n   |Dataset Name |Description |Link |\n   | --- | --- | --- |\n   |EgoOrientBench |Egocentric spatial understanding benchmark |[Hugging Face Link Link](https://huggingface.co/datasets/LLDDSS/Awesome_Spatial_VQA_Benchmarks) |\n   |GeoMeter(real) |A depth-aware spatial reasoning benchmark |"
      ]
    },
    {
      "url": "https://spatial-vlm.github.io/",
      "title": "Spatial VLM: Endowing Vision-Language Models with Spatial ...",
      "publish_date": null,
      "excerpts": [
        "its ability on both qualitative and quantitative spatial VQA.\nFinally, we demonstrate that this VLM unlocks novel downstream\napplications in chain-of-thought spatial reasoning and robotics\ndue to its quantitative estimation capability.\n\n## Limitations of multimodal LLMs\n\nHumans can perform spatial reasoning while VLMs doesn't.\n\n**Motivation:** Humans effortlessly determine spatial\nrelationships, such as the positioning of objects relative to\neach other or estimating distances and sizes. This natural\nproficiency in direct spatial reasoning tasks contrasts with the\ncurrent limitations of VLMs. Can we imbue VLMs with spatial\nreasoning abilities akin to those of humans?\n\n**Key insight:** We hypothesize that the limited the spatial\nreasoning abilities of current VLMs is not due to a fundamental\nlimitation of their architecture, but rather is a limitation in\ncommon datasets available at scale on which such models are\ntrained. We co-train a multimodal large language model on\n\n...\n\nDue to its ability to intuitively reason about space\nquantiatively in real-world units, SpatialVLM can be used as a\nfine-grained reward-annotator for robotics tasks. In the figure\nbelow, SpatialVLM correctly assigns a monotonically decreasing\ndistance estimation for an robot hand approaching a coke can,\nwhich can be used as a reward signal for reinforcement learning.\n\nComparison with baselines.\n\nIn the figure below, we show SpatialVLM can be prompted to\nannotate dense rewards for open-vocabulary robotic tasks, unlike\nmany prior methods that can only annotate a binary label of\nsuccess or failure.\n\nreward heatmap.\n\n## Code (3rd Party Community Implementation)\n\nAfter releasing this paper, we were greeted with enthusiasm by the VLM research community. A shout-out to a user named remyxai for providing an open-source implementation of the data synthesis pipeline that closely follows our method. Check it out at: <https://github.com/remyxai/VQASynth>\n\n[Comparison with baselines."
      ]
    },
    {
      "url": "https://www.deepnlp.org/content/articles/spatialvlm%3A-endowing-vision-language-models-with-spatial-reasoning-capabilities",
      "title": "SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities",
      "publish_date": null,
      "excerpts": [
        "Vision Language Models (VLMs) have shown impressive performance in some VQA benchmarks but struggle with 3D spatial reasoning such as recognizing distances or size differences between physical objects."
      ]
    },
    {
      "url": "https://www.alphaxiv.org/abs/2512.16561",
      "title": "N3D-VLM: Native 3D Grounding Enables Accurate Spatial Reasoning in Vision-Language Models | alphaXiv",
      "publish_date": "2025-12-18",
      "excerpts": [
        "... Spa- tialReasoner [21] enhances spatial understanding by esti- mating object position and orientation. However, it oper- ates in constrained scenarios, does not capture object size, and demonstrates ...  and positions, supporting both 3D detectio"
      ]
    },
    {
      "url": "https://xdimlab.github.io/Orientation_Matters/",
      "title": "Orientation Matters: Making 3D Generative Models Orientation-Aligned",
      "publish_date": null,
      "excerpts": [
        "# Orientation Matters: Making 3D Generative Models Orientation-Aligned\n\n### NeurIPS 2025\n\n[Yichong Lu](https://yichonglu.github.io) 1,2\\* , Yuzhuo Tian 1\\* , Zijin Jiang 1\\* , Yikun Zhao ¹ , Yuanbo Yang 1,2 , [Hao Ouyang](https://ken-ouyang.github.io/) ² , [Haoji Hu](https://scholar.google.com/citations?user=kFnuXyAAAAAJ&hl=zh-TW) ¹ , Huimin Yu ¹ , [Yujun Shen](https://shenyujun.github.io/) ² [Yiyi Liao](https://yiyiliao.github.io) ¹\n\n¹ Zhejiang University, ² Ant Group\n\n[Paper](https://drive.google.com/file/d/1kVpaZPBYNnlf9u5KCcxa4pRvuEpa8TIk/view?usp=drive_link) [arXiv](https://arxiv.org/abs/2506.08640) [Video](https://youtu.be/_g3krVsVXs4) [Code](https://github.com/YichongLu/Orientation_Matters) [Hugging Face logo Dataset](https://huggingface.co/datasets/Louischong/Objaverse-OA) [Hugging Face logo Demo](https://huggingface.co/spaces/Louischong/Trellis-OA)\n\n## Overview\n\nTeaser image demonstrating Marigold depth estimation.\n\n...\n\nenabled by our aligned object generation, including **zero-shot model-free object\norientation estimation** via analysis-by-synthesis and **efficient arrow-based object\nmanipulation** .\n\n## Dataset Curation\n\nTeaser image demonstrating Marigold depth estimation.\n\nWe employ VLM pre-processing and manual correction to curate our Objaverse-OA dataset, striking a balance between efficiency and accuracy. We show the error rate of VLM’s estimation across different categories above. We\nobserve that (1) the VLM demonstrates particular difficulty in recognizing front-facing\norientations for stick-like objects, and (2) a significant portion of recognition errors occur when\nprocessing objects with inherently ambiguous or unclear frontal views. These challenges highlight the necessity\nof our manual curation.\n\n## Orientation-Aligned 3D Generation  \nBased on Two Representative Frameworks\n\n  \n### Pipeline\n\nTeaser image demonstrating Marigold depth estimation."
      ]
    },
    {
      "url": "https://www.alphaxiv.org/abs/2509.25390",
      "title": "SpinBench: Perspective and Rotation as a Lens on Spatial Reasoning in VLMs | alphaXiv",
      "publish_date": "2026-02-28",
      "excerpts": [
        "* **Multi-View Cars:** To test reasoning in more structured, real-world categories, the benchmark uses sequences of vehicles sampled at 4 5 ∘ intervals.\n* **Stereo Faces:** Human faces are naturally asymmetrical and have clear \"front\" and \"side\" orientations. This makes them ideal for testing egocentric (viewer-centered) versus allocentric (object-centered) perspectives.\n\nA key methodological contribution of SPINBENCH is the use of \"premise-based\" tasks. In some perspective-taking experiments, the spatial relationship is explicitly stated in the text prompt (e.g., \"The cup is to the left of the plate. If you move to the opposite side, where is the cup?\"). This setup is designed to decouple visual grounding from spatial inference. If a model fails here, the error lies in its geometric logic rather than its ability to \"see\" the objects in the image.\n\n## Findings: The Reality of VLM Spatial Reasoning\nThe evaluation of 43 different models—ranging from smaller open-source versions to large proprietary systems like GPT-5—revealed significant gaps in current AI capabilities. While some models showed strong performance in basic tasks, their reasoning often faltered as the complexity increased.\n\nOne of the most prominent findings was the **egocentric bias** . Models were much more likely to correctly identify rotations or positions from the viewer's perspective than from the object's perspective. For example, if a face rotated \"to its own left,\" many models would mistakenly identify the rotation based on how it appeared to the viewer. This indicates that VLMs may lack a robust internal representation of object-centric coordinates.\n\nAnother major observation was the **lack of consistency** . Many models were easily confused by syntactic changes. If a model correctly identified that \"A is left of B,\" it might fail to agree that \"B is right of A\" when the question was rephrased."
      ]
    }
  ],
  "warnings": null,
  "usage": [
    {
      "name": "sku_search",
      "count": 1
    }
  ],
  "session_id": "ses_fd81e747fffey16zO59Xh0VoM8"
}
```

**Tool: websearch**

**Input:**
```json
{
  "numResults": 6,
  "query": "reddit r/MachineLearning vision language models spatial reasoning benchmark discussion 2025 2026"
}
```

**Output:**
```
{
  "search_id": "search_339534842d3adf1b77f86ecf883cf99a",
  "results": [
    {
      "url": "https://aclanthology.org/2025.findings-naacl.204",
      "title": "NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models - ACL Anthology",
      "publish_date": "2025-04-01",
      "excerpts": [
        "[NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models](https://aclanthology.org/2025.findings-naacl.204/) . In _Findings of the Association for Computational Linguistics: NAACL 2025_ , pages 3680–3708, Albuquerque, New Mexico. Association for Computational Linguistics.\nCite (Informal):\n    [NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models](https://aclanthology.org/2025.findings-naacl.204/) (Pandya et al., Findings 2025)\nCopy Citation:\n    BibTeX Markdown MODS XML Endnote More\noptions…\nPDF:\n    <https://aclanthology.org/2025.findings-naacl.204.pdf>\n\n[PDF](https://aclanthology.org/2025.findings-naacl.204.pdf \"Open PDF of 'NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models'\") Cite [Search](https://www.semanticscholar.org/search?+q=NTSEBENCH%3A+Cognitive+Reasoning+Benchmark+for+Vision+Language+Models \"Search for 'NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models' on Semantic Scholar\") Fix data\n\n* * *\n\n...\n\n204/) (Pandya et al., Findings 2025)\n\n##### ACL\n\n* Pranshu Pandya, Vatsal Gupta, Agney S Talwarr, Tushar Kataria, Dan Roth, and Vivek Gupta. 2025. [NTSEBENCH: Cognitive Reasoning Benchmark for Vision Language Models](https://aclanthology.org/2025.findings-naacl.204/) . In _Findings of the Association for Computational Linguistics: NAACL 2025_ , pages 3680–3708, Albuquerque, New Mexico. Association for Computational Linguistics.\n\nCopy Markdown to\nClipboard Copy ACL to\nClipboard\n\nThe ACL Anthology is managed and built by the ACL Anthology team of volunteers.\n\n_Site last built on 21 August 2026 at 03:17 UTC with [commit 1522185](https://github.com/acl-org/acl-anthology/tree/1522185a6ad81090e9b62c74679259c945a16eb7) ._"
      ]
    },
    {
      "url": "https://arxiv.org/abs/2602.03916",
      "title": "[2602.03916] SpatiaLab: Can Vision-Language Models Perform Spatial Reasoning in the Wild?",
      "publish_date": "2026-02-03",
      "excerpts": [
        "[](https://arxiv.org/IgnoreMe) [archive](https://arxiv.org/)\n\n[Search](https://arxiv.org/search) [Submit](https://arxiv.org/user/create) [Donate](https://info.arxiv.org/about/donate.html) \n\n# Computer Science > Computer Vision and Pattern Recognition\n\n**arXiv:2602.03916** (cs)\n\n[Submitted on 3 Feb 2026 ( [v1](https://arxiv.org/abs/2602.03916v1) ), last revised 10 May 2026 (this version, v3)]\n\n# Title: SpatiaLab: Can Vision-Language Models Perform Spatial Reasoning in the Wild?\n\nAuthors: [Azmine Toushik Wasi](https://arxiv.org/search/cs?searchtype=author&query=Wasi,+A+T) , [Wahid Faisal](https://arxiv.org/search/cs?searchtype=author&query=Faisal,+W) , [Abdur Rahman](https://arxiv.org/search/cs?searchtype=author&query=Rahman,+A) , [Mahfuz Ahmed Anik](https://arxiv.org/search/cs?searchtype=author&query=Anik,+M+A) , [Munem Shahriar](https://arxiv.org/search/cs?searchtype=author&query=Shahriar,+M) , [Mohsin Mahmud Topu](https://arxiv.org/search/cs?\n\n...\n\n|Comments: |Accepted to ICLR 2026 ( [this https URL](https://openreview.net/forum?id=fWWUPOb0CT) ). 92 Pages. 42 Figures and 29 Tables |\n| --- | --- |\n|Subjects: |Computer Vision and Pattern Recognition (cs.CV) ; Computational Engineering, Finance, and Science (cs.CE); Computation and Language (cs.CL); Machine Learning (cs.LG) |\n|Cite as: |[arXiv:2602.03916](https://arxiv.org/abs/2602.03916) [cs.CV] |\n| |(or [arXiv:2602.03916v3](https://arxiv.org/abs/2602.03916v3) [cs.CV] for this version) |\n| |<https://doi.org/10.48550/arXiv.2602.03916>\n\nFocus to learn more\n\narXiv-issued DOI via DataCite |\n|Journal reference: |ICLR 2026 |\n\n## Submission history\n\nFrom: Azmine Toushik Wasi  [view email ]  \n**[[v1]](/abs/2602.03916v1)** Tue, 3 Feb 2026 17:52:02 UTC (5,336 KB)  \n**[[v2]](/abs/2602.03916v2)** Fri, 27 Feb 2026 09:56:46 UTC (5,336 KB)  \n**[v3]** Sun, 10 May 2026 15:38:24 UTC (5,319 KB)\n\nFull-text links:\n\n## Access Paper:\n\n* View PDF\n* [HTML (experimental)](https://arxiv.org/html/2602.\n\n...\n\nrequTask=upload&url=https://arxiv.org/abs/2602.03916&description=SpatiaLab: Can Vision-Language Models Perform Spatial Reasoning in the Wild? \"Bookmark on BibSonomy\") [Reddit](https://reddit.com/submit?url=https://arxiv.org/abs/2602.03916&title=SpatiaLab: Can Vision-Language Models Perform Spatial Reasoning in the Wild? \"Bookmark on Reddit\")\n\nBibliographic Tools\n\n# Bibliographic and Citation Tools\n\nBibliographic Explorer Toggle\n\nBibliographic Explorer _( [What is the Explorer?](https://info.arxiv.org/labs/showcase.html) )_\n\nConnected Papers Toggle\n\nConnected Papers _( [What is Connected Papers?](https://www.connectedpapers.com/about) )_\n\nLitmaps Toggle\n\nLitmaps _( [What is Litmaps?](https://www.litmaps.co/) )_\n\nscite.ai Toggle\n\nscite Smart Citations _( [What are Smart Citations?](https://www.scite.ai/) )_\n\nCode, Data, Media\n\n# Code, Data and Media Associated with this Article\n\nalphaXiv Toggle\n\nalphaXiv _( [What is alphaXiv?](https://alphaxiv.org/) )_\n\nLinks to Code Toggle"
      ]
    },
    {
      "url": "https://openreview.net/forum?id=fWWUPOb0CT",
      "title": "SpatiaLab: Can Vision–Language Models Perform Spatial Reasoning in the Wild? | OpenReview",
      "publish_date": "2026-01-26",
      "excerpts": [
        "**OpenReview** .net\n\n**OpenReview** .net\n\n**OpenReview** .net\n\n[back arrow Go to **ICLR 2026 Conference** homepage](https://openreview.net/group?id=ICLR.cc/2026/Conference \"Venue Homepage\")\n\n## SpatiaLab: Can Vision–Language Models Perform Spatial Reasoning in the Wild?\n\n[Download PDF](https://openreview.net/pdf?id=fWWUPOb0CT \"Download PDF\")\n\n### [Azmine Toushik Wasi](https://openreview.net/profile?id=~Azmine_Toushik_Wasi1 \"~Azmine_Toushik_Wasi1\") , [Wahid Faisal](https://openreview.net/profile?id=~Wahid_Faisal1 \"~Wahid_Faisal1\") , [Abdur Rahman](https://openreview.net/profile?id=~Abdur_Rahman2 \"~Abdur_Rahman2\") , [Mahfuz Ahmed Anik](https://openreview.net/profile?id=~Mahfuz_Ahmed_Anik1 \"~Mahfuz_Ahmed_Anik1\") , [Munem Shahriar](https://openreview.net/profile?id=~Munem_Shahriar2 \"~Munem_Shahriar2\") , [Mohsin Mahmud Topu](https://openreview.net/profile?id=~Mohsin_Mahmud_Topu1 \"~Mohsin_Mahmud_Topu1\") , [Sadia Tasnim Meem](https://openreview.net/profile?\n\n...\n\n0](https://creativecommons.org/licenses/by/4.0/ \"Licensed under Creative Commons Attribution 4.0 International\")\n\n**Keywords:** Spatial reasoning, Vision–language models, Large languge models, Reasoning Models, LLM Evaluation, Spatial Understanding\n\n**TL;DR:** SpatiaLab presents a comprehensive benchmark for evaluating vision-language models' spatial reasoning capabilities across realistic, diverse scenarios, revealing significant gaps compared to human performance.\n\n**Abstract:** Spatial reasoning is a fundamental aspect of human cognition, yet it remains a major challenge for contemporary vision–language models (VLMs). Prior work largely relied on synthetic or LLM-generated environments with limited task designs and puzzle-like setups, failing to capture the real-world complexity, visual noise, and diverse spatial relationships that VLMs encounter."
      ]
    },
    {
      "url": "https://neurips.cc/virtual/2025/poster/121802",
      "title": "NeurIPS Poster SURDS: Benchmarking Spatial Understanding and Reasoning in Driving Scenarios with Vision Language Models",
      "publish_date": "2026-04-15",
      "excerpts": [
        "We benchmark leading general-purpose VLMs, including GPT, Gemini, and Qwen, revealing persistent limitations in fine-grained spatial understanding. To address these deficiencies, we go beyond static evaluation and explore whether alignment techniques can improve spatial reasoning performance."
      ]
    },
    {
      "url": "https://arxiv.org/html/2506.03135v3",
      "title": "OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models",
      "publish_date": null,
      "excerpts": [
        "delving into spatial reasoning for vision language models\") ) , we identified several limitations in existing benchmarks, such as reliance on generated images (Szymanska et al. , 2024 , Fu et al. , 2024b , Kamath et al. , [2023](https://arxiv.org/html/.bib572 \"What’s \\\"up\\\" with vision-language models? investigating their struggle with spatial reasoning\") , Liu et al. , 2023a , Rajabi and Kosecka, 2023 , Shiri et al. , 2024 ) , LLM-generated templates (Linghu et al. , 2024 , Du et al. , 2024 , Rädsch et al. , 2025 evaluation gaps with a framework for scalable and cost-effective benchmark generation\") ) , and domain-specific focus (Xie et al. , [2025](https://arxiv.org/html/.bib636 \"Are vlms ready for autonomous driving? an empirical study from the reliability, data, and metric perspectives\") , Chow et al. , 2025 , Danish et al. , 2024 ) . These issues hinder their comprehensiveness and real-world applicability.\nTo address these gaps, our study proposes a comprehensive and integrative spatial reasoning benchmark.\n\n### 5\\.2 Spatial Vision-Language Models\n\nSpatial vision-language models integrate computer vision (He et al. , 2022 , Oquab et al. , 2024 , Radford et al. , 2021 ) and natural language processing (Bai et al. , 2023 , Wang et al. , 2024c , Brown et al. , 2020 , Anil et al. , 2023 , Touvron et al. , 2023a ; b , Zhang et al. , 2024b ) to enhance machine understanding of spatial relationships and mental intelligence. Recent research (Qi et al. , 2024 , Chen et al. , 2024 , Cheng et al. , 2024 , Cai et al. , 2024 , Song et al. , 2024 , Yuan et al. , 2024 , Qi et al. , 2025 , Chen et al. , 2025b ) has increasingly focused on extending vision-language models to support spatial reasoning in dynamic and 3D environments. One of the pioneering works in this domain, SpatialVLM (Chen et al.\n\n...\n\nBirchfield (2024) RoboSpatial: teaching spatial understanding to 2d and 3d vision-language models for robotics . CoRR abs/2411.16537 . External Links: 2411\\.16537 Cited by: Table 1 , §1 , §5.1 , §5.2 .\n* I. Stogiannidis, S. McDonagh, and S. A. Tsaftaris (2025) Mind the gap: benchmarking spatial reasoning in vision-language models . CoRR abs/2503.19707 . External Links: 2503\\.19707 Cited by: §2.1 , §5.2 .\n* E. Szymanska, M. Dusmanu, J. Buurlage, M. Rad, and M. Pollefeys (2024) Space3D-bench: spatial 3d question answering benchmark . CoRR abs/2408.16662 . External Links: 2408\\.16662 Cited by: Table 1 , §1 , §2.1 , §5.1 , §5.1 .\n* Y. Tang, A. Qu, Z. Wang, D. Zhuang, Z. Wu, W. Ma, S. Wang, Y. Zheng, Z. Zhao, and J. Zhao (2024) Sparkle: mastering basic spatial capabilities in vision language models elicits generalization to composite spatial reasoning . CoRR abs/2410.16162 . External Links: 2410\\.16162 Cited by: §5.2 .\n* E. C. Tolman (1948) Cognitive maps in rats and men. ."
      ]
    },
    {
      "url": "https://papers.nips.cc/paper_files/paper/2025/file/d2f2ca2c305e1a9c29bf00a676f0a500-Paper-Conference.pdf",
      "title": "[PDF] Reinforcing Spatial Reasoning in Vision-Language Models with ...",
      "publish_date": null,
      "excerpts": [
        "Extensive experiments across five diverse spatial reasoning benchmarks demonstrate the effectiveness of VILASR, which achieves substantial improvements over"
      ]
    },
    {
      "url": "https://en.papernotes.org/CVPR2026/vlm_reasoning/spatialqa_a_benchmark_for_evaluating_spatial_logical_reasoning_in_vision-languag/",
      "title": "[Paper Note] SpatiaLQA: A Benchmark for Evaluating Spatial Logical Reasoning in Vision-Language Models",
      "publish_date": "2026-05-08",
      "excerpts": [
        "- AV-Reasoner: Improving and Benchmarking Clue-Grounded Audio-Visual Counting for MLLMs\n        - AXG-Reasoner: Error Detection and Explanation in Long Task Videos with Vision-Language Models\n        - Beyond 3D VQAs: Injecting 3D Spatial Priors into Vision-Language Models for Enhanced Geometric Reasoning\n        - Beyond Multiple Choice: Verifiable OpenQA for Robust Vision-Language RFT\n        - Beyond Perceptual Shortcuts: Causal-Inspired Debiasing Optimization for Generalizable Video Reasoning in Lightweight MLLMs\n        - Boosting Reasoning in Large Multimodal Models via Activation Replay\n        - BOP-Ask: Object-Interaction Reasoning for Vision-Language Models\n        - Breaking the Regional Perception Bottleneck of Multimodal Large Language Models via External Reasoning Framework\n        - Can a Second-View Image Be a Language? Geometric and Semantic Cross-Modal Reasoning for X-ray Prohibited Item Detection\n\n...\n\n- Generate, Analyze, and Refine: Training-Free Sound Source Localization via MLLM Meta-Reasoning\n        - Geoint-R1: Formalizing Multimodal Geometric Reasoning with Dynamic Auxiliary Constructions\n        - GGBench: A Geometric Generative Reasoning Benchmark for Unified Multimodal Models\n        - Graph-to-Frame RAG: Visual-Space Knowledge Fusion for Training-Free and Auditable Video Reasoning\n        - Grounded Chain-of-Thought for Multimodal Large Language Models\n        - GThinker: Towards General Multimodal Reasoning via Cue-Guided Rethinking\n        - HandVQA: Diagnosing and Improving Fine-Grained Spatial Reasoning about Hands in Vision-Language Models\n        - Hear you are: Teaching LLMs Spatial Reasoning with Vision and Spatial Sound\n        - Hierarchical Process Reward Models are Symbolic Vision Learners\n        - HoneyBee: Data Recipes for Vision-Language Reasoners\n        - Improving Vision-language Models with Perception-centric Process Reward Models\n\n...\n\n- Self-Critical Distillation Network for Video-based Commonsense Captioning\n        - SpaceTools: Tool-Augmented Spatial Reasoning via Double Interactive RL\n        - SpatiaLQA: A Benchmark for Evaluating Spatial Logical Reasoning in Vision-Language Models SpatiaLQA: A Benchmark for Evaluating Spatial Logical Reasoning in Vision-Language Models\n                  \n                  Table of contents\n                  \n            * TL;DR\n            * Background & Motivation\n            * Method\n            * Key Experimental Results\n            * Highlights & Insights\n            * Limitations & Future Work\n            * Related Work & Insights\n            * Rating\n            * Related Papers\n        - SpatialStack: Layered Geometry-Language Fusion for 3D VLM Spatial Reasoning\n        - Stable and Efficient Single-Rollout RL for Multimodal Reasoning\n        - StaR-KVQA: Structured Reasoning Traces for Implicit-Knowledge Visual Question Answering\n\n...\n\n* Related Papers\n\n[CVPR 2026][VLM Reasoning][Spatial Logical Reasoning] The SpatiaLQA benchmark is proposed (9,605 QA pairs, 241 real indoor scenes) to systematically evaluate 41 VLMs on spatial logical reasoning. A Recursive Scene Graph-Aided Reasoning (RSGAR) method is designed to enhance the spatial logical reasoning capabilities of VLMs.\n\nTags: CVPR 2026 · VLM Reasoning · Spatial Logical Reasoning · VLM Benchmark · Scene Graph · Indoor Scene Understanding · Multi-step Reasoning\n\nCVPR 2026 VLM Reasoning Spatial Logical Reasoning VLM Benchmark Scene Graph Indoor Scene Understanding Multi-step Reasoning\n\n# SpatiaLQA: A Benchmark for Evaluating Spatial Logical Reasoning in Vision-Language Models ¶\n\n**Conference** : CVPR 2026  \n**arXiv** : [2602\\.20901](https://arxiv.org/abs/2602.20901)  \n**Code** : <https://github.com/xieyc99/SpatiaLQA>  \n**Area** : Multimodal VLM  \n**Keywords** : Spatial Logical Reasoning, VLM Benchmark, Scene Graph, Indoor Scene Understanding, Multi-step Reasoning\n\n...\n\n* Value: ⭐⭐⭐⭐ The benchmark resources are of high value to the community; the method leaves significant room for further improvement.\n\n## Related Papers ¶\n\n* [[CVPR 2026] QUANTIPHY: A Quantitative Benchmark Evaluating Physical Reasoning Abilities of Vision-Language Models](../quantiphy_a_quantitative_benchmark_evaluating_physical_reasoning_abilities_of_vi/)\n* [[ICLR 2026] Spatial-DISE: A Unified Benchmark for Evaluating Spatial Reasoning in Vision-Language Models](../../../ICLR2026/vlm_reasoning/spatial-dise_a_unified_benchmark_for_evaluating_spatial_reasoning_in_vision-lang/)\n* [[ICLR 2026] OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models](../../../ICLR2026/vlm_reasoning/omnispatial_towards_comprehensive_spatial_reasoning_benchmark_for_vision_languag/)\n* [[CVPR 2026] Learning to Reason in 4D: Dynamic Spatial Understanding for Vision Language Models](../learning_to_reason_in_4d_dynamic_spatial_understanding_for_vision_language_model/)\n* [[CVPR 2026] Keep it SymPL: Symbolic Projective Layout for Allocentric Spatial Reasoning in Vision-Language Models](../keep_it_sympl_symbolic_projective_layout_for_allocentric_spatial_reasoning_in_vi/)\n\n✨ This site is machine-translated by AI for academic reference; please report any errors."
      ]
    },
    {
      "url": "https://openreview.net/forum?id=6nZKT2rL0H",
      "title": "OmniSpatial: Towards Comprehensive Spatial Reasoning ...",
      "publish_date": "2026-01-26",
      "excerpts": [
        "TL;DR: OmniSpatial is a large-scale comprehensive benchmark that reveals persistent gaps in VLMs’ spatial reasoning across dynamic, logical, interaction, and perspective-taking tasks, while PointGraph and SpatialCoT offer promising improvements."
      ]
    },
    {
      "url": "https://www.emergentmind.com/topics/vision-language-model-benchmarks",
      "title": "Vision–Language Model Benchmarks - emergentmind.com",
      "publish_date": null,
      "excerpts": [
        "Vision–Language Model Benchmarks\n\nPapers\n\nTopics\n\nAuthors\n\nRecent\n\nView all\n\nSearch\n\n2000 character limit reached\n\nChrome Extension\n\n[Install our Chrome Extension](https://chromewebstore.google.com/detail/emergent-mind-%E2%80%94-arxiv-int/hgmnadjffdiipehljmhagdgpaoiiklml) to automatically enhance arXiv.\n\nSponsor\n\nPromote your business to millions of monthly visitors.\n\n# Vision–Language Model Benchmarks\n\nUpdated 5 March 2026\n\n* Vision–language benchmarks are systematic evaluations that quantify multimodal reasoning and cross-modal generalization using structured tasks and precise metrics.\n* They employ diverse methodologies including parallel translation pipelines, modular item normalization, and taxonomic categorization to ensure rigorous testing.\n* Empirical findings reveal persistent performance gaps in spatial reasoning, low-resource languages, and long-context compositional tasks, guiding future innovations.\nVision–LLM benchmarks are systematic evaluations designed to assess the multimodal and [cross-modal reasoning](https://www.emergentmind.com/topics/cross-modal-reasoning-0b6528aa-3463-46ae-9399-d4fb8479c7a1) capabilities of large models operating over both images and language. Over the past several years, the rapid evolution of vision–LLMs ( [VLMs](https://www.emergentmind.com/topics/qwen3-vl-vision-language-models-vlms) ) has necessitated increasingly sophisticated, fine-grained, and scalable benchmarking protocols to rigorously measure task proficiency, generalization, multilinguality, and reasoning under diverse, often challenging, real-world conditions.\n\n## 1\\. Evolution and Taxonomy of Vision–Language Benchmarks\n\nBenchmark design has shifted from small-scale, single-modality or English-centered datasets to complex, multilingual, multi-domain, and multi-turn settings. Early benchmarks—such as VQAv2, [COCO](https://www.emergentmind.\n\n...\n\n* **Specialized domains** including geospatial (GEOBench-VLM ( Danish et al., 2024 )), top-down views (TDBench ( Hou et al., 1 Apr 2025 )), and spatial reasoning (SRBench ( Stogiannidis et al., 25 Mar 2025 ))\n* **Automated, LLM-driven alignment and scoring frameworks** ( [Auto-Bench](https://www.emergentmind.com/topics/auto-bench) ( Ji et al., 2023 )) for scalable, cost-effective, and consistent evaluation\n\nBenchmarks are often organized according to key axes: perception, knowledge, reasoning (single-step and multi-hop), linguistic robustness, multi-image fusion, bias and prior disentanglement, and the ability to correctly process different symbolizations of language (e.g., “text as pixels” in VISTA-Bench ( Liu et al., 4 Feb 2026 )).\n\n## 2\\. Core Benchmark Construction Methodologies\n\nThe methodology for constructing contemporary vision–language benchmarks involves several steps to ensure both the rigor and breadth of the evaluation:\n\n...\n\n, 4 Feb 2026 ) shows per-model drops of 2–31 points depending on rendering complexity, with reasoning tasks hit hardest.\n* **Long-context and multi-image limitations** : Models degrade significantly on extended context (MMLongBench: best SOTA ∼ 063%, open models ∼ 150%), and multi-image reasoning is bottlenecked by lack of cross-image relational pretraining (MIRB ( Zhao et al., 2024 ), VisChainBench ( Lyu et al., 7 Dec 2025 )).\n* **Fine-grained and low-resource challenges** : For extremely low-resource languages or fine-grained tasks, performance approaches random chance (MVL-SIB ( Schmidt et al., 18 Feb 2025 ): SOTA models ∼ 225% in cross-modal tasks for languages like N'Koo).\n* **Language prior and bias** : All evaluated [LVLMs](https://www.emergentmind.\n\n...\n\nRecommendations for future benchmarks and training include incorporating domain-adaptive pretraining, diversified low-resource language data, enriched exposure to multi-image and multi-turn reasoning, advances in unified (visual and symbolic) tokenization, and protocol extensions for open-ended, partial-credit, and culture-adaptive scoring.\n\n## 7\\. Impact and Open Challenges\n\nVision–language benchmarks have fundamentally redefined the boundaries of VLM evaluation, enabling nuanced cross-modal assessment and accelerating advances in model design, instruction-tuning, and modality-robust [representation learning](https://www.emergentmind.com/topics/representation-learning) . Notwithstanding, persistent deficits in spatial, reasoning, and multilingual generalization underscore the necessity of continued benchmark-driven development. Emerging domains—such as regulatory-aligned AI safety (e.g., multimodal disinformation with regulatory alignment in VLDBench ( Raza et al.\n, 17 Feb 2025 )) and fine-grained visual semantics (InsightVision ( Yin et al., 19 Feb 2025 ))—reflect the growing complexity and societal import of modern vision–language intelligence.\n\nAs of 2026, the landscape is characterized by scalable, extensible, and multifaceted benchmarks that jointly span technical rigor and real-world relevance. Systematic, multi-dimensional evaluation remains indispensable for the principled diagnosis and advancement of vision–LLMs.\n\n[Markdown](https://www.emergentmind.com/users/sign_up?redirect_to=https%3A%2F%2Fwww.emergentmind.com%2Farticles%2Fvision-language-model-benchmarks) [Report Issue](https://www.emergentmind.com/users/sign_up?redirect_to=https%3A%2F%2Fwww.emergentmind.com%2Farticles%2Fvision-language-model-benchmarks) [Upgrade to Chat](https://www.emergentmind.com/pricing?utm_source=chat-button)\n\nReferences (17)\n\n1\\.\n\nPISA-Bench: The PISA Index as a Multilingual and Multimodal Metric for the Evaluation of Vision-Language Models (2025)\n\n2\\.\nMVL-SIB: A Massively Multilingual Vision-Language Benchmark for Cross-Modal Topical Matching (2025)\n\n3\\.\n\nVLURes: Benchmarking VLM Visual and Linguistic Understanding in Low-Resource Languages (2025)\n\n4\\.\n\nMMLongBench: Benchmarking Long-Context Vision-Language Models Effectively and Thoroughly (2025)\n\n5\\.\n\nVisChainBench: A Benchmark for Multi-Turn, Multi-Image Visual Reasoning Beyond Language Priors (2025)\n\n6\\.\n\nBeyond Visual Understanding: Introducing PARROT-360V for Vision Language Model Benchmarking (2024)\n\n7\\.\n\nGEOBench-VLM: Benchmarking Vision-Language Models for Geospatial Tasks (2024)\n\n8\\.\n\nTDBench: Benchmarking Vision-Language Models in Understanding Top-Down Images (2025)\n\n9\\.\n\nMind the Gap: Benchmarking Spatial Reasoning in Vision-Language Models (2025)\n\n10\\.\n\nLarge Language Models as Automated Aligners for benchmarking Vision-Language Models (2023)\n\n11\\.\n\nVISTA-Bench: Do Vision-Language Models Really Understand Visualized Text as Well as Pure Text? (2026)\n\n12\\.\nInsightVision: A Comprehensive, Multi-Level Chinese-based Benchmark for Evaluating Implicit Visual Semantics in Large Vision Language Models (2025)\n\n13\\.\n\nVLRMBench: A Comprehensive and Challenging Benchmark for Vision-Language Reward Models (2025)\n\n14\\.\n\nBenchmarking Multi-Image Understanding in Vision and Language Models: Perception, Knowledge, Reasoning, and Multi-Hop Reasoning (2024)\n\n15\\.\n\nVLind-Bench: Measuring Language Priors in Large Vision-Language Models (2024)\n\n16\\.\n\nMultilingual Vision-Language Models, A Survey (2025)\n\n17\\.\n\nVLDBench Evaluating Multimodal Disinformation with Regulatory Alignment (2025)\n\n### Topic to Video (Beta)\n\nNo one has generated a video about this topic yet.\n\nSign Up to Generate All Videos [Subscribe on YouTube](https://www.youtube.com/@EmergentMindAI?sub_confirmation=1)\n\n### Whiteboard\n\nNo one has generated a whiteboard explanation for this topic yet.\n\nSign Up to Generate\n\n### Follow Topic\nGet notified by email when new papers are published related to **Vision–Language Model Benchmarks** .\n\n[Sign Up to Follow Topic by Email](https://www.emergentmind.com/users/sign_up?redirect_to=%2Ftopics%2Fvision-language-model-benchmarks)\n\n### Continue Learning\n\n1. What methodological advancements have driven the evolution of vision–language benchmarks?\n2. How do recent benchmarks address multilinguality and cultural nuances in evaluation?\n3. In what ways are automated LLM-driven scoring frameworks enhancing benchmark scalability?\n4. How do task-specific error metrics inform improvements in multimodal model design?\n5. Find recent papers about multilingual and cultural evaluation in vision–language models.\n\n### Related Topics\n\n1. Vision-Centric Benchmarks\n2. Massive Multilingual Multimodal Benchmark\n3. Contrastive VLM Benchmark Overview\n4. Multilingual LLM Evaluation\n5. Visual Reasoning Benchmarks\n6. Multilingual Benchmarks Overview\n7. Vision-Language Models\n8.\nTemporal Benchmarks for Vision-Language Models\n9. VISTA-Bench: Multimodal Evaluation Suite\n10. Multimodal Reasoning Benchmarks\n\nContent\n\nOverview References Topic to Video Whiteboard Follow Topic Continue Learning Related Topics\n\nStay informed about trending AI papers:"
      ]
    },
    {
      "url": "https://iclr.cc/virtual/2026/poster/10011350",
      "title": "ICLR Poster OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models",
      "publish_date": "2026-04-17",
      "excerpts": [
        "# OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models\n\nMengdi Jia ⋅ Zekun Qi ⋅ Shaochen Zhang ⋅ Wenyao Zhang ⋅ XinQiang Yu ⋅ Jiawei He ⋅ He Wang ⋅ Li Yi\n\n### Abstract\n\nSpatial reasoning is a key aspect of cognitive psychology and remains a bottleneck for current vision-language models (VLMs). While extensive research has aimed to evaluate or improve VLMs' understanding of basic spatial relations, such as distinguishing left from right, near from far, and object counting, these tasks cover only the most elementary layer of spatial reasoning and are largely approaching saturation in the latest reasoning models. In this work, we introduce OmniSpatial, a comprehensive and challenging benchmark for spatial reasoning, grounded in cognitive psychology. OmniSpatial covers four major categories: dynamic reasoning, complex spatial logic, spatial interaction, and perspective-taking, with 50 fine-grained subcategories."
      ]
    }
  ],
  "warnings": null,
  "usage": [
    {
      "name": "sku_search",
      "count": 1
    }
  ],
  "session_id": "ses_fd81e747fffey16zO59Xh0VoM8"
}
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 10.2s)

_Thinking:_

Let me try to fetch actual Reddit discussions — search Reddit directly for spatial reasoning VLM discussions. One more search targeting reddit threads specifically.

**Tool: websearch**

**Input:**
```json
{
  "numResults": 6,
  "query": "reddit.com/r/MachineLearning OR r/LocalLLaMA \"spatial reasoning\" VLM \"left and right\" OR orientation OR \"facing\" thread comments"
}
```

**Output:**
```
{
  "search_id": "search_db00403cae4f5a12f92ff1dbc51ffe60",
  "results": [
    {
      "url": "https://huggingface.co/blog/KBayoud/spatial-reasoning-in-vlms",
      "title": "Seeing Isn’t Understanding: The Spatial Reasoning Gap in Vision-Language Models",
      "publish_date": "2025-07-13",
      "excerpts": [
        "* **Projective** : Describes direction, such as above/below, in front/behind, or left/right.\n* **Metric** : Involves size or distance, like how big something is or how far apart two objects are.\n\nIn fields like digital mapping (e.g., GPS or GIS systems), computers need to understand these relationships to answer questions like “What’s near me?” or “What’s inside this region?”\n\n##  Mental Rotation\n\nMental rotation is the ability to imagine how an object would look if turned or viewed from a different angle. Humans do this naturally — for example, we can look at a chair from the front and picture what it would look like from the side.\n\nFor vision-language models, this is much harder. Even if a model recognizes an object, it may struggle to identify the same object when it’s rotated or viewed from a new perspective.\n\nMental rotation requires models not just to recognize objects, but to mentally transform how they appear in space.\n\n...\n\nSpatial orientation helps us find our way in complex environments — like knowing where we are in a room, how to get to the door, or what’s behind us. Our brains combine visual, bodily, and auditory information to build a mental map of surroundings.\n\nTwo main frames of reference organize this spatial information:\n\n* **Egocentric** : Based on our own body — e.g., “the chair is on my right.”\n* **Allocentric** : Based on landmarks — e.g., “the chair is next to the window,” regardless of where you stand.  \n  This flexibility lets us move through spaces, remember routes, and adapt when environments change.\n\nFor vision-language models, understanding spatial orientation means recognizing where things are — not just in an image, but relative to each other and to the viewer. This is essential for following navigation instructions in real-world settings, interacting with 3D environments or augmented reality, etc.\n\n##  A Comparative Evaluation of Spatial Skills in VLMs\n\n...\n\n* **Misplaced visual focus** : It’s not just about attention quantity but also its location — the model sometimes focuses too little on the right objects or too much on irrelevant ones, causing spatial errors.\n\n[image/png](https://cdn-uploads.huggingface.co/production/uploads/645a5c08c266796265b8fd12/sPS2LB3sYlqwGGP-Msekw.png)\n\n* **Training Data Bias & Overreliance on unimodal priors** : Models like **[Llava](https://huggingface.co/llava-hf/llava-1.5-7b-hf)** tend to be more confident when predicting common relationships like “left” or “right,” but struggle with less frequent ones such as “under” or “behind.” This bias leads them to perform well on these common relationships and to guess based on familiar language patterns rather than actual visual evidence for the underrepresented ones, resulting in hallucinations in spatial relationships.\n\n[image/png](https://cdn-uploads.huggingface.co/production/uploads/645a5c08c266796265b8fd12/U1O1EA0TRggPIBlbpeyep.png)\n\n...\n\nRyukiRi Jul 27, 2025\n\nNice blog! Thanks!\n\nReply\n\nEdit Preview\n\nUpload images, audio, and videos by dragging in the text input, pasting, or clicking here .\n\nTap or paste here to upload images\n\nComment\n\n·  or  to comment\n\n[Upvote 12](https://huggingface.co/login?next=%2Fblog%2FKBayoud%2Fspatial-reasoning-in-vlms)\n\n* \n* \n* \n* \n* \n* \n* \n* \n* \n* \n* \n* \n*\n\n## Models mentioned in this article 1\n\n#### llava-hf/llava-1.5-7b-hf Image-Text-to-Text • 7B • Updated Jun 6, 2025 • 2\\.81M • 370\n\n## Datasets mentioned in this article 1\n\n#### juletxara/visual-spatial-reasoning Updated Sep 11, 2024 • 188 • 18\n\nSystem theme\n\nCompany\n\nTOS Privacy About [Careers](https://apply.workable.com/huggingface/) \n\nWebsite\n\nModels Datasets Spaces Pricing Docs"
      ]
    },
    {
      "url": "https://cvpr.thecvf.com/virtual/2024/poster/31284",
      "title": "CVPR Poster SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities",
      "publish_date": "2026-04-16",
      "excerpts": [
        "* Select Year: (2024)\n  \n    + 2026\n        \n    * * *\n    + 2025\n        \n    * * *\n    + 2024\n        \n    * * *\n    + 2023\n* Home\n* Schedule\n* Workshops\n* Tutorials\n* Keynotes\n* Awards\n* Papers\n* Sponsors\n* Organizers\n* \n\n  \n  \nPoster\n\n# SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities\n\nBoyuan Chen ⋅ Zhuo Xu ⋅ Sean Kirmani ⋅ brian ichter ⋅ Dorsa Sadigh ⋅ Leonidas Guibas ⋅ Fei Xia\n\n2024 Poster\n\n[Project Page](https://spatial-vlm.github.io/) [Paper PDF](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_SpatialVLM_Endowing_Vision-Language_Models_with_Spatial_Reasoning_Capabilities_CVPR_2024_paper.html) [ [Poster](https://cvpr.thecvf.com/media/PosterPDFs/CVPR%202024/31284.png?t=1716953434.450158 \"Poster\") ] [ [Paper PDF](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_SpatialVLM_Endowing_Vision-Language_Models_with_Spatial_Reasoning_Capabilities_CVPR_2024_paper.html \"Paper PDF\") ]\n\n### Abstract\n\n...\n\nBy co-training a VLM with this dataset, we significantly improve its performance in both qualitative and quantitative spatial VQA. Additionally, this enhanced VLM enables new applications in chain-of-thought spatial reasoning and robotics, particularly in quantitative estimation.\n\nChat is not available.\n\nSuccessful Page Load\n\n  \n### Contact Us\n\n[CVPR Help Desk](https://support.conferences.computer.org/cvpr/help-desk)\n\nPlease contact us with questions\nabout the following topics:\n\nAuthor - Paper Submission,\nAuthor - Open Review Issues,\nAuthor - Camera-Ready Paper,\nRegistration - General,\nRegistration - Cancellation,\nChildcare/Guests,\nExpo/Guests,\nLodging,\nVisa Letter,\nReviewer - Open Review Issues,\nReviewer - General Issues,\nArea Chair Issues,\n\n[Website and Invitation Letter Help](https://cvpr.thecvf.com/Help/Contact?select=website)\n\nUse the website help link for issues including login, inactive accounts, invitation letters\npapers not associated with a registration.\n\n###### Useful links"
      ]
    },
    {
      "url": "https://arxiv.org/html/2506.21656v1",
      "title": "Fine-Grained Preference OptimizationImproves Spatial Reasoning in VLMs",
      "publish_date": null,
      "excerpts": [
        "Recent advances in Chain-of-Thought (CoT) prompting have introduced step-by-step reasoning [ [70](https://arxiv.org/html/2506.21656v1.bib70) ] , but standard CoT traces are often too brief or abstract to capture fine-grained spatial logic.\nIn contrast, Long Chain-of-Thought (LongCoT) prompting produces richer, more interpretable reasoning paths that better support comprehension [ [71](https://arxiv.org/html/2506.21656v1.bib71) , [43](https://arxiv.org/html/2506.21656v1.bib43) , [9](https://arxiv.org/html/2506.21656v1.bib9) ] .\nStill, such prompting must go beyond simple depth estimation, as accurate spatial reasoning requires understanding occlusions, relative orientations, and positional ambiguity, all of which are difficult to capture without structured, fine-grained supervision.\n\nTo address these challenges, we introduce Spatial Reasoner-R1 , a novel VLM designed to perform spatial reasoning directly from 2D images.\n\n...\n\n21656v1 \"Appendix A Related Work ‣ 4.4 Ablations ‣ 4.3 Qualitative Examples ‣ 4.2 Experimental Results ‣ 4.1 Experimental Setup ‣ 4 Experiments ‣ Fine-Grained Preference OptimizationImproves Spatial Reasoning in VLMs\") .\n\n## 3 Method\n\nRefer to caption Figure 1 : Method Overview including SpatialReasoner-R1 model architecture (left) and training pipeline (right). SpatialReasoner-R1 is a VLM that takes as input a text instruction, visual prompts, and an image, and generates LongCoT reasoning responses. To train SpatialReasoner-R1, we (1) generate reasoning paths using M3CTS, (2) construct fine-grained preference pairs via reward-based selection, and (3) train with fine-grained DPO (fDPO) to optimize descriptive and logical reasoning separately.\n\n### 3\\.1 Spatial Reasoning from Images\n\nSpatial reasoning is a core vision-language challenge, requiring models to understand visual layouts and perform logical inference over spatial relationships.\n\n...\n\nEach candidate $s_{k,t}\\in\\mathcal{S}_{\\text{c}}$ generated during expansion is evaluated based on three distinct criteria: (i) visual description accuracy against the original image, (ii) spatial correctness of inferred spatial relationships utilizing both original and depth-derived images, and (iii) logical coherence of the textual reasoning steps.\nThe evaluation score $R(s_{k,t})$ is computed as:\n\n|$R(s_{k,t})=\\frac{1}{M}\\sum_{m=1}^{M}\\left[\\mathbb{I}^{(m)}_{\\text{visual}}(s_{%\nk,t})+\\mathbb{I}^{(m)}_{\\text{spatial}}(s_{k,t})+\\mathbb{I}^{(m)}_{\\text{%\nlogical}}(s_{k,t})\\right],$ |(7) |\n| --- | --- |\n\nwhere $M$ is the number of evaluation models, and each $\\mathbb{I}^{(m)}_{\\text{eval}}(s_{k,t})$ indicator function defined as:\n\n|$\\mathbb{I}^{(m)}_{\\text{eval}}(s_{k,t})=\\{+1\\ (\\text{fully accurate}),\\ 0\\ (%\n\\text{neutral}),\\ -1\\ (\\text{inaccurate})\\}.$ |(8) |\n| --- | --- |\n\nWe preserve high-quality paths by pruning the candidate set according to the evaluation score, i.e.\n\n...\n\n\\text{c}}^{*}}N(s_{c})R(s_{c})}{N(s_{k,t})+\\sum_{s_{c}\\in\\mathcal{S}_{\\text{c}%\n}^{*}}N(s_{c})},\\qquad N(s_{k,t})\\leftarrow N(s_{k,t})+\\sum_{s_{c}\\in\\mathcal{%\nS}_{\\text{c}}^{*}}N(s_{c}).$ |(9) |\n| --- | --- |\n\nSelect. This phase is responsible for choosing the most promising candidate state for further exploration in the next iteration of tree expansion. We use the Upper Confidence Bound (UCB) strategy to select the next state $s_{k^{\\prime},t+1}^{\\star}$ to traverse, based on updated values and visitation statistics. UCB ensures that high-value paths are prioritized, while also exploring less-visited nodes to discover new reasoning trajectories. The candidate selected maximizes the UCB objective, i.e. ,\n\n|$s_{k^{\\prime},t+1}^{\\star}\\;=\\;\\operatorname*{arg\\,max}_{s_{c}\\in\\mathcal{S}_{%\n\\text{c}}^{*}}\\left[V(s_{c})\\;+\\;\\alpha\\,\\sqrt{\\frac{\\log N(s_{k,t})}{1+N(s_{c%\n})}}\\right],$ |(10) |\n| --- | --- |\n\n...\n\nSpatial Reasoner-R1 VLMs. We also include SpatialReasoner-R1 4B and 8B variants with different training strategies such as SpatialReasoner-R1 SFT, SpatialReasoner-R1 DPO, trained with standard DPO, and SpatialReasoner-R1 fDPO trained with the proposed fine-grained DPO method.\n\nTable 1 : Spatial Reasoning Success Rates ( $\\uparrow$ ) on SpatialRGPT-Bench . Classification (top) and numeric distance/direction (bottom). are General Large VLMs, are Customized VLMs, are Spatial Reasoner-R1 variants. “/” indicates that the model refuses to provide a response for that metric.\n\n{NiceTabular} l c c c c c c c[colortbl-like] Below / Above Left / Right Big / Small Tall / Short Wide / Thin Behind / Front Qual Acc Gemini 2.0 Flash [ [20](https://arxiv.org/html/2506.21656v1.bib20) ] 58\\.33 68.57 16.98 50.00 15.38 53.63 44.29  \nLlama 4 Maverick [ [47](https://arxiv.org/html/2506.21656v1.bib47) ] 54\\.17 61.90 33.02 50.89 25.96 55.45 47.18  \nGemini 1.5 Pro [ [62](https://arxiv.org/html/2506.21656v1.\n\n...\n\n2 Experimental Results ‣ 4.1 Experimental Setup ‣ 4 Experiments ‣ Fine-Grained Preference OptimizationImproves Spatial Reasoning in VLMs\") provides qualitative examples that demonstrate SpatialReasoner-R1’s advanced capability for coherent, multi-step spatial reasoning. Spatial Reasoner-R1 first estimates the fireplace and TV-stand widths at 1.2m and 1.4m, then computes $\\frac{1.2}{2}+0.2\\,\\text{(gap)}+\\frac{1.4}{2}=1.5\\text{m}$ ,\na value that nearly matches the reference while transparently tying each term to an observed feature.\nIn contrast, InternVL2.5-78B adopts similar width guesses (1.2m, 1.5m) but assumes “the distance between the fireplace and the TV stand seems to be about the width of one object”. This assumption is inconsistent with what is shown in the image. Gemini 1.5 Pro aligns the fireplace’s right edge with the TV’s left edge, assigns both objects a 1m width, and combines only half a fireplace width (0.5m) with one quarter of the stand width (0.25m)."
      ]
    },
    {
      "url": "https://arxiv.org/html/2509.06266v1",
      "title": "Spatial Reasoning with Vision-Language Models in Ego-Centric Multi-View Scenes",
      "publish_date": null,
      "excerpts": [
        "Our results reveal a notable performance gap between human level scores and VLM performance, highlighting that current VLMs still fall short of human level spatial understanding. To bridge this gap, we propose Ego3D-VLM, a post-training framework that enhances 3D spatial reasoning of VLMs."
      ]
    },
    {
      "url": "https://www.reddit.com/r/LocalLLaMA/comments/1apdbcw/an_experiment_to_reproduce_spatialvlm/",
      "title": "An Experiment to Reproduce SpatialVLM - Synthesizing ... - Reddit",
      "publish_date": null,
      "excerpts": [
        "Inspired by their work, I made a notebook to analyze an image and help evaluate the spatial relationships between objects in the scene. In this experiment, I found ZoeDepth and LLaVA 1.6 helpful for estimating depth and generating image captions."
      ]
    },
    {
      "url": "https://spatial-vlm.github.io/",
      "title": "Spatial VLM: Endowing Vision-Language Models with Spatial ...",
      "publish_date": null,
      "excerpts": [
        "# Spatial VLM: Endowing Vision-Language Models with Spatial\nReasoning Capabilities\n\n[Boyuan Chen](https://boyuan.space/) 1,2,\\*,† , [Zhuo Xu](https://drzhuoxu.github.io/) 1,\\* , [Sean Kirmani](https://kirmani.ai/) ¹ , [Brian Ichter](https://brianichter.com/) ¹ , [Danny Driess](https://dannydriess.github.io/) ¹ , [Pete Florence](https://www.peteflorence.com/) ¹ , [Dorsa Sadigh](https://dorsa.fyi/) 1,3 , [Leonidas Guibas](https://geometry.stanford.edu/member/guibas/) 1,3 , [Fei Xia](https://fxia22.github.io/) ¹\n\n† Work done while interning at Google DeepMind. \\* Equal contribution alphabetically.\n\n  \n* DeepMind Logo ¹ Google DeepMind\n* MIT Logo ² MIT\n* Stanford Logo ³ Stanford University\n\n  \n**CVPR 2024**\n\n  \n[Paper](https://arxiv.org/abs/2401.12168) [Video](https://www.youtube.com/watch?v=_z9b5E_obbE) Code (3rd party)\n\n## Abstract\n\nUnderstanding and reasoning about spatial relationships is a\nfundamental capability for Visual Question Answering (VQA) and\nrobotics.\n\n...\n\nnote = {GitHub repository},\n        url = {https://github.com/remyxai/VQASynth/tree/main}\n      }\n```"
      ]
    },
    {
      "url": "https://www.reddit.com/r/singularity/comments/19dg7bl/spatialvlm_endowing_visionlanguage_models_with/",
      "title": "SpatialVLM: Endowing Vision-Language Models with Spatial ...",
      "publish_date": null,
      "excerpts": [
        "Our work features the first Internet-scale 3D spatial reasoning dataset in metric space. By co-training a VLM on such data, we significantly enhance its ability on both qualitative and quantitative spatial VQA."
      ]
    },
    {
      "url": "https://www.deepnlp.org/content/articles/spatialvlm%3A-endowing-vision-language-models-with-spatial-reasoning-capabilities",
      "title": "SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities",
      "publish_date": null,
      "excerpts": [
        "Vision Language Models (VLMs) have shown impressive performance in some VQA benchmarks but struggle with 3D spatial reasoning such as recognizing distances or size differences between physical objects."
      ]
    },
    {
      "url": "https://github.com/vulab-AI/Awesome-Spatial-VLMs",
      "title": "Awesome Spatial VLMs - GitHub",
      "publish_date": null,
      "excerpts": [
        "[Training - 24 datasets](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Dataset_SVQA.md) [Evaluation - 54 benchmarks](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Benchmark_SVQA.md)\n\n🤝 This repository will be continuously updated, and we warmly invite contributions. **If you have a paper, dataset, or model to add, please submit a pull request or open an issue for discussion.**\n\n## Table of Contents\n\n* Table of Contents\n* Overview\n* 🚀 Awesome Papers\n  \n    + Training-Free Prompting\n    + Model-Centric Enhancements\n    + Explicit 2D Information Injection\n    + 3D Information Enhancement\n    + Data-Centric Spatial Enhancement\n* 📚 Datasets and Benchmarks\n  \n    + Spatially-Oriented Training Corpora\n    + Evaluation Benchmarks\n* 🏆 Spatial VLM Leaderboard & Evaluation Toolkit\n  \n    + 🏅 Main Leaderboard\n    + 🧑‍🔬 How to Evaluate Your Model\n* Citation\n\n## Overview\n\n...\n\n* [NeurIPS2024] SpatialPIN: Enhancing Spatial Reasoning Capabilities of Vision-Language Models through Prompting and Interacting 3D Priors ( _University of Oxford_ ) [[paper]](https://arxiv.org/pdf/2403.13438) [[code]](https://github.com/dannymcy/zeroshot_task_hallucination_code) ;\n* [CoRR2025] SoFar: Language-Grounded Orientation Bridges Spatial Reasoning and Object Manipulation ( _Tsinghua University_ ) [[paper]](https://arxiv.org/pdf/2502.13143) [[code]](https://github.com/qizekun/SoFar) ;\n **Visual Prompting Methods**\n\n* [arXiv2023] Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V ( _Microsoft Research, Redmond_ ) [[paper]](https://arxiv.org/pdf/2310.11441) [[code]](https://github.com/microsoft/SoM) ;\n* [NeurIPS2023] Fine-Grained Visual Prompting ( _Nanjing University of Science and Technology_ ) [[paper]](https://arxiv.org/pdf/2306.04356) [[code]](https://github.com/ylingfeng/FGVP) ;\n* [arXiv2024] I Know About “Up”!\n\n...\n\ncom/BAAI-DCAI/SpatialBot) [[checkpoint]](https://huggingface.co/RussRobin/SpatialBot-3B) ;\n* [NeurIPS2025] RoboRefer: Towards Spatial Referring with Reasoning in Vision-Language Models for Robotics ( _Beihang University_ ) [[paper]](https://arxiv.org/pdf/2506.04308) [[code]](https://github.com/Zhoues/RoboRefer) [[checkpoint]](https://huggingface.co/collections/Zhoues/roborefer-and-refspatial-6857c97848fab02271310b89) ;\n* [NeurIPS2025] SSR: Enhancing Depth Perception in Vision-Language Models via Rationale-Guided Spatial Reasoning ( _Westlake University_ ) [[paper]](https://arxiv.org/pdf/2505.12448) [[code]](https://github.com/yliu-cs/SSR) [[checkpoint]](https://huggingface.co/collections/yliu-cs/ssr-682d44496b64e4edd94092bb) ;\n* [NeurIPS2025] SD-VLM: Spatial Measuring and Understanding with Depth-Encoded Vision-Language Models ( _Zhejiang University_ ) [[paper]](https://arxiv.org/pdf/2509.17664) [[code]](https://github.com/cpystan/SD-VLM) [[checkpoint]](https://huggingface.\nco/cpystan/SD-VLM-7B) ;\n\n* [NeurIPS2025] SPATIALLM: Training Large Language Models for Structured Indoor Modeling ( _Manycore Tech Inc._ ) [[paper]](https://arxiv.org/pdf/2506.07491) [[code]](https://github.com/manycore-research/SpatialLM) [[checkpoint]](https://huggingface.co/manycore-research/SpatialLM1.1-Qwen-0.5B)\n\n* [Arxiv2025] 3D Aware Region Prompted Vision Language Model ( _UC San Diego_ ) [[paper]](https://arxiv.org/pdf/2509.13317) ;\n **Implicit 3D from Egocentric Views**\n\n* [arXiv2025] VLM-3R: Vision-Language Models Augmented with Instruction-Aligned 3D Reconstruction ( _UT Austin_ ) [[paper]](https://arxiv.org/pdf/2505.20279) [[code]](https://github.com/VITA-Group/VLM-3R) ;\n* [arXiv2025] Spatial-MLLM: Boosting MLLM Capabilities in Visual-based Spatial Intelligence ( _Tsinghua University_ ) [[paper]](https://arxiv.org/pdf/2505.23747) [[code]](https://github.com/diankun-wu/Spatial-MLLM) ;\n\n...\n\n* [ICLR2025] SPARTUN3D: Situated Spatial Understanding of 3D World in Large Language Models ( _Michigan State University & UC Davis_ ) [[paper]](https://arxiv.org/pdf/2410.03878) ;\n* [ICML2025] Orient Anything: Learning Robust Object Orientation Estimation from Rendering 3D Models ( _Zhejiang University_ ) [[paper]](https://arxiv.org/pdf/2412.18605) [[code]](https://github.com/SpatialVision/Orient-Anything?tab=readme-ov-file) [[checkpoint]](https://huggingface.co/Viglong/Orient-Anything/blob/main/croplargeEX2/dino_weight.pt) ;\n* [WACV2025] LLaVA-SpaceSGG: Visual Instruct Tuning for Open-vocabulary Scene Graph Generation with Enhanced Spatial Relations ( _City University of Hong Kong_ ) [[paper]](https://arxiv.org/pdf/2412.06322) [[code]](https://github.com/Endlinc/LLaVA-SpaceSGG?tab=readme-ov-file) [[checkpoint]](https://huggingface.co/wumengyangok/LLaVA-SpaceSGG/tree/main) ;\n* [NeurIPS2025] Actial: Activate Spatial Reasoning Ability of Multimodal Large Language Models ( _Nanjing University_ ) [[paper]](https://openreview.net/pdf?id=jquTBzt3Av) [[code]](https://github.com/warmsnow-sh/Actial) [[checkpoint]](https://huggingface.co/Osilly/Acital-Qwen-2.5VL-7B) ;\n\n## 📚 Datasets and Benchmarks\n\n> A comprehensive list of datasets for training and evaluation.\n> \n> \n\n### Spatially-Oriented Training Corpora\n\n[Dataset](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Dataset_SVQA.md)\n\n### Evaluation Benchmarks\n\n[Benchmark](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/data_benchmark/Benchmark_SVQA.md)\n\n## 🏆 Spatial VLM Leaderboard & Evaluation Toolkit\n\n### 🏅 Main Leaderboard\n\nThe table below presents the main results from our survey, comparing [38 VLMs](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/evaluation/README.md) across 9 benchmarks . Scores are QA Accuracy (%).\nBenchmarks are grouped by our Cognitive Hierarchy.\n\n[Leaderboard](https://github.com/vulab-AI/Awesome-Spatial-VLMs/blob/main/samples/leaderboard.jpg)\n\nWe invite the community to benchmark new models using our suite. Please to add your model's results!\n\n### 🧑‍🔬 How to Evaluate Your Model\n\n1. **Selected Benchmarks for the Leaderboard**  \n   We collect existing spatial benchmarks used in the literature and standardize their usage for evaluation in the hugging face repo [Hugging Face](https://huggingface.co/datasets/LLDDSS/Awesome_Spatial_VQA_Benchmarks) .  \n   The table below summarizes the key datasets used to benchmark spatial VLMs on our leaderboard.\n   \n   |Dataset Name |Description |Link |\n   | --- | --- | --- |\n   |EgoOrientBench |Egocentric spatial understanding benchmark |[Hugging Face Link Link](https://huggingface.co/datasets/LLDDSS/Awesome_Spatial_VQA_Benchmarks) |\n   |GeoMeter(real) |A depth-aware spatial reasoning be"
      ]
    },
    {
      "url": "https://www.alphaxiv.org/abs/2509.25390",
      "title": "SpinBench: Perspective and Rotation as a Lens on Spatial Reasoning in VLMs | alphaXiv",
      "publish_date": "2026-02-28",
      "excerpts": [
        "\" To ensure robustness, researchers used symmetrical and syntactic augmentations—asking the same question in different ways or flipping the perspective—to see if the model's answers remained consistent.\n3. **Dynamic Translation:** This involves reasoning about linear movement. Models are presented with two sequential frames where an object has moved (e.g., shifted to the right), and they must identify the nature of this displacement while the camera remains static.\n4. **Dynamic Rotation:** This task targets rotational transformations. Models must determine if an object has rotated clockwise or counter-clockwise between two frames. This is particularly challenging because it requires understanding the object's orientation relative to both the viewer and its own center.\n5. **Canonical View Selection:** Here, models are asked to map an object to a standard viewpoint. For instance, given a front view of a car, the model might be asked to identify which image represents its left side.\n6.\n**Mental Rotation:** This is one of the more cognitively demanding tasks, requiring the model to mentally simulate a transformation. Given an image and a command (e.g., \"rotate this chair 4 5 ∘ to the right\"), the model must select the resulting orientation from several candidates.\n7. **Perspective Taking:** The most complex category, this involves reasoning about how an entire scene changes when the observer's viewpoint shifts. This includes predicting how object-relative positions transform (Relation Transformation) and selecting the correct scene image from a new perspective (Scene Selection).\n\nTo measure performance accurately, the benchmark uses Cohen's kappa κ to correct for accuracy that might occur by chance:\n\nκ = 1 − p e ​ p o ​ − p e ​ ​\n\nIn this equation, p o ​ represents the observed agreement (the raw accuracy), and p e ​ is the probability of agreement by chance.\n\n...\n\n* **Multi-View Cars:** To test reasoning in more structured, real-world categories, the benchmark uses sequences of vehicles sampled at 4 5 ∘ intervals.\n* **Stereo Faces:** Human faces are naturally asymmetrical and have clear \"front\" and \"side\" orientations. This makes them ideal for testing egocentric (viewer-centered) versus allocentric (object-centered) perspectives.\n\nA key methodological contribution of SPINBENCH is the use of \"premise-based\" tasks. In some perspective-taking experiments, the spatial relationship is explicitly stated in the text prompt (e.g., \"The cup is to the left of the plate. If you move to the opposite side, where is the cup?\"). This setup is designed to decouple visual grounding from spatial inference. If a model fails here, the error lies in its geometric logic rather than its ability to \"see\" the objects in the image.\n\n## Findings: The Reality of VLM Spatial Reasoning\nThe evaluation of 43 different models—ranging from smaller open-source versions to large proprietary systems like GPT-5—revealed significant gaps in current AI capabilities. While some models showed strong performance in basic tasks, their reasoning often faltered as the complexity increased.\n\nOne of the most prominent findings was the **egocentric bias** . Models were much more likely to correctly identify rotations or positions from the viewer's perspective than from the object's perspective. For example, if a face rotated \"to its own left,\" many models would mistakenly identify the rotation based on how it appeared to the viewer. This indicates that VLMs may lack a robust internal representation of object-centric coordinates.\n\nAnother major observation was the **lack of consistency** . Many models were easily confused by syntactic changes. If a model correctly identified that \"A is left of B,\" it might fail to agree that \"B is right of A\" when the question was rephrased.\n\n...\n\n0001 ) for premise-based tasks further confirms that these models struggle with the underlying logic of spatial transformation, even when the visual components are simplified.\n\n## Scaling Behaviors and Emergent Capabilities\n\nThe study also investigated how spatial reasoning improves as models get larger. Interestingly, not all spatial skills improve at the same rate.\n\n* **Object-Relation Grounding:** This skill showed a linear, monotonic improvement. As models grew from 1 B to 38 B parameters, they became steadily better at identifying simple \"left/right\" relations.\n* **Identity Matching:** This task exhibited what researchers call an \"emergent capability.\" Smaller models often performed no better than chance, but once the model size reached the 7 B to 8 B \\+ range, performance suddenly jumped to near-perfect levels. This suggests that a certain threshold of model complexity is required to grasp the concept of 3D object identity across views.\n\n...\n\nBaiqiao Yin, Qineng Wang, Pingyue Zhang, Jianshu Zhang, Kangrui Wang, Zihan Wang, Jieyu Zhang, Keshigeyan Chandrasegaran, Han Liu, Ranjay Krishna, Saining Xie, Manling Li, Jia- jun Wu, and Li Fei-Fei. Spatial mental modeling from limited views, 2025. URL https: //arxiv.org/abs/2506.21458.\n\n[Does spatial cognition emerge in frontier models?](https://alphaxiv.org/abs/2410.06468)\n\nThis work is another recent and important benchmark cited to frame the problem space and establish the state-of-the-art. By referencing failures exposed by SPACE, the authors position SPINBENCH as a necessary tool to address the open question of whether VLMs possess genuine spatial reasoning capabilities.\n\nSanthosh Kumar Ramakrishnan, Erik Wijmans, Philipp Kraehenbuehl, and Vladlen Koltun. Does spatial cognition emerge in frontier models? arXiv preprint arXiv:2410.06468, 2024.\n\n## Audio\n\nGenerate audio summary →\n\n## Discussion\n\nComment\n\nView PDF\n\n[ZhangYuyou-10/SpinBench](https://github."
      ]
    }
  ],
  "warnings": null,
  "usage": [
    {
      "name": "sku_search",
      "count": 1
    }
  ],
  "session_id": "ses_fd81e747fffey16zO59Xh0VoM8"
}
```

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 40.6s)

_Thinking:_

I now have a solid picture of the landscape. Let me give the honest novelty assessment.

Key competitive landscape findings (2025–2026):
- VSR itself (2023) already documented "models are at chance for orientation relations" — cited 501×
- SpinBench (2026): 43 models, egocentric bias, consistency failures under rephrasing — overlaps with Paper 1's coherence finding and orientation weakness
- OrientSAM (2026): explicitly identifies object orientation as key bottleneck for reference-centric reasoning, proposes fix — directly competes with Paper 1's "orientation bottleneck" claim AND provides a method that improves it
- SITE, Spatial-DISE (ICLR 2026), OmniSpatial (ICLR 2026), MMSI-Bench, SpatiaLab (ICLR 2026), SAT, VSI-Bench — benchmark flood; "spatial reasoning is hard for VLMs" is extremely well-trodden
- Sparkle: "mastering basic spatial capabilities elicits generalization" — relates to Paper 2's fine-tuning decomposition
- SoFar: "Language-Grounded Orientation Bridges Spatial Reasoning and Object Manipulation" — orientation-focused
- Orient Anything (ICML 2025): orientation estimation

So the user's concern is valid: "VLMs are bad at spatial reasoning / orientation" is NOT novel as a headline in 2026. The market is flooded with benchmarks confirming it. What remains novel:
- Paper 1's specific angle (interventions don't close it + accuracy/coherence dissociation + poor transfer) is a diagnostic study — moderately novel but crowded space.
- Paper 2's angle (fine-tuning as controlled intervention decomposed into ΔA/ΔG/ΔC across seeds) is a *methodological/evaluative* contribution — this is genuinely less explored; most work either builds benchmarks or proposes fixes, few rigorously audit what fine-tuning actually changes. This fits E&D track best precisely because novelty isn't "spatial is hard" but "here's how to measure what training changes."
- Paper 3 (equivariance algebra, law-sensitivity) is mechanistic and fairly novel in framing, though related to equivariance literature.

Reddit/community sentiment: community widely knows VLMs are bad at left/right, spatial tasks ("VLMs can't count fingers or tell left from right" meme-level knowledge). So a paper whose headline is "VLMs bad at orientation" would get "we know" from reviewers. Papers must sell the *evaluation methodology* or *mechanistic insight*, not the observation.

Recommendation stays Paper 2, sharpened: lead with the capability-vector protocol, not the phenomenon. Also note Paper 3's law-sensitivity finding (obeys wrong laws) is actually quite novel-sounding and could be strong if framed against equivariance literature — but synthetic-only limits E&D fit.

Keep answer structured and honest.

Good instinct to pressure-test this. I searched the recent literature and community discussion (Reddit/LocalLLaMA, alphaXiv, HF blog, ICLR/CVPR 2026 proceedings). Honest verdict:

## The uncomfortable truth: "VLMs are bad at spatial/orientation" is NOT novel in 2026

The field is saturated with papers confirming your Paper 1's headline observation:

| Work | Overlap |
|---|---|
| **VSR itself** (TACL'23, 501 citations) | Already stated verbatim: *"tested models are... incapable of recognising relations concerning the orientations of objects"* |
| **SpinBench** (2026, 43 models incl. GPT-5) | Egocentric bias + **consistency failures under rephrasing** — overlaps both your orientation and coherence findings |
| **OrientSAM** (2026) | Explicitly names **object orientation as the bottleneck**, diagnoses a camera-centric shortcut, *and fixes it* (+30pp on reference-centric reasoning) |
| **SITE, Spatial-DISE & OmniSpatial** (both ICLR 2026), SpatiaLab (ICLR 2026), MMSI-Bench, SAT | Benchmark flood all reporting "orientation/perspective is weakest" |
| **Sparkle** (MIT), SpatialVLM line | Fine-tuning on basic spatial data to improve reasoning — adjacent to Paper 2's question |

Community sentiment matches: on r/LocalLLaMA and HF discussions, "VLM can't tell left from right / which way something faces" is folk knowledge, not news. A reviewer reading Paper 1's abstract will think *"yes, we know — SpinBench/OrientSAM/SITE said it bigger."*

## Where actual novelty survives

1. **Paper 2 — strongest, but only if you lead with the protocol, not the phenomenon.** Nobody in this flood is doing seed-replicated causal decomposition of what LoRA actually changes (ΔA/ΔG/ΔC moving independently, replicated across backbones). That's an evaluation-methodology contribution — exactly what the E&D track rewards. Frame: *"accuracy gains from spatial fine-tuning are not a single capability"* — not *"VLMs are weak at orientation."*
2. **Paper 3 — the new phase-2 result is genuinely novel**: a latent trained to obey a transformation algebra complies ~300× better than augmentation **but obeys a *wrong* law equally well (15/15 seeds)**. That's a specificity/law-sensitivity result nobody else has published. Its weakness is synthetic-only scope, not novelty.
3. **Paper 1 — weakest on novelty.** It's a competent diagnostic, but every component (orientation ceiling, prompting fails, probes at chance, poor transfer) now exists in stronger/bigger form elsewhere. As-is, highest desk-risk for "incremental over known results."

## Bottom line

Novelty ranking after the web check: **Paper 2 > upgraded Paper 3 > Paper 1** — same order as before, but more emphatic. If anything, the search strengthens the case for submitting Paper 2 by Aug 28 with the framing pushed toward the measurement methodology, and letting Paper 3 mature into its unique law-sensitivity story. Paper 1 should probably not go to WACV R2 without repositioning around the transfer-harm result (75.1→71.6%, p=0.004), which is its most defensible fresh claim.

---

## User

yeah we only submit one for sure so u think that upgraded paper 3 is still not as good as slightly rewritten paper 2

---

## Assistant (Build · Ox Alpha Free (Unlimited) · 39.1s)

_Thinking:_

The user asks: submitting only one — is upgraded Paper 3 still not as good as a slightly rewritten Paper 2?

Give a direct, well-reasoned verdict. Consider: E&D track fit, evidence strength, risk. Paper 2: real benchmarks, seeds, preregistered, positive replicable findings, methodology contribution, kit frozen. Paper 3 upgraded: novel law-sensitivity finding but synthetic-only, single task (binary axis ceiling), behavioral test uninformative by construction, one backbone in phase2? Phase2 added Qwen2-VL-7B support and N=128/2048 scaling; the 15-seed canonical was presumably on the synthetic setup with some backbone. Still mechanistic, narrow.

Also deadline feasibility: Paper 2 needs only slight rewrite (framing); Paper 3 would need substantial integration of phase-2 results into paper by Aug 28 — risky.

Verdict: Yes — rewritten Paper 2 remains the pick. But be honest about conditions under which Paper 3 could win: if reviewers value mechanistic novelty, but E&D track explicitly evaluates dataset/eval advancement — Paper 3 isn't even an evaluation contribution really; it's a method/negative result, better for Algorithms track or ICLR-style venue. That's decisive: Paper 3 is arguably miscategorized for E&D.

Keep concise-ish.

Yes — for **this** venue and deadline, rewritten Paper 2 is still the clear pick. Four reasons:

1. **Track fit is decisive.** The WACV E&D review criteria literally ask *"does this advance evaluation tools/practices for testing AI systems?"* Paper 2 *is* that: a reusable measurement protocol (ΔA/ΔG/ΔC capability vector + transformation battery) applied to real models on a real benchmark. Paper 3 isn't an evaluation contribution at all — it's a mechanistic methods/negative-result study on synthetic scenes. It's arguably miscategorized for E&D and would fare better at an Algorithms-track or ICLR-type venue later.

2. **Evidence base.** Paper 2: VSR, two backbones × 4 seeds each, replication on Qwen3-VL, every effect seed-consistent, preregistered protocol, frozen kit with hashes. Paper 3 even post-upgrade: one synthetic scene family, binary task at ceiling "by construction" (the abstract admits the behavioral composition test is uninformative), depth probe flat, headline = compliance-without-transfer-plus-wrong-law-compliance. Novel, yes; convincing to an E&D panel that it "meaningfully advances a CV sub-area," less so.

3. **Deadline risk asymmetry.** Paper 2 needs only framing edits (lead with the protocol; demote orientation-weakness observations to motivation). That's days. Paper 3 needs the phase-2/15-seed/no-box diagnostics woven into a coherent submission — the branch history shows active churn *this week* (latent collapse, easyA v2). Submitting a moving target in 6 days is how desk-rejects and hostile reviews happen.

4. **Reviewer psychology.** Paper 2 gives reviewers something to say yes to (positive, replicated, methodological). Paper 3 gives them a sophisticated null — even done fairly, that's an uphill fight against a NeurIPS-E&D-style rubric.

**One caveat:** if the phase-2 work finishes cleanly and you'd rather not rush Paper 2's rewrite quality, holding Paper 3 for Round 1 of the next cycle (fully polished, possibly expanded beyond synthetic) is a legitimate strategy — just don't submit both to the same round. But if exactly one goes in by Aug 28: **Paper 2, lightly rewritten.**

Want me to do the actual rewrite pass on the Paper 2 abstract/intro now (shift emphasis to the capability-vector protocol), plus a pre-submission checklist audit of the kit?

---

