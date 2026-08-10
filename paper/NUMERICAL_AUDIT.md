# Numerical Audit: Every Headline Number → Artifact

Audit date: 2026-08-10. Every headline number in `paper/main.tex` / `paper/suppl.tex`
traced to a committed artifact. The audit script
`scripts/make_paper_figures.py` recomputes the VSR and SITE tables directly from
the raw prediction CSVs; its full output is archived at `paper/fig/audit_output.txt`.

## Headline numbers (user list)

| Number | Where it appears | Artifact (file → value) | Verdict |
|---|---|---|---|
| **74.0** | Abstract, Table 1 | `results/smolvlm2_metrics_2195_20260808_214536.json` → `global.accuracy = 0.73986`; CSV recompute: 1624/2195 = 74.0% | ✅ bit-identical |
| **80.9** | Abstract, Table 1 | `results/qwen2vl_7b_metrics_20260809_064919.json` → `0.80911`; CSV: 1776/2195 | ✅ |
| **62.8** | Abstract, §4 | 2B zero-shot orientation family = 86/137 = 62.77% (computed from `smolvlm2_baseline_2195_20260808_214536.csv` via `orientation_analysis.json` per-relation cells 70.3/53.8/59.1/58.3) | ✅ (86 = 45+21+13+7) |
| **63.5** | Abstract, Table 1 | `qwen2vl_7b_metrics_20260809_064919.json` → `by_family.orientation = 0.63504`; CSV: 87/137 | ✅ |
| **66.4** | Table 1 | `7B_hardneg_lora_metrics_20260809_164619.json` → `0.66423`; CSV: 91/137 | ✅ |
| **36.9** | Abstract, §6.4, Fig 2 | `results/consistency_stats_all.json` → `7B_zero_shot.FF.cons = 38/103 = 36.89%`; `consistency_report.md` | ✅ |
| **66.0** | Abstract, §6.4, Fig 2 | `consistency_stats_all.json` → `LM_only_LoRA.FF.cons = 68/103 = 66.02%` | ✅ |
| **77.7** | Abstract, §6.4, Fig 2 | `consistency_stats_all.json` → `hardneg_LoRA.FF.cons = 80/103 = 77.67%` | ✅ |
| **75.1** | Abstract, Table 4, §7 | `results/site/zeroshot_7b_predictions.csv` (primary = 993 rows, 746 correct = 75.13%) ≡ `zeroshot_image_metrics.json` `0.75126` | ✅ both artifacts agree |
| **47.3** | ⚠️ NOT in paper — see below | `zeroshot_image_metrics.json` → `orientation_heuristic.n = 1824, raw 0.47259` | ⚠️ superseded |
| **71.6** | §4.3, App C | `results/probe/clear_subset_results.json` → ungrounded merger-linear strict-subset test acc `0.71656` | ✅ |

## SITE secondary-subset discrepancy (47.3 vs 48.3) — RESOLVED

Two committed artifacts disagree on the secondary (orientation-keyword) subset:

- `results/site/zeroshot_image_metrics.json` (run-time metrics): n = 1,824, raw 47.3%, CAA 22.6%.
- `results/site/zeroshot_7b_predictions.csv` (row-level, final): n = 2,024 rows tagged `secondary` (incl. overlaps), raw 48.32%, CAA 23.96%.

Resolution: the **frozen protocol** `results/site/site_protocol.json` (config hash
`28f4cc09887477af`) defines the secondary subset with 2,024 image IDs — exactly
matching the CSV. All other numbers (all-images 54.2/31.1, primary 75.1/59.2,
modalities, per-source) are **bit-identical** between the two artifacts
(verified by recomputation). The 1,824 figure was computed from an
intermediate results state before the final resume pass re-tagged rows.

**Decision:** the paper reports the CSV+protocol-consistent values
(2,024; 48.3%; 24.0%) and documents the discrepancy explicitly in §7 and
App. G. Both values support the same conclusion (orientation ≪ primary).
`47.3` remains traceable to the metrics JSON if a reviewer asks.

## All p-values in the paper

| p-value | Artifact | Verdict |
|---|---|---|
| HardNeg vs General overall: 0.508 (52/60) | `hardneg_analysis_report.md` | ✅ |
| Weak families pooled: 0.461 (20/26) | same | ✅ |
| Projector overall worse: 0.0043 | `results/vision_side_comparison.json` + `vision_side_report.md` | ✅ |
| Vision+Proj overall worse: 0.0122 | same | ✅ |
| Projector orientation: 0.86; V+Proj: 0.85 | same | ✅ |
| Per-relation (IDs 7–16): 0.25–1.00 | same (enumerated in App. D) | ✅ |
| Two-stage: 0.0003 (45/16), <0.0001 (47/14), 0.0037 (44/20), 0.0004 (47/18) | `results/two_stage_results.json` → `mcnemar` | ✅ |
| Consistency: <0.0001 (117/43), 0.29 (31/41), 0.18 (63/48), 0.47 (65/56) | `consistency_report.md` (stats from flip CSVs) | ✅ |

## Other verified claims

- 2B General 76.6 / Targeted 76.5 / structured 68.3: metrics JSONs `0.76629/0.76538/0.68337` ✅
- 7B Projector 82.9 (orient. 64.2), Vision+Proj 83.1 (64.2): metrics JSONs `0.82870/0.83103`, `by_family.orientation = 0.64234` both ✅
- Orientation per-relation (4 conditions): `orientation_analysis.json` + hardneg CSV ✅ (Fig 1 data)
- Deep-dive taxonomy 18/8/6/5/4/4/2/1 = 48; 37.5/16.7/12.5/10.4/8.3/8.3/4.2/2.1% ✅ `orientation_persistent_annotations.csv`/report
- Probes T1/T2/T3 all cells: `results/probe/probe_results.json`, `patch_probe_results.json` ✅
- Grounded probes incl. 71.7% geometry cell (CV 61.1%): `grounded_probe_results.json` ✅
- Clear-subset 68.9/71.1/71.6 & generative 64.1/66.0/68.2, 68.9/72.2/78.4: `clear_subset_results.json` ✅
- Two-stage 4-way classifier CV 44.1–45.8%: `two_stage_results.json` ✅
- Consistency n: left/right 245, front/behind 314, facing 103, parallel/perp 34; front/behind 57.0→70.7→71.3%; both-True 5.9/32.4/32.4/14.7/38.2% ✅ `consistency_stats_all.json`
- SITE by-source table (22 rows): recomputed from CSV ≡ report ✅ (e.g., CLEVR 92.6/88.3, VSR 85.9/71.8, SAT 46.4/−7.1)
- SITE secondary by-category: 866/488/346/186/91/47 = 2,024 ✅ (audit output)
- HardNeg persistent: 20→15 still failing, 5 fixed of 48 ✅ `hardneg_analysis_report.md`
- Scaling transitions 28/23/22/64; adaptation 20/30/27/60 ✅ `orientation_analysis.json`

## Known limitations recorded in the paper (App. G)

- Single seed per condition; per-run seeds not recorded in metrics JSONs.
- `requirements.txt` stale; environment described per run in App. G.
- 2B structured prompt: single run.
- The `lineno.sty` UTF-8 warning and font-shape warnings are artifacts of the
  official CVPR template under the XeTeX engine (reproduced with the pristine
  author kit); they do not affect output.
