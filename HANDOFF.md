# Session Handoff — 2026-08-15 (EquiOrient + Paper 3 + Phase 2)

**Session scope:** Thunder Compute runbook → Modal migration → Paper 3 complete → Phase-2 redesign + foundation + dev gate
**Branches touched:** `research/equiorient` (Paper 3), `research/equiorient-phase2` (Phase 2)
**Worktrees:**
- `Desktop\VLM-Spatial-Reasoning-EquiOrient` → `research/equiorient`
- `Desktop\VLM-Spatial-Reasoning-EquiOrient-Phase2` → `research/equiorient-phase2`
**Modal account:** `khagendrakhatri365` (Starter, $30/mo credit); hf-token secret rotated and committed.

---

## 1. Paper 3 — DONE (submit to WACV 2027 E&D)

**Status:** submission-ready. Branch `research/equiorient`, latest commit `ee669cf` (suppl.pdf added).

**What was built this session:**
- Phase-1 six-arm pilot (corrected harness — paired z(x)/z(Tx) structural losses, manipulation check, per-transform metrics, depth probes)
- Two-regime replication (v1 4-object, v2 5-object)
- Full hostile review (3 agents × 2 rounds, zero losses discovered, corrected, re-run)
- Complete manuscript (`paper/main.pdf`, 5 pages + 2-page `suppl.pdf`), WACV-style, compiled via Tectonic
- OpenReview kit: `paper/OPENREVIEW_SUBMISSION.md` (title, abstract, deadlines, file checklist)

**Key result:** EquiOrient achieves strong latent algebra compliance (held-out V∘H error 0.045 vs 14.65 augmentation, 325×) with correct-vs-wrong specificity (0.033 vs 4.89 on H), but no measurable downstream transfer (behavioral ceiling, depth probe flat).

**Deadlines:** Aug 21 enrollment · Aug 28 paper · Aug 30 supplementary.

---

## 2. Paper 1 / Paper 2 — FROZEN

