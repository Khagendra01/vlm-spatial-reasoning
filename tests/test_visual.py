"""Unit tests for Tier-C1 visual transforms and metrics (protocol section 12).

Covers the required pre-full-run validation: hflip determinism, flip-expected
vs invariant scope separation, expected-label law (flip vs stability), no
global label flip, validity-table mapping integrity, metric toy cases.
"""

import json

import pytest
from PIL import Image

from src.grounding import config, visual
from src.grounding.visual_metrics import direction_summary


class TestScope:
    def test_flip_relations_are_mirrored_axis_only(self):
        assert visual.FLIP_EXPECTED_RELATIONS == {
            "left of", "right of", "at the left side of", "at the right side of",
        }

    def test_invariant_relations_are_vertical_depth(self):
        assert visual.INVARIANT_RELATIONS == {
            "above", "below", "in front of", "behind",
        }

    def test_scopes_are_disjoint(self):
        assert not (visual.FLIP_EXPECTED_RELATIONS & visual.INVARIANT_RELATIONS)

    def test_no_global_label_flip(self):
        records = [r for r in json.load(open(config.IDS_FILE))["examples"]
                   if r["image_available"]]
        for row in visual.eligible_rows(records, "hflip_invariant"):
            assert row["expected_transformed_label"] == row["label"]


class TestTransformBuild:
    @pytest.fixture()
    def records(self):
        payload = json.load(open(config.IDS_FILE))
        return [r for r in payload["examples"] if r["image_available"]]

    def test_flip_expected(self, records):
        for row in visual.eligible_rows(records, "hflip_flip"):
            assert row["expected_prediction_behavior"] == "flip_expected"
            assert row["expected_transformed_label"] == (not row["label"])
            assert row["relation"] in visual.FLIP_EXPECTED_RELATIONS
            assert row["statement"] == row["original_statement"]

    def test_invariant_stability(self, records):
        for row in visual.eligible_rows(records, "hflip_invariant"):
            assert row["expected_prediction_behavior"] == "expected_invariant"
            assert row["expected_transformed_label"] == row["label"]
            assert row["relation"] in visual.INVARIANT_RELATIONS
            assert row["statement"] == row["original_statement"]

    def test_statement_never_edited(self, records):
        for t in visual.TRANSFORMS:
            for row in visual.eligible_rows(records, t):
                assert row["statement"] == row["original_statement"]
                assert row["transform_name"] == "hflip"

    def test_eligibility_deterministic(self, records):
        for t in visual.TRANSFORMS:
            a = [r["example_id"] for r in visual.eligible_rows(records, t)]
            b = [r["example_id"] for r in visual.eligible_rows(records, t)]
            assert a == b


class TestImageFlip:
    def test_flip_is_deterministic(self):
        img = Image.new("RGB", (8, 6))
        px = img.load()
        for y in range(6):
            for x in range(8):
                px[x, y] = (x * 30, y * 40, 128)
        a = visual.flip_image(img)
        b = visual.flip_image(img)
        assert list(a.getdata()) == list(b.getdata())

    def test_flip_is_reflection(self):
        img = Image.new("RGB", (8, 6))
        px = img.load()
        for y in range(6):
            for x in range(8):
                px[x, y] = (x, y, 0)
        flipped = visual.flip_image(img)
        for y in range(6):
            for x in range(8):
                assert flipped.getpixel((x, y)) == img.getpixel((7 - x, y))

    def test_double_flip_restores(self):
        img = Image.new("RGB", (9, 7), (1, 2, 3))
        assert list(visual.flip_image(visual.flip_image(img)).getdata()) \
            == list(img.getdata())


