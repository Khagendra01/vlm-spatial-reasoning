# OpenReview Submission Metadata — WACV 2027 Round 2 (Evaluations & Dataset Track)

Prepared for the Round 2 enrollment deadline: **August 21, 2026, Anywhere on Earth**.
Submission site: `https://openreview.net/group?id=thecvf.com/WACV/2027/Conference` (Round 2).

Everything below is ready to paste into the OpenReview form. Two items require
personal action before/at enrollment: (1) author list (decide before Aug 21 —
authors cannot be added/removed after enrollment, only reordered until the
paper deadline), and (2) OpenReview profiles + conflicts for every author.

---

## 1. Title

```
Beyond Spatial Accuracy: Diagnosing Persistent Orientation Failures in Vision–Language Models
```

## 2. Abstract (≤ 5000 characters; current length ≈ 1,830)

```
Aggregate spatial accuracy can hide sharply different capabilities within vision--language
models (VLMs). We study object-relative orientation as a diagnostic case. On Visual Spatial
Reasoning (VSR), moving from a compact 2.2B model to a larger 7B VLM substantially improves
overall, depth, horizontal, and containment accuracy, but orientation changes only modestly.
Except for structured prompting, which degrades performance, trained conditions on both models
remain in a narrow 62--66% orientation band. We test structured prompting, general and
targeted LoRA, hard negatives, visual/projector adaptation, frozen and object-grounded
representation probes, and object-centric decomposition; none of the tested configurations
reliably closes the gap, and a single-annotator clean-label sensitivity analysis shows that
annotation ambiguity does not explain it away.

Accuracy also fails to capture relational coherence. LM-side adaptation significantly
improves consistency over zero-shot, while hard-negative training raises facing/facing-away
consistency from 66.0% to 77.7% with facing accuracy unchanged at 68.9%; the additional
pooled consistency gain over LM-only is not significant. Cross-dataset evaluation on SITE
shows that VSR-trained adaptation does not transfer cleanly: it is neutral overall and
significantly harms official spatial-relationship reasoning (75.1%→71.6%, p=0.004). A
preregistered orientation-vocabulary slice is analyzed as exploratory evidence rather than
as direct replication of the VSR construct. The results point to a persistent orientation
bottleneck in which orientation is not robustly decodable by the tested frozen-feature
readouts and relational decisions are not always propagated coherently, while also showing
that task-specific spatial adaptation can transfer poorly.
```

## 3. Track / subject area

- **Track:** C) Evaluations & Dataset Track (a.k.a. "Datasets Track" in the LaTeX kit;
  header on the compiled paper reads "Anonymous WACV Datasets Track submission").
- The paper is a failure-mode analysis / negative-result diagnostic study with a
  preregistered external-validation protocol — squarely within the track's scope
  ("testing, stress-testing, auditing, comparing, and interpreting AI/ML systems").
- In OpenReview select the corresponding primary subject area for the Evaluation &
  Dataset track; do NOT select Algorithms.

## 4. Keywords / research areas (suggested)

```
vision-language models; spatial reasoning; orientation; failure analysis;
evaluation methodology; negative results; benchmark analysis; logical consistency;
cross-dataset transfer; reproducibility
```

## 5. Authors

**ACTION REQUIRED before Aug 21 AoE.** Decide the final list and order now; authors
cannot be added or removed after enrollment (only reordered until Aug 28).

- [ ] Author 1 (submitter): name, institution, email — fill in
- [ ] Author 2 (if applicable — e.g., advisor): decide whether contribution meets
      authorship bar; if yes, they must be enrolled on day 1
- [ ] Every author: complete OpenReview profile (see checklist below) and confirm
      conflicts are set

If an advisor contributed substantially (research direction, experimental guidance,
paper editing), include them BEFORE enrollment — WACV will not allow adding them later.

## 6. OpenReview profile checklist (each author)

1. OpenReview ID
2. Name / current position
3. Confirmed email (institutional preferred; non-institutional approval can take up to
   two weeks)
4. Personal links (where applicable)
5. Education / career history
6. Advisors / relations / conflicts (including domain conflicts)
7. Specific expertise areas
8. Recent publications (where applicable)

## 7. Conflicts of interest

Primary author responsibility: verify every co-author has registered institutional
and personal conflicts (advisors, collaborators, institutions, domains) before
enrollment. Incomplete conflict info can cause summary rejection.

## 8. Deadlines (WACV 2027 Round 2, all AoE)

| Event | Date |
|---|---|
| Paper enrollment (title/abstract/authors) | Aug 21, 2026 |
| Paper submission (main.pdf) | Aug 28, 2026 |
| Supplementary material (supplementary.pdf / code zip) | Aug 30, 2026 |
| Reviews + final decisions | Oct 9, 2026 |
| Camera-ready | Nov 2, 2026 |

Note: new Round 2 papers have **no rebuttal/revision phase** — decisions come from the
reviews directly. The submission must be clean on arrival.
