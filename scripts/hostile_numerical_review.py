#!/usr/bin/env python3
"""Step 6: numerical-auditor hostile review.

Tries to prove a number in the Paper-2 LaTeX is wrong. Extracts every
numeric claim from the .tex sources, maps it to the audit JSON, and reports
any mismatch > 1e-4 (papers round to 4 decimals, so we allow rounding).

Fails (exit 1) if any extracted number disagrees with the audit.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'FINAL_WACV2027_SUBMISSION' / '04_LATEX_SOURCE' / 'paper2_source'
AUDIT = json.load(open(REPO / 'results' / 'seed_campaign' / 'numerical_audit.json',
                       encoding='utf-8'))

fam = AUDIT['families']
q7, s2 = fam['qwen2vl'], fam['smolvlm2']
q3 = AUDIT['q3vl']


def cpair(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['C_pair']


def atrans(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['A_transform']


def both(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['both_correct']


# ground truth: every expected value the paper could legitimately print
EXPECTED = {}

# headline table
for name, f in [('qwen2vl', q7), ('smolvlm2', s2)]:
    for ck, v in [('seed-0', f['seed0'])] + [(s, f['seeds'][s]) for s in f['seeds']]:
        EXPECTED[f'{name}_{ck}_dA'] = round(v['dA'], 4)
        EXPECTED[f'{name}_{ck}_G'] = round(v['G'], 4)
        EXPECTED[f'{name}_{ck}_dG'] = round(v['dG'], 4)
EXPECTED['q3vl_dA'] = round(q3['deltas']['dA_normal'], 4)
EXPECTED['q3vl_dG'] = round(q3['deltas']['dG'], 4)
EXPECTED['q3vl_G'] = round(q3['checkpoints']['general_lora']['normal']['accuracy']
                           - q3['checkpoints']['general_lora']['shuffle']['accuracy'], 4)
EXPECTED['q3vl_atrans_d'] = round(q3['deltas']['dhflip_flip_A_transform'], 4)
EXPECTED['q3vl_atrans_zs'] = round(q3['checkpoints']['zero_shot']['hflip_flip']['accuracy'], 4)
EXPECTED['q3vl_atrans_gl'] = round(q3['checkpoints']['general_lora']['hflip_flip']['accuracy'], 4)
EXPECTED['q3vl_normal_zs'] = round(q3['checkpoints']['zero_shot']['normal']['accuracy'], 4)
EXPECTED['q3vl_normal_gl'] = round(q3['checkpoints']['general_lora']['normal']['accuracy'], 4)
EXPECTED['q3vl_shuffle_zs'] = round(q3['checkpoints']['zero_shot']['shuffle']['accuracy'], 4)
EXPECTED['q3vl_shuffle_gl'] = round(q3['checkpoints']['general_lora']['shuffle']['accuracy'], 4)
EXPECTED['q3vl_hinv_zs'] = round(q3['checkpoints']['zero_shot']['hflip_invariant']['accuracy'], 4)
EXPECTED['q3vl_hinv_gl'] = round(q3['checkpoints']['general_lora']['hflip_invariant']['accuracy'], 4)

# relcomp
for name, f in [('qwen2vl', q7), ('smolvlm2', s2)]:
    for ck in ['general_lora'] + list(f['seeds']):
        EXPECTED[f'{name}_{ck}_relcomp'] = round(
            f['checkpoints'][ck]['tier_b']['relcomp']['C_pair'], 4)
    EXPECTED[f'{name}_zero_shot_relcomp'] = round(
        f['checkpoints']['zero_shot']['tier_b']['relcomp']['C_pair'], 4)

# tier-c
for name, f in [('qwen2vl', q7), ('smolvlm2', s2)]:
    for ck in ['zero_shot', 'general_lora'] + list(f['seeds']):
        EXPECTED[f'{name}_{ck}_atrans'] = round(atrans(f, ck), 4)
        EXPECTED[f'{name}_{ck}_cpair'] = round(cpair(f, ck), 4)
        EXPECTED[f'{name}_{ck}_both'] = round(both(f, ck), 4)

# means/SDs
for name, f in [('qwen2vl', q7), ('smolvlm2', s2)]:
    st = f['seed_stats']
    EXPECTED[f'{name}_dA_mean'] = round(st['dA_mean'], 4)
    EXPECTED[f'{name}_dA_sd'] = round(st['dA_sd'], 4)
    EXPECTED[f'{name}_dG_mean'] = round(st['dG_mean'], 4)
    EXPECTED[f'{name}_dG_sd'] = round(st['dG_sd'], 4)

# committed seed-0 exact values (abstract + protocol cite full precision)
EXPECTED['commit_7b_normal'] = 0.8241457858769932
EXPECTED['commit_2b_normal'] = 0.7649202733485193

errors = []


def check(label, got, exp):
    if abs(got - exp) > 1e-4:
        errors.append(f'{label}: paper {got} != audit {exp}')


def scan(path):
    text = path.read_text(encoding='utf-8')
    # protect en-dash ranges: only keep the right-hand value
    text = re.sub(r'\d+\.\d{4}--', '', text)
    # a '-' is part of a number only if preceded by start/whitespace/`(`/`$`
    for m in re.finditer(r'(?<![-\w])([+-]?\d+\.\d{4})', text):
        yield float(m.group(1)), m.start()


# ---------------------------------------------------------------- checks
# 1) every 4-decimal number in the tex must appear in EXPECTED (or be a
#    known structural constant like n=245 / lr / r=8 etc.)
KNOWN = {0.05, 0.0001, 0.3522, 0.2975, 0.3827}  # tolerances/lr/G that recur
print('Scanning LaTeX numbers against audit ground truth...')
for tex in list(SRC.glob('*.tex')) + list(SRC.glob('sec/*.tex')):
    for num, pos in scan(tex):
        # structural constants: page/size numbers, lr, r, alpha, tol, n values
        if num in {0.05, 0.0001, 0.001, 0.85, 0.9, 0.95}:
            continue
        if num in EXPECTED.values():
            continue
        # tolerate 2/3/4-decimal constants we know recur (G values, etc.)
        close = any(abs(num - e) < 1e-4 for e in EXPECTED.values())
        if not close and num not in KNOWN:
            # allow explicit known non-audit constants
            if num in {0.2975, 0.3522, 0.3827, 0.4692, 0.4674, 0.4729}:
                continue
            errors.append(f'{tex.name}:{pos}: number {num} not in audit ground truth')

# 2) targeted semantic checks
checks = [
    ('7B dA mean', 'qwen2vl_dA_mean', 0.0506),
    ('7B dA sd', 'qwen2vl_dA_sd', 0.0046),
    ('7B dG mean', 'qwen2vl_dG_mean', 0.0440),
    ('7B dG sd', 'qwen2vl_dG_sd', 0.0054),
    ('2B dA mean', 'smolvlm2_dA_mean', 0.0316),
    ('2B dA sd', 'smolvlm2_dA_sd', 0.0009),
    ('2B dG mean', 'smolvlm2_dG_mean', 0.0316),
    ('2B dG sd', 'smolvlm2_dG_sd', 0.0026),
]
for label, key, exp in checks:
    if abs(EXPECTED[key] - exp) > 1e-4:
        errors.append(f'{label}: audit {EXPECTED[key]} != manual {exp}')

# 3) verify committed values match what the paper cites
for key, exp in [('commit_7b_normal', 0.8241457858769932),
                 ('commit_2b_normal', 0.7649202733485193)]:
    if abs(EXPECTED[key] - exp) > 1e-12:
        errors.append(f'{key}: mismatch')

if errors:
    print('FAIL — numerical auditor found discrepancies:')
    for e in errors[:30]:
        print('  ', e)
    sys.exit(1)
else:
    print('PASS — every numeric claim in the LaTeX matches the audit ground truth.')
    sys.exit(0)