class TestValidityRows:
    def test_every_relation_classified_both_transforms(self):
        records = [r for r in json.load(open(config.IDS_FILE))["examples"]
                   if r["image_available"]]
        rows = visual.build_validity_rows(records)
        by_key = {(r["transform"], r["relation"]): r for r in rows}
        relations = {r["relation"] for r in records}
        for t in visual.TRANSFORMS:
            for rel in relations:
                assert (t, rel) in by_key
                assert by_key[(t, rel)]["status"] in (
                    "strict_included", "not_in_scope")

    def test_flip_expected_only_for_mirrored_axis(self):
        records = [r for r in json.load(open(config.IDS_FILE))["examples"]
                   if r["image_available"]]
        for row in visual.build_validity_rows(records):
            if row["transform"] == "hflip_flip":
                if row["status"] == "strict_included":
                    assert row["relation"] in visual.FLIP_EXPECTED_RELATIONS

    def test_eligible_counts_match_rows(self):
        records = [r for r in json.load(open(config.IDS_FILE))["examples"]
                   if r["image_available"]]
        doc = visual.build_eligible_ids_doc(records)
        for t in visual.TRANSFORMS:
            rows = visual.eligible_rows(records, t)
            assert doc["transforms"][t]["n_eligible"] == len(rows)
            assert len(doc["transforms"][t]["entries"]) == len(rows)


class TestDirectionMetrics:
    def _row(self, eid, pred, truth, expected, normal_correct):
        return {
            "example_id": eid,
            "prediction": pred,
            "ground_truth": truth,
            "expected_transformed_label": expected,
            "expected_prediction_behavior": "flip_expected",
            "relation_family": "horizontal",
            "relation": "left of",
            "correct": normal_correct,
        }

    def test_flip_direction_toy(self):
        rows_t = [
            self._row("a", True, True, False, True),
            self._row("b", False, True, False, True),
            self._row("c", True, False, True, False),
        ]
        rows_n = [self._row("a", None, None, None, True),
                  self._row("b", None, None, None, True),
                  self._row("c", None, None, None, False)]
        d = direction_summary(rows_t, rows_n)
        # a: flips (obey) + normal-correct; b: wrong-direction; c: stable-but-wrong
        assert d["C"] == pytest.approx(2 / 3)
        assert d["both_correct"] == pytest.approx(1 / 3)
        assert d["wrong_direction"] == pytest.approx(1 / 3)
        assert d["change_rate"] == pytest.approx(2 / 3)
        assert d["invalid_rate"] == 0.0

    def test_invalid_counts_as_non_obey(self):
        rows_t = [self._row("a", None, True, False, True)]
        rows_n = [self._row("a", None, None, None, True)]
        d = direction_summary(rows_t, rows_n)
        assert d["C"] == 0.0
        assert d["invalid_rate"] == 1.0

    def test_response_flip_vs_normal_prediction(self):
        rows_t = [
            self._row("a", True, True, False, True),
            self._row("b", False, True, False, True),
            self._row("c", False, False, True, True),
        ]
        rows_n = [
            self._row("a", False, None, None, True),
            self._row("b", True, None, None, True),
            self._row("c", False, None, None, True),
        ]
        d = direction_summary(rows_t, rows_n)
        # a: True->False flips; b: False->True flips; c: False->False stays
        assert d["response_flip"] == pytest.approx(2 / 3)
        assert d["response_rate"] == pytest.approx(2 / 3)
        assert d["response_stability"] is None

    def test_response_stability_vs_normal_prediction(self):
        def row(eid, pred, truth, expected, ncorr):
            r = self._row(eid, pred, truth, expected, ncorr)
            r["expected_prediction_behavior"] = "expected_invariant"
            r["relation_family"] = "vertical"
            return r
        rows_t = [
            row("a", True, True, True, True),
            row("b", True, True, True, True),
            row("c", False, True, True, True),
        ]
        rows_n = [
            row("a", True, None, None, True),
            row("b", False, None, None, True),
            row("c", False, None, None, True),
        ]
        d = direction_summary(rows_t, rows_n)
        # a: True->True stays; b: True->False changed; c: False->False stays
        assert d["response_stability"] == pytest.approx(2 / 3)
        assert d["response_rate"] == pytest.approx(2 / 3)
        assert d["response_flip"] is None

    def test_response_indicators_invalid_side(self):
        rows_t = [self._row("a", True, True, False, True)]
        rows_n = [self._row("a", None, None, None, True)]
        d = direction_summary(rows_t, rows_n)
        assert d["response_flip"] == 0.0  # normal-side invalid -> not a flip
        assert d["response_rate"] == 0.0