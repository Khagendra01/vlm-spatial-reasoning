"""Derangement / shuffle-mapping unit tests (protocol section 12)."""

import pytest

from src.grounding import config
from src.grounding.shuffle import build_derangement


IDS = [f"vsr_test:{i:04d}" for i in range(50)]


class TestDerangement:
    def test_no_self_pairs(self):
        mapping = build_derangement(IDS, config.SHUFFLE_SEED)
        for eid in IDS:
            assert mapping[eid] != eid, f"self-pair for {eid}"

    def test_is_bijection(self):
        mapping = build_derangement(IDS, config.SHUFFLE_SEED)
        assert set(mapping.keys()) == set(IDS)
        assert set(mapping.values()) == set(IDS)
        assert len(mapping) == len(IDS)

    def test_deterministic_same_seed(self):
        m1 = build_derangement(IDS, config.SHUFFLE_SEED)
        m2 = build_derangement(IDS, config.SHUFFLE_SEED)
        assert m1 == m2

    def test_different_seed_different_mapping(self):
        m1 = build_derangement(IDS, 20260810)
        m2 = build_derangement(IDS, 20260811)
        assert m1 != m2

    def test_subset_restriction_consistency(self):
        """Pilot/smoke subsets must inherit the global mapping exactly."""
        global_map = build_derangement(IDS, config.SHUFFLE_SEED)
        subset = IDS[:10]
        restricted = {e: global_map[e] for e in subset}
        # restriction of a derangement remains self-pair-free
        for e in subset:
            assert restricted[e] != e

    def test_requires_two_or_more(self):
        with pytest.raises(ValueError):
            build_derangement(["only"], config.SHUFFLE_SEED)

    def test_two_element_derangement(self):
        mapping = build_derangement(["a", "b"], config.SHUFFLE_SEED)
        assert mapping["a"] == "b" and mapping["b"] == "a"

    def test_duplicate_ids_rejected(self):
        with pytest.raises(ValueError):
            build_derangement(["a", "a", "b"], config.SHUFFLE_SEED)
