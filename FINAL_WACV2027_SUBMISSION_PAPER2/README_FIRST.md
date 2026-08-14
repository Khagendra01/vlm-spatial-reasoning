# WACV 2027 Round 2 — PAPER 2 FINAL SUBMISSION KIT

Everything you need is in this folder. Read this file first.

Paper: "What Spatial Fine-Tuning Actually Changes: A Multi-Seed Decomposition of Accuracy, Evidence Dependence, and Semantic Consistency in Vision-Language Models"
Track: Evaluations & Dataset Track (Datasets Track)

> This is the SECOND paper's kit (Paper 1 = "Beyond Spatial Accuracy...",
> in `FINAL_WACV2027_SUBMISSION/`). Keep the two kits separate; each has its
> own upload folder and its own OpenReview submission.

---

## Folder contents

| Folder | What's inside | When you need it |
|---|---|---|
| `01_UPLOAD_THIS/` | **main.pdf** + **supplementary.pdf** + **wacv2027_code.zip** | The three files you upload to OpenReview. Hashes verified against the manifest. |
| `02_OPENREVIEW_ENROLLMENT/` | `OPENREVIEW_SUBMISSION.md` (+ title/abstract as plain text) | **Aug 21 AoE** — enrollment: title, abstract, authors. Paste-ready. |
| `03_DOCS_CHECKLISTS/` | Submission checklist with SHA-256s + Reproducibility + Anonymity checklist | Before each upload; reference as needed. |
| `04_LATEX_SOURCE/paper2_source/` | Full WACV LaTeX source (main.tex, suppl.tex, wacv.sty, sec/, fig/, bibs) | Only if a rebuild is ever needed (e.g., administrative PDF fix — rebuild, then new commit). |

---

## Deadline card (all Anywhere on Earth)

| Date | Action |
|---|---|
| **Aug 21, 2026** | **Enrollment**: create OpenReview submission, paste title + abstract (files in `02_OPENREVIEW_ENROLLMENT/`), add FINAL author list (no adds/removes after), verify all authors' profiles + conflicts |
| **Aug 28, 2026** | Upload `01_UPLOAD_THIS/main.pdf` (<= 50 MB; 8 pages incl. figures/tables + reference pages) |
| **Aug 30, 2026** | Upload `01_UPLOAD_THIS/supplementary.pdf` and/or `01_UPLOAD_THIS/wacv2027_code.zip` (<= 200 MB) |
| Oct 9, 2026 | Reviews + final decisions (no rebuttal for new Round 2 papers) |

---

## Upload checklist (do in order)

1. [ ] **Enrollment (Aug 21)**: OpenReview submission at
      `https://openreview.net/group?id=thecvf.com/WACV/2027/Conference`
      - paste title/abstract from `02_OPENREVIEW_ENROLLMENT/`
      - add authors (decided BEFORE this date) — confirm profiles/conflicts.
2. [ ] **After enrollment**: run `python set_paper_id.py <your_paper_id>`
      (see `01_UPLOAD_THIS/FINALIZE_BEFORE_UPLOAD.txt`) — this puts the real
      paper number in the PDF headers and rebuilds both PDFs.
3. [ ] **Aug 28**: upload `01_UPLOAD_THIS/main.pdf`; verify SHA-256.
4. [ ] **Aug 30**: upload `01_UPLOAD_THIS/supplementary.pdf` +
      `01_UPLOAD_THIS/wacv2027_code.zip`; verify SHA-256s.

---

## What is already done (no further work needed at freeze)

- LaTeX compiled clean (main.pdf 5 pp, supplementary.pdf 1 p; 0 undefined
  citations, 0 overfull boxes; figures embedded; references resolved).
- All numbers independently audited (PASS) and cross-checked against the
  paper text (hostile numerical review PASS).
- Claim hierarchy, literature/novelty audit, hostile review, and the
  submission freeze are committed in `results/seed_campaign/`.
- GPU compute remains OFF — nothing in this kit requires model compute.
