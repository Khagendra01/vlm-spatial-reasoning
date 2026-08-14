"""Unit tests for Tier-B semantic transforms and metrics (protocol section 12).

Covers the required pre-full-run validation: parser audit correctness,
deterministic derangement (of statements), validity-table mapping integrity,
no parallel/perpendicular complement, metric toy cases, and pairing.
"""

import json

import pytest

from src.grounding import config, semantic
from src.grounding.semantic_metrics import (family_breakdown, obey_indicator,
                                            transitions_matrix, transform_summary,
                                            pair_consistency_indicator,
                                            pair_consistency_indicators)


class TestComplementMap:
    def test_pairs_are_symmetric(self):
        for rel, comp in semantic.STRICT_COMPLEMENT_PAIRS.items():
            assert semantic.STRICT_COMPLEMENT_PAIRS[comp] == rel

    def test_no_self_pairs(self):
        for rel, comp in semantic.STRICT_COMPLEMENT_PAIRS.items():
            assert rel != comp

    def test_no_parallel_perpendicular(self):
        assert "parallel to" not in semantic.STRICT_COMPLEMENT_PAIRS
        assert "perpendicular to" not in semantic.STRICT_COMPLEMENT_PAIRS
        assert "parallel to" in semantic._UNSAFE_RELCOMP_REASONS

    def test_no_overlap_between_maps(self):
        strict = set(semantic.STRICT_COMPLEMENT_PAIRS)
        sym = set(semantic.SYMMETRIC_RELATIONS)
        cont = set(semantic.CONTAINMENT_INVERSE_MAP)
        excluded = (set(semantic._SOFT_RELCOMP_REASONS)
                    | set(semantic._UNSAFE_RELCOMP_REASONS))
        assert not (strict & sym | strict & cont | sym & cont)
        assert not (excluded & (strict | sym | cont))


class TestParserAudit:
    def test_parse_simple(self):
        assert semantic.parse_subject_object(
            "The cat is on the table", "on") == ("cat", "table")

    def test_parse_multitoken(self):
        assert semantic.parse_subject_object(
            "The person is at the left side of the dining table",
            "at the left side of") == ("person", "dining table")

    def test_parse_contains_verb(self):
        assert semantic.parse_subject_object(
            "The box contains the cake", "contains") == ("box", "cake")

    def test_reconstruct(self):
        s, o = semantic.parse_subject_object(
            "The bird is above the cat", "above")
        assert semantic.reconstruct_statement(s, "above", o) == "The bird is above the cat"

    def test_unparsable(self):
        assert semantic.parse_subject_object(
            "Bird above cat (no template)", "above") == (None, None)

    def test_same_subject_object_rejected(self):
        assert semantic.parse_subject_object(
            "The cat is next to the cat", "next to") == (None, None)

    def test_audit_all_frozen_rows(self):
        payload = json.load(open(config.IDS_FILE))
        records = [r for r in payload["examples"] if r["image_available"]]
        stats = semantic.audit_parser(records)
        assert stats["total"] == len(records)
        assert stats["parsed"] + stats["parse_failed"] + stats["reconstruct_failed"] \
            == stats["total"]


class TestTransforms:
    @pytest.fixture()
    def records(self):
        payload = json.load(open(config.IDS_FILE))
        records = [r for r in payload["examples"] if r["image_available"]]
        semantic.audit_parser(records)
        return records

    def test_relcomp_flips_label(self, records):
        for row in semantic.eligible_rows(records, "relcomp"):
            assert row["expected_prediction_behavior"] == "flip_law"
            assert row["expected_transformed_label"] == (not row["label"])
            assert row["statement"] != row["original_statement"]
            # relation must be the predeclared complement
            assert row["relation"] in semantic.STRICT_COMPLEMENT_PAIRS

    def test_sorev_stability(self, records):
        for row in semantic.eligible_rows(records, "sorev"):
            assert row["expected_prediction_behavior"] == "stability_law"
            assert row["expected_transformed_label"] == row["label"]
            assert row["relation"] in semantic.SYMMETRIC_RELATIONS

    def test_continv_paraphrase(self, records):
        for row in semantic.eligible_rows(records, "continv"):
            assert row["expected_prediction_behavior"] == "paraphrase_law"
            assert row["expected_transformed_label"] == row["label"]
            assert row["relation"] in semantic.CONTAINMENT_INVERSE_MAP

    def test_no_degenerate_identity_transforms(self, records):
        for t in semantic.TRANSFORMS:
            for row in semantic.eligible_rows(records, t):
                assert row["statement"] != row["original_statement"]

    def test_eligibility_deterministic(self, records):
        a = [r["example_id"] for r in semantic.eligible_rows(records, "relcomp")]
        b = [r["example_id"] for r in semantic.eligible_rows(records, "relcomp")]
        assert a == b


