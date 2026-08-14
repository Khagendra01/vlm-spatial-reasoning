# Anonymity Checklist — Paper 2

**Status: PASS at freeze (2026-08-14).** Reviewed the LaTeX sources and the
upload artifacts for identifying information. GPU off; no new artifacts
created after this scan.

## Scan results

| Artifact | Identifying content found | Verdict |
|---|---|---|
| main.tex + sec/*.tex + suppl.tex | None — "Anonymous Authors / Anonymous Institution", `\wacvPaperID{*****}` | PASS |
| references.bib | Public arXiv/venue entries only; no author self-citations | PASS |
| figures (3 PNGs) | Data plots only; no names, URLs, or institutional marks | PASS |
| wacv2027_code.zip | Scripts reference only repo-relative paths and model names (Qwen2-VL-7B, SmolVLM2-2B, Qwen3-VL-8B); no author identifiers | PASS |

## Things to re-check at upload time (Aug 28 / Aug 30)

- [ ] After `set_paper_id.py` — re-scan `main.pdf`/`supplementary.pdf`
      headers for stray names (the build is deterministic; only the paper
      ID changes).
- [ ] If any new file is added to the code zip, re-scan it: no real names,
      emails, institutional URLs, or "code available at <repo>" lines that
      identify the authors.
- [ ] OpenReview author field on the submission form must remain empty for
      the review version (the reviewer-facing PDF is anonymous regardless).

## Decision-log provenance

Anonymity for the paper body was part of the original protocol (Paper 1
same convention). This checklist is the Paper-2 mirror. The decision log
(`SPATIAL_REASONING_DECISION_LOG.md`) holds the governance entries.
