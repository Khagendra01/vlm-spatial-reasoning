# Baseline Reconciliation: Paper-1 (80.91%) vs Tier-A (76.99%) zero-shot normal

- **Date:** 2026-08-11
- **Question:** why does the frozen Paper-1 7B zero-shot VSR test accuracy (0.80911) differ from the Tier-A full normal-condition accuracy (0.76993)?
- **Status:** root cause isolated and reproduced; documentation only (no protocol change, no numbers modified).

## Paper-1 numbers (master branch, frozen artifacts)

| checkpoint | accuracy | source |
|---|---|---|
| 7B zero-shot | 0.80911 (1776/2195) | results/qwen2vl_7b_metrics_20260809_064919.json |
| 7B General LoRA | 0.84692 (1859/2195) | results/7B_general_lora_metrics_20260809_094930.json |
| 7B HardNeg LoRA | 0.84328 (1851/2195) | results/7B_hardneg_lora_metrics_20260809_164619.json |

## Paper-2 (Tier-A full) numbers (research/spatial-grounding-audit)

| checkpoint | accuracy | source |
|---|---|---|
| 7B zero-shot | 0.76993 (1690/2195) | results/grounding/analysis/tier_a_metrics_full.json |
| 7B General LoRA | 0.82415 | same |
| 7B HardNeg LoRA | 0.82916 | same |

## Contract diff (Paper-1 evaluator = scripts/run_7b_pipeline.py phase1; Tier-A = scripts/grounding/run_tier_a.py + src/grounding)

| element | Paper-1 | Tier-A | effect |
|---|---|---|---|
| prompt | identical template | identical | none |
| max_new_tokens | 5 | 5 | none |
| sampling | greedy (do_sample=False) | greedy | none |
| dtype / attn | bf16 / eager | bf16 / eager | none |
| images | raw cached JPEG -> processor | 392px long-side cap (BILINEAR) -> processor | **the only behaviorally relevant difference** |
| chat template | apply_chat_template(padding=True) | same + truncation=True | inert (see reproduction) |
| parser | inline parse_tf | src/evaluation/parser.py parse_true_false (identical file on both branches) | none (0 raw-output-identical rows reclassified) |
| example set/order | dataset order, id = index | dataset order, vsr_test:<index> | identical (verified: same 2195 rows, content hashes) |
| env | transformers>=4.48.0 floor only | transformers 5.14.1 | residual ~3% noise, unpinnable |

## Alignment evidence (Paper-1 predictions CSV vs Tier-A zero_shot_normal.csv)

- 1987/2195 same prediction; **208 differ**.
- **0** examples share the same raw model output but a different parsed label -> parser contributes nothing; all 208 are genuinely different model outputs.
- Raw-output transitions among the 208: 142 True->False, 66 False->True (net accuracy loss 86 correct rows).
- Disagreements span all relation families (vertical 34, topology_contact 36, depth 40, horizontal 31, proximity 23, orientation 17, containment 11, compositional 7, other 9) — consistent with an input-fidelity effect, not a parser or single-relation effect.

## GPU reproduction (all 208 disagreements, zero-shot Qwen2-VL-7B, current env)

| variant | match Paper-1 | match Tier-A |
|---|---|---|
| P1: raw image, padding=True (Paper-1 exact) | 201/208 (96.6%) | 7/208 |
| A: 392-cap + padding + truncation (Tier-A exact) | 4/208 | 204/208 (98.1%) |
| A1: raw image + padding + truncation | 201/208 | 7/208 |
| A2: 392-cap + padding (no truncation) | 4/208 | 204/208 |

## Conclusion

- The uniform **392px long-side image cap** alone explains ~97% of the prediction changes (and the residual ~3% is environment-version noise with no recorded Paper-1 exact versions).
- The cap is **intentional and documented** (docs/TECHNIQUES.md section 4), frozen in config.py (MAX_LONG_SIDE=392), and recorded in every Tier-A/B/C run_metadata.json.
- **Internal validity of Tier A/B/C is unaffected:** the cap is a constant across checkpoints and conditions; all paired ΔA / ΔG / ΔC / D1 conclusions are checkpoint-symmetric.
- **Cross-paper comparability requires a caveat:** absolute Tier-A accuracies must not be compared to Paper-1 without citing the cap difference. Paper-2 can either keep the 392px contract (documenting this reconciliation) or rerun under the full-resolution Paper-1 contract (new freeze + runs; existing numbers unchanged).

## Artifacts

- disagreement IDs: /tmp/opencode/disagreement_ids.json
- reproduction summary: /tmp/opencode/repro_summary.json
- reproduction script: /tmp/opencode/repro_baseline.py
- decision-log entry: research/DECISION_LOG.md (2026-08-11)
