"""Collapse checks: detect if the latent representation has degenerated.

A collapsed latent (near-zero variance, rank collapse, trivial z) would
make low equivariance error meaningless.  These checks flag such cases.
"""
from __future__ import annotations

import numpy as np


def check_collapse(zx_arr: np.ndarray, zy_arr: np.ndarray,
                   min_var: float = 1e-6,
                   min_eff_rank: float = 10.0,
                   min_norm: float = 0.01) -> dict:
    """Check for latent collapse across multiple indicators.

    Returns: {passed: bool, reasons: [str], metrics: {...}}
    """
    z = np.concatenate([zx_arr, zy_arr], axis=-1)  # (N, 256)
    reasons = []

    # 1. variance check
    var_per_dim = z.var(axis=0)
    frac_zero = float((var_per_dim < min_var).mean())
    if frac_zero > 0.5:
        reasons.append(f"variance collapse: {frac_zero:.1%} of dims near zero")

    # 2. effective rank
    cov = np.cov(z.T)
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = np.maximum(eigvals, 0)
    total = eigvals.sum()
    if total > 1e-12:
        probs = eigvals / total
        eff_rank = 1.0 / (np.sum(probs ** 2) + 1e-12)
        if eff_rank < min_eff_rank:
            reasons.append(
                f"rank collapse: effective rank {eff_rank:.1f} < {min_eff_rank}")
    else:
        eff_rank = 0
        reasons.append("rank collapse: covariance is zero")

    # 3. norm check
    norms = np.sqrt((z ** 2).sum(axis=-1))
    mean_norm = float(norms.mean())
    if mean_norm < min_norm:
        reasons.append(
            f"norm collapse: mean L2 norm {mean_norm:.4f} < {min_norm}")

    # 4. dead neurons: fraction of dims with zero variance
    dead_frac = float((var_per_dim < 1e-8).mean())

    return {
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "mean_norm": round(mean_norm, 4),
        "eff_rank": round(float(eff_rank), 2),
        "frac_near_zero_var": round(frac_zero, 4),
        "frac_dead_neurons": round(dead_frac, 4),
    }
