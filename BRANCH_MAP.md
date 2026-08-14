# Repository Branch Map

Last updated: 2026-08-14 (branch reorganization)

## Canonical branches

| Branch | What it is | Workspace clone |
|---|---|---|
| `master` | Trunk. Default branch on GitHub. Shared code, docs, scripts, results. | both |
| `paper1/wacv2027` | **Paper 1**: "Beyond Spatial Accuracy: Diagnosing Persistent Orientation Failures in Vision-Language Models" (WACV 2027 Datasets Track). Contains the Capability Audit Ladder manuscript, external flagship eval CSVs, `FINAL_WACV2027_SUBMISSION/` (Paper-1 submission kit). | `Desktop\VLM-Spatial-Reasoning` |
| `paper2/wacv2027` | **Paper 2**: "What Spatial Fine-Tuning Actually Changes" (WACV 2027 Datasets Track). Seed campaign (ΔA/ΔG/ΔC, multi-seed, Qwen2-VL-7B / SmolVLM2-2B / Qwen3-VL-8B), independent numerical audit, claim hierarchy, figures/tables, `FINAL_WACV2027_SUBMISSION_PAPER2/` (Paper-2 submission kit). | `Documents\vlm-spatial-reasoning` |
| `research/equiorient` | EquiOrient study line (separate research thread: protocol freeze, MUTATE novelty gate, decision log under `research/`). | — |

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
