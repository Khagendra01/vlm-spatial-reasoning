# EquiOrient — Novelty Gate

**Date initialized:** 2026-08-10  
**Status:** OPEN — project may not proceed to confirmatory training until this gate is closed.  

---

## 1. Gate question

> **Has relation-aware latent transformation equivariance for spatial VLM reasoning already been done closely enough that EquiOrient would be only a relabeling of prior work?**

The project proceeds only if the answer is **no**, with a precise novelty boundary.

---

## 2. Current novelty target

The intended novelty is **not** generic view consistency, data augmentation, geometric priors, multi-view reasoning, or output-level transformation consistency.

The target is:

> **A pair-conditioned spatial latent `z(x,a,b)` with an explicit relation-dependent transformation action `ρ_r(T)` such that training directly constrains `z(T(x),a,b) ≈ ρ_r(T) z(x,a,b)`, and evaluation tests whether this structure transfers to held-out transforms / relation families beyond matched augmentation and output-consistency baselines.**

This target must remain differentiable from all close prior work below.

---

## 3. Close prior work identified in the initial search

### SVQA-R1 — Reinforcing Spatial Reasoning in MLLMs via View-Consistent Reward Optimization

- Source: OpenReview, ES-Reasoning @ ICLR 2026.
- Core method: Spatial-GRPO with rewards for consistent answers/reasoning across perturbed views.
- Perturbations include horizontal flipping plus 2D in-plane rotation / perspective warping.
- **Overlap risk:** very high for any EquiOrient version framed as “train on transformations / enforce view consistency.”
- **Required distinction:** EquiOrient must supervise transformation structure **inside a learned spatial latent**, not only output/reasoning consistency.

### SAGE — Self-Evolving Spatial Reasoning in Vision Language Models via Geometric Logic Consistency

- Source: arXiv:2605.18162.
- Core method: GRPO with geometric and linguistic duality consistency; dynamic operation pool.
- **Overlap risk:** high for generic complement/duality consistency.
- **Required distinction:** explicit latent transformation action and held-out transformation fidelity.

### GASP — Beyond 3D VQAs: Injecting 3D Spatial Priors into Vision-Language Models for Enhanced Geometric Reasoning

- Source: CVPR 2026.
- Core method: geometric priors injected into transformer layers; contrastive point-correspondence objective enforces 2D view-invariance; depth consistency supervision.
- **Overlap risk:** high for representation-level view-invariance / geometry supervision.
- **Required distinction:** relation-conditioned **equivariance** (state changes predictably when relation changes), not generic correspondence invariance; pairwise relation structure and transformation-law generalization must be central.

### STAR-R1 — Multi-View Spatial TrAnsformation Reasoning by Reinforcing Multimodal LLMs

- Source: CVPR 2026.
- Core method: process-supervised SFT + referential-aware RL for multi-view transformation reasoning.
- **Overlap risk:** medium-high for generic multi-view transformation learning.
- **Required distinction:** latent representation law rather than CoT/RL trajectory optimization.

### SpaceMind — Camera-Guided Modality Fusion for Spatial Reasoning in Vision-Language Models

- Source: CVPR 2026.
- Core method: camera-conditioned fusion of spatial and visual encoders.
- **Overlap risk:** medium for viewpoint-aware representations.
- **Required distinction:** EquiOrient is not merely camera conditioning and should work with explicit transformation algebra.

### Perspective-Aware Reasoning in VLMs via Mental Imagery Simulation

- Source: ICCV 2025.
- Core method: scene abstraction plus perspective-change simulation using detection / segmentation / orientation estimation.
- **Overlap risk:** medium for perspective-transform reasoning.
- **Required distinction:** learned latent equivariance vs inference-time scene abstraction/simulation.

### Keep it SymPL — Symbolic Projective Layout for Allocentric Spatial Reasoning

- Source: CVPR 2026.
- Core method: projective symbolic layouts for allocentric/egocentric reasoning.
- **Overlap risk:** medium for reference-frame transformations.
- **Required distinction:** latent transformation law vs symbolic reformulation.

### Learning Multi-View Spatial Reasoning from Cross-View Relations (XVR)

