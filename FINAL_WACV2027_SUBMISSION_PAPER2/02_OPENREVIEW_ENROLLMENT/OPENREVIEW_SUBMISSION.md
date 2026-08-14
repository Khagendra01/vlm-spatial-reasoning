# WACV 2027 OpenReview Enrollment (Paper 2)

**Action date: Aug 21, 2026 (Anywhere on Earth).**
OpenReview submission page:
`https://openreview.net/group?id=thecvf.com/WACV/2027/Conference`

## What to paste (paste-ready files in this folder)

| Field | Source file |
|---|---|
| Title | `title.txt` |
| Abstract | `abstract_paste.txt` |

## Step-by-step

1. Create the OpenReview submission at the WACV 2027 conference group.
2. Paste title + abstract from `title.txt` / `abstract_paste.txt`.
   - Note: the abstract uses `Delta A / Delta G / Delta C` (ASCII-safe) in the
     paste file; the paper itself renders them as math symbols.
3. Add the FINAL author list. **No adds/removes after Aug 21.**
4. Verify every author's OpenReview profile exists and mark conflicts
   (WACV uses the profile-based conflict system; double-check co-authors,
   collaborators, institution affiliations).
5. Record the assigned **paper ID** (e.g. `1234`).
6. Run the finalize step:
   ```
   python set_paper_id.py <your_paper_id>
   ```
   (script at `FINAL_WACV2027_SUBMISSION_PAPER2/set_paper_id.py`)
   This rebuilds `main.pdf` + `supplementary.pdf` with
   "Submission #<id>" in the header and replaces the files in
   `01_UPLOAD_THIS/`.
7. Re-verify SHA-256 hashes (they change after the ID is set) and update
   `03_DOCS_CHECKLISTS/WACV2027_SUBMISSION_CHECKLIST.md`.

## Deadlines after enrollment

| Date (AoE) | Action |
|---|---|
| Aug 28, 2026 | Upload `01_UPLOAD_THIS/main.pdf` (<= 50 MB; 8 pages incl. figures/tables + references) |
| Aug 30, 2026 | Upload `01_UPLOAD_THIS/supplementary.pdf` + `01_UPLOAD_THIS/wacv2027_code.zip` (<= 200 MB) |
| Oct 9, 2026 | Reviews + final decisions (no rebuttal for Round 2 papers) |

## Paper identity (for the submission form)

- **Track:** Evaluations & Dataset Track (Datasets Track)
- **Title:** What Spatial Fine-Tuning Actually Changes: A Multi-Seed
  Decomposition of Accuracy, Evidence Dependence, and Semantic Consistency
  in Vision-Language Models
- **Keywords:** spatial reasoning; vision-language models; visual grounding;
  fine-tuning; multi-seed evaluation; LoRA
- **Anonymous:** YES — do NOT fill author names on the submission form until
  the author list is final (and even then the review version stays anonymous).
