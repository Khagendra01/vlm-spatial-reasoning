"""Extract all numbers for the paper tables."""
import json
from pathlib import Path
from collections import defaultdict

results_dir = Path('results/phase2_confirmatory')

# Collect all results by arm
by_arm = defaultdict(list)
for f in sorted(results_dir.glob('result_*_s*.json')):
    d = json.loads(f.read_text())
    by_arm[d['arm']].append(d)

print("=== TABLE 1: Unseen Accuracy (mean +/- std over 5 seeds) ===")
print(f"{'Arm':25s} {'Unseen':>10s} {'Worst':>10s} {'Struct L':>12s} {'Ans L':>10s}")
print("-" * 70)
for arm in ['original_sft', 'augmentation', 'output_consistency',
            'latent_invariance', 'equiorient', 'wrong_geometry']:
    runs = by_arm[arm]
    unseen_vals = []
    worst_vals = []
    struct_vals = []
    ans_vals = []
    for r in runs:
        ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
        ev = r.get(ek, {})
        unseen_vals.append(ev.get('unseen_accuracy', 0))
        worst_vals.append(ev.get('worst_unseen_accuracy', 0))
        sl = r.get('train_loss', {}).get('structural', [0, 0])
        struct_vals.append(sl[1] if len(sl) > 1 else sl[0])
        al = r.get('train_loss', {}).get('answer', [0, 0])
        ans_vals.append(al[1] if len(al) > 1 else al[0])

    import numpy as np
    u_arr = np.array(unseen_vals)
    w_arr = np.array(worst_vals)
    s_arr = np.array(struct_vals)
    a_arr = np.array(ans_vals)
    print(f"{arm:25s} {u_arr.mean():.4f}+/-{u_arr.std():.4f} "
          f"{w_arr.mean():.4f}+/-{w_arr.std():.4f} "
          f"{s_arr.mean():.6f}+/-{s_arr.std():.6f} "
          f"{a_arr.mean():.4f}+/-{a_arr.std():.4f}")

print("\n=== PER-TRANSISTION ACCURACY (5-seed mean) ===")
elements = ['I', 'R', 'R2', 'R3', 'H', 'RH', 'R2H', 'R3H']
header = f"{'Arm':25s}" + "".join(f"{g:>8s}" for g in elements)
print(header)
print("-" * (25 + 8*8))
for arm in ['original_sft', 'augmentation', 'output_consistency',
            'latent_invariance', 'equiorient', 'wrong_geometry']:
    runs = by_arm[arm]
    per_g = {g: [] for g in elements}
    for r in runs:
        ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
        pt = r.get(ek, {}).get('per_transform', {})
        for g in elements:
            per_g[g].append(pt.get(g, 0))
    row = f"{arm:25s}"
    for g in elements:
        arr = np.array(per_g[g])
        row += f"{arr.mean():>8.4f}"
    print(row)

print("\n=== TRAINING LOSS CURVES ===")
for arm in ['equiorient', 'wrong_geometry', 'output_consistency', 'latent_invariance']:
    runs = by_arm[arm]
    for r in runs[:1]:
        sl = r.get('train_loss', {}).get('structural', [])
        al = r.get('train_loss', {}).get('answer', [])
        print(f"  {arm}: answer={al} structural={sl}")

print("\n=== INDIVIDUAL SEED DELTAS ===")
for seed in [101, 202, 303, 404, 505]:
    aug = [r for r in by_arm['augmentation'] if r['seed'] == seed]
    eq = [r for r in by_arm['equiorient'] if r['seed'] == seed]
    if aug and eq:
        a_ek = 'test_eval' if 'test_eval' in aug[0] else 'dev_eval'
        e_ek = 'test_eval' if 'test_eval' in eq[0] else 'dev_eval'
        a = aug[0].get(a_ek, {}).get('unseen_accuracy', 0)
        e = eq[0].get(e_ek, {}).get('unseen_accuracy', 0)
        print(f"  Seed {seed}: aug={a:.4f} eq={e:.4f} delta={e-a:.4f}")