- Source: CVPR 2026.
- Core method: large cross-view relation training dataset for correspondence, verification, localization.
- **Overlap risk:** medium for multi-view training/data.
- **Required distinction:** structural objective rather than dataset scale.

### Learning to Reason in 4D — Dynamic Spatial Understanding for VLMs

- Source: CVPR 2026.
- Core method: 4D-aware data + geometry selection module using camera poses, point clouds, object orientations and trajectories.
- **Overlap risk:** medium if EquiOrient drifts into dynamic 3D/4D geometry injection.
- **Required distinction:** static/controlled transformation algebra first; dynamic world-state modeling belongs to a later paper unless necessary.

### G²VLM — Geometry Grounded Vision Language Model with Unified 3D Reconstruction and Spatial Reasoning

- Source: CVPR 2026.
- **Overlap risk:** medium for explicit geometry-grounded VLMs.
- **Required distinction:** relation transformation law and equivariance, not unified reconstruction.

### The Dual Mechanisms of Spatial Reasoning in Vision-Language Models

- Source: arXiv:2603.22278.
- Core finding: vision encoder spatial layout signals plus language-backbone relation representations; intervention on vision-derived features improves reasoning.
- **Overlap risk:** medium-high for claims about where spatial representations live.
- **Required distinction:** do not claim first mechanistic spatial representation intervention; test a different structural property: transformation equivariance.

---

## 4. Search expansion required before gate closure

Search at minimum:

- `equivariant vision-language model spatial reasoning`
- `SE(2) SE(3) equivariant multimodal transformer language`
- `group equivariant VLM`
- `latent equivariance multimodal spatial reasoning`
- `equivariant representation learning vision language`
- `relation equivariance spatial VLM`
- `transformation equivariance LLM vision spatial`
- `camera equivariant multimodal reasoning`
- `object pose equivariance VLM`
- `viewpoint equivariance vision-language`
- `spatial representation group action multimodal`

Search sources:

- arXiv
- OpenReview
- CVF Open Access
- PMLR
- ACL Anthology
- robotics venues (CoRL, RSS, ICRA, IROS)
- NeurIPS / ICML / ICLR proceedings

Also search 3D vision literature even if it is not VLM-specific. An older equivariant representation method could invalidate method novelty if we simply attach language supervision to it.

---

## 5. Novelty matrix fields

For every close paper record:

```text
citation
publication status / date
research question
backbone / architecture
what transforms are used
whether transform metadata is known
training objective
representation-level or output-level
invariance or equivariance
whether action rho(T) is explicit
object-pair conditioned or global
seen-transform evaluation
unseen-transform evaluation
held-out relation transfer
spatial benchmarks
main claim
exact overlap with EquiOrient
remaining distinction
risk: low / medium / high / fatal
```

---

## 6. Fatal overlap criteria

EquiOrient must be killed or substantially redesigned if a prior paper already does all or most of:

1. VLM spatial reasoning;
2. pair-conditioned or relation-specific latent representation;
3. explicit known transformation action on that latent;
4. direct equivariance loss rather than only answer consistency;
5. comparison against matched augmentation / consistency baselines;
6. held-out transformation generalization;
7. similar target relations (orientation/reference-frame reasoning).

A different model name or dataset does not rescue novelty.

---

## 7. Non-fatal overlap

The following are expected and acceptable if clearly cited:

- view augmentation;
- multi-view spatial datasets;
- answer-consistency rewards;
- camera embeddings;
- contrastive correspondence invariance;
- object-pair feature extraction;
- standard equivariant neural-network mathematics;
- ordinary LoRA/SFT/RL.

Novelty must come from the **specific structural learning question and evidence**, not from claiming these primitives are new.

---

## 8. Gate-closing deliverable

Before implementation, add a section titled `FINAL NOVELTY VERDICT` containing:

- at least 20 closest papers after deduplication;
- top 5 threat papers with side-by-side method comparison;
- exact sentence defining what EquiOrient does that each top threat does not;
- a yes/no decision: `PROCEED`, `MUTATE`, or `KILL`;
- the final allowed novelty claim;
- the final forbidden claims.

Until that exists, **no full GPU training is confirmatory research**.
