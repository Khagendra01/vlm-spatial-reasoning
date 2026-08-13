# EquiOrient — Novelty Gate

**Date initialized:** 2026-08-10  
**Gate closed:** 2026-08-13  
**Status:** **CLOSED — MUTATE**  
**Search basis:** primary papers / official proceedings / arXiv / OpenReview only; 30 close or foundational works after deduplication.  

---

## 1. Gate question

> **Has relation-aware latent transformation equivariance for spatial VLM reasoning already been done closely enough that EquiOrient would be only a relabeling of prior work?**

### Gate answer

**No single paper found in this search implements the full conjunction required for EquiOrient, but the original novelty target is too broad and overlaps materially with several 2025–2026 VLM papers and with established equivariant-representation-learning literature.**

Therefore the correct gate outcome is **`MUTATE`**, not `PROCEED` and not `KILL`.

The project may proceed only under the narrower target defined in §2 and the redesigned pilot in §9. The protocol authority and machine-readable config must be amended to match this mutation before any EquiOrient GPU pilot is treated as confirmatory research.

---

## 2. Final mutated novelty target

### 2.1 Abandoned target

The following formulation is **not sufficiently distinctive** and is retired:

> “Learn a pair-conditioned spatial latent with a relation-dependent equivariance loss under transformed views.”

Why it is retired:

- latent spatial shaping inside VLMs already exists;
- representation-level geometric supervision inside VLMs already exists;
- continuous / object-centric spatial latent tokens already exist;
- view-consistency and transformation-based spatial VLM training already exist;
- latent group-action / equivariance learning is an established representation-learning problem.

### 2.2 New target

> **EquiOrient trains an answer-relevant object-pair spatial state to obey a predeclared heterogeneous transformation algebra. Rather than conditioning the action on the ground-truth relation label, known visual transformations act through fixed or tightly constrained geometry-derived operators on typed spatial-state components. The primary test is whether this structure improves generalization to held-out transformation compositions beyond matched augmentation, output-consistency, invariance, and wrong-geometry controls.**

Conceptually:

```text
z(x, a, b) = [z_h, z_v, z_d, z_pose, ...]

z(T(x), a, b) ~= rho(T) z(x, a, b)
```

where `rho(T)` is not an arbitrary high-capacity network and does not receive the true answer relation. It is a predeclared action derived from the geometry / coordinate semantics of `T`, with block actions that may differ across typed state components.

Examples:

- horizontal reflection acts non-trivially on the horizontal component and leaves guaranteed orthogonal components unchanged;
- vertical reflection acts non-trivially on the vertical component;
- their composition must agree with the product of the corresponding latent actions;
- invariant relation channels remain invariant under transformations that provably preserve them;
- object-local pose actions are deferred until their semantics are validated separately.

### 2.3 What must be new in the evidence, not merely the notation

The paper is not novel merely because it writes `rho(T)`.

The method contribution survives only if all of the following are true:

1. `z` is on the actual answer path, not an auxiliary probe the VLM can ignore;
2. `rho(T)` is predeclared / structurally constrained and does not encode the ground-truth answer;
3. the same paired training examples and compute are used for the critical baselines;
4. EquiOrient beats augmentation-only and output-consistency training on **held-out composition**, not only seen transforms;
5. a wrong-action / shuffled-transform control performs worse than the correct geometry action;
6. improved latent transformation fidelity is accompanied by improved paired task behavior;
7. later external validation tests whether the effect survives beyond the synthetic generator.

---

## 3. Search scope and interpretation rule

Search families covered:

- 2025–2026 VLM spatial reasoning / geometric supervision;
- VLM latent spatial representations and continuous spatial tokens;
- transformed-view / multi-view consistency training;
- viewpoint and reference-frame reasoning;
- explicit 3D / camera / world-model geometry injection;
- general equivariant representation learning;
- learned latent group actions / homomorphisms;
- equivariant language / vision-language-action models.

Important interpretation rule:

> **Novelty belongs to the conjunction of answer-path pair state + heterogeneous geometry-derived latent actions + held-out compositional generalization + matched causal controls. None of the individual primitives is claimed as new.**

No “first” claim is permitted from this gate alone. A fresh literature pass is required again immediately before submission.

---

## 4. 30-paper novelty matrix

Legend:

