# OpenReview Submission Kit — EquiOrient Phase 2

## Title
EquiOrient: Evaluating Latent Transformation Equivariance for Compositional Spatial Reasoning

## Abstract
Can training a VLM's answer-relevant spatial latent to obey a predeclared geometric transformation algebra improve compositional generalization beyond matched augmentation and output-consistency baselines? We test this on the dihedral group D4 (horizontal reflection H and 90-degree rotation R, with five held-out compositions including noncommutative pairs like RH), using 8-way compass-direction labels on synthetic scenes with dense homogeneous clutter. We compare six matched arms differing only in structural objective, under a fully deterministic protocol (seeded initialization, SHA-256-seeded data noise, provenance-annotated results). EquiOrient achieves clear law-consistent latent algebra compliance: the structural loss is nonzero and convergent, and the wrong-geometry arm learns its own incorrect law. Behaviorally, at the scarce-data regime (N=128, fifteen matched seeds) behavior is sensitive to the correctness of the imposed law: the correct law is significantly distinguishable from the wrong law (+0.68pp, 95% CI [+0.5, +0.9]pp, p<0.0001, 15/15 seeds), yet correct structural supervision does not outperform plain augmentation (-0.9pp, CI [-2.3, +0.5]pp, n.s.). At N>=512 every arm reaches ceiling (>=0.999) because the VLM backbone's region-pooled features are already robust to D4 transforms. The result is a precisely quantified mixed outcome: at low data, behavior is sensitive to whether the imposed geometric law is correct, but correct structural supervision does not outperform unconstrained augmentation, and no behavioral differentiation once the backbone saturates the task.

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
- main.pdf (5 pages main body, WACV format, references excluded)
- suppl.pdf (any length, but no additional datasets or improved method versions per WACV rules)
- main.tex (source)
- main.bib (bibliography)

## Checklist
- [x] Main body within 8-page WACV limit (currently 5 pages)
- [x] Anonymous submission (no author names/affiliations)
- [x] Supplementary material does not introduce new datasets or improved methods
- [x] All experimental results are reproducible from committed code + frozen ledgers
- [x] Pre-registered confirmatory YAML committed before result inspection
- [x] No rebuttal available (Round 2) — paper must be self-contained

## WACV-Specific Notes
- Round 2: no rebuttal period. Paper must be complete and self-contained.
- Supplement may NOT contain additional datasets or improved method versions.
- Page limit is strict: 8 pages main body, references excluded. Current manuscript: 5 pages.

## Neutral Title for Enrollment
"EquiOrient: Evaluating Latent Transformation Equivariance for Compositional Spatial Reasoning"

(Title may be revised before submission based on final results, but this neutral framing is appropriate for enrollment.)
