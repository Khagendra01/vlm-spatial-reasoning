# OpenReview Submission Kit — EquiOrient Phase 2

## Title
EquiOrient: Evaluating Latent Transformation Equivariance for Compositional Spatial Reasoning

## Abstract
Can training a VLM's answer-relevant spatial latent to obey a predeclared geometric transformation algebra improve compositional generalization beyond matched augmentation and output-consistency baselines? We test this on the dihedral group D4 (horizontal reflection H and 90-degree rotation R, with five held-out compositions including noncommutative pairs like RH), using 8-way compass-direction labels on synthetic scenes with dense homogeneous clutter. We compare six matched arms differing only in structural objective across five seeds and three data scales. EquiOrient achieves strong, specific latent algebra compliance: the correct-vs-wrong specificity score is consistently positive, and the wrong-geometry arm learns its own incorrect law. However, behavioral accuracy on all held-out compositions is at ceiling for every arm (>=0.98), because the VLM backbone's region-pooled features are already robust to D4 transforms. This is a clear mechanistic negative: representation-level geometric fidelity is achievable and measurable, but does not translate into behavioral improvement when the backbone already solves the task.

## Track
Evaluation Datasets and Benchmarks (E&D)

## Keywords
spatial reasoning, equivariance, compositionality, VLM evaluation, negative results, dihedral group

## Author Information
- Anonymous (to be filled at enrollment, Aug 21)

## Deadlines
- Aug 21, 2026 AoE: Enrollment (author list locked)
- Aug 28, 2026 AoE: Full paper submission
- Aug 30, 2026 AoE: Supplementary material

## Required Files
- main.pdf (8 pages, WACV format, excluding references)
- suppl.pdf (any length, but no additional datasets or improved method versions per WACV rules)
- main.tex (source)
- main.bib (bibliography)

## Checklist
- [ ] 8-page main body (WACV limit, excludes references)
- [ ] Anonymous submission (no author names/affiliations)
- [ ] Supplementary material does not introduce new datasets or improved methods
- [ ] All experimental results are reproducible from committed code + frozen ledgers
- [ ] Pre-registered confirmatory YAML committed before result inspection
- [ ] No rebuttal available (Round 2) — paper must be self-contained

## WACV-Specific Notes
- Round 2: no rebuttal period. Paper must be complete and self-contained.
- Supplement may NOT contain additional datasets or improved method versions.
- The second backbone (Qwen2-VL-7B) and data-scale results, if included, must be in the main paper.
- Page limit is strict: 8 pages main body, references excluded.

## Neutral Title for Enrollment
"EquiOrient: Evaluating Latent Transformation Equivariance for Compositional Spatial Reasoning"

(Title may be revised before submission based on final results, but this neutral framing is appropriate for enrollment.)
