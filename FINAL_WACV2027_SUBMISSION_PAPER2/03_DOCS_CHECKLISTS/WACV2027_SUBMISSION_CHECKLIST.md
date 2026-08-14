# WACV 2027 Submission Checklist — Paper 2

**Kit:** `FINAL_WACV2027_SUBMISSION_PAPER2/`
**Status at freeze:** all three upload artifacts built and hashed (2026-08-14).
**GPU compute:** OFF (no further model compute; this is the post-compute layer).

## Upload artifacts (01_UPLOAD_THIS/)

| File | Size | SHA-256 | Status |
|---|---|---|---|
| main.pdf | 0.42 MB | `D6AF008E927E893FBB52A6B88B8BD69FBE5F4973BC15D7A6282EBE02F04CBBA6` | Built (5 pp, anonymous `#*****`) — upload Aug 28 |
| supplementary.pdf | 0.12 MB | `A4A55543A9BBC61A2C468063C87F3B4C4A3EBC9FCF639082265B579DA85BD57B` | Built (1 p, anonymous) — upload Aug 30 |
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