class TestMetricToys:
    def _row(self, eid, pred, expected, correct=None):
        return {
            "example_id": eid,
            "prediction": pred,
            "expected_transformed_label": expected,
            "correct": correct if correct is not None else (pred is not None),
            "relation_family": "horizontal",
            "relation": "left of",
        }

    def test_transform_summary(self):
        rows_t = [
            self._row("a", True, True),
            self._row("b", True, False),
            self._row("c", None, False),
        ]
        rows_n = [self._row("a", None, None, True),
                  self._row("b", None, None, True),
                  self._row("c", None, None, False)]
        s = transform_summary(rows_t, rows_n)
        assert s["n"] == 3
        assert s["C"] == pytest.approx(1 / 3)  # only 'a' obeys
        assert s["both_correct"] == pytest.approx(1 / 3)
        assert s["invalid_rate"] == pytest.approx(1 / 3)

    def test_obey_indicator_alignment(self):
        rows_t = [self._row("a", True, True), self._row("b", False, False)]
        rows_n = [self._row("a", True, False, False), self._row("b", True, False, True)]
        pairs = obey_indicator(rows_t, rows_n)
        assert [o for o, _ in pairs] == [True, True]
        assert [b for _, b in pairs] == [False, True]  # b obeys AND normal-correct

    def test_transitions_matrix(self):
        def make(pred, exp):
            return [self._row("a", pred, exp)]
        rows = {"zero_shot": make(True, True), "general_lora": make(True, True),
                "hardneg_lora": make(True, True)}
        tr = transitions_matrix(rows)
        assert tr["P1"]["delta_C"] == 0.0
        assert tr["P1"]["n"] == 1
        assert "exact_p" in tr["P1"]["mcnemar"]

    def test_family_breakdown(self):
        rows = [self._row("a", True, True)]
        fb = family_breakdown(rows)
        assert fb["horizontal"]["n"] == 1
        assert fb["horizontal"]["C"] == 1.0

    def _law_row(self, eid, pred, expected, law):
        row = self._row(eid, pred, expected)
        row["expected_prediction_behavior"] = law
        return row

    def test_pair_consistency_flip_unchanged_answer(self):
        rows_t = [self._law_row("a", False, False, "flip_law")]
        rows_n = [self._row("a", False, None, False)]
        s = transform_summary(rows_t, rows_n)
        assert s["A_transform"] == 1.0   # transformed accuracy, old C
        assert s["C_pair"] == 0.0        # no answer change -> not consistent
        assert pair_consistency_indicator(rows_t, rows_n) == [False]
    def test_pair_consistency_flip_changed_answer(self):
        rows_t = [self._law_row("a", True, True, "flip_law")]
        rows_n = [self._row("a", False, None, False)]
        assert transform_summary(rows_t, rows_n)["C_pair"] == 1.0
        assert pair_consistency_indicator(rows_t, rows_n) == [True]

    def test_pair_consistency_stability_kept_answer(self):
        rows_t = [self._law_row("a", False, False, "stability_law")]
        rows_n = [self._row("a", False, None, False)]
        assert transform_summary(rows_t, rows_n)["C_pair"] == 1.0

    def test_pair_consistency_stability_changed_answer(self):
        rows_t = [self._law_row("a", True, False, "stability_law")]
        rows_n = [self._row("a", False, None, False)]
        s = transform_summary(rows_t, rows_n)
        assert s["A_transform"] == 0.0   # wrong vs expected label
        assert s["C_pair"] == 0.0        # answer changed -> not consistent
        assert s["both_correct"] == 0.0

    def test_pair_consistency_paraphrase_law(self):
        rows_t = [self._law_row("a", True, True, "paraphrase_law")]
        rows_n = [self._row("a", True, None, True)]
        assert transform_summary(rows_t, rows_n)["C_pair"] == 1.0

    def test_pair_consistency_invalid_counts_non_consistent(self):
        rows_t = [self._law_row("a", None, False, "flip_law")]
        rows_n = [self._row("a", False, None, False)]
        assert pair_consistency_indicator(rows_t, rows_n) == [False]

    def test_pair_consistency_transitions(self):
        rows = {
            "zero_shot": [self._law_row("a", False, False, "flip_law")],
            "general_lora": [self._law_row("a", True, True, "flip_law")],
            "hardneg_lora": [self._law_row("a", True, True, "flip_law")],
        }
        normal = {
            "zero_shot": [self._row("a", False, None, False)],
            "general_lora": [self._row("a", False, None, False)],
            "hardneg_lora": [self._row("a", False, None, False)],
        }
        cons = pair_consistency_indicators(rows, normal)
        tr = transitions_matrix(rows, indicator=cons)
        assert tr["P1"]["delta_C"] == pytest.approx(1.0)   # C_pair 0 -> 1
        assert tr["D1"]["delta_C"] == pytest.approx(0.0)