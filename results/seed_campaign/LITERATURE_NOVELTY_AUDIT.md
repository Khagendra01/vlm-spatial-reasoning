# Paper-2 R1: Literature & Novelty Audit (Step 3)

**Date:** 2026-08-14 (post-compute; GPU off). Re-checks literature published
during and after the compute campaign (Mar–Aug 2026), fixes the exact novelty
sentence, and records the current claim boundary.

---

## 1. Related work re-verified (with availability status)

| Paper | ID / date | What it does | Key metric | Differs from us |
|---|---|---|---|---|
| Beyond Accuracy (medical VQA) | 2603.03437, Mar 2026 | real/blank/shuffled images; RLVR vs image-text RLVR on 4 medical benchmarks | **VRS = A(real) − A(shuffle)** (== our G), IS, HVRR | Medical domain; RLVR training objective (not ordinary LoRA); no semantic-consistency axis; no fresh-seed analysis |
| Seeing without Looking | 2605.22903, May 2026 (CVPR-W GRAIL-V) | global/local visual interventions, token-geometry analysis | accuracy vs evidence-sensitivity | Audits pretrained models; no fine-tuning transition; no public dataset |
| Consistent Yet Wrong / ViewDiag | 2606.02742v2, Jun 2026 | multi-view consistency vs metric accuracy (Hypersim/ScanNet/KITTI360); latent collapse probe | stability vs error regimes | **No controlled fine-tuning transition**; different intervention (viewpoint); their "consistency≠grounding" is our ΔC-vs-ΔG dissociation family, but static |
| VisualFLIP | 2606.07872, Jun 2026 | 687 paired same-question minimal-edit image flips; Accp + Collapse Rate | Accp, CR | **Dataset still gated (401 on HF, checked 2026-08-14)**; evaluation-only, no adaptation analysis; our hflip is global reflection, not minimal local edit |
| CORAL (medical) | 2607.03647, Jul 2026 | Qwen2.5-VL-7B LoRA + Contrastive Grounding Objective; blank/shuffled/hard-neg | VRS, VHR | Introduces a new grounding-aware **training objective**; medical domain; no ordinary-fine-tuning audit |
| Med-OPD | 2607.16303, Jul 2026 | evidence-aware on-policy distillation for Med-VLMs | MEA token-level evidence dependence | Training-method paper; medical; not an audit |
| Evidence-RL (orchestrator-reported, Aug 8 2026) | not independently re-fetched (not in arXiv cs.CV search hits above) | RL rewarding causal reliance on local evidence | — | New RL objective, not an audit of ordinary fine-tuning |

Nothing found (searches: `visual reliance`/`evidence dependence` + cs.CV,
`visual grounding` + `fine-tuning` + cs.CV, both sorted by submission date)
does **our** experiment: treat an *ordinary* spatial task fine-tuning as the
controlled intervention and jointly measure ΔA (benchmark), ΔG
(correct-image dependence), ΔC (semantic pair consistency) and Tier-C
transformation behavior, with multiple fresh training seeds across two
backbone families.

## 2. Novelty boundary (what is NOT ours)

- Normal-minus-shuffle gap **G** is not novel: VRS in Beyond Accuracy 2026 is
  defined identically (A(real) − A(shuffle)).
- "Accuracy ≠ grounding" is established context (Beyond Accuracy, Seeing
  without Looking, VisualFLIP).
- "Consistency ≠ grounding" is established context (Consistent Yet Wrong /
  ViewDiag; also VisualFLIP's collapse rate).
- Shuffled images as a test are not novel.

## 3. Exact novelty sentence (frozen for the paper)

> Prior work establishes that benchmark accuracy can diverge from visual
> evidence reliance, including real/blank/shuffled auditing (Beyond Accuracy
> 2026), consistency-vs-grounding dissociations (Consistent Yet Wrong;
> VisualFLIP), and grounding-aware training objectives (CORAL). What has not
> been examined is whether **ordinary spatial task fine-tuning itself** —
> the standard LoRA recipe with no grounding-aware objective — moves
> benchmark accuracy, correct-image dependence, and semantic pair
> consistency as a *jointly measured vector of capability changes*, and
> whether those changes replicate across training seeds and backbone
> families. We provide the first controlled, multi-seed, cross-backbone
> study of that decomposition.

Scope guards (from CLAIM_HIERARCHY.md Tier-3, unchanged):
- No VisualFLIP reproduction claim (global reflection ≠ minimal local edit;
  our C_pair is a collapse-style paired answer-update metric *following*
  VisualFLIP, difference stated).
- No VRS/G novelty claim.
- Qwen3-VL-8B extension is post-confirmatory; only ΔA/ΔG/A_transform
  computed; no C_pair claim.

## 4. Claims numerically justified (audited, Step-1 PASS)

- ΔA positive across all fresh seeds, both confirmatory backbones. ✅
- ΔG positive across all fresh seeds, both confirmatory backbones. ✅
- Fresh-seed C_pair within 0.05 of legacy General (7B and 2B). ✅
- All fresh 2B hflip C_pair > 2B zero-shot. ✅
- Qwen3-VL supports only stated post-confirmatory quantities. ✅

## 5. Open items / re-check schedule

- VisualFLIP official dataset/harness: re-check HF `DidiZhu/VisualFLIP`
  weekly; if released before WACV deadline (Aug 28), optional bonus external
  validation (1 GPU-hour, ~$0.35; requires explicit compute unlock —
  currently GPU OFF).
- Re-run this audit if any of the above papers releases a v2/updated dataset
  before submission.
