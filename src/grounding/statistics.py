"""Paired statistics for the Tier-A audit (protocol section 9).

- exact McNemar (binomial exact two-sided) for paired binary correctness;
- paired bootstrap CIs (percentile) for accuracy differences and gaps;
- bootstrap CI for the difference-in-differences DeltaG_shuffle(u->v),
  resampling example-level quadruples (u_normal, u_shuffle, v_normal,
  v_shuffle);
- effect sizes alongside p-values (Cohen's h for accuracy differences,
  McNemar odds ratio b/c for paired correctness).

All resampling uses the frozen BOOTSTRAP_SEED and BOOTSTRAP_ITERATIONS from
config, so CIs are deterministic across machines.
"""

import math

import numpy as np
from scipy.stats import binom

from . import config


def exact_mcnemar(u_correct: list, v_correct: list) -> dict:
    """Exact McNemar on paired binary correctness (u vs v).

    b = pairs where u wrong and v right; c = pairs where u right and v wrong.
    H0: b == c. Exact two-sided p via binomial(b+c, 0.5).
    """
    b = sum(1 for uc, vc in zip(u_correct, v_correct) if (not uc) and vc)
    c = sum(1 for uc, vc in zip(u_correct, v_correct) if uc and (not vc))
    n_disc = b + c
    if n_disc == 0:
        p_value = 1.0
    else:
        k = min(b, c)
        p_value = 2.0 * binom.cdf(k, n_disc, 0.5)
        p_value = min(1.0, p_value)
    chi2 = 0.0 if n_disc == 0 else ((abs(b - c) - 1) ** 2) / n_disc
    or_ = float("inf") if c == 0 else (b / c if b > 0 else 0.0)
    return {
        "b": b,
        "c": c,
        "discordant_n": n_disc,
        "exact_p": round(float(p_value), 6),
        "continuity_chi2": round(float(chi2), 4),
        "mcnemar_odds_ratio": or_,
    }


def _rng():
    return np.random.default_rng(config.BOOTSTRAP_SEED)


def paired_bootstrap_ci(pair_diffs: list, alpha: float = 0.05,
                        n_iter: int = None) -> dict:
    """Percentile bootstrap CI for the mean of paired per-example diffs."""
    n_iter = n_iter or config.BOOTSTRAP_ITERATIONS
    diffs = np.asarray(pair_diffs, dtype=float)
    if diffs.size == 0:
        return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "n": 0}
    rng = _rng()
    means = np.empty(n_iter)
    n = diffs.shape[0]
    idx = rng.integers(0, n, size=(n_iter, n))
    means = diffs[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "mean": round(float(diffs.mean()), 6),
        "ci_lower": round(float(lo), 6),
        "ci_upper": round(float(hi), 6),
        "n": int(n),
        "n_iter": int(n_iter),
        "seed": config.BOOTSTRAP_SEED,
    }


def bootstrap_did_ci(quads: list, alpha: float = 0.05, n_iter: int = None) -> dict:
    """Bootstrap CI for DeltaG_shuffle(u->v).

    quads: per-example (u_normal_correct, u_shuffle_correct,
                          v_normal_correct, v_shuffle_correct).
    Resample examples (not rows) so within-example pairing is preserved;
    per resample:  DeltaG = (A_v,norm - A_v,shuf) - (A_u,norm - A_u,shuf).
    """
    n_iter = n_iter or config.BOOTSTRAP_ITERATIONS
    arr = np.asarray(quads, dtype=float)
    if arr.size == 0:
        return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "n": 0}
    n = arr.shape[0]
    rng = _rng()

    def did(sub):
        return ((sub[:, 2].mean() - sub[:, 3].mean())
                - (sub[:, 0].mean() - sub[:, 1].mean()))

    point = did(arr)
    idx = rng.integers(0, n, size=(n_iter, n))
    dist = np.array([did(arr[i]) for i in idx])
    lo, hi = np.percentile(dist, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "mean": round(float(point), 6),
        "ci_lower": round(float(lo), 6),
        "ci_upper": round(float(hi), 6),
        "n": int(n),
        "n_iter": int(n_iter),
        "seed": config.BOOTSTRAP_SEED,
    }


def cohens_h(p1: float, p2: float) -> float:
    return 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))
