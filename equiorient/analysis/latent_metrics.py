"""Collapse-resistant latent metrics for Phase 2.

Raw ||rho(T)z(x) - z(Tx)|| can improve by shrinking z.  These metrics
expose collapse and separate genuine equivariance from magnitude shrinkage.

Metrics:
  E_norm: normalized equivariance error (divided by average norm)
  latent_norm: mean L2 norm of z vectors
  variance_per_dim: per-dimension variance across the dataset
  effective_rank: rank of the z covariance matrix (proxy for dimensionality)
  cosine_agreement: mean cosine similarity between rho(T)z(x) and z(Tx)
  z_ablation_accuracy: accuracy when z is zeroed (tests answer causality)
"""
from __future__ import annotations

import numpy as np


def normalized_equivariance_error(zx_list: list, ztx_list: list,
                                  rho_vec: tuple) -> float:
    """E_norm = ||rho(g)z(x) - z(Tx)|| / (0.5*(||rho(g)z(x)|| + ||z(Tx)||) + eps)

    Lower is better; collapse-safe: if z shrinks uniformly, E_norm stays ~1.
    """
    eps = 1e-8
    diffs = []
    norms_pred = []
    norms_target = []
    sxx, sxy, syx, syy = rho_vec
    for (zx0, zx1), (gx0, gx1) in zip(zx_list, ztx_list):
        pred0 = sxx * zx0 + sxy * zx1
        pred1 = syx * zx0 + syy * zx1
        d = np.sqrt((pred0 - gx0) ** 2 + (pred1 - gx1) ** 2)
        np_ = np.sqrt(pred0 ** 2 + pred1 ** 2)
        nt = np.sqrt(gx0 ** 2 + gx1 ** 2)
        diffs.append(d)
        norms_pred.append(np_)
        norms_target.append(nt)
    avg_norm = 0.5 * (np.mean(norms_pred) + np.mean(norms_target)) + eps
    return float(np.mean(diffs) / avg_norm)


def latent_norm_stats(zx_list: list, zy_list: list) -> dict:
    """Mean L2 norm of z = [zx; zy]."""
    norms = [np.sqrt(x ** 2 + y ** 2)
             for x, y in zip(zx_list, zy_list)]
    return {
        "mean_norm": round(float(np.mean(norms)), 4),
        "std_norm": round(float(np.std(norms)), 4),
    }


def variance_per_dim(zx_arr: np.ndarray, zy_arr: np.ndarray) -> dict:
    """Per-dimension variance of z = [zx; zy]. Returns dict with stats."""
    z = np.concatenate([zx_arr, zy_arr], axis=-1)  # (N, 256)
    var = z.var(axis=0)
    return {
        "mean_var": round(float(var.mean()), 6),
        "min_var": round(float(var.min()), 6),
        "max_var": round(float(var.max()), 6),
        "frac_near_zero": round(float((var < 1e-6).mean()), 4),
    }


def effective_rank(zx_arr: np.ndarray, zy_arr: np.ndarray) -> dict:
    """Effective rank via participation ratio of covariance eigenvalues."""
    z = np.concatenate([zx_arr, zy_arr], axis=-1)  # (N, 256)
    cov = np.cov(z.T)
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = np.maximum(eigvals, 0)
    total = eigvals.sum()
    if total < 1e-12:
        return {"eff_rank": 0, "top5_eigvals": []}
    probs = eigvals / total
    eff_rank = 1.0 / (np.sum(probs ** 2) + 1e-12)
    top5 = sorted(eigvals.tolist(), reverse=True)[:5]
    return {
        "eff_rank": round(float(eff_rank), 2),
        "top5_eigvals": [round(float(v), 4) for v in top5],
    }


def cosine_agreement(zx_list: list, ztx_list: list,
                     rho_vec: tuple) -> dict:
    """Mean cosine similarity between rho(g)z(x) and z(Tx)."""
    sxx, sxy, syx, syy = rho_vec
    sims = []
    for (zx0, zx1), (gx0, gx1) in zip(zx_list, ztx_list):
        pred0 = sxx * zx0 + sxy * zx1
        pred1 = syx * zx0 + syy * zx1
        num = pred0 * gx0 + pred1 * gx1
        den = (np.sqrt(pred0 ** 2 + pred1 ** 2) *
               np.sqrt(gx0 ** 2 + gx1 ** 2) + 1e-8)
        sims.append(float(num / den))
    return {
        "mean_cosine": round(float(np.mean(sims)), 4),
        "min_cosine": round(float(min(sims)), 4),
    }
