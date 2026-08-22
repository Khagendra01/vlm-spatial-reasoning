"""Collapse-safe metrics for the E2 real-image bridge (generalized D-dim).

Extends equiorient.analysis.latent_metrics (2-D synthetic z) to arbitrary
token-pooled feature dimensions used for natural-image checkpoints.
"""
from __future__ import annotations

import numpy as np


def normalized_equivariance_error(zx: np.ndarray, ztx: np.ndarray,
                                  rho: np.ndarray | None = None) -> float:
    """E_norm = mean ||rho z(x) - z(Tx)|| / avg norm (+eps), any rho.

    rho=None means identity law (used when no trained reflection
    representation exists for real-image tokens). Collapse-safe: uniform
    shrinkage drives E_norm to 2 (not toward 0), so low error can only be
    achieved by genuine agreement, never by shrinking z.
    """
    eps = 1e-8
    pred = zx if rho is None else zx @ rho.T
    diffs = np.linalg.norm(pred - ztx, axis=1)
    norms_pred = np.linalg.norm(pred, axis=1)
    norms_target = np.linalg.norm(ztx, axis=1)
    avg_norm = 0.5 * (norms_pred.mean() + norms_target.mean()) + eps
    return float(diffs.mean() / avg_norm)


def cosine_agreement(zx: np.ndarray, ztx: np.ndarray,
                     rho: np.ndarray | None = None) -> float:
    pred = zx if rho is None else zx @ rho.T
    num = (pred * ztx).sum(axis=1)
    den = np.linalg.norm(pred, axis=1) * np.linalg.norm(ztx, axis=1) + 1e-8
    return float((num / den).mean())


def latent_norm_stats(z: np.ndarray) -> dict:
    norms = np.linalg.norm(z, axis=1)
    return {"mean_norm": round(float(norms.mean()), 4),
            "std_norm": round(float(norms.std()), 4)}


def effective_rank(z: np.ndarray) -> int:
    """Rank of the covariance above 1% of total spectral energy."""
    s = np.linalg.svd(z - z.mean(axis=0, keepdims=True),
                      compute_uv=False)
    energy = np.cumsum(s ** 2)
    total = energy[-1] + 1e-12
    return int(np.searchsorted(energy, 0.99 * total) + 1)


def paired_delta_stats(values_before, values_after) -> dict:
    d = np.asarray(values_after, dtype=float) - np.asarray(values_before, dtype=float)
    pos = int((d > 0).sum()); neg = int((d < 0).sum())
    from scipy.stats import wilcoxon
    stat_p = wilcoxon(d).pvalue if len(d) and not np.allclose(d, 0) else 1.0
    return {"n_pairs": int(len(d)), "mean_delta": round(float(d.mean()), 6),
            "positive": pos, "negative": neg, "wilcoxon_p": float(stat_p)}


def spearman_bootstrap(xs, ys, n_boot: int = 10000, seed: int = 42) -> dict:
    from scipy.stats import spearmanr
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    assert len(xs) == len(ys) and len(xs) >= 3
    rho, p = spearmanr(xs, ys)
    rng = np.random.default_rng(seed)
    boots = []
    n = len(xs)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        r, _ = spearmanr(xs[idx], ys[idx])
        if not np.isnan(r):
            boots.append(r)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"spearman_rho": round(float(rho), 4), "p_value": float(p),
            "ci95_low": round(float(lo), 4), "ci95_high": round(float(hi), 4),
            "n": int(n), "ci_width": round(float(hi - lo), 4)}
