# Novelty Audit — literature-positioning pass for the WACV 2027 submission

Date: 2026-08-10. Scope: strengthen Related Work / novelty positioning before
submission. No models rerun, no prediction CSVs or frozen metrics changed,
`paper-freeze-v1` untouched. Every new citation was verified from a primary
source before inclusion (arXiv API metadata, PMLR proceedings, CVF open access,
DBLP).

## Verified close prior works

### 1. AdaptVis — "Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective on Focus Areas"
- Research question: why do VLMs fail on simple spatial relations; attention-level
  mechanistic diagnosis on VSR-type tasks.
- Verification: arXiv:2503.01773 (v3); **ICML 2025 confirmed** — title found in
  PMLR v267 proceedings (https://proceedings.mlr.press/v267/); authors: Shiqi
  Chen, Tongyao Zhu, Ruochen Zhou, Jinghan Zhang, Siyang Gao, Juan Carlos
  Niebles, Mor Geva, Junxian He, Jiajun Wu, Manling Li.
- Overlap: same benchmark family (VSR), same question class (why spatial
  reasoning fails); attention-localization diagnosis.
- Already known: attention misalignment with object locations correlates with
  spatial failure.
- What remains distinct in our work: decodability under frozen-feature readouts
  (pooled/patch-vote/object-grounded), component-adaptation interventions,
  complementary-relation consistency, label sensitivity, and VSR→SITE transfer —
  a diagnostic ladder rather than attention tracing.

### 2. "When More Is Less: A Systematic Analysis of Spatial and Commonsense Information for Visual Spatial Reasoning"
- Research question: when does injecting spatial cues / commonsense / CoT into
  VSR prompts help or hurt.
- Verification: arXiv:2602.21619 (v1, Feb 2026; "Under review"); authors Muku
  Akasaka, Soyeon Caren Han.
- Overlap: VSR + prompting interventions; our structured-prompt negative result
  is in this family.
- Already known: extra information can hurt, depending on model/setup.
- Distinct: we do not claim prompting generally fails; we cite this work to
  contextualize the tested-2B-condition negative result.

### 3. "Probing Visual Concepts in Lightweight Vision-Language Models for Automated Driving"
- Research question: are specific visual concepts linearly decodable from VLM
  intermediate activations (automated-driving domain)?
- Verification: arXiv:2603.06054 (Mar 2026); journal_ref on arXiv:
  **Transactions on Machine Learning Research, 2026**. Authors: Nikos
  Theodoridis, Reenu Mohandas, Ganesh Sistu, Anthony Scanlan, Ciarán Eising,
  Tim Brophy.
- Overlap: linear decodability probing of VLM representations (incl.
  orientation-relevant concepts).
- Already known: concept decodability varies and can identify information-flow
  bottlenecks.
- Distinct: we probe VSR's orientation relation family with pooled, patch-vote,
  and object-grounded readouts over the exact conditioning features of the
  generative model, and pair decodability with adaptation/consistency
  interventions; we explicitly disclaim firstness of orientation probing.

### 4. CREG — "Compass Relational Evidence Graph for Characterizing Directional Structure in VLM Spatial-Reasoning Attribution"
- Research question: is attribution evidence in Qwen2-VL organized by the
  queried spatial relation (directional structure)?
- Verification: arXiv:2603.20475 (v4, Mar 2026); authors Kaizhen Tan, Yang Feng,
  Heqing Du.
- Overlap: same model family (Qwen2-VL), spatial benchmarks, directional/
  orientation evidence.
- Already known: heatmaps often reflect image layout rather than relation
  structure; compass-aligned readouts quantify this.
- Distinct: we measure decodability under frozen readouts + test whether
  adaptation changes it + complementary-relation consistency + transfer; we
  explicitly state we are not the first to inspect directional information in
  Qwen2-VL.

### 5. "Mind the Gap: Benchmarking Spatial Reasoning in Vision-Language Models"
- Verification: arXiv:2503.19707 (Mar 2025); authors Ilias Stogiannidis,
  Steven McDonagh, Sotirios A. Tsaftaris. **NOTE: the submitted title differs
  from the one provided ("Diagnosing Spatial Reasoning Failures"); the verified
  public title is "Benchmarking Spatial Reasoning in Vision-Language Models".**
  DBLP lists it as CoRR preprint only; not found in the CVF WACV 2026
  proceedings. Cited as arXiv preprint.
- Overlap: broad contemporary spatial-failure benchmarking.
- Distinct: our study is narrower and deeper (orientation family, interventions,
  mechanism diagnostics, consistency, transfer).

### 6. SAGE (already cited, retained)
- Consistency-oriented training with geometric/linguistic duality
  (liu2026sage). Retained; wording strengthened so we do not claim that
  "accuracy and consistency can diverge" is itself novel. Our distinct
  empirical observation is the VSR complementary-relation analysis: strict
  facing/facing-away pairs where LM-only and HardNeg have identical original
  facing accuracy (68.9%) but different complementary consistency
  (66.0% vs 77.7%), with the HardNeg-vs-LM pooled difference non-significant
  (p=0.29).

## Novelty boundary statement (now in Related Work)

"Prior work has thus already established spatial and orientation weaknesses in
VLMs and has begun to analyze those failures through prompting, attention,
representation probing, and consistency-based training. Our contribution is
therefore not the first identification of orientation difficulty or spatial
inconsistency. Instead, we revisit the known VSR orientation weakness in modern
generative VLMs and subject the same relation family to a controlled diagnostic
ladder spanning adaptation, frozen and object-grounded readouts, visual-side
interventions, complementary-relation consistency, label sensitivity, and
cross-dataset transfer."

## Claims audited (novelty wording)

- Structured prompting: cited When More Is Less; claim now scoped to the tested
  2B condition and prompt; no "prompting fails generally".
- Probes: canonical claim unchanged — "orientation is not robustly decodable by
  the tested frozen-feature readouts"; never "information is absent" / "the
  vision encoder is the cause"; prior probing (Theodoridis et al.) and
  attribution (CREG) acknowledged.
- Consistency: prior work acknowledged; statistical language preserved exactly
  (LM-only-vs-zero-shot pooled strict p<0.0001 significant; HardNeg facing
  66.0→77.7% descriptive relative to LM-only; HardNeg-vs-LM pooled p=0.29 not
  significant).
- SITE: unchanged — transfer-first framing, official category strong, VSR-LoRA
  harms it (p=0.004), orientation slice exploratory, confound OR 0.84 p=0.29,
  high-precision subset post-hoc.
- No "first / has not been studied / we causally locate / novel framework"
  claims remain (grep-verified; remaining "first" occurrences are explicit
  disclaimers).

## Primary-source identifiers used for verification

| Paper | Identifier |
|---|---|
| AdaptVis | arXiv:2503.01773; PMLR v267 (ICML 2025) |
| When More Is Less | arXiv:2602.21619 |
| Probing Visual Concepts | arXiv:2603.06054; TMLR 2026 |
| CREG | arXiv:2603.20475 |
| Mind the Gap | arXiv:2503.19707 (preprint; no venue found) |

## Threat assessment

No discovered work materially threatens the full paper's novelty as positioned:
the combination of (a) relation-family persistence across two VLMs with a broad
intervention ladder, (b) object-grounded decodability + adaptation pairing,
(c) VSR-specific accuracy/coherence separation with the identical-accuracy
HardNeg dissociation, and (d) VSR→SITE negative transfer is not covered by any
single prior paper. The two closest works (AdaptVis, CREG) are cited and
differentiated explicitly.