- Paper 1 (`paper1/wacv2027`): no changes. Exported to `Desktop\WACV2027_Papers\Paper1_Beyond_Spatial_Accuracy\`.
- Paper 2 (`paper2/wacv2027`): no changes. Exported to `Desktop\WACV2027_Papers\Paper2_What_Spatial_FineTuning_Changes\`.

---

## 3. EquiOrient Phase 2 — IN PROGRESS (dev gate, harder data)

**Branch:** `research/equiorient-phase2` (branch `research/equiorient`, latest commit `9cb9a84` on the phase2 worktree).
**Worktree:** `Desktop\VLM-Spatial-Reasoning-EquiOrient-Phase2`
**Modal scaffold:** `modal/equiorient_phase2.py` (runs on L40S with GPU, rebuilds data in-sandbox, always rebuilds to avoid stale-volume bugs)

### What was built this session (Phase 2):

| Module | Files | Status |
|---|---|---|
| D4 algebra | `equiorient/algebra/d4.py`, `representation.py`, `wrong_representation.py`, `label_action.py`, `identifiability_audit.py` | ✅ gate PASS |
| Data | `equiorient/data/scene_generator_v2.py`, `transforms.py`, `renderer.py`, `manifests.py`, `validate_dataset.py` | ✅ gate PASS |
| Models | `equiorient/models/pair_encoder_v2.py` (z=[zx;zy], 256-dim, 8-class head), `qwen3_features.py` | ✅ gate PASS |
| Objectives | `equiorient/objectives/answer.py`, `output_consistency.py`, `invariance.py`, `equiorient.py`, `wrong_geometry.py` | ✅ gate PASS |
| Tests | `equiorient/tests/test_phase2_gate.py` (45 tests) | ✅ 45/45 |
| Harness | `equiorient/experiments/train.py` (six arms, D4, paired losses, manipulation check, dev eval) | ✅ tiny smoke PASS |
| Freeze | `equiorient/freezes/phase2_confirmatory.yaml` (ledger draft) | ✅ |
| Modal | `modal/equiorient_phase2.py` | ✅ cloud gate PASS |
| Dataset | `results/phase2_data/` (20,480 examples, harder regime: smaller targets, 6-10 distractors, overlap, noise) | ✅ validated |

### Bugs caught and fixed this session (the dev gate working as designed):

| Bug | How found | Fix |
|---|---|---|
| `pooled()` mapped math coords directly to grid cells (+96 offset + y-flip missing) | dev run: R/R2/R3 at ~0% (transformed views pooled wrong cells) | Converted math→pixel before cell lookup |
| `transform_scene()` copied ORIGINAL label to every view (wrong answer targets for transformed images) | dev run: R/R2/R3 still at ~0% after pooling fix (labels wrong) | Compute π_g(label) for each view |
| Modal data volume served stale dataset | dev runs after fix showed identical numbers to pre-fix run | Always rebuild in-sandbox (shutil.rmtree + build) |

### Dev gate result (harder data, seed 101, N=512):

**Both augmentation AND equiorient scored 1.0000 on ALL 8 transforms including all 5 unseen D4 elements.** Augmentation unseen = 1.0 → dev gate FAILS on non-ceiling (requirement: <0.95).

**Consequence:** confirmatory run must NOT launch. Task difficulty was escalated: distractors 6-10, smaller targets (6-9 px), mild overlap, per-pixel background noise. Rebuild committed (`9cb9a84`, manifest SHA `859ddfc2`).

**IN PROGRESS right now:** both dev runs (augmentation + equiorient) are running on Modal L40S with the harder data. Logs: `p2_aug7.log`, `p2_eq7.log`. The scaffolds always rebuild data in-sandbox, so they'll get the new harder dataset.

### Architecture summary (the orchestrator's design):

- **D4 group:** H=horizontal reflection, R=90° CCW rotation; R²=180°, R³=270°, RH, R²H, R³H unseen
- **Correct rho:** G_g ⊗ I₁₂₈ on z=[z_x; z_y]∈R²⁵⁶
- **Wrong rho:** ρ̃(R)=R₁₈₀=-I, ρ̃(H)=H; self-consistent but geometrically wrong
- **Identifiability audit:** all 5 unseen elements distinguish correct from wrong (Phase-1 symmetry collision eliminated: ρ(R²)=−I ≠ ρ̃(R²)=I)
- **8-way directional labels** (not binary); label action π_g is exact
- **Sparse training exposure:** identity + one generator per scene, 50/50
- **Dataset:** 512 dev / 2048 train pool / 512 val / 1024 test scenes; harder regime with noise, overlap, 6–10 distractors

---

## 4. Modal setup (reusable)

- Account: `khagendrakhatri365` Starter ($30/mo, pay-per-second)
- HF secret: `hf-token` (value committed to Modal — rotated token, per-session only)
- Volumes: `equiorient-hf-cache` (Qwen3-VL-8B model, shared across Phase 1 + 2), `equiorient-phase2-data` (always rebuilt), `equiorient-results`
- L40S recommended (48 GB, matches A6000 class, $1.95/hr); A100-40GB as fallback
- Cost ~$0.30/min on L40S; dev runs ~15–25 min ≈ $0.50–0.80 each

---

## 5. What happens next (the orchestrator's timeline)

| Date | Task |
|---|---|
| **Now** | finish harder-data dev runs (augmentation must be <95% unseen to proceed) |
| **Aug 16** | if non-ceiling passes: λ/config selection from dev; confirmatory YAML committed |
| **Aug 18–20** | five-seed × six-arm primary experiment (30 runs on L40S) |
| **Aug 20** | locked primary analysis; neutral title for enrollment |
| **Aug 21** | WACV 2027 enrollment deadline |
| **Aug 21–23** | data-scale runs (N=128, N=2048) + optional second backbone (Qwen2-VL-7B, 3 seeds) |
| **Aug 23** | no more method changes |
| **Aug 23–25** | write 8-page manuscript |
| **Aug 25–26** | independent reproduction of every headline table/figure |
| **Aug 26–27** | hostile reviewer simulation |
| **Aug 27** | PDF freeze |
| **Aug 28** | submit to WACV 2027 E&D (AoE) |

---

## 6. Key decisions / constraints (do NOT override)

1. **Paper 1 and Paper 2 are frozen.** Do not reopen experiments on either.
2. **All GPU compute goes to Paper 3 / EquiOrient.** Branch `research/equiorient-phase2`.
3. **Phase-1 artifacts are untouched on `research/equiorient`** — they're historical evidence only.
4. **Hard gate:** no confirmatory run until augmentation unseen accuracy <95% at N=512 (dev gate).
5. **The confirmatory YAML (`phase2_confirmatory.yaml`) must be committed before inspecting confirmatory results.**
6. **Do not optimize for a favorable EquiOrient result. Optimize for decisiveness.** (orchestrator instruction)
7. **Three acceptable outcomes only:** (a) EquiOrient improves behavior → positive method paper; (b) latent improves huge + behavior doesn't, tight CI → mechanistic negative; (c) latent effect disappears / unstable → KILL, don't submit.
