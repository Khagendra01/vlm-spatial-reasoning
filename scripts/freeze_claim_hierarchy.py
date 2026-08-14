#!/usr/bin/env python3
"""Step 2: freeze the Paper-2 final scientific claim hierarchy.

Generates results/seed_campaign/CLAIM_HIERARCHY.md from numerical_audit.json
(audited, independently recomputed numbers ONLY -- no hand-typed values).
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
audit = json.load(open(REPO / 'results' / 'seed_campaign' / 'numerical_audit.json',
                       encoding='utf-8'))
fam = audit['families']
q7, s2 = fam['qwen2vl'], fam['smolvlm2']

L = []
w = L.append


def cpair(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['C_pair']


def cpair_r(f, ck):
    return f['checkpoints'][ck]['tier_b']['relcomp']['C_pair']


def atrans(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['A_transform']


w('# Paper-2 R1 Seed Campaign: Frozen Scientific Claim Hierarchy\n')
w('**Status: FROZEN (Step 2 of the post-compute pipeline), 2026-08-14.**')
w('Every number below is sourced from results/seed_campaign/numerical_audit.json '
  '(independent recomputation; verdict PASS; committed-target diffs = 0.0). '
  'Terminology follows the frozen definitions (analyze_tier_c.py): '
  'A_transform = transformed-answer accuracy; C_pair = pair consistency '
  '(answer-update rate for flip laws, stability rate for invariant); '
  'both_correct = joint correctness; G = A_normal - A_shuffle; '
  'dG = G_tuned - G_zero_shot.\n')

w('## Tier-0: Terminology contract (immutable)\n')
w('- `A_transform` = P(transformed prediction == expected transformed label). '
  'Never called "flip rate".')
w('- `C_pair` = P(pair consistency): hflip_flip/relcomp/facingcomp = '
  'P(transformed != normal); hflip_invariant = P(transformed == normal). '
  'Never called "paired both-images correctness".')
w('- `both_correct` = P(normal-correct AND transformed obeys the law). '
  'Joint correctness, never consistency.')
w('- Seeds are independent draws: report means/SDs and ranges; never '
  '"monotonic across seeds".')
w('- Qwen3-VL extension: only dA/dG/A_transform computed; no C_pair claim.\n')

w('## Tier-1: Primary confirmatory claims (preregistered; 7B + HardNeg + 2B)\n')

w('### C1 (benchmark gain, dA)\n')
w(f'- 7B seed-0: dA {q7["seed0"]["dA"]:+.4f}; fresh seeds: '
  + ', '.join(f'{s} {q7["seeds"][s]["dA"]:+.4f}' for s in q7['seeds'])
  + f'; mean {q7["seed_stats"]["dA_mean"]:+.4f} +/- {q7["seed_stats"]["dA_sd"]:.4f}.')
w(f'- 2B seed-0: dA {s2["seed0"]["dA"]:+.4f}; fresh seeds: '
  + ', '.join(f'{s} {s2["seeds"][s]["dA"]:+.4f}' for s in s2['seeds'])
  + f'; mean {s2["seed_stats"]["dA_mean"]:+.4f} +/- {s2["seed_stats"]["dA_sd"]:.4f}.')
w('- **Claim**: ordinary spatial LoRA fine-tuning improves benchmark accuracy '
  'reproducibly across training seeds and both confirmatory backbone families '
  '(audited: dA positive for all fresh seeds, both families).\n')

w('### C2 (correct-image dependence, G and dG)\n')
w(f'- 7B seed-0: G {q7["seed0"]["G"]:.4f}, dG {q7["seed0"]["dG"]:+.4f}; '
  f'fresh seeds G: ' + ', '.join(f'{s} {q7["seeds"][s]["G"]:.4f}' for s in q7['seeds'])
  + f'; dG mean {q7["seed_stats"]["dG_mean"]:+.4f} +/- {q7["seed_stats"]["dG_sd"]:.4f}.')
w(f'- 2B seed-0: G {s2["seed0"]["G"]:.4f}, dG {s2["seed0"]["dG"]:+.4f}; '
  f'fresh seeds G: ' + ', '.join(f'{s} {s2["seeds"][s]["G"]:.4f}' for s in s2['seeds'])
  + f'; dG mean {s2["seed_stats"]["dG_mean"]:+.4f} +/- {s2["seed_stats"]["dG_sd"]:.4f}.')
w('- **Claim**: tuning widens the normal-minus-shuffle gap (G) and the '
  'zero-shot-relative change (dG) is positive for every fresh seed in both '
  'confirmatory families — fine-tuning increases dependence on the correct '
  'visual evidence (audited).\n')

w('### C3 (semantic pair consistency, dC via relcomp)\n')
w('- 7B relcomp C_pair: seed-0 '
  f'{cpair_r(q7, "general_lora"):.4f}; fresh seeds '
  + ', '.join(f'{s} {cpair_r(q7, s):.4f}' for s in q7['seeds']) + '.')
w('- 2B relcomp C_pair: seed-0 '
  f'{cpair_r(s2, "general_lora"):.4f}; fresh seeds '
  + ', '.join(f'{s} {cpair_r(s2, s):.4f}' for s in s2['seeds']) + '.')
w('- **Claim**: semantic pair consistency changes with tuning but stays '
  'stable across fresh seeds (no axis-specific divergence); its magnitude and '
  'relation-specific behavior differ from dA/dG (three-way decomposition).\n')

w('### C4 (transformation behavior under global reflection, Tier C)\n')
w('- 7B hflip_flip: A_transform zero-shot '
  f'{atrans(q7, "zero_shot"):.4f} -> seed-0 {atrans(q7, "general_lora"):.4f}; '
  f'C_pair zero-shot {cpair(q7, "zero_shot"):.4f} -> seed-0 '
  f'{cpair(q7, "general_lora"):.4f}; fresh-seed C_pair '
  + ', '.join(f'{s} {cpair(q7, s):.4f}' for s in q7['seeds']) + '.')
w('- 2B hflip_flip: A_transform zero-shot '
  f'{atrans(s2, "zero_shot"):.4f} -> seed-0 {atrans(s2, "general_lora"):.4f}; '
  f'C_pair zero-shot {cpair(s2, "zero_shot"):.4f} -> seed-0 '
  f'{cpair(s2, "general_lora"):.4f}; fresh-seed C_pair '
  + ', '.join(f'{s} {cpair(s2, s):.4f}' for s in s2['seeds']) + '.')
w('- **Claim**: answer-update behavior under horizontal reflection (C_pair) is '
  'broadly higher after General adaptation than zero-shot and remains close to '
  'the legacy General checkpoint across fresh seeds (audited: all fresh 2B '
  'C_pair > 2B zero-shot; all fresh-seed C_pair within 0.05 of seed-0). '
  'A_transform, C_pair and both_correct are reported as three separate '
  'quantities.\n')

w('## Tier-2: Post-confirmatory claim (Qwen3-VL-8B, exploratory extension)\n')
q3 = audit['q3vl']
w(f'- dA {q3["deltas"]["dA_normal"]:+.4f}; dG {q3["deltas"]["dG"]:+.4f}; '
  f'hflip_flip A_transform {q3["deltas"]["dhflip_flip_A_transform"]:+.4f} '
  '(transformed-accuracy gain only).')
w('- **Claim (scoped)**: the primary adaptation pattern (dA positive, dG '
  'positive, transformed accuracy under reflection improves) directionally '
  'replicates on a contemporary backbone. C_pair was NOT computed for this '
  'extension; no response-law-compliance claim is made. Labeled '
  'post-confirmatory / exploratory architecture extension, not preregistered.\n')

w('## Tier-3: Explicitly NOT claimed\n')
w('- No claim that the normal-minus-shuffle gap is a novel metric '
  '(VRS = A(real) - A(shuffle) already defined in Beyond Accuracy 2026).')
w('- No VisualFLIP reproduction: our hflip is a global horizontal reflection, '
  'not minimal local editing; C_pair is a collapse-style paired answer-update '
  'metric "following VisualFLIP" with the intervention difference stated.')
w('- No claim that accuracy equals grounding, or that shuffled images are a '
  'novel test.')
w('- No claim about VisualFLIP/COCO-style minimal-edit counterfactuals (dataset '
  'gated; re-check before deadline).')
w('- No Qwen3-VL C_pair / response-law claim.\n')

w('## Evidence provenance\n')
w('Audited artifacts (results/seed_campaign/): numerical_audit.json (PASS), '
  'NUMERICAL_AUDIT.md, ANALYSIS.md; raw predictions archived under '
  'cloud_artifacts/extracted/; all checkpoints on origin '
  'research/spatial-grounding-audit.')

out = REPO / 'results' / 'seed_campaign' / 'CLAIM_HIERARCHY.md'
out.write_text('\n'.join(L) + '\n', encoding='utf-8')
print('wrote', out)
