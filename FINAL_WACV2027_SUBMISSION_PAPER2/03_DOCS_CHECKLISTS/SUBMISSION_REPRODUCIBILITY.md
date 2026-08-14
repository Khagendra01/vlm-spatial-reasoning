# Submission Reproducibility — Paper 2

**Frozen artifact chain (all committed on `research/spatial-grounding-audit`):**

1. **Raw predictions** — `results/seed_campaign/cloud_artifacts/extracted/
   <qwen2vl|smolvlm2|q3vl>/results/grounding/predictions/*.csv|*.jsonl`
   (battery zips archived under `results/seed_campaign/cloud_artifacts/`).
2. **Frozen protocol** — `results/grounding/protocol/`: `vsr_test_ids.json`
   (n=2195), `visual_eligible_ids.json` (hflip_flip 245, hflip_invariant
   421), `semantic_eligible_ids.json` (relcomp 666), `facing_eligible_ids.json`
   (facingcomp 103), `shuffle_mapping.json`, `run_config_snapshot.json`.
3. **Training recipe** — `configs/seed_campaign/SEED_CAMPAIGN.json` +
   `SPATIAL_REASONING_DECISION_LOG.md` (seed-0 recipe: epochs 2, lr 1e-4,
   LoRA r=8 alpha=16 dropout 0.05, bf16, gradient checkpointing; fresh seeds
   differ only in the explicit per-run seed 101/202/303).
4. **Independent numerical audit** — `scripts/audit_paper2_numbers_independent.py`
   (no analyzer imports; recomputes every headline quantity from raw
   predictions + frozen manifests; hard-fail rules). Verdict PASS;
   committed-target reproduction byte-identical (7B normal 0.82414579,
   2B 0.76492027, abs diff 0.0). Hostile-tested: planted single-prediction
   flips → FAIL → restore → PASS.
5. **Analysis + figures + tables** — `results/seed_campaign/ANALYSIS.md`,
   `figures/` (fig1-3 PNG + PUBLICATION_TABLES.md), all generated from the
   audit JSON (no hand-typed numbers).
6. **Claim hierarchy** — `results/seed_campaign/CLAIM_HIERARCHY.md` (C1-C5).
7. **Literature/novelty audit** — `results/seed_campaign/LITERATURE_NOVELTY_AUDIT.md`.
8. **Hostile reviews** — `results/seed_campaign/HOSTILE_REVIEW.md` +
   `scripts/hostile_numerical_review.py` (scans the paper's LaTeX numbers
   against the audit; PASS).

## Reproduce the numbers (local, no GPU)

```
python scripts/audit_paper2_numbers_independent.py   # -> numerical_audit.json
python scripts/render_audit_md.py                     # -> NUMERICAL_AUDIT.md
python scripts/freeze_claim_hierarchy.py              # -> CLAIM_HIERARCHY.md
python scripts/make_pub_figures.py                    # -> figures/ + tables
python scripts/hostile_numerical_review.py            # -> paper-number scan
python scripts/grounding/analyze_seed_campaign.py     # -> ANALYSIS.md
```

## Reproduce the paper (local, no GPU)

```
cd FINAL_WACV2027_SUBMISSION_PAPER2/04_LATEX_SOURCE/paper2_source
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
pdflatex suppl.tex && pdflatex suppl.tex
```
(MiKTeX 26.5 toolchain; `wacv.sty` + `ieeenat_fullname.bst` included.)

## GPU-dependent artifacts (NOT in the code zip)

Model checkpoints, adapter weights, and the raw image cache live in the
repository/archive per the decision log; they are large and excluded from
`wacv2027_code.zip`. The audit, analysis, figures, and paper require only
the prediction artifacts + manifests above.
