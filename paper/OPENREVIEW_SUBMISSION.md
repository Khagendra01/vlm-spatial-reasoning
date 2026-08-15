# OpenReview Submission Metadata â€” WACV 2027 Round 2 (Evaluations & Dataset Track)

Prepared 2026-08-15 for the Round 2 enrollment deadline: **August 21, 2026, AoE**.
Submission site: `https://openreview.net/group?id=thecvf.com/WACV/2027/Conference` (Round 2).
Paper: **Paper 3 â€” EquiOrient** (branch `research/equiorient`, latest commit
`cd4eda6`). Everything below is ready to paste into the OpenReview form.
Regenerate title/abstract from source any time with:
`python paper/extract_openreview.py`.

Two items require personal action before/at enrollment: (1) the **author
list** (authors cannot be added/removed after enrollment, only reordered
until the paper deadline), and (2) **OpenReview profiles + conflict
declarations** for every author.

---

## 1. Title

```
EquiOrient: Latent Transformation Equivariance without Measurable Downstream Transfer
```

## 2. Abstract (â‰¤ 5000 characters; current length â‰ˆ 1,585)

```
Can training an answer-relevant object-pair spatial state in a visionâ€“language
model (VLM) to obey a predeclared, geometry-derived transformation algebra deliver
measurable downstream transfer beyond matched augmentation, output-consistency, and
invariance controls? We test this with a one-seed falsification pilot on synthetic
plan-view scenes rendered for Qwen3-VL-8B-Instruct. We use a manipulation-verified
implementation with per-epoch structural-loss logging and a nonzero-loss assertion,
and compare six matched arms sharing the same answer path while differing only in
data or structural objective. The result is a clean separation. When the loss is
actually applied, the latent complies with the predeclared algebra: on a held-out
transform composition never seen in training, EquiOrient's equivariance error is
0.0452 vs. 14.6516 for augmentation-only (a 324Ã— reduction), and the per-transform
correct-vs-wrong contrast discriminates sharply (0.0331 vs. 4.8945 on the
horizontal reflection), with a wrong-geometry control that obeys its own
(incorrect) law per-transform. Yet no measurable downstream transfer appears: the
behavioral composition test is uninformative by construction (the task reduces to a
binary left/right axis on which the answer algebra is closed, so every arm reaches
ceiling), and a held-out relation-family probe (depth) is flat across arms
(0.53â€“0.55). The paper is a mechanistic negative: representation-level algebra
compliance is achievable and measurable, but it did not transfer to behavior or to
an unseen relation family within Phase-1 scope.
```

## 3. Track / subject area

- **Track:** C) Evaluations & Dataset Track (a.k.a. "Datasets Track" in the
  LaTeX kit; header on the compiled paper reads "Anonymous WACV Datasets Track
  submission").
- Fit: the paper analyzes an evaluation failure mode (algebra closure and
  transform symmetry making a composition test non-diagnostic), audits
  representation-level intervention outcomes, and provides a wrong-action
  causal control â€” squarely within the track's scope ("testing, stress-testing,
  auditing, comparing, and interpreting AI/ML systems"; the 2027 CFP explicitly
  welcomes negative results and critical analyses).
- In OpenReview select the Evaluations & Dataset track subject area; **do NOT
  select Algorithms**.

## 4. Keywords / research areas (suggested)

```
vision-language models; spatial reasoning; transformation equivariance;
representation learning; evaluation methodology; negative results; causal control;
benchmark saturation
```

## 5. Deadlines (Round 2, WACV 2027)

| Item | Date |
|---|---|
| New-paper registration | **Aug 21, 2026, AoE** |
| Paper submission (main.pdf) | **Aug 28, 2026, AoE** |
| Supplementary (suppl.pdf) | **Aug 30, 2026, AoE** |

## 6. Files checklist

- [x] `paper/main.pdf` â€” compiled 2026-08-15, **5 pages** (limit 8 + refs),
      anonymous review mode, machine-generated numbers only
- [x] Source: `paper/main.tex`, `numbers.tex` (auto-generated), `main.bib`,
      `figures/fig1_rho.png`, `fig2_contrast.png`, `fig3_probe.png`
- [ ] **Supplementary** â€” recommended: full per-arm matrices, compute ledger,
      per-transform rho tables, loss curves, algebra verification, compute ledger,
      voided-run provenance

- [ ] **Code zip** (WACV reproducibility) â€” harness, generators, freeze YAMLs,
      Modal scaffold, extract/make scripts; committed on `research/equiorient`
- [ ] Anonymity: no author names/links in PDF or artifacts (current: "Anonymous
      Authors")

## 7. Pre-enrollment actions (you)

1. Decide the author list + ordering (locked at enrollment).
2. Create/confirm OpenReview profiles for all authors; add conflict
   declarations.
3. Optional: assemble the supplementary (`suppl.tex`) and the code zip.
4. Register the paper on Aug 21; upload `main.pdf` by Aug 28.
