"""Clean N=128 analysis: paired contrasts with bootstrap CIs.
Primary contrasts (predeclared):
  1. EquiOrient - augmentation
  2. EquiOrient - wrong_geometry
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '.')

d = Path('results/n128_clean')
ARMS = ['augmentation', 'output_consistency', 'equiorient', 'wrong_geometry']
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]

# Load paired results
data = {}
for s in SEEDS:
    data[s] = {}
    for a in ARMS:
        f = d / f'result_{a}_s{s}.json'
        if not f.exists():
            print(f"MISSING {a} s{s}")
            continue
        r = json.loads(f.read_text())
        ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
        data[s][a] = r.get(ek, {}).get('unseen_accuracy', 0)

# Summary table
print("=" * 75)
print("CLEAN N=128 RESULTS (10 matched seeds, deterministic)")
print("=" * 75)
print(f"{'Seed':>6} {'Aug':>8} {'OC':>8} {'Eq':>8} {'Wrong':>8} | {'Eq-Aug':>8} {'Eq-Wrong':>8}")
print("-" * 75)
eq_aug = []
eq_wrong = []
for s in SEEDS:
    aug = data[s]['augmentation']
    oc = data[s]['output_consistency']
    eq = data[s]['equiorient']
    wg = data[s]['wrong_geometry']
    da = (eq - aug) * 100
    dw = (eq - wg) * 100
    eq_aug.append(eq - aug)
    eq_wrong.append(eq - wg)
    print(f"{s:>6} {aug:>8.4f} {oc:>8.4f} {eq:>8.4f} {wg:>8.4f} | {da:>+7.2f}pp {dw:>+7.2f}pp")

eq_aug = np.array(eq_aug)
eq_wrong = np.array(eq_wrong)

def bootstrap_ci(deltas, n_boot=10000, seed=42):
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        idx = rng.choice(len(deltas), size=len(deltas), replace=True)
        means.append(deltas[idx].mean())
    arr = np.array(means)
    return arr.mean(), np.percentile(arr, 2.5), np.percentile(arr, 97.5)

from scipy import stats

print("\n" + "=" * 75)
print("PRIMARY CONTRASTS (predeclared)")
print("=" * 75)

# Contrast 1: Eq - Aug
m1, lo1, hi1 = bootstrap_ci(eq_aug)
t1, p1 = stats.ttest_rel(
    [data[s]['equiorient'] for s in SEEDS],
    [data[s]['augmentation'] for s in SEEDS])
print(f"\n[1] EquiOrient - augmentation:")
print(f"    Mean: {m1*100:+.2f}pp")
print(f"    95% CI: [{lo1*100:+.2f}, {hi1*100:+.2f}] pp")
print(f"    Paired t-test: t={t1:.3f}, p={p1:.3f}")
print(f"    Wins: {sum(1 for x in eq_aug if x > 0)}/{len(eq_aug)} seeds")
print(f"    Conclusion: {'POSITIVE (Eq > Aug)' if lo1 > 0 else 'NOT significant'}")

# Contrast 2: Eq - Wrong
m2, lo2, hi2 = bootstrap_ci(eq_wrong)
t2, p2 = stats.ttest_rel(
    [data[s]['equiorient'] for s in SEEDS],
    [data[s]['wrong_geometry'] for s in SEEDS])
print(f"\n[2] EquiOrient - wrong_geometry:")
print(f"    Mean: {m2*100:+.2f}pp")
print(f"    95% CI: [{lo2*100:+.2f}, {hi2*100:+.2f}] pp")
print(f"    Paired t-test: t={t2:.3f}, p={p2:.3f}")
print(f"    Wins: {sum(1 for x in eq_wrong if x > 0)}/{len(eq_wrong)} seeds")
print(f"    Conclusion: {'POSITIVE (Eq > Wrong)' if lo2 > 0 else 'NOT significant'}")

# Per-arm summary
print("\n" + "=" * 75)
print("PER-ARM SUMMARY")
print("=" * 75)
for a in ARMS:
    vals = np.array([data[s][a] for s in SEEDS])
    print(f"  {a:25s} mean={vals.mean():.4f} std={vals.std():.4f} "
          f"min={vals.min():.4f} max={vals.max():.4f}")
