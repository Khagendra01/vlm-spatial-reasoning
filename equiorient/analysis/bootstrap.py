"""Hierarchical paired bootstrap for ΔA = A_equiorient - A_augmentation.

Resamples training seeds → within each seed, resamples test scene IDs →
preserves method pairing → computes ΔA → 10 000 bootstrap replicates.

Predeclared minimum practically meaningful difference: 0.03 (3 pp).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def paired_bootstrap(run_dir: Path, n_boot: int = 10_000,
                     seed: int = 42,
                     min_effect: float = 0.03) -> dict:
    """Compute hierarchical paired bootstrap CI for ΔA.

    Requires per-scene results from both augmentation and equiorient
    on the same seeds.  If only aggregate results exist, falls back
    to a seed-level paired bootstrap (less powerful but valid).
    """
    aug_files = sorted(run_dir.glob("result_augmentation_*.json"))
    eq_files = sorted(run_dir.glob("result_equiorient_*.json"))

    aug_seeds = {}
    for f in aug_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        aug_seeds[d["seed"]] = d.get("test_eval", d.get("dev_eval", {}))

    eq_seeds = {}
    for f in eq_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        eq_seeds[d["seed"]] = d.get("test_eval", d.get("dev_eval", {}))

    common_seeds = sorted(set(aug_seeds) & set(eq_seeds))
    if not common_seeds:
        return {"error": "no common seeds between augmentation and equiorient"}

    # Individual seed deltas
    seed_deltas = {}
    for s in common_seeds:
        a = aug_seeds[s].get("unseen_accuracy", float("nan"))
        e = eq_seeds[s].get("unseen_accuracy", float("nan"))
        seed_deltas[s] = round(e - a, 4)

    vals = np.array([seed_deltas[s] for s in common_seeds])
    rng = np.random.default_rng(seed)

    # Seed-level bootstrap (since we don't have per-scene breakdowns here)
    boot_means = []
    for _ in range(n_boot):
        idx = rng.choice(len(vals), size=len(vals), replace=True)
        boot_means.append(float(vals[idx].mean()))
    boot_arr = np.array(boot_means)
    ci_lo, ci_hi = float(np.percentile(boot_arr, 2.5)), float(
        np.percentile(boot_arr, 97.5))

    return {
        "mean_delta": round(float(vals.mean()), 4),
        "ci_95": [round(ci_lo, 4), round(ci_hi, 4)],
        "individual_deltas": seed_deltas,
        "n_seeds": len(common_seeds),
        "min_effect": min_effect,
        "conclusion": (
            "meaningful benefit" if ci_lo > 0 and vals.mean() >= min_effect
            else "no evidence of meaningful benefit"
            if ci_lo <= 0 or ci_hi <= 0
            else "inconclusive"
        ),
    }


def per_scene_bootstrap(run_dir: Path, n_boot: int = 10_000,
                        seed: int = 42,
                        min_effect: float = 0.03) -> dict:
    """Full hierarchical bootstrap if per-scene data is available."""
    aug_data = _load_per_scene(run_dir, "augmentation")
    eq_data = _load_per_scene(run_dir, "equiorient")
    if not aug_data or not eq_data:
        return paired_bootstrap(run_dir, n_boot, seed, min_effect)

    # Match by scene_id across seeds
    common = set(aug_data.keys()) & set(eq_data.keys())
    rng = np.random.default_rng(seed)
    boot_means = []
    for _ in range(n_boot):
        # Resample seeds
        seed_sample = rng.choice(sorted(common), size=len(common),
                                 replace=True)
        accs = []
        for s in seed_sample:
            a_scenes = aug_data[s]
            e_scenes = eq_data[s]
            scene_ids = sorted(set(a_scenes) & set(e_scenes))
            if not scene_ids:
                continue
            scene_sample = rng.choice(scene_ids, size=len(scene_ids),
                                      replace=True)
            for sc in scene_sample:
                accs.append(float(e_scenes[sc]) - float(a_scenes[sc]))
        if accs:
            boot_means.append(float(np.mean(accs)))

    boot_arr = np.array(boot_means)
    ci_lo, ci_hi = float(np.percentile(boot_arr, 2.5)), float(
        np.percentile(boot_arr, 97.5))
    return {
        "mean_delta": round(float(boot_arr.mean()), 4),
        "ci_95": [round(ci_lo, 4), round(ci_hi, 4)],
        "min_effect": min_effect,
        "n_bootstrap": n_boot,
    }


def _load_per_scene(run_dir: Path, arm: str) -> dict:
    """Try to load per-scene accuracy from result files."""
    out = {}
    for f in run_dir.glob(f"result_{arm}_*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        seed = d["seed"]
        ps = d.get("per_scene_accuracy", {})
        if ps:
            out[seed] = ps
    return out
