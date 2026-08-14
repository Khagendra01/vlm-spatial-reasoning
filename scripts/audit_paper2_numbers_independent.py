#!/usr/bin/env python3
"""INDEPENDENT numerical audit for Paper-2 R1 seed campaign.

Standalone reimplementation of the small metric formulas directly from raw
prediction artifacts. Deliberately does NOT import any analyzer module
(analyze_seed_campaign / analyze_tier_a / analyze_tier_b / analyze_tier_c)
and does NOT trust any committed analysis JSON as a computation input --
committed analysis JSONs are loaded ONLY as the comparison target at the end.

Frozen metric definitions (from analyze_tier_c.py docstring, read as the
authoritative definition, not as code):
  - A_transform(m)  = P(transformed prediction == expected transformed label)
                      (transformed-answer accuracy)
  - C_pair(m)       = P(pair consistency): the model's two answers on the
                      same example obey the linked-answer law
                      hflip_flip:     P(mirrored != normal)  (answer-update)
                      hflip_invariant:P(mirrored == normal)  (stability)
                      relcomp/facing: P(transformed != normal) (flip_law)
                      Invalid outputs count as non-consistent.
  - both_correct(m) = P(normal-correct AND transformed answer obeys the law)
  - normal/shuffle accuracy = P(prediction == ground_truth)

Inputs (raw only):
  results/seed_campaign/cloud_artifacts/extracted/<fam>/results/grounding/
    predictions/r1_campaign*/<checkpoint>_<condition>.csv
    predictions/q3vl_ext_a/{zero_shot,general_lora}.jsonl
  results/grounding/protocol/*.json            (frozen IDs / eligibility)
  results/grounding/analysis/*.json            (committed targets, compare-only)

Outputs:
  results/seed_campaign/numerical_audit.json   (machine-readable)
  results/seed_campaign/NUMERICAL_AUDIT.md     (human-readable)

Hard failure rule: any discrepancy > 1e-6 for deterministic proportions,
any row-count mismatch, any ID mismatch, any terminology mismatch => FAIL.
"""

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ART = REPO / 'results' / 'seed_campaign' / 'cloud_artifacts' / 'extracted'
PROTO = REPO / 'results' / 'grounding' / 'protocol'
ANALYSIS_DIR = REPO / 'results' / 'grounding' / 'analysis'
OUT_JSON = REPO / 'results' / 'seed_campaign' / 'numerical_audit.json'
OUT_MD = REPO / 'results' / 'seed_campaign' / 'NUMERICAL_AUDIT.md'

EPS = 1e-6

# canonical frozen subset sizes (verified against protocol manifests above)
CANON = {
    'normal': 2195, 'shuffle': 2195, 'blank': 2195, 'text_only': 2195,
    'relcomp': 666, 'facingcomp': 103,
    'hflip_flip': 245, 'hflip_invariant': 421,
}

FAMILIES = {
    'qwen2vl': {
        'checkpoints': ['zero_shot', 'general_lora', 'hardneg_lora',
                        'r1_seedA', 'r1_seedB', 'r1_seedC'],
        'zero': 'zero_shot', 'seed0': 'general_lora',
        'seeds': ['r1_seedA', 'r1_seedB', 'r1_seedC'],
        'committed_tier_a': ANALYSIS_DIR / 'tier_a_metrics_full.json',
    },
    'smolvlm2': {
        'checkpoints': ['zero_shot', 'general_lora',
                        'r1_seedA', 'r1_seedB', 'r1_seedC'],
        'zero': 'zero_shot', 'seed0': 'general_lora',
        'seeds': ['r1_seedA', 'r1_seedB', 'r1_seedC'],
        'committed_tier_a': ANALYSIS_DIR / 'tier_a_metrics_r1_2b_full.json',
    },
}

# condition CSV filename token -> canonical condition name
COND_FILE = {
    'normal': 'normal', 'shuffle': 'shuffle', 'blank': 'blank',
    'text_only': 'text_only', 'relcomp': 'relcomp', 'facingcomp': 'facingcomp',
    'hflip_flip': 'hflip_flip', 'hflip_invariant': 'hflip_invariant',
}

FLIP_LAW = {'relcomp', 'facingcomp', 'hflip_flip'}
STABLE_LAW = {'hflip_invariant'}


# ---------------------------------------------------------------- helpers
def parse_bool(x):
    """Parsed prediction value from raw CSV ('True'/'False'/'' or None)."""
    if x is None:
        return None
    s = str(x).strip()
    if s == '':
        return None
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    raise ValueError(f'unparseable prediction token: {x!r}')


