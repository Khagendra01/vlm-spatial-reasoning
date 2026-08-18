"""Full analysis: confirmatory + scale results."""
import json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np
sys.path.insert(0, '.')

results_dir = Path('results')

# Load all results
all_results = defaultdict(list)
for d in ['phase2_confirmatory', 'phase2_scale_128', 'phase2_scale_2048']:
    rd = results_dir / d
    for f in sorted(rd.glob('result_*_s*.json')):
        data = json.loads(f.read_text())
        data['_experiment'] = d
        all_results[d].append(data)

print("=" * 70)
print("FULL RESULTS SUMMARY")
print("=" * 70)

for exp_name, runs in all_results.items():
    print(f"\n--- {exp_name} ---")
    by_arm = defaultdict(list)
    for r in runs:
        by_arm[r['arm']].append(r)
    
    for arm in ['augmentation', 'output_consistency', 'equiorient', 'wrong_geometry']:
        vals = []
        for r in by_arm[arm]:
            ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
            vals.append(r.get(ek, {}).get('unseen_accuracy', 0))
        arr = np.array(vals)
        print(f"  {arm:25s} mean={arr.mean():.4f} std={arr.std():.4f} n={len(arr)}")

# Scaling summary
print("\n" + "=" * 70)
print("SCALING SUMMARY (augmentation vs equiorient)")
print("=" * 70)
for n_train in [128, 512, 2048]:
    if n_train == 512:
        exp = 'phase2_confirmatory'
    else:
        exp = f'phase2_scale_{n_train}'
    runs = all_results[exp]
    aug_vals = [r.get('test_eval' if 'test_eval' in r else 'dev_eval', {}).get('unseen_accuracy', 0)
                for r in runs if r['arm'] == 'augmentation']
    eq_vals = [r.get('test_eval' if 'test_eval' in r else 'dev_eval', {}).get('unseen_accuracy', 0)
               for r in runs if r['arm'] == 'equiorient']
    if aug_vals and eq_vals:
        a = np.mean(aug_vals)
        e = np.mean(eq_vals)
        delta = e - a
        print(f"  N={n_train:>5d}: aug={a:.4f} eq={e:.4f} delta={delta:+.4f}")

print("\nDone!")
