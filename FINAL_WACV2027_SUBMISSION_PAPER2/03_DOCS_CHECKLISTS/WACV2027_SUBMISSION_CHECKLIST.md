# WACV 2027 Submission Checklist — Paper 2

**Kit:** `FINAL_WACV2027_SUBMISSION_PAPER2/`
**Status at freeze:** all three upload artifacts built and hashed (2026-08-14).
**Update 2026-08-22:** main.pdf rebuilt after protocol-first abstract/intro
rewrite (`paper2/abstract-rewrite`, commit `5b6f49f`); hash above refreshed;
`02_OPENREVIEW_ENROLLMENT/abstract_paste.txt` synced to the new abstract.
Note: rebuild used tectonic 0.15.0 (MiKTeX unavailable on this machine);
layout re-verified: 6 pp incl. references, review header + line numbers intact,
within the 8-page limit. If preferred, rebuild once more with MiKTeX before
upload and refresh the hash again.
**FINAL 2026-08-22 (post-enrollment): OpenReview submission #3083 confirmed.
`set_paper_id.py` steps executed manually with tectonic (script is
MiKTeX/Windows-bound): ID 3083 set in main.tex + suppl.tex, both PDFs
rebuilt and copied to 01_UPLOAD_THIS. Verified: "Submission #3083" header on
both, no author leaks, main 6 pp incl. refs / suppl 1 p. Hashes above are
the FINAL upload hashes.**
**GPU compute:** OFF (no further model compute; this is the post-compute layer).

## Upload artifacts (01_UPLOAD_THIS/)

| File | Size | SHA-256 | Status |
|---|---|---|---|
| main.pdf | 0.31 MB | `76DC7A505AB3E1051653A1EC4C5515F833AE4CDD6DBE74EFD81CA53896D0F278` | FINAL: paper ID 3083 set, rebuilt 2026-08-22 (6 pp incl. references, anonymous, tectonic 0.15.0) — upload Aug 28 |
| supplementary.pdf | 0.04 MB | `6E0FB23DF2FF0622267E7198BEFEAE186F78B935E6330C1E8CD4139480A52D6D` | FINAL: paper ID 3083 set, rebuilt 2026-08-22 (1 p, anonymous) — upload Aug 30 |
| wacv2027_code.zip | 0.45 MB | `9ABAE8E33210799A939A80AC55FB5D7056F066045815147CC2B09B31267DAF88` | Built (39 entries) — upload Aug 30 |

> After Aug 21 enrollment: run `set_paper_id.py <id>` and RE-COMPUTE these
> hashes (they will change for the two PDFs; the zip does not contain the
> paper ID and stays unchanged).

## Checklist (do in order)

### Before Aug 21 (enrollment)
- [ ] Author list finalized (no adds/removes after Aug 21)
- [ ] All author OpenReview profiles verified
- [ ] Conflicts checked on the submission form
- [ ] Title + abstract pasted from `02_OPENREVIEW_ENROLLMENT/`
- [ ] Paper ID recorded; `set_paper_id.py <id>` run
- [ ] New hashes recorded above

### Aug 28 (main.pdf)
- [ ] `main.pdf` re-built with real paper ID and header verified
      ("Submission #<id>")
- [ ] Page count within limit (5 pp total incl. references; limit 8 + refs)
- [ ] No "??" / undefined refs / missing figures in the compiled log
      (verified at freeze: 0 undefined citations, 0 overfull boxes)
- [ ] SHA-256 verified against checklist
- [ ] Uploaded to OpenReview

### Aug 30 (supplementary + code)
- [ ] `supplementary.pdf` built with real paper ID
- [ ] `wacv2027_code.zip` contents verified (scripts + seed_campaign
      artifacts + protocol manifests; 39 entries; no raw checkpoints —
      documented in zip README)
- [ ] Anonymity scan re-run on the zip (see ANONYMITY_CHECKLIST.md)
- [ ] SHA-256 verified against checklist
- [ ] Uploaded to OpenReview

## Numerical integrity gate (hard-fail rules, from Step 1 audit)

- [ ] `scripts/audit_paper2_numbers_independent.py` → verdict PASS
      (last run: PASS, zero issues; hostile-tested)
- [ ] Every number in the paper is sourced from `numerical_audit.json`
      (verified by `scripts/hostile_numerical_review.py` → PASS)
- [ ] Terminology contract held: A_transform = transformed-answer accuracy;
      C_pair = pair consistency; both_correct = joint correctness
