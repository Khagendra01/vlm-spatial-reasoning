# Repository Branch Map

Last updated: 2026-08-14 (branch reorganization + master backfill)

## Governance model (how the repo grows)

```
master  ← TRUNK: single source of truth for ALL shared research code,
           protocol definitions, configs, tests, and shared docs.
           (src/, scripts/, configs/, tests/, research/ live ONLY here.)
   │
   ├── paper1/wacv2027   ← Paper-1-specific: manuscript, external-eval CSVs,
   │                        submission kit FINAL_WACV2027_SUBMISSION/
   ├── paper2/wacv2027   ← Paper-2-specific: seed-campaign outputs,
   │                        submission kit FINAL_WACV2027_SUBMISSION_PAPER2/
   └── (future papers branch from master, same pattern)
```

**Rules:**
1. New shared research code (scripts, src, configs, tests, protocol docs)
   → developed on a branch → **merged back to master when stable**.
2. Paper branches hold ONLY paper-specific artifacts: manuscripts,
   per-paper analysis outputs, submission kits. Never duplicated shared code.
3. Before starting any new paper: branch fresh from **master** (pulls all
   shared code), not from an older paper branch.
4. Pull master into a paper branch when shared code updates are needed
   (rare mid-paper; the frozen submission layer never syncs mid-deadline).
5. `research/equiorient` = Paper-3 research line (EquiOrient): pulls shared
   code from master (merged 2026-08-14, `d76c1e6`), pushes stable infra back
   to master, and carries NO paper-specific artifacts (Paper-1-era leftovers
   removed `6124eab`; canonical copies on paper1/wacv2027).

## Branch contents

| Branch | What it is | Workspace clone |
|---|---|---|
| `master` | Trunk. Default branch on GitHub. Shared code + protocol + tests + shared docs. | both |
| `paper1/wacv2027` | **Paper 1**: "Beyond Spatial Accuracy..." (WACV 2027 Datasets Track). Manuscript at `submission/wacv2027/source/`, external flagship eval CSVs, Paper-1 submission kit `FINAL_WACV2027_SUBMISSION/`. | `Desktop\VLM-Spatial-Reasoning` |
| `paper2/wacv2027` | **Paper 2**: "What Spatial Fine-Tuning Actually Changes" (WACV 2027 Datasets Track). Seed campaign outputs, audit artifacts, Paper-2 submission kit `FINAL_WACV2027_SUBMISSION_PAPER2/`. | `Documents\vlm-spatial-reasoning` |
| `research/equiorient` | **Paper 3** (EquiOrient): method paper on transformation-equivariant spatial representation learning. Status: novelty gate CLOSED (MUTATE verdict); protocol/config amendment + transformation algebra pending before GPU. Own docs under `research/EQUIORIENT_*` + `configs/equiorient_protocol.yaml` + shared layer from master. | — |

## Kit ownership

- Paper-1 kit `FINAL_WACV2027_SUBMISSION/` lives on **`paper1/wacv2027`** (moved verbatim from the Paper-2 line; commits `00d85b8` on paper1, `44df918` on paper2).
- Paper-2 kit `FINAL_WACV2027_SUBMISSION_PAPER2/` lives on **`paper2/wacv2027`**.
- The old `FINAL_WACV2027_SUBMISSION/04_LATEX_SOURCE/paper2_source/` copy was a byte-identical duplicate (hash-verified); deleted, zero loss.

## Master backfill (2026-08-14, commit `4408735`)

Master was stale relative to the shared research layer built on the Paper-2
line. Backfilled with 60 files that were **pure additions** vs the master
base (verified: 0 modifications, 0 deletions — no conflicts, no history
rewrite): `src/grounding/`, `src/evaluation/battery.py`, `scripts/grounding/`,
audit scripts, `configs/` (grounding protocol + seed campaign), `tests/`,
`research/` docs. Paper-2-specific artifacts intentionally left on paper2.

## Archive tags (old branch names, preserved forever)

| Tag | Points at |
|---|---|
| `archive/paper-draft-v1` | former Paper-1 branch tip `e3bd95b` |
| `archive/research-spatial-grounding-audit` | former Paper-2 branch tip `586ad24` |
| `archive/external-eval-flagship-v1` | former external-eval branch tip `dd8517a` |
| `archive/research-equiorient` | former equiorient tip `1161b24` |

## Renaming history (2026-08-14)

- `paper-draft-v1` → `paper1/wacv2027` (Paper 1)
- `research/spatial-grounding-audit` → `paper2/wacv2027` (Paper 2)
- `external-eval/flagship-v1` → `paper1/external-eval` → **deleted** (fully merged into `paper1/wacv2027`; raw provenance CSVs live at repo root on that branch and canonical copies under `results/iaa/`; archive tag preserved)
- `research/equiorient` → kept unchanged
- Open DRAFT PR #1 ("Start conference-style paper draft", head `paper-draft-v1`) auto-closed by branch deletion; its content is fully in `paper1/wacv2027`.

## Submission state (2026-08-14)

Both papers target WACV 2027 (Datasets Track), same deadline card:

| Date (AoE) | Action |
|---|---|
| Aug 21 | OpenReview enrollment (paste title/abstract, final author list) |
| Aug 28 | Upload main.pdf |
| Aug 30 | Upload supplementary.pdf + code zip |

- Paper 1 kit: `FINAL_WACV2027_SUBMISSION/` (PDFs, checklists, hashes in `03_DOCS_CHECKLISTS/`)
- Paper 2 kit: `FINAL_WACV2027_SUBMISSION_PAPER2/` (same layout; compiled main.pdf 5pp + supplementary.pdf 1p + wacv2027_code.zip, SHA-256s in checklist)
- GPU compute: OFF for both.
