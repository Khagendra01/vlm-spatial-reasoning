"""Statistics unit tests: exact McNemar, bootstrap CIs, DID bootstrap."""

import numpy as np

from src.grounding.statistics import (bootstrap_did_ci, cohens_h,
                                      exact_mcnemar, paired_bootstrap_ci)


class TestExactMcNemar:
    def test_all_agree(self):
        u = [True, True, False]
        v = [True, True, False]
        r = exact_mcnemar(u, v)
        assert r["b"] == 0 and r["c"] == 0
        assert r["exact_p"] == 1.0

    def test_known_toy_counts(self):
        # 20 examples: 10 broken (u right, v wrong), 2 fixed (u wrong, v right),
        # 8 concordant (u/v both false)
        u = [True] * 10 + [False] * 10
        v = [False] * 10 + [True] * 2 + [False] * 8
        r = exact_mcnemar(u, v)
        assert r["b"] == 2 and r["c"] == 10
        # exact two-sided binomial p with n=12, k=2 under p=0.5
        from scipy.stats import binom
        expected = 2 * binom.cdf(2, 12, 0.5)
        # exact_mcnemar reports p rounded to 6 decimals
        assert abs(r["exact_p"] - round(min(1.0, float(expected)), 6)) < 1e-12

    def test_odds_ratio(self):
        u = [True] * 10 + [False] * 10
        v = [False] * 10 + [True] * 2 + [False] * 8
        r = exact_mcnemar(u, v)
        assert r["mcnemar_odds_ratio"] == 2 / 10


class TestPairedBootstrapCi:
    def test_deterministic(self):
        diffs = [1, -1, 0, 1, 1, -1, 1, 0, 1, 1] * 10
        a = paired_bootstrap_ci(diffs, n_iter=500)
        b = paired_bootstrap_ci(diffs, n_iter=500)
        assert a == b

    def test_ci_contains_mean(self):
        diffs = [1, 1, 1, 0, 0, 1, -1, 1] * 25
        r = paired_bootstrap_ci(diffs, n_iter=500)
        assert r["ci_lower"] <= r["mean"] <= r["ci_upper"]

    def test_zero_variance(self):
        diffs = [1.0] * 50
        r = paired_bootstrap_ci(diffs, n_iter=200)
        assert r["mean"] == 1.0 and r["ci_lower"] == 1.0 and r["ci_upper"] == 1.0


class TestBootstrapDid:
    def test_recovers_known_did(self):
        # u: normal 0.9, shuffle 0.7 -> G=0.2; v: normal 0.9, shuffle 0.5 -> G=0.4
        # DID = 0.2. Build 100 examples.
        rng = np.random.default_rng(7)
        n = 100
        u_norm = rng.random(n) < 0.9
        u_shuf = rng.random(n) < 0.7
        v_norm = u_norm.copy()
        v_shuf = rng.random(n) < 0.5
        quads = list(zip(u_norm, u_shuf, v_norm, v_shuf))
        r = bootstrap_did_ci(quads, n_iter=1000)
        assert abs(r["mean"] - 0.2) < 0.02
        assert r["ci_lower"] <= r["mean"] <= r["ci_upper"]

    def test_deterministic(self):
        quads = [(True, False, True, True)] * 40 + [(False, False, True, False)] * 20
        a = bootstrap_did_ci(quads, n_iter=300)
        b = bootstrap_did_ci(quads, n_iter=300)
        assert a == b

    def test_empty(self):
        r = bootstrap_did_ci([])
        assert r["n"] == 0


class TestEffectSize:
    def test_cohens_h_zero(self):
        assert abs(cohens_h(0.5, 0.5)) < 1e-12

    def test_cohens_h_positive(self):
        assert cohens_h(0.5, 0.7) > 0
        assert cohens_h(0.7, 0.5) < 0
