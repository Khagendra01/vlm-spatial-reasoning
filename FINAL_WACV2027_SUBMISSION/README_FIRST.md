# WACV 2027 Round 2 — FINAL SUBMISSION KIT

Everything you need is in this folder. Read this file first.

Paper: "Beyond Spatial Accuracy: Diagnosing Persistent Orientation Failures in Vision–Language Models"
Track: Evaluations & Dataset Track (Datasets Track)
Frozen at tag `wacv2027-submission-v1` → commit `344c5ca7739d775274f13ae7aedf6d31f34675f2`

---

## Folder contents

| Folder | What's inside | When you need it |
|---|---|---|
| `01_UPLOAD_THIS/` | **main.pdf** · **supplementary.pdf** · **wacv2027_code.zip** | The three files you upload to OpenReview. Hashes verified against the manifest. |
| `02_OPENREVIEW_ENROLLMENT/` | `OPENREVIEW_SUBMISSION.md` (+ title/abstract as plain text) | **Aug 21 AoE** — enrollment: title, abstract, authors. Paste-ready. |
| `03_DOCS_CHECKLISTS/` | Submission checklist with SHA-256s · Reproducibility · Anonymity checklist + scan record · Novelty audit | Before each upload; reference as needed. |
| `04_LATEX_SOURCE/wacv2027_source/` | Full WACV LaTeX source (main.tex, suppl.tex, wacv.sty, sec/, fig/, bibs) | Only if a rebuild is ever needed (e.g., administrative PDF fix → rebuild, then new commit/tag). |

---

## Deadline card (all Anywhere on Earth)

| Date | Action |
|---|---|
| **Aug 21, 2026** | **Enrollment**: create OpenReview submission, paste title + abstract, add FINAL author list (no adds/removes after this), verify all authors' profiles + conflicts |
| **Aug 28, 2026** | Upload `01_UPLOAD_THIS/main.pdf` (≤ 50 MB; 8 pages incl. figures/tables + reference pages) |
| **Aug 30, 2026** | Upload `01_UPLOAD_THIS/supplementary.pdf` and/or `wacv2027_code.zip` (≤ 200 MB) |
| Oct 9, 2026 | Reviews + final decisions (no rebuttal for new Round 2 papers) |

---

## Upload checklist (do in order)

1. [ ] **Enrollment (Aug 21)**: OpenReview submission at
      `https://openreview.net/group?id=thecvf.com/WACV/2027/Conference`
      → paste title/abstract from `02_OPENREVIEW_ENROLLMENT/`
      → add authors (decided BEFORE this date) → confirm profiles/conflicts.
2. [ ] **After enrollment**: run `python set_paper_id.py <your_paper_id>`
      (see `01_UPLOAD_THIS/FINALIZE_BEFORE_UPLOAD.txt`) — this puts the real
      OpenReview paper number into the header ("Submission #<id>") and
      rebuilds the two PDFs. The "***** / Datasets Track / CONFIDENTIAL
      REVIEW COPY" header is otherwise the official WACV review format.
3. [ ] **Aug 28**: upload `main.pdf`. After upload, re-download and verify:
      - SHA-256 matches `03_DOCS_CHECKLISTS/WACV2027_SUBMISSION_CHECKLIST.md`
        (or the updated hashes printed by the finalize script)
      - Header reads "WACV 2027 Submission #<id>. Datasets Track."
      - ≤ 8 content pages (+ references)
4. [ ] **Aug 30**: upload `supplementary.pdf` + `wacv2027_code.zip`; verify hashes the same way.

---

## Before you click submit — final visual pass (human)

Open `01_UPLOAD_THIS/main.pdf` and `supplementary.pdf` at 100% zoom and check:
figures 2 / 4 / 5, the failure collage, tiny axis labels/legends, table and
citation wrapping, and the page-7→8 reference transition. This is the only
remaining gate — the science, statistics, and anonymity are done.

---

## If OpenReview ever needs an administrative change (not scientific)

Do NOT rewrite this package or the tag. Make the change in
`04_LATEX_SOURCE/wacv2027_source/`, rebuild, create a new commit + new tag
(e.g., `wacv2027-submission-v2`), and update this folder. `wacv2027-submission-v1`
stays immutable.