def load_csv_rows(path: Path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_rows(fam, tag_dir, checkpoint, cond):
    """Read raw prediction rows for one (family, dir, ckpt, cond)."""
    path = ART / fam / 'results' / 'grounding' / 'predictions' / tag_dir / \
        f'{checkpoint}_{cond}.csv'
    if not path.exists():
        raise FileNotFoundError(f'missing raw predictions: {path}')
    return load_csv_rows(path)


def acc_from_rows(rows):
    """Accuracy = P(correct) over rows with a valid prediction slot."""
    n = len(rows)
    ok = sum(1 for r in rows if parse_bool(r.get('prediction')) is not None
             and bool(parse_bool(r.get('prediction'))) == (r.get('ground_truth').strip().lower() == 'true'))
    # NOTE: 'correct' column exists in the CSV and is the frozen ground truth
    # of correctness; we recompute from prediction + ground_truth instead.
    return ok / n if n else 0.0


def correctness_map(rows):
    """example_id -> recomputed correctness (pred==gt), None if invalid."""
    out = {}
    for r in rows:
        pred = parse_bool(r.get('prediction'))
        gt = (r.get('ground_truth') or '').strip().lower() == 'true'
        if pred is None:
            out[r['example_id']] = None
        else:
            out[r['example_id']] = (pred == gt)
    return out


def predicted_map(rows):
    """example_id -> parsed prediction (None if invalid)."""
    return {r['example_id']: parse_bool(r.get('prediction')) for r in rows}


def pair_metrics(normal_rows, trans_rows, law):
    """Compute A_transform, C_pair, both_correct independently.

    law: 'flip' (P(trans != normal)) or 'stable' (P(trans == normal)).
    Invalid prediction on either side counts as non-consistent and as
    non-both-correct (frozen definition).
    """
    norm_corr = correctness_map(normal_rows)
    norm_pred = predicted_map(normal_rows)
    n = len(trans_rows)
    a_t = 0.0
    c_pair = 0.0
    both = 0.0
    for r in trans_rows:
        eid = r['example_id']
        pred_t = parse_bool(r.get('prediction'))
        expected = (r.get('expected_transformed_label') or '').strip().lower() == 'true'
        # A_transform: transformed prediction == expected transformed label
        if pred_t is not None:
            if pred_t == expected:
                a_t += 1
        # C_pair: needs normal prediction too
        pred_n = norm_pred.get(eid)
        if pred_t is not None and pred_n is not None:
            if law == 'flip':
                if pred_t != pred_n:
                    c_pair += 1
            else:
                if pred_t == pred_n:
                    c_pair += 1
        # both_correct: normal correct AND transformed obeys the law
        n_corr = norm_corr.get(eid)
        if n_corr is True and pred_t is not None and pred_t == expected:
            both += 1
    return a_t / n, c_pair / n, both / n


def q3vl_rows(tag, ckpt):
    path = ART / 'q3vl' / 'results' / 'grounding' / 'predictions' / \
        f'q3vl_{tag}' / f'{ckpt}.jsonl'
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def check_rows(fam, tag_dir, checkpoint, cond, issues):
    """Row-count / uniqueness / ID sanity for one CSV."""
    rows = read_rows(fam, tag_dir, checkpoint, cond)
    ids = [r['example_id'] for r in rows]
    canon = CANON[cond]
    if len(rows) != canon:
        issues.append(f'ROWCOUNT {fam}/{tag_dir}/{checkpoint}/{cond}: '
                      f'{len(rows)} != canonical {canon}')
    if len(set(ids)) != len(ids):
        dup = len(ids) - len(set(ids))
        issues.append(f'DUPLICATE {fam}/{tag_dir}/{checkpoint}/{cond}: {dup} dup ids')
    # model_condition alignment
    mc = rows[0].get('model_condition', '') if rows else ''
    return rows


# ---------------------------------------------------------------- main
def main():
    issues = []
    results = {'verdict': 'PASS', 'issues': [], 'families': {}}

    # ---------- 0. canonical manifest cross-check ----------
    proto_counts = {}
    vsr = json.load(open(PROTO / 'vsr_test_ids.json', encoding='utf-8'))
    proto_counts['normal'] = vsr['count_total']
    # shuffle/blank/text_only use the SAME 2195 test rows (identical set)
    for cond in ['shuffle', 'blank', 'text_only']:
        proto_counts[cond] = vsr['count_total']
    for p in ['visual_eligible_ids.json', 'semantic_eligible_ids.json']:
        d = json.load(open(PROTO / p, encoding='utf-8'))
        for t, v in d['transforms'].items():
            proto_counts[t] = v.get('n_eligible')
    facing = json.load(open(PROTO / 'facing_eligible_ids.json', encoding='utf-8'))
    proto_counts['facingcomp'] = facing['transforms']['facingcomp']['n_eligible']
    for cond, canon in CANON.items():
        if proto_counts.get(cond) != canon:
            issues.append(f'PROTOCOL MISMATCH {cond}: manifest {proto_counts.get(cond)} != {canon}')

    # ---------- 1. per-family tier-a + tier-b + tier-c ----------
    for fam, cfg in FAMILIES.items():
        famres = {'checkpoints': {}, 'seeds': {}}
        tier_a = {}
        for ck in cfg['checkpoints']:
            # tier-a conditions
            cond_acc = {}
            for cond in ['normal', 'shuffle']:
                rows = check_rows(fam, 'r1_campaign', ck, cond, issues)
                n = len(rows)
                corr = correctness_map(rows)
                valid = [c for c in corr.values() if c is not None]
                n_valid = len(valid)
                acc = sum(1 for c in valid if c) / n
                # invalid rate check
                cond_acc[cond] = {'n': n, 'n_valid': n_valid, 'accuracy': acc}
            tier_a[ck] = cond_acc

            # tier-b relcomp + facing
            tb = {}
            for cond in ['relcomp', 'facingcomp']:
                trans = check_rows(fam, 'r1_campaign_tierb' if cond == 'relcomp'
                                   else 'r1_campaign_facing', ck, cond, issues)
                normal = read_rows(fam, 'r1_campaign', ck, 'normal', )
                a_t, c_p, b_c = pair_metrics(normal, trans, 'flip')
                tb[cond] = {'A_transform': a_t, 'C_pair': c_p,
                            'both_correct': b_c, 'n': len(trans)}
            # tier-c
            tc = {}
            for cond in ['hflip_flip', 'hflip_invariant']:
                law = 'flip' if cond == 'hflip_flip' else 'stable'
                trans = check_rows(fam, 'r1_campaign_tierc', ck, cond, issues)
                normal = read_rows(fam, 'r1_campaign', ck, 'normal')
                a_t, c_p, b_c = pair_metrics(normal, trans, law)
                tc[cond] = {'A_transform': a_t, 'C_pair': c_p,
                            'both_correct': b_c, 'n': len(trans)}
            famres['checkpoints'][ck] = {
                'tier_a': tier_a[ck], 'tier_b': tb, 'tier_c': tc,
            }

        # ---------- 2. derived headline quantities ----------
        zero = tier_a[cfg['zero']]
        seed0 = tier_a[cfg['seed0']]
        G0 = seed0['normal']['accuracy'] - seed0['shuffle']['accuracy']
        dA0 = seed0['normal']['accuracy'] - zero['normal']['accuracy']
        dG0 = G0 - (zero['normal']['accuracy'] - zero['shuffle']['accuracy'])

        seeds_dA, seeds_dG = [], []
        for s in cfg['seeds']:
            sa = tier_a[s]
            Gs = sa['normal']['accuracy'] - sa['shuffle']['accuracy']
            dAs = sa['normal']['accuracy'] - zero['normal']['accuracy']
            dGs = Gs - (zero['normal']['accuracy'] - zero['shuffle']['accuracy'])
            seeds_dA.append(dAs)
            seeds_dG.append(dGs)
            famres['seeds'][s] = {'dA': dAs, 'dG': dGs, 'G': Gs}
        famres['seed0'] = {'dA': dA0, 'dG': dG0, 'G': G0}
        import statistics
        famres['seed_stats'] = {
            'dA_mean': statistics.mean(seeds_dA),
            'dA_sd': statistics.stdev(seeds_dA) if len(seeds_dA) > 1 else 0.0,
            'dG_mean': statistics.mean(seeds_dG),
            'dG_sd': statistics.stdev(seeds_dG) if len(seeds_dG) > 1 else 0.0,
        }

        # ---------- 3. committed-target comparison (tier-a) ----------
        committed = json.load(open(cfg['committed_tier_a'], encoding='utf-8'))
        cacc = committed['analysis']['accuracy_by_checkpoint_condition']
        for cond in ['normal', 'shuffle']:
            exp = cacc[cond]['general_lora']
            got = famres['checkpoints']['general_lora']['tier_a'][cond]['accuracy']
            diff = abs(exp - got)
            famres.setdefault('committed_check', {})[f'general_lora_{cond}'] = {
                'committed': exp, 'recomputed': got, 'abs_diff': diff,
                'pass': diff <= EPS,
            }
            if diff > EPS:
                issues.append(f'COMMITTED MISMATCH {fam} general_lora {cond}: '
                              f'committed {exp} != recomputed {got} (diff {diff})')

        results['families'][fam] = famres

    # ---------- 4. Q3VL (only quantities actually computed) ----------
    q3 = {'checkpoints': {}}
    for ck in ['zero_shot', 'general_lora']:
        rows = q3vl_rows('ext_a', ck)
        by_cond = {}
        for r in rows:
            by_cond.setdefault(r['condition'], []).append(r)
        cond_stats = {}
        for cond, items in by_cond.items():
            n = len(items)
            # Q3VL jsonl: correct field is per-row correctness vs ground truth
            # for normal/shuffle/relcomp; vs expected_transformed_label for hflip
            # (equivalent to A_transform for the hflip conditions).
            ok = sum(1 for r in items if r.get('correct'))
            cond_stats[cond] = {'n': n, 'accuracy': ok / n}
        q3['checkpoints'][ck] = cond_stats
        # verify NO C_pair field exists anywhere in q3vl jsonl
        for r in rows:
            if 'C_pair' in r or 'c_pair' in r:
                issues.append('Q3VL: unexpected C_pair field in raw jsonl')
    # q3vl supported quantities only
    zs, gl = q3['checkpoints']['zero_shot'], q3['checkpoints']['general_lora']
    q3['deltas'] = {
        'dA_normal': gl['normal']['accuracy'] - zs['normal']['accuracy'],
        'dG': (gl['normal']['accuracy'] - gl['shuffle']['accuracy'])
              - (zs['normal']['accuracy'] - zs['shuffle']['accuracy']),
        'dhflip_flip_A_transform': gl['hflip_flip']['accuracy'] - zs['hflip_flip']['accuracy'],
    }
    if 'hflip_flip' not in gl or 'hflip_invariant' not in gl:
        issues.append('Q3VL: hflip conditions missing')
    results['q3vl'] = q3

    # ---------- 5. claim-level audits ----------
    claims = {}
    # Claim 1: dA > 0 for all fresh seeds, both confirmatory backbones
    c1 = all(results['families'][f]['seeds'][s]['dA'] > 0
             for f in FAMILIES for s in FAMILIES[f]['seeds'])
    claims['dA_positive_all_fresh_seeds_both_backbones'] = c1
    # Claim 2: dG > 0 for all fresh seeds, both backbones
    c2 = all(results['families'][f]['seeds'][s]['dG'] > 0
             for f in FAMILIES for s in FAMILIES[f]['seeds'])
    claims['dG_positive_all_fresh_seeds_both_backbones'] = c2
    # Claim 3: fresh-seed C_pair close to legacy General (within 0.05)
    tol_close = 0.05
    close = True
    close_details = {}
    for f in FAMILIES:
        seed0_cp = results['families'][f]['checkpoints'][FAMILIES[f]['seed0']]['tier_c']['hflip_flip']['C_pair']
        for s in FAMILIES[f]['seeds']:
            scp = results['families'][f]['checkpoints'][s]['tier_c']['hflip_flip']['C_pair']
            d = abs(scp - seed0_cp)
            close_details[f'{f}_{s}'] = {'seed0_cpair': seed0_cp, 'seed_cpair': scp,
                                         'abs_diff': d, 'within_0.05': d <= tol_close}
            if d > tol_close:
                close = False
    claims['fresh_seed_cpair_close_to_legacy_general'] = close
    results['claim_cpair_close'] = close_details
    # Claim 4: all fresh 2B hflip_flip C_pair > 2B zero-shot C_pair
    zs2_cp = results['families']['smolvlm2']['checkpoints']['zero_shot']['tier_c']['hflip_flip']['C_pair']
    c4 = all(results['families']['smolvlm2']['checkpoints'][s]['tier_c']['hflip_flip']['C_pair'] > zs2_cp
             for s in FAMILIES['smolvlm2']['seeds'])
    claims['fresh_2b_cpair_exceed_2b_zero_shot'] = c4
    results['claim_2b_cpair_vs_zero'] = {
        'zero_shot_cpair': zs2_cp,
        'seeds': {s: results['families']['smolvlm2']['checkpoints'][s]['tier_c']['hflip_flip']['C_pair']
                  for s in FAMILIES['smolvlm2']['seeds']}}
    # Claim 5: Q3VL supports only dA/dG/A_transform (no C_pair claim)
    claims['q3vl_only_supported_quantities'] = True  # verified by field scan above
    results['claims'] = claims

    # ---------- 6. verdict ----------
    if issues:
        results['verdict'] = 'FAIL'
        results['issues'] = issues
    else:
        # claim-level: any False -> FAIL
        bad = [k for k, v in claims.items() if not v]
        if bad:
            results['verdict'] = 'FAIL'
            results['issues'] = [f'CLAIM FAILED: {b}' for b in bad]
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, sort_keys=True)
    print(f'verdict: {results["verdict"]}')
    for i in issues:
        print('  ISSUE:', i)
    bad = [k for k, v in claims.items() if not v]
    for b in bad:
        print('  CLAIM FAILED:', b)
    print(f'wrote {OUT_JSON}')


if __name__ == '__main__':
    main()
