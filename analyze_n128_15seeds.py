"""Final 15-seed clean N=128 analysis with predeclared contrasts."""
import json, sys
from pathlib import Path
import numpy as np
from scipy import stats
sys.path.insert(0, '.')

d = Path('results/n128_clean')
ARMS = ['augmentation', 'output_consistency', 'equiorient', 'wrong_geometry']
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010,
         1111, 1212, 1313, 1414, 1515]

data = {}
for s in SEEDS:
    data[s] = {}
    for a in ARMS:
        f = d / f'result_{a}_s{s}.json'
        r = json.loads(f.read_text())
        ek = 'test_eval' if 'test_eval' in r else 'dev_eval'
        data[s][a] = r.get(ek, {}).get('unseen_accuracy', 0)

print("=== 15-SEED CLEAN N=128 (canonical) ===")
print(f"{'Seed':>6} {'Aug':>8} {'OC':>8} {'Eq':>8} {'Wrong':>8}")
for s in SEEDS:
    print(f"{s:>6} {data[s]['augmentation']:>8.4f} "
          f"{data[s]['output_consistency']:>8.4f} "
          f"{data[s]['equiorient']:>8.4f} "
          f"{data[s]['wrong_geometry']:>8.4f}")

eq_aug = np.array([data[s]['equiorient'] - data[s]['augmentation'] for s in SEEDS])
eq_wrong = np.array([data[s]['equiorient'] - data[s]['wrong_geometry'] for s in SEEDS])
aug = np.array([data[s]['augmentation'] for s in SEEDS])
eq = np.array([data[s]['equiorient'] for s in SEEDS])
wrong = np.array([data[s]['wrong_geometry'] for s in SEEDS])

def boot_ci(x, n=10000):
    rng = np.random.default_rng(42)
    m = [rng.choice(x, size=len(x), replace=True).mean() for _ in range(n)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

t1, p1 = stats.ttest_rel(eq, aug)
t2, p2 = stats.ttest_rel(eq, wrong)
lo1, hi1 = boot_ci(eq_aug)
lo2, hi2 = boot_ci(eq_wrong)

print()
print(f"MEANS: Aug={aug.mean():.4f} Eq={eq.mean():.4f} Wrong={wrong.mean():.4f}")
print(f"[1] Eq-Aug: {eq_aug.mean()*100:+.2f}pp "
      f"CI=[{lo1*100:+.2f},{hi1*100:+.2f}] p={p1:.3f} wins={sum(eq_aug>0)}/15")
print(f"[2] Eq-Wrong: {eq_wrong.mean()*100:+.2f}pp "
      f"CI=[{lo2*100:+.2f},{hi2*100:+.2f}] p={p2:.4f} wins={sum(eq_wrong>0)}/15")
print()
print(f"CONCLUSION: Eq-Aug {'SIGNIFICANT' if lo1>0 else 'NOT significant (n.s.)'}")
print(f"            Eq-Wrong {'SIGNIFICANT' if lo2>0 else 'NOT significant (n.s.)'}")
