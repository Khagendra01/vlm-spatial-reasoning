"""Final analysis for the paper: clean N=128 + N=512 ceiling + N=2048."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '.')

print("=" * 70)
print("FINAL PAPER NUMBERS")
print("=" * 70)

# ==== Clean N=128 (10 matched seeds, deterministic) ====
d = Path('results/n128_clean')
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]
ARMS128 = ['augmentation', 'output_consistency', 'equiorient', 'wrong_geometry']

data = {}
for s in SEEDS:
    data[s] = {}
    for a in ARMS128:
        f = d / f'result_{a}_s{s}.json'
        r = json.loads(f.read_text())
        ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
        data[s][a] = r.get(ek, {}).get('unseen_accuracy', 0)

print("\n--- N=128 CLEAN (10 matched seeds) ---")
print(f"{'Seed':>6} {'Aug':>8} {'OC':>8} {'Eq':>8} {'Wrong':>8}")
for s in SEEDS:
    print(f"{s:>6} {data[s]['augmentation']:>8.4f} "
          f"{data[s]['output_consistency']:>8.4f} "
          f"{data[s]['equiorient']:>8.4f} "
          f"{data[s]['wrong_geometry']:>8.4f}")

# Paired deltas
eq_aug = np.array([data[s]['equiorient'] - data[s]['augmentation'] for s in SEEDS])
eq_wrong = np.array([data[s]['equiorient'] - data[s]['wrong_geometry'] for s in SEEDS])

from scipy import stats
def boot_ci(x, n=10000):
    rng = np.random.default_rng(42)
    m = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(n)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

t1, p1 = stats.ttest_rel([data[s]['equiorient'] for s in SEEDS],
                         [data[s]['augmentation'] for s in SEEDS])
t2, p2 = stats.ttest_rel([data[s]['equiorient'] for s in SEEDS],
                         [data[s]['wrong_geometry'] for s in SEEDS])
lo1, hi1 = boot_ci(eq_aug)
lo2, hi2 = boot_ci(eq_wrong)

print(f"\nEq-Aug: mean={eq_aug.mean()*100:+.2f}pp CI=[{lo1*100:+.2f},{hi1*100:+.2f}] p={p1:.3f}")
print(f"Eq-Wrong: mean={eq_wrong.mean()*100:+.2f}pp CI=[{lo2*100:+.2f},{hi2*100:+.2f}] p={p2:.4f}")

# ==== N=512 (30 runs, ceiling) ====
print("\n--- N=512 (30 runs) ---")
d512 = Path('results/phase2_confirmatory')
from collections import defaultdict
by_arm = defaultdict(list)
for f in sorted(d512.glob('result_*.json')):
    r = json.loads(f.read_text())
    ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
    by_arm[r['arm']].append(r.get(ek, {}).get('unseen_accuracy', 0))
for a in ['original_sft','augmentation','output_consistency',
          'latent_invariance','equiorient','wrong_geometry']:
    arr = np.array(by_arm[a])
    print(f"  {a:25s} mean={arr.mean():.4f} std={arr.std():.4f}")

# ==== N=2048 (20 runs, ceiling) ====
print("\n--- N=2048 (20 runs) ---")
d2048 = Path('results/phase2_scale_2048')
by_arm2 = defaultdict(list)
for f in sorted(d2048.glob('result_*.json')):
    r = json.loads(f.read_text())
    ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
    by_arm2[r['arm']].append(r.get(ek, {}).get('unseen_accuracy', 0))
for a in ['augmentation','output_consistency','equiorient','wrong_geometry']:
    arr = np.array(by_arm2[a])
    print(f"  {a:25s} mean={arr.mean():.4f} std={arr.std():.4f}")

print("\nDONE")
