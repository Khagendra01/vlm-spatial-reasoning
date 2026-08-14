#!/usr/bin/env python3
"""Render NUMERICAL_AUDIT.md from numerical_audit.json (post-audit only)."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
d = json.load(open(REPO / 'results' / 'seed_campaign' / 'numerical_audit.json',
                   encoding='utf-8'))

L = []
w = L.append
w('# Paper-2 R1 Seed Campaign: Independent Numerical Audit\n')
w(f'**Verdict: {d["verdict"]}**\n')
w('Method: standalone reimplementation (scripts/audit_paper2_numbers_independent.py) '
  'of the frozen metric formulas directly from raw prediction CSVs/JSONL and frozen '
  'protocol manifests. No analyzer module imported; committed analysis JSONs loaded '
  'only as comparison targets. Hard-fail rule: any deterministic-proportion '
  'discrepancy > 1e-6, any row-count/ID mismatch, any terminology mismatch => FAIL.\n')

if d['issues']:
    w('## Issues\n')
    for i in d['issues']:
        w(f'- {i}')
    w('')

w('## Claim-level audit\n')
for k, v in d['claims'].items():
    w(f'- **{k}**: {"PASS" if v else "FAIL"}')
w('')

for fam in ['qwen2vl', 'smolvlm2']:
    f = d['families'][fam]
    w(f'## {fam}\n')
    w('### Committed-target check (general_lora, tier-a)\n')
    w('| condition | committed | recomputed | abs diff | pass |')
    w('|---|---|---|---|---|')
    for k, v in f['committed_check'].items():
        w(f'| {k} | {v["committed"]:.8f} | {v["recomputed"]:.8f} | '
          f'{v["abs_diff"]:.2e} | {v["pass"]} |')
    w('')
    w('### Headline quantities\n')
    w(f'- seed-0: dA {f["seed0"]["dA"]:+.4f}, dG {f["seed0"]["dG"]:+.4f}, '
      f'G {f["seed0"]["G"]:.4f}')
    for s, v in f['seeds'].items():
        w(f'- {s}: dA {v["dA"]:+.4f}, dG {v["dG"]:+.4f}, G {v["G"]:.4f}')
    st = f['seed_stats']
    w(f'- fresh-seed dA: mean {st["dA_mean"]:.4f} +/- {st["dA_sd"]:.4f}; '
      f'dG: mean {st["dG_mean"]:.4f} +/- {st["dG_sd"]:.4f}')
    w('')
    w('### Tier-C hflip_flip (n=245)\n')
    w('| checkpoint | A_transform | C_pair | both_correct |')
    w('|---|---|---|---|')
    for ck in ['zero_shot', 'general_lora'] + [s for s in f['seeds']]:
        v = f['checkpoints'][ck]['tier_c']['hflip_flip']
        w(f'| {ck} | {v["A_transform"]:.4f} | {v["C_pair"]:.4f} | '
          f'{v["both_correct"]:.4f} |')
    w('')

q3 = d['q3vl']
w('## Qwen3-VL-8B (extension; only computed quantities)\n')
w('| checkpoint | normal | shuffle | hflip_flip A_transform | hflip_invariant A_transform |')
w('|---|---|---|---|---|')
for ck in ['zero_shot', 'general_lora']:
    c = q3['checkpoints'][ck]
    w(f'| {ck} | {c["normal"]["accuracy"]:.4f} | {c["shuffle"]["accuracy"]:.4f} '
      f'| {c["hflip_flip"]["accuracy"]:.4f} | {c["hflip_invariant"]["accuracy"]:.4f} |')
w('')
w('Q3VL deltas: dA {:+.4f}, dG {:+.4f}, hflip_flip A_transform {:+.4f} (transformed-'
  'accuracy gain only; C_pair NOT computed for the extension).'.format(
      q3['deltas']['dA_normal'], q3['deltas']['dG'],
      q3['deltas']['dhflip_flip_A_transform']))
w('')

w('## Terminology audit\n')
w('- A_transform = P(transformed prediction == expected transformed label): '
  'transformed-answer accuracy. Used consistently in tables above (never "flip rate").')
w('- C_pair = P(pair consistency): linked-answer law compliance '
  '(hflip_flip/relcomp/facing: P(transformed != normal); hflip_invariant: '
  'P(transformed == normal)). Recomputed by joining normal and transformed '
  'predictions on example_id.')
w('- both_correct = P(normal-correct AND transformed obeys the law): joint '
  'correctness, never consistency.')
w('- Seeds are independent draws: fresh-seed statements report means/SDs and '
  'ranges, never "monotonic".')

out = REPO / 'results' / 'seed_campaign' / 'NUMERICAL_AUDIT.md'
out.write_text('\n'.join(L) + '\n', encoding='utf-8')
print('wrote', out)
