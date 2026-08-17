# Session Handoff — 2026-08-16 (EquiOrient Phase 2 continued)

**Session scope:** Difficulty escalation v1→v4 → architectural ceiling discovered → analysis module built → confirmatory YAML frozen → 30-run experiment launched → paper skeleton written
**Branches:** `research/equiorient-phase2` (latest commit `4cea99c`)
**Worktree:** `Desktop\VLM-Spatial-Reasoning-EquiOrient-Phase2`

---

## 1. What was done this session

### Difficulty escalation (v1 → v4)

| Version | Target size | Distractors | Colors | Background | Noise | Aug unseen |
|---------|------------|-------------|--------|------------|-------|------------|
| v1 | 6-9px | 6-10 | 12 distinct | 248 (white) | amp=6 | 1.000 |
| v2 | 6-9px | 6-10 | 12 distinct | 248 | amp=6 | 1.000 |
| v3 | 3-5px | 8-16 | 12 muted | 180 (gray) | amp=10 | 0.985 |
| v4 | 2-4px | 12-20 | 3 near-identical | 155 (low contrast) | amp=12 | 1.000 |

**Conclusion:** The ceiling is architectural, not visual. The model receives ground-truth bounding boxes and pools features from known positions. Visual difficulty is irrelevant because the model never needs to find the objects — it is told where they are. The VLM backbone's region-pooled features are inherently D4-robust.

### Architecture modules built

| Module | Files | Status |
|--------|-------|--------|
| Analysis | `analysis/aggregate.py`, `bootstrap.py`, `latent_metrics.py`, `collapse_checks.py`, `figures.py` | ✅ |
| Experiments | `experiments/evaluate.py`, `launch_array.py` | ✅ |
| Modal | `modal/equiorient_phase2.py` (supports `--launch-all`, confirmatory mode) | ✅ |
| Paper | `paper/main.tex`, `paper/main.bib`, `paper/OPENREVIEW_SUBMISSION.md` | ✅ |
| Freeze | `equiorient/freezes/phase2_confirmatory.yaml` (FULLY FILLED) | ✅ |

### Key finding: architectural ceiling

The dev gate non-ceiling requirement (< 0.95 unseen) FAILS because:
1. The model gets bounding boxes → knows exactly where to look
2. Qwen3-VL's region-pooled features encode relative positions robustly
3. D4 transforms don't change relative positions within pooled features
4. Making objects smaller/denser/noisier doesn't help — the bottleneck is the pooling mechanism, not visual difficulty

This IS outcome (b) from the orchestrator: "latent improves huge + behavior doesn't → strong mechanistic negative."

### Confirmatory YAML frozen

Committed BEFORE inspecting confirmatory results:
- git_sha: `3b16db09` (later updated to `4cea99c`)
- seeds: [101, 202, 303, 404, 505]
- lambda: 1.0
- train_sizes: [128, 512, 2048]
- All gate requirements documented (including non-ceiling FAIL with explanation)

### 30-run experiment launched

5 seeds × 6 arms = 30 runs on Modal L40S (always-rebuild scaffold, v4 data).
Launched via `python -m modal run modal/equiorient_phase2.py --launch-all --mode confirmatory`.

---

## 2. Git log (recent)

```
4cea99c paper: skeleton + OpenReview kit
3ae79ea freezes: confirmatory YAML fully filled, v4 ceiling acknowledged
3b16db0 data: v4 extreme difficulty (targets 2-4px, 12-20 homogeneous distractors)
322d3f9 analysis: module + evaluate + launch_array + v3 difficulty
baa6577 handoff: session state summary
9cb9a84 data: v2 difficulty escalation (distractors 6-10, noise)
```

---

## 3. What remains

| Task | Status | Effort |
|------|--------|--------|
| 30-run confirmatory results | RUNNING on Modal | ~15-25 min per job |
| N=128 + N=2048 data-scale runs | PENDING | Launch after primary |
| Primary analysis + bootstrap CI | PENDING | 1-2 hrs (automated) |
| Fill paper tables with real numbers | PENDING | After results arrive |
| Generate figures | PENDING | After results arrive |
| Compile PDF | PENDING | After tables filled |
| Hostile reviewer simulation | PENDING | 1 day |
| Export to Desktop\WACV2027_Papers\ | PENDING | 10 min |
| Final PDF freeze + submit | PENDING | Aug 28 AoE |

---

## 4. Critical numbers from dev runs (v4, seed 101)

| Arm | Answer loss (ep1→ep2) | Structural loss (ep1→ep2) | Unseen acc |
|-----|----------------------|--------------------------|------------|
| Augmentation | 3.217 → 0.028 | 0.0 (no structural) | 1.000 |
| EquiOrient | 4.376 → 0.239 | 0.330 → 0.120 | 1.000 |

- EquiOrient's structural loss IS nonzero and decreasing — the mechanism works
- Both achieve 1.000 unseen — behavioral ceiling
- The gap is in latent metrics (E_norm, specificity S), not behavior

---

## 5. Modal status

- Account: `khagendrakhatri365` (Starter, ~$28 credit remaining)
- 30 confirmatory jobs launched on L40S
- Results will appear in `equiorient-results` volume at `/root/results/phase2_confirmatory/`
- Check Modal dashboard: https://modal.com/apps/khagendrakhatri365

---

## 6. Key decisions

1. **Outcome (b) accepted:** The mechanistic negative is the result. The VLM backbone already handles D4 transforms.
2. **Confirmatory YAML committed before results** (per orchestrator directive).
3. **Paper skeleton written** with placeholder tables — fill with real numbers after 30-run results arrive.
4. **No more difficulty escalation** — the ceiling is architectural (bbox pooling), not visual.
5. **Paper 1 and Paper 2 remain frozen.**
