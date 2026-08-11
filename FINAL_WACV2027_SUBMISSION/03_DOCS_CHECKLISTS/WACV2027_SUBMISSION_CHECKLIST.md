# WACV 2027 Round 2 — Submission Manifest & Checklist

Final submission artifacts for the Evaluations & Dataset track.
Build source: `paper-draft-v1` @ `f07c361fcd0109aa3da5d9023bfa2edf9fda2201`
(pre-tag revision; the WACV package is generated from that state).
PDFs compiled with Tectonic 0.17.0 (XeTeX engine), official WACV 2027 author kit
(`wacv.sty`, `[review,datasets]` — anonymous Datasets Track review version).

## Files to upload

| # | File | Size | Pages | SHA-256 |
|---|---|---|---|---|
| 1 | `main.pdf` | 877,825 B | 8 total: content ≤ 7 pp, references on pp 7–8 (limit: 8 content pp + ref pages) | `bc27ecece8e4a6083b5ea01cf2e8d9be314514cd30c0d7a0abe629b4f0a38c08` |
| 2 | `supplementary.pdf` | 2,076,681 B | 8 (supplement has no page limit) | `31e36bc6a3674e582af1bb8c7de9215e7f9b816d17fece94326d6f22ea5cee74` |
| 3 | `wacv2027_code.zip` | 721,068 B | — (59 files, ≤ 200 MB limit) | `81b2ba73455ed7c970b7c9709167bda9b8fe28fbffa313c9ce079aeb85bbd45a` |

SHA-256 values recorded at package build time (Tectonic 0.17.0, reproducible
builds from `source/`). Re-verify with `Get-FileHash`/`sha256sum` immediately
before upload — they must match exactly; any difference means the file changed.

Submission-safety calibration (final pass): `paper-freeze-v1` tag name, the
SITE protocol config hashes (`28f4cc09887477af`, `4d371713c96ee0d9`), and all
"preregistered" wording removed from the upload artifacts (replaced with
"frozen experimental snapshot" / "pre-specified", with the protocol content
unchanged). The uploaded `run_metadata.json` carries placeholder snapshot
labels (`config-snapshot-a/b`); the private repository copy retains the real
hashes. The abstract clean-label sentence now reads "the pattern persists after
excluding examples flagged as ambiguous". No experiments, metrics, figures,
tables, or statistical results changed.

## OpenReview upload order (Round 2)

1. **Aug 21 AoE — enrollment:** create the submission at
   `https://openreview.net/group?id=thecvf.com/WACV/2027/Conference`; paste title
   and abstract from `OPENREVIEW_SUBMISSION.md`; add the **final** author list
   (no additions/removals after this date; reordering allowed until Aug 28).
2. **Aug 28 AoE — main paper:** upload `main.pdf` (PDF only, ≤ 50 MB). Confirm
   the compiled header shows "Anonymous WACV Datasets Track submission" and the
   paper is ≤ 8 pages excluding references.
3. **Aug 30 AoE — supplementary:** upload `supplementary.pdf` **and/or**
   `wacv2027_code.zip` (≤ 200 MB; PDF or ZIP only). The code zip may be uploaded
   in addition to the PDF.
4. After each upload: re-download from OpenReview and verify page count, SHA-256,
   and that the PDFs still open (server-side processing must not alter them).

## Pre-upload checklist

- [ ] Paper: 8-page limit respected (7 content pages + reference pages).
- [ ] Paper: track header is the Datasets Track (not Algorithms/Applications).
- [ ] Paper + supplement: double-blind (see `ANONYMITY_CHECKLIST.md`; scan record
      in `anonymity_scan_output.txt` — 0 identity hits).
- [ ] Supplement: contains no new datasets, no improved-method results, no
      corrected version of the main paper (it is a strict superset of the
      main-paper analyses, all from the same frozen results).
- [ ] Code zip: anonymized, no weights/media, README + requirements included,
      CPU-reproducible commands verified.
- [ ] All authors have approved OpenReview profiles (institutional email
      preferred) and conflicts registered — before Aug 21.
- [ ] Abstract ≤ 5000 characters (current ≈ 1,830).
- [ ] No rebuttal is available for new Round 2 papers — the submission must be
      final on Aug 28.

## Deadline card

| Event | Date (AoE) |
|---|---|
| Round 2 enrollment (title/abstract/authors) | Aug 21, 2026 |
| Round 2 paper submission | Aug 28, 2026 |
| Round 2 supplementary material | Aug 30, 2026 |
| Reviews + final decisions (no rebuttal for new R2) | Oct 9, 2026 |
| Camera-ready (accepted papers) | Nov 2, 2026 |

## Post-submission rules to respect

- Do not post the submission or an identifiable version publicly until after
  decisions (arXiv is permitted per WACV FAQ, but an arXiv version with the same
  title/abstract could break anonymity — decide consciously; the FAQ allows it).
- No author changes after enrollment; no links to external materials from the
  submission.
- Authors who submit must be willing to review (WACV expects 3-4 papers/round).

## Package contents (this folder)

```
main.pdf                     WACV main paper (7 pp + refs)
supplementary.pdf            WACV supplementary (8 pp)
wacv2027_code.zip            anonymized code + data + README (721 KB)
source/                      WACV LaTeX sources (wacv.sty, main.tex, suppl.tex,
                             sec/, fig/, references.bib, preamble.tex)
OPENREVIEW_SUBMISSION.md     paste-ready enrollment metadata
SUBMISSION_REPRODUCIBILITY.md  environment/datasets/commands/expected outputs
ANONYMITY_CHECKLIST.md       double-blind audit + evidence
anonymity_scan_output.txt    automated scan record (upload artifacts only)
WACV2027_SUBMISSION_CHECKLIST.md  this file
```
