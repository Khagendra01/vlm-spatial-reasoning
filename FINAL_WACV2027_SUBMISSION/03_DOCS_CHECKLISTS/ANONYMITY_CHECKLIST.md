# Anonymity Audit — WACV 2027 Round 2 submission package

Double-blind requirement (WACV Author Guidelines): "reviewers cannot, beyond
reasonable doubt, infer the names of the authors from the submission and the
additional material." Desk rejection applies to identity leaks in the paper or
supplementary code. This checklist documents the automated and manual audit
performed on the artifacts in this folder.

## 1. Automated scan (evidence below)

Searched all submission artifacts (LaTeX sources, scripts, READMEs, data files,
ZIP contents) for identifying tokens. Full scan output is in
`anonymity_scan_output.txt` (regenerated with: `python scripts/audit_anonymity.py`).

Tokens scanned:

| Token class | Examples | Result |
|---|---|---|
| Author names / usernames | "Khage", "khagendra", "khatri" | 0 hits in artifacts |
| Emails | @gmail, @example.org (placeholder only), personal domains | 0 real hits |
| Machine paths (Windows) | `C:\Users\Khage`, `C:\Users\` | 0 hits |
| Machine paths (Linux box) | `/home/ubuntu/vlm-spatial-reasoning` | 0 hits (sanitized in archive copies) |
| Repo identity | "VLM-Spatial-Reasoning", "vlm-spatial-reasoning", "paper-draft-v1" | 0 hits in paper/suppl; 0 in code archive |
| GitHub identity | "github.com/Khagendra01" | 0 hits |
| Git commit hashes (7+ hex) | e.g. `f07c361` | 0 hits (removed from App. G; the SITE protocol config hash `28f4cc09887477af` is retained as a scientific preregistration artifact, not a repo reference) |
| Other repo tags | "paper-freeze-v1" (internal tag) | removed from submission sources |
| Acknowledgments / grants | n/a | paper contains no acknowledgments section |

## 2. PDF metadata

Checked with pypdf:

| PDF | Title field | Author field | Producer | Creator |
|---|---|---|---|---|
| main.pdf | (title set by \title; no names) | absent | xdvipdfmx (0.1) | LaTeX with hyperref |
| supplementary.pdf | same | absent | xdvipdfmx (0.1) | LaTeX with hyperref |

No author/institution metadata embedded.

## 3. Manual checklist (human pass, do before upload)

- [ ] Visual scan of every page of `main.pdf` and `supplementary.pdf` for names,
      logos, watermarks, affiliation hints in figure content.
- [ ] Figures: the failure-grid and VSR/SITE charts contain no text overlays
      beyond axis/caption labels (generated programmatically).
- [ ] The code ZIP: no license/copyright headers with names (all scripts carry
      neutral docstrings); no comments referencing the authors.
- [ ] No external links anywhere in the paper or supplementary (per WACV
      guidance; reviewers cannot follow links that might identify authors).
- [ ] OpenReview profiles will be created with institutional emails; author list
      finalized before Aug 21 enrollment (see OPENREVIEW_SUBMISSION.md).

## 4. Known retained strings (deliberate, non-identifying)

- `28f4cc09887477af` — SITE frozen-protocol config hash (preregistration artifact).
- `anonymous@example.org`-style placeholders removed from the WACV sources; the
  compiled review PDFs render the template's "Anonymous WACV submission" header.
- Dataset/model identifiers (HF paths) — required for reproducibility, not identity.

## 5. Actions taken during package build (for the record)

- Removed repo name and all git commit SHAs from the supplementary artifact index
  (App. G); replaced with "anonymized archive accompanying this submission".
- Sanitized `/home/ubuntu/vlm-spatial-reasoning` hard-coded working directories
  in every script shipped in `wacv2027_code.zip` (ROOT-relative chdir instead).
- Excluded internal docs (research handoffs, audit memos referencing repo state)
  from the package; they are not part of the submission.
- Suppressed author placeholders in LaTeX sources; review mode renders anonymous
  headers automatically.
