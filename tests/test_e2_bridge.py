"""CPU-only tests for the E2 real-image bridge (no torch/GPU needed)."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from equiorient.analysis.bridge_metrics import (
    cosine_agreement, effective_rank, normalized_equivariance_error,
    spearman_bootstrap)
from equiorient.data.e2_behavior import (
    flip_compliance, select_subset)


def test_e_norm_perfect_equivariance_is_zero():
    rng = np.random.default_rng(0)
    zx = rng.normal(size=(64, 16))
    assert normalized_equivariance_error(zx, zx) == 0.0


def test_e_norm_is_collapse_safe():
    rng = np.random.default_rng(1)
    zx = rng.normal(size=(64, 16))
    ztx = rng.normal(size=(64, 16))
    shrunk_zx = zx * 1e-6
    err = normalized_equivariance_error(zx, ztx)
    collapsed = normalized_equivariance_error(shrunk_zx, ztx)
    assert 0.5 < err < 2.0
    assert abs(collapsed - 2.0) < 0.05
    assert collapsed > err


def test_cosine_bounds_and_identity():
    rng = np.random.default_rng(2)
    zx = rng.normal(size=(32, 8))
    assert cosine_agreement(zx, zx) == pytest.approx(1.0)
    cos = cosine_agreement(zx, -zx)
    assert cos == pytest.approx(-1.0)


def test_effective_rank_recovers_rank():
    rng = np.random.default_rng(3)
    z = rng.normal(size=(200, 5)) @ rng.normal(size=(5, 10))
    assert effective_rank(z) <= 6


def test_spearman_detects_monotone():
    x = np.arange(20, dtype=float)
    r = spearman_bootstrap(x, 3 * x + 1, n_boot=200, seed=7)
    assert r["spearman_rho"] == pytest.approx(1.0)
    assert r["ci95_low"] > 0.9


def test_spearman_bootstrap_ci_brackets_point():
    rng = np.random.default_rng(4)
    x = rng.normal(size=30)
    y = 0.5 * x + rng.normal(size=30) * 0.8
    r = spearman_bootstrap(x, y, n_boot=500, seed=11)
    assert r["ci95_low"] <= r["spearman_rho"] <= r["ci95_high"]


def _write_hflip_csv(path, ids):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "example_id", "prediction", "expected_transformed_label"])
        w.writeheader()
        for i, eid in enumerate(ids):
            w.writerow({"example_id": eid,
                        "prediction": "true" if i % 2 == 0 else "false",
                        "expected_transformed_label": "true" if i % 2 == 0 else "false"})


def test_subset_selection_deterministic_and_intersected(tmp_path):
    ids_path = tmp_path / "vsr_test_ids.json"
    json.dump([f"vsr_test:{i:04d}" for i in range(1000)], open(ids_path, "w"))
    eligible = {f"vsr_test:{i:04d}" for i in range(0, 800)}
    s1 = select_subset(ids_path, eligible, n=50)
    s2 = select_subset(ids_path, eligible, n=50)
    assert s1 == s2 and len(s1) == 50
    assert all(e in eligible for e in s1)


def test_flip_compliance_recomputed_from_rows(tmp_path):
    p = tmp_path / "hflip_flip.csv"
    ids = [f"vsr_test:{i:04d}" for i in range(10)]
    rows = []
    for i, eid in enumerate(ids):
        exp = "True" if i % 2 == 0 else "False"
        pred_ok = "True" if i % 3 != 0 else ("False" if exp == "True" else "True")
        rows.append({"example_id": eid, "prediction": pred_ok.lower(),
                     "expected_transformed_label": exp})
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    res = flip_compliance(rows, subset_ids=set(ids[:5]))
    assert res["n"] == 5
    manual = sum(1 for i in range(5)
                 if (rows[i]["prediction"] == rows[i]["expected_transformed_label"].lower()))
    assert res["compliance_rate"] == manual / 5