- **Level:** `OUT` output / reasoning level; `REP` representation level; `ARCH` architectural equivariance.
- **Action:** whether an explicit latent transformation/group action comparable to `rho(T)` is central.
- **Pair:** whether the representation is explicitly object-pair conditioned.
- **Comp:** whether held-out transformation composition / action sequence generalization is central.
- Risk is overlap risk for the **mutated** EquiOrient target, not a quality judgment about the cited work.

| # | Work | Venue/date | Core overlap | Level | Action | Pair | Comp | Remaining distinction for EquiOrient | Risk |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | [Uncovering and Shaping the Latent Representation of 3D Scene Topology in VLMs](https://arxiv.org/abs/2605.07148) | arXiv, May 2026 | isolates a causal spatial subspace; mathematically shapes it with Dirichlet-energy regularization; synthetic-to-real spatial gains | REP | no transform action | no | no | transformation algebra and composition rather than topology/smoothness | **VERY HIGH** |
| 2 | [GASP: Beyond 3D VQAs](https://openaccess.thecvf.com/content/CVPR2026/html/Yeh_Beyond_3D_VQAs_Injecting_3D_Spatial_Priors_into_Vision-Language_Models_CVPR_2026_paper.html) | CVPR 2026 | deep representation-level geometric supervision; correspondence view-invariance + depth consistency | REP | no explicit relation-state action | correspondence-level, not query pair state | no | relation-changing equivariance and composition rather than generic correspondence invariance | **VERY HIGH** |
| 3 | [Chain of Spatial Thoughts: Modality-Agnostic Spatial Grounding for VLMs](https://arxiv.org/abs/2608.10278) | arXiv, Aug 2026 | explicit continuous spatial representations; scene-level geometry + object-centric spatial attributes distilled into latent tokens used for reasoning | REP | no transformation algebra reported | object-centric | no | predeclared transform action and compositional generalization | **VERY HIGH** |
| 4 | [SAGE: Self-Evolving Spatial Reasoning via Geometric Logic Consistency](https://arxiv.org/abs/2605.18162) | arXiv, May 2026 | paired geometric / linguistic operations with predictable answer mappings; consistency reward in GRPO | OUT | no latent action | task relation pairs | unseen data, not latent composition | answer-path latent structural law rather than output duality consistency | **HIGH** |
| 5 | [SVQA-R1: Reinforcing Spatial Reasoning via View-Consistent Reward Optimization](https://openreview.net/forum?id=o2E8oa2frj) | ES-Reasoning @ ICLR 2026 | horizontal flips, in-plane rotations, perspective warps; rewards view-consistent answers/reasoning | OUT | no latent action | no explicit pair latent | no | internal structured action + composition rather than view-consistency reward | **HIGH** |
| 6 | [Think with 3D / 3DThinker](https://openaccess.thecvf.com/content/CVPR2026/html/Chen_Think_with_3D_Geometric_Imagination_Grounded_Spatial_Reasoning_from_Limited_CVPR_2026_paper.html) | CVPR 2026 | VLM-generated 3D latent aligned to a 3D foundation model, followed by outcome optimization | REP | no transformation algebra | no explicit relation-pair state | no | explicit pair transform law + held-out composition | **HIGH** |
| 7 | [The Dual Mechanisms of Spatial Reasoning in VLMs](https://arxiv.org/abs/2603.22278) | arXiv, Mar 2026 | identifies spatial representations in vision encoder / LM; causal interchange interventions; spatial-feature intervention improves accuracy | REP | intervention, not equivariance training | object-associated tokens | no | training a typed transform algebra rather than locating/amplifying existing signals | **HIGH** |
| 8 | [GeoWorld-VLM: Geometry from World Models for VLMs](https://arxiv.org/abs/2605.16713) | arXiv, May 2026 | aligns VLM visual features with camera-conditioned world-model spatial representations; improves VSR / What’sUp | REP | camera trajectory used by teacher, no latent group law | no explicit pair latent | no | explicit pair-state algebra and composition | **HIGH** |
| 9 | [Chain-of-Visual-Thought: Continuous Visual Tokens](https://arxiv.org/abs/2511.19418) | arXiv, Nov 2025 | VLM predicts compact continuous visual tokens distilled from depth/segmentation/edge/DINO experts | REP | no | no | no | relation-specific transform structure rather than dense perceptual token distillation | MEDIUM-HIGH |
| 10 | [Latent Implicit Visual Reasoning](https://openaccess.thecvf.com/content/CVPR2026/html/Li_Latent_Implicit_Visual_Reasoning_CVPR_2026_paper.html) | CVPR 2026 | learned task-adaptive latent visual reasoning tokens used inside LMM reasoning | REP | no | no | no | explicit geometric action and pair semantics | MEDIUM-HIGH |
| 11 | [STAR-R1](https://openaccess.thecvf.com/content/CVPR2026/html/Li_STAR-R1_Multi-View_Spatial_TrAnsformation_Reasoning_by_Reinforcing_Multimodal_LLMs_CVPR_2026_paper.html) | CVPR 2026 | multi-view transformation reasoning with process-SFT + referential-aware RL | OUT | no | referential reasoning, not explicit pair latent law | no | representation algebra and composition | MEDIUM-HIGH |
| 12 | [SpaceMind](https://openaccess.thecvf.com/content/CVPR2026/html/Zhao_SpaceMind_Camera-Guided_Modality_Fusion_for_Spatial_Reasoning_in_Vision-Language_Models_CVPR_2026_paper.html) | CVPR 2026 | camera-guided fusion of spatial and visual encoders | REP | camera-conditioned fusion, not group action | no | no | transformation-law learning rather than camera fusion | MEDIUM |
| 13 | [Learning Multi-View Spatial Reasoning from Cross-View Relations (XVR)](https://openaccess.thecvf.com/content/CVPR2026/html/Jeong_Learning_Multi-View_Spatial_Reasoning_from_Cross-View_Relations_CVPR_2026_paper.html) | CVPR 2026 | large cross-view relation dataset; VLM fine-tuning for correspondence / verification / localization | OUT/REP | no | cross-view objects | no | structural objective rather than dataset-scale supervision | MEDIUM |
| 14 | [G²VLM](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_G2VLM_Geometry_Grounded_Vision_Language_Model_with_Unified_3D_Reconstruction_CVPR_2026_paper.html) | CVPR 2026 | jointly learns 3D reconstruction and spatial reasoning from multi-view/video data | REP | no explicit latent action | no | no | pairwise transform algebra rather than unified reconstruction | MEDIUM |
| 15 | [Learning to Reason in 4D](https://openaccess.thecvf.com/content/CVPR2026/html/Zhou_Learning_to_Reason_in_4D_Dynamic_Spatial_Understanding_for_Vision_CVPR_2026_paper.html) | CVPR 2026 | camera poses, point clouds, object orientations/trajectories; geometry-token selection for dynamic spatial reasoning | REP | geometry metadata, not latent action law | object-level | viewpoint transformations in data, not algebra test | static typed action/composition first | MEDIUM |
| 16 | [Grounded 3D-Aware Spatial Vision-Language Modeling (GR3D)](https://openaccess.thecvf.com/content/CVPR2026/html/Cheng_Grounded_3D-Aware_Spatial_Vision-Language_Modeling_CVPR_2026_paper.html) | CVPR 2026 | explicit/implicit 2D grounding + monocular 3D grounding; region tokens enter spatial CoT | REP | no | region/entity grounded | no | transform algebra rather than grounding architecture | MEDIUM |
| 17 | [Perspective-Aware Reasoning via Mental Imagery Simulation](https://openaccess.thecvf.com/content/ICCV2025/html/Lee_Perspective-Aware_Reasoning_in_Vision-Language_Models_via_Mental_Imagery_Simulation_ICCV_2025_paper.html) | ICCV 2025 | scene abstraction + explicit perspective-change simulation using external vision tools | OUT / symbolic | explicit simulation, not learned latent group action | object-centric abstraction | no | learned answer-path state rather than inference-time simulation | MEDIUM |
| 18 | [Keep it SymPL](https://openaccess.thecvf.com/content/CVPR2026/html/Jang_Keep_it_SymPL_Symbolic_Projective_Layout_for_Allocentric_Spatial_Reasoning_CVPR_2026_paper.html) | CVPR 2026 | symbolic projective layouts for egocentric/allocentric reasoning | OUT / symbolic | symbolic projective transform | object-layout | no | learned latent transformation structure | MEDIUM |
| 19 | [Thinking with Blueprints](https://openaccess.thecvf.com/content/CVPR2026F/html/Ma_Thinking_with_Blueprints_Assisting_Vision-Language_Models_in_Spatial_Reasoning_via_CVPRF_2026_paper.html) | CVPR Findings 2026 | object-centric structured blueprint + blueprint-aware reward + anti-shortcut augmentation | OUT / structured | no | object-centric | no | continuous answer-path equivariant state and composition | MEDIUM |
| 20 | [Consistent Yet Wrong](https://arxiv.org/abs/2606.02742) | CVPRW 2026 | multi-view evidence-sensitivity audit + latent probe; consistency can coexist with wrong answers | REP diagnostic | no | object-pair tracks | no | training structural equivariance rather than diagnosing collapse | MEDIUM |
| 21 | [Large Language-Geometry Model / EquiLLM](https://arxiv.org/abs/2502.11149) | arXiv, Feb 2025 | explicit E(3)-equivariant encoder/adaptor around an LLM for physical 3D systems | ARCH | yes, architectural E(3) equivariance | graph/physical entities | group structure built in | VLM image reasoning + pair semantic state, not physical-system prediction | **HIGH conceptual** |
| 22 | [Toward Embodiment Equivariant Vision-Language-Action Policy](https://arxiv.org/abs/2509.14630) | arXiv, Sep 2025 | formulates VLA policy equivariance to embodiment configuration transforms; equivariant action decoder | ARCH/OUT | yes | robot/action state | configuration generalization | spatial relation-state equivariance rather than policy/action-space equivariance | MEDIUM-HIGH |
| 23 | [Homomorphism AutoEncoder](https://proceedings.mlr.press/v202/keurti23a.html) | ICML 2023 | autoencoder with latent group representation; equivariance-derived homomorphism loss; predicts sequences of actions | REP | **yes** | no | **yes, action sequences** | apply a constrained typed action to answer-relevant VLM pair states and demonstrate behavioral benefit | **VERY HIGH mathematical** |
| 24 | [Equivariance by Contrast](https://openreview.net/forum?id=kvI0QTVRQD) | NeurIPS 2025 | jointly learns latent embedding and invertible linear group representation from transformed pairs; identifiability result | REP | **yes** | no | group operations evaluated | VLM spatial semantics / answer-path pair state / heterogeneous relation channels | **VERY HIGH mathematical** |
| 25 | [Learning Group Actions on Latent Representations](https://proceedings.neurips.cc/paper_files/paper/2024/hash/e63309e532688c722177f81e99f94f32-Abstract-Conference.html) | NeurIPS 2024 | learns group actions directly in autoencoder latent space | REP | **yes** | no | group-action generalization | VLM spatial reasoning and fixed geometry-derived semantic action | HIGH mathematical |
| 26 | [Equivariant Representation Learning via Class-Pose Decomposition](https://proceedings.mlr.press/v206/marchetti23b.html) | AISTATS 2023 | latent decomposed into invariant class + symmetry-group pose; relative-symmetry supervision | REP | yes | no | symmetry generalization | object-pair VLM state and downstream spatial reasoning | HIGH mathematical |
| 27 | [Self-supervised Transformation Learning for Equivariant Representations](https://proceedings.neurips.cc/paper_files/paper/2024/hash/972cd27c994a806e187ef1c2f5254059-Abstract-Conference.html) | NeurIPS 2024 | learns transformation representations from image pairs and corresponding equivariant representations | REP | learned transform representation | no | complex transforms tested | typed VLM relation-state algebra and behavioral composition | MEDIUM-HIGH |
| 28 | [Unsupervised Learning of Group Invariant and Equivariant Representations](https://proceedings.neurips.cc/paper_files/paper/2022/hash/cf3d7d8e79703fe947deffb587a83639-Abstract-Conference.html) | NeurIPS 2022 | separates invariant latent term and equivariant group-action component | REP | yes | no | general groups | VLM relation semantics / answer pathway / matched spatial task baselines | MEDIUM-HIGH |
| 29 | [Learning Disentangled Representations and Group Structure of Dynamical Environments](https://proceedings.neurips.cc/paper_files/paper/2020/hash/e449b9317dad920c0dd5ad0a2a2d5e49-Abstract.html) | NeurIPS 2020 | learns group-structured latent transformations from sequential interactions | REP | yes | no | long-horizon prediction | VLM pairwise spatial reasoning and known typed geometry | MEDIUM |
| 30 | [Transformation Properties of Learned Visual Representations](https://arxiv.org/abs/1412.7659) | arXiv 2014 | argues good visual latents should transform linearly under scene motions; uses group-representation theory | REP/theory | yes conceptually | no | not VLM task composition | modern VLM answer-path intervention and empirical method comparison | FOUNDATIONAL |

### Foundational architecture context (not counted as a close-paper threat)

Classical equivariant architectures already establish that group representations and transform laws themselves are not novel primitives: [Group Equivariant CNNs](https://proceedings.mlr.press/v48/cohenc16.html) (ICML 2016), [3D Steerable CNNs](https://proceedings.neurips.cc/paper/2018/hash/488e4104520c6aab692863cc1dba45af-Abstract.html) (NeurIPS 2018), and [General E(2)-Equivariant Steerable CNNs](https://proceedings.neurips.cc/paper/2019/hash/45d6637b718d0f24a237069fe41b0db4-Abstract.html) (NeurIPS 2019).

---

## 5. Top-5 threat matrix

### Threat 1 — Wang & Gao 2026: latent spatial shaping in VLMs

**Paper:** [Uncovering and Shaping the Latent Representation of 3D Scene Topology in Vision-Language Models](https://arxiv.org/abs/2605.07148)

| Dimension | Prior work | Mutated EquiOrient |
|---|---|---|
| VLM spatial reasoning | yes | yes |
| internal spatial representation | yes; isolated causal spatial subspace | yes; explicit pair state on answer path |
| mathematical structural prior | Laplacian-eigenmap interpretation + Dirichlet-energy regularizer | geometry-derived transformation action |
| synthetic training | yes | yes |
| real benchmark transfer | yes | required after internal freeze |
| explicit transform action | no | **yes** |
| held-out composition | no | **primary** |
| matched augmentation / output-consistency / wrong-action controls | not the central design | **mandatory** |

**Exact distinction sentence:**

> Wang & Gao shape a topology-preserving spatial subspace with a Dirichlet-energy objective; EquiOrient instead tests whether an answer-path object-pair state can be trained to obey a predeclared transformation algebra whose composition predicts behavior on unseen interventions.

**Threat consequence:** EquiOrient may not claim first spatial latent discovery, first causal spatial subspace, first mathematical latent shaping, or first synthetic-to-real latent regularization for VLM spatial reasoning.

---

### Threat 2 — GASP: representation-level geometric supervision

**Paper:** [Beyond 3D VQAs: Injecting 3D Spatial Priors into VLMs](https://openaccess.thecvf.com/content/CVPR2026/html/Yeh_Beyond_3D_VQAs_Injecting_3D_Spatial_Priors_into_Vision-Language_Models_CVPR_2026_paper.html)

| Dimension | GASP | Mutated EquiOrient |
|---|---|---|
| VLM internal representation supervision | yes | yes |
| geometry source | point correspondence + depth | controlled transform algebra |
| principal structural property | correspondence view-invariance + depth consistency | heterogeneous equivariance / invariance by state component |
| layer integration | deep supervision across transformer layers | pair state on answer path |
| held-out composition algebra | not central | **primary** |
| wrong-geometry control | not central | **mandatory** |

**Exact distinction sentence:**

> GASP injects fundamental geometric priors by enforcing correspondence invariance and depth consistency; EquiOrient asks whether relation-relevant state components should transform non-uniformly under the same intervention and whether the resulting algebra composes on unseen transformations.

**Threat consequence:** “representation-level geometry supervision for spatial VLMs” is not a novelty claim.

---

### Threat 3 — Chain of Spatial Thoughts / Space Tokens

**Paper:** [Chain of Spatial Thoughts: Modality-Agnostic Spatial Grounding for Vision Language Models](https://arxiv.org/abs/2608.10278)

| Dimension | Space Tokens | Mutated EquiOrient |
|---|---|---|
| explicit continuous spatial representation | yes | yes |
| object-centric spatial attributes | yes | yes / pair-conditioned |
| representation used during reasoning | yes | **required** |
| decodability / interpretability | yes | secondary |
| explicit geometric transform action | not reported as central | **yes** |
| unseen action composition | not reported as central | **primary** |

**Exact distinction sentence:**

> Space Tokens distill scene geometry and object-centric spatial attributes into continuous latent tokens for reasoning; EquiOrient does not claim spatial tokens themselves as new, but constrains a query pair state to follow known transformation operators and evaluates unseen operator composition.

**Threat consequence:** no “first continuous spatial token / first object-centric spatial latent in a VLM” claim.

---

### Threat 4 — Homomorphism AutoEncoder

**Paper:** [Homomorphism AutoEncoder — Learning Group Structured Representations from Observed Transitions](https://proceedings.mlr.press/v202/keurti23a.html)

| Dimension | HAE | Mutated EquiOrient |
|---|---|---|
| latent group representation | yes | uses known / constrained spatial action |
| equivariance-derived loss | yes | yes |
| homomorphism / composition | yes | **yes; central evaluation** |
| learns action group | yes | does **not** claim this; geometry action is predeclared |
| VLM / language semantics | no | yes |
| answer relevance | reconstruction / transition prediction | pair state is on final-answer pathway |
| heterogeneous natural-language relation semantics | no | yes, through typed spatial state rather than one universal relation group |

**Exact distinction sentence:**

> HAE already establishes latent group-representation learning and homomorphism-based compositional structure; EquiOrient’s contribution must therefore be the VLM-specific question of whether a constrained spatial action on an answer-relevant object-pair state improves compositional spatial reasoning beyond matched behavioral training baselines.

**Threat consequence:** no first claim for latent group actions, homomorphism losses, or compositional equivariant representation learning.

---

### Threat 5 — SAGE / geometric duality consistency

**Paper:** [Self-Evolving Spatial Reasoning in Vision Language Models via Geometric Logic Consistency](https://arxiv.org/abs/2605.18162)

| Dimension | SAGE | Mutated EquiOrient |
|---|---|---|
| paired transformations with predictable answer law | yes | yes |
| spatial VLM training | yes | yes |
| consistency objective | output / reward level | matched baseline only |
| representation transformation law | no explicit latent action reported | **central** |
| composition of latent actions | no | **primary** |
| wrong-action causal control | no | **mandatory** |

**Exact distinction sentence:**

> SAGE trains VLMs to remain logically consistent under paired geometric and linguistic operations; EquiOrient treats such output consistency as a baseline and asks whether enforcing the corresponding structure on the answer-path spatial state yields additional generalization to transformations never trained jointly.

**Threat consequence:** transformation-pair consistency is not EquiOrient’s novelty.

---

## 6. Why the project is not killed

The fatal-overlap criterion required a prior work to cover most of this conjunction:

1. spatial VLM reasoning;
2. answer-relevant object-pair spatial state;
3. explicit geometry-derived action on that state;
4. direct representation-level equivariance constraint;
5. matched augmentation and output-consistency baselines;
6. wrong-geometry control;
7. held-out transformation **composition** as primary evidence;
8. downstream paired spatial correctness tied to the latent structure.

**No paper in the 30-work matrix was found to satisfy this conjunction.**

However, each individual primitive is heavily occupied. The method is viable only if it proves that the *structural action itself* contributes beyond the neighboring alternatives.

---

## 7. Final allowed and forbidden claims

### Allowed novelty claim

Use a claim of this form only if the experiments support it:

> **We study whether an answer-relevant object-pair spatial state in a VLM can be trained to obey predeclared heterogeneous geometric transformation actions. Under matched paired data and compute, we test whether this representation-level constraint provides compositional generalization beyond augmentation, output-consistency, invariance, and wrong-action controls.**

A stronger results-dependent claim may be made only after the method beats the matched controls on held-out composition and external transfer is characterized.

### Allowed framing

- structured transformation algebra for an answer-path pair state;
- heterogeneous equivariance rather than universal invariance;
- known geometry acting on typed spatial state components;
- compositional generalization as evidence of learned structure;
- causal usefulness of the pair state if ablation / patching supports it;
- relation-family boundaries and null results where the algebra does not transfer.

### Forbidden claims

Do **not** claim any of the following:

- first spatial latent representation in a VLM;
- first object-centric / continuous spatial token in a VLM;
- first representation-level spatial intervention in a VLM;
- first latent spatial regularization for VLM reasoning;
- first geometric-prior training for VLM spatial reasoning;
- first view-consistent / transformation-consistent spatial VLM training;
- first latent equivariance or group-action representation learning;
- first homomorphism / composition loss in representation learning;
- first equivariant language model / first language model using equivariance;
- first multi-view / viewpoint-aware spatial reasoning method;
- that natural-language spatial relations collectively form one mathematical group;
- that `rho(T)` may receive the ground-truth answer relation without an explicit leakage analysis;
- that lower latent equivariance error alone proves improved reasoning;
- that an auxiliary equivariant head ignored by the answer pathway constitutes mechanistic improvement;
- any universal claim about VLM spatial intelligence from synthetic-only evidence.

### Firstness rule

No “first” wording enters an abstract, introduction, or contribution list without a fresh pre-submission search. This gate establishes a **defensible difference**, not historical firstness.

---

## 8. Required method mutation before GPU work

The old notation `rho_r(T)` is potentially misleading because conditioning directly on the ground-truth relation may leak answer semantics and because the full natural-language relation set does not form one clean transformation group.

The implementation must instead satisfy these constraints:

### 8.1 Typed pair state

Start with a deliberately small state:

```text
z(x,a,b) = [z_horizontal, z_vertical, z_invariant]
```

The first pilot need not include depth or intrinsic pose. Add those only after their transformation semantics are independently validated.

### 8.2 Fixed / tightly constrained action

Use predeclared low-capacity operators for the pilot, preferably fixed orthogonal / sign / permutation block actions. Do not begin with a flexible MLP `rho` capable of memorizing pair mappings.

The action gets:

- transform identity / parameters;
- state-component type implied by the frozen algebra.

The action does **not** get:

- ground-truth answer label;
- original relation token as a shortcut to the target answer;
- test-set-specific parameters.

### 8.3 Answer-path requirement

`z` must participate in the computation producing the final answer. At minimum, the pair state must be injected as a token / residual / adapter feature consumed by the answer pathway.

A post-hoc probe is insufficient.

### 8.4 Causal usefulness check

After training:

- zero or corrupt `z`;
- optionally swap `z` between matched counterfactual pairs;
- measure whether the claimed behavioral gain degrades predictably.

If the model ignores `z`, the method claim fails even if latent equivariance error is low.

---

## 9. Redesigned 24–48 h falsification pilot

This pilot replaces the broader pilot in the original study plan. It is intentionally small and hostile to the hypothesis.

### 9.1 Pilot purpose

Test one question only:

> **Does correct latent transformation structure provide a measurable advantage on an unseen composition that cannot be explained by seeing transformed data, answer-consistency training, generic invariance, or generic regularization?**

### 9.2 No GPU until three CPU / engineering gates pass

Before the pilot:

1. **Transformation-algebra gate** — machine-readable `rho` tables; identity, inverse, and composition unit tests all pass.
2. **Synthetic-data gate** — labels are exact; split is by underlying scene seed; at least 50 stratified pairs are manually checked.
3. **Representation-feasibility gate** — one modern open VLM exposes a stable pair-feature path and the proposed `z` is verified to enter the answer pathway.

The exact backbone revision is frozen only after Gate 3. Model size is not a novelty variable.

### 9.3 Pilot relation families

Use only three behaviors whose transformation laws are unambiguous:

1. **horizontal:** left / right;
2. **vertical:** above / below;
3. **global-transform invariant:** parallel / perpendicular in controlled synthetic geometry.

Do **not** put facing/facing-away into the first pilot. Object-local orientation is scientifically important but introduces extra pose/semantic complexity; it becomes a second-stage test only after the simple algebra works.

### 9.4 Pilot transformations

Define two generators:

```text
H = horizontal reflection
V = vertical reflection
```

Training may contain `H` and `V` individually.

The key held-out test is their composition:

```text
C = V ∘ H   # equivalent to 180-degree planar rotation for the controlled scene
```

No training example is presented under `C` as a composed transformation.

Required algebra:

```text
rho(I) = I
rho(H)^2 = I
rho(V)^2 = I
rho(V ∘ H) = rho(V) rho(H)
```

The synthetic generator must validate the corresponding truth-label action independently of the learned model.

### 9.5 Pilot pair state and action

Minimal conceptual state:

```text
z = [z_h, z_v, z_inv]
```

Example pilot action behavior:

```text
rho(H): non-trivial action on z_h; identity on z_v and z_inv
rho(V): identity on z_h; non-trivial action on z_v; identity on z_inv
rho(VH): rho(V) @ rho(H)
```

The exact dimensionality and matrix form are frozen in the protocol amendment before training.

### 9.6 Matched training conditions

All critical conditions use the **same paired scenes, same number of sample presentations, same optimizer budget, same backbone, and same answer supervision**.

Run:

```text
A. ordinary SFT/LoRA compute-matched control
B. paired transformation augmentation only
C. output-consistency training on the paired views
D. latent-invariance control: z(Tx) ~= z(x)
E. EquiOrient: z(Tx) ~= rho(T) z(x)
F. wrong-geometry control: same latent loss, but a frozen incorrect/shuffled rho mapping
```

Condition F is mandatory. If F matches E, the result is generic latent regularization, not evidence for the geometric action.

### 9.7 Loss contract

For EquiOrient:

```text
L = L_task + lambda_equiv * L_equiv
L_equiv = d(z(Tx,a,b), rho(T) z(x,a,b))
```

`lambda_equiv` must be selected using validation data under a predeclared rule. No test-set lambda sweep.

The augmentation and consistency conditions receive the same paired examples and compute; only the structural loss differs.

### 9.8 Primary pilot metrics

Primary:

1. **held-out-composition task accuracy** on `C`;
2. **held-out-composition both-correct rate** for original + `C` pair;
3. **composition equivariance error**
   `d(z(Cx), rho(V)rho(H)z(x))`;
4. EquiOrient minus the strongest of B/C/D/F on metrics 1–3.

Secondary:

- seen-H and seen-V accuracy;
- ordinary untransformed accuracy;
- expected-change / expected-invariance rates by relation family;
- invalid output rate;
- representation collapse diagnostics (norm / variance / rank);
- answer-path `z` ablation / corruption effect.

### 9.9 Pilot go / mutate / kill rule

This is a **one-seed falsification pilot**, not final evidence about training robustness.

`PROCEED_TO_MAIN` requires all of:

1. EquiOrient improves held-out-composition both-correct rate by at least **3 absolute percentage points** over the strongest matched B/C/D/F baseline;
2. paired example bootstrap CI for that pilot difference is directionally positive (used only as a pilot stability check, not a multi-seed robustness claim);
3. held-out composition equivariance error is at least **20% lower** than augmentation-only **and** wrong-geometry control;
4. ordinary untransformed accuracy is not degraded by more than **2 pp** relative to the best matched task baseline;
5. wrong-geometry control does not reproduce the EquiOrient task gain;
6. corrupting / ablating `z` measurably removes the EquiOrient advantage.

`MUTATE` if the latent structural metric improves but behavioral composition does not, or if the answer-path dependency is weak but nonzero.

`KILL_METHOD_CLAIM` if any of:

- augmentation/output consistency matches EquiOrient on held-out composition;
- wrong `rho` matches correct `rho`;
- only seen transforms improve;
- `z` can be removed without changing the gain;
- the representation collapses to a trivial low-information solution;
- transformation labels/actions cannot be validated exactly.

No extra backbone, relation family, or transform is added merely because the pilot is unfavorable.

### 9.10 After a successful pilot

Only then:

1. freeze the confirmatory protocol;
2. run multiple training seeds for EquiOrient and the strongest matched baselines;
3. add harder transformation classes (including object-local pose only after semantic validation);
4. test held-out relation transfer where the action structure is genuinely shared;
5. run external real/rendered benchmark transfer;
6. evaluate general-capability preservation;
7. perform hostile novelty / geometry / statistics review again.

---

## 10. Final novelty verdict

# `MUTATE`

### Why not `KILL`

No searched work was found to combine VLM spatial reasoning, an answer-path object-pair state, explicit geometry-derived state actions, matched augmentation/output-consistency/wrong-action controls, and held-out transformation composition as the primary behavioral test.

### Why not `PROCEED` unchanged

The original target overlaps too broadly with:

- VLM latent spatial shaping;
- VLM continuous spatial tokens;
- deep geometric representation supervision;
- transformed-view consistency training;
- established latent group-action / equivariant representation learning.

### Final project boundary

EquiOrient is permitted to proceed only as:

> **A controlled test of whether a typed, answer-relevant object-pair spatial state that obeys the correct predeclared transformation algebra yields compositional spatial generalization beyond matched behavioral and wrong-geometry controls.**

The novelty is the **specific structural hypothesis plus the hostile evidence design**, not “equivariance,” “spatial latents,” “transform training,” or “group actions” individually.

### Governance consequence

Gate 0 is closed. Because the verdict is `MUTATE`, the following must happen before the first GPU pilot:

- append the mutation to `EQUIORIENT_DECISION_LOG.md`;
- amend `EQUIORIENT_PROTOCOL_FREEZE.md` and `configs/equiorient_protocol.yaml` to replace ground-truth-relation-conditioned `rho_r(T)` with the typed geometry-action formulation;
- freeze the H/V/composition pilot algebra and wrong-geometry control;
- pass the CPU algebra, data, and representation-feasibility gates.

Until those protocol amendments are committed, **GPU training remains non-confirmatory and should not start**.
