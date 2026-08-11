"""Prediction schema / CSV round-trip / pairing tests."""

import json
import os

import pytest

from src.grounding import config
from src.grounding.predictions import (PREDICTION_FIELDS, build_prediction_row,
                                       read_predictions, verify_paired_ids,
                                       write_predictions)


def _checkpoint(label="7B_zero_shot", adapter=None):
    return {"model_id": config.BASE_MODEL_ID,
            "adapter_path": adapter,
            "label": label}


def _record(eid="vsr_test:0000"):
    return {
        "example_id": eid, "image_link": "http://x/0.jpg",
        "statement": "The cat is on the mat.", "label": True,
        "relation": "on", "family": "topology_contact",
        "subject": "cat", "object": "mat", "content_hash": "abc",
    }


def _input_row(eid="vsr_test:0000", transform="normal"):
    meta = {"axis": "evidence", "condition": transform}
    if transform == "shuffle_image":
        meta = {**meta, "seed": config.SHUFFLE_SEED, "replacement_example_id": "vsr_test:0001"}
    return {
        "example_id": eid, "statement": "The cat is on the mat.",
        "label": True, "relation": "on", "family": "topology_contact",
        "image_link": "http://x/0.jpg",
        "source_image_id": "http://x/0.jpg",
        "replacement_image_id": None if transform != "shuffle_image" else "vsr_test:0001",
        "transformed_image_id": "http://x/0.jpg",
        "transform_name": transform,
        "transform_version": config.TRANSFORM_VERSION,
        "transform_metadata": meta,
    }


class TestPredictionRow:
    def test_fields_present(self):
        row = build_prediction_row(_record(), _input_row(), True, "True",
                                   _checkpoint(), "run_x",
                                   config.prompt_hash(), config.parser_hash(), "h")
        assert set(PREDICTION_FIELDS) <= set(row.keys())

    def test_correct_logic(self):
        row = build_prediction_row(_record(), _input_row(), False, "False",
                                   _checkpoint(), "run_x", "p", "q", "h")
        assert row["correct"] is False
        row2 = build_prediction_row(_record(), _input_row(), True, "True",
                                    _checkpoint(), "run_x", "p", "q", "h")
        assert row2["correct"] is True

    def test_invalid_prediction_not_correct(self):
        row = build_prediction_row(_record(), _input_row(), None, "garbage",
                                   _checkpoint(), "run_x", "p", "q", "h")
        assert row["prediction"] is None and row["correct"] is False
        assert row["raw_output"] == "garbage"

    def test_condition_mapping(self):
        row = build_prediction_row(_record(), _input_row(transform="shuffle_image"),
                                   True, "True", _checkpoint(), "run_x", "p", "q", "h")
        assert row["condition"] == "shuffle"
        assert row["shuffle_seed"] == config.SHUFFLE_SEED
        row2 = build_prediction_row(_record(), _input_row(transform="blank_image"),
                                    True, "True", _checkpoint(), "run_x", "p", "q", "h")
        assert row2["condition"] == "blank"


class TestCsvRoundTrip:
    def test_roundtrip(self, tmp_path):
        rows = []
        for i in range(5):
            rec = _record(f"vsr_test:{i:04d}")
            inp = _input_row(f"vsr_test:{i:04d}", "normal" if i % 2 else "text_only")
            rows.append(build_prediction_row(
                rec, inp, bool(i % 2), "True" if i % 2 else "False",
                _checkpoint(), "rt", "p", "q", "h"))
        path = tmp_path / "preds.csv"
        write_predictions(path, rows)
        back = read_predictions(path)
        assert len(back) == len(rows)
        assert back[0]["ground_truth"] is True
        assert back[1]["prediction"] is True  # i=1 -> parsed True
        assert back[2]["prediction"] is False  # i=2 -> parsed False
        assert back[0]["condition"] == "text_only"

    def test_expected_transformed_label_type_recovery(self, tmp_path):
        # regression: read_predictions must convert expected_transformed_label
        # to a real bool, otherwise bool("False") == True corrupts obey metrics
        rows = [{"example_id": "vsr_test:0001", "paired_parent_id": "vsr_test:0001",
                 "split": "test", "condition": "hflip_flip", "intervention_axis": "visual",
                 "statement": "s", "original_statement": "s", "relation": "left of",
                 "relation_family": "horizontal", "subject": "a", "object": "b",
                 "ground_truth": True, "expected_transformed_label": False,
                 "expected_prediction_behavior": "flip_expected", "prediction": True,
                 "correct": False, "raw_output": "True", "model_id": "m",
                 "model_revision": None, "model_condition": "zero_shot",
                 "adapter_path": "", "adapter_hash": "", "training_seed": None,
                 "prompt_version": "p", "parser_version": "q", "image_id": "i",
                 "source_image_id": "i", "replacement_image_id": None,
                 "transformed_image_id": "i", "transform_name": "hflip",
                 "transform_version": "tier_c_v0.1", "transform_metadata": "{}",
                 "shuffle_seed": None, "generation_settings": "{}", "run_id": "r",
                 "git_commit": "g", "protocol_version": "v0.1"}]
        path = tmp_path / "et.csv"
        write_predictions(path, rows)
        back = read_predictions(path)[0]
        assert back["expected_transformed_label"] is False
        assert back["ground_truth"] is True
        assert back["prediction"] is True
        assert back["correct"] is False

    def test_paired_ids_equal(self, tmp_path):
        rows_a = [build_prediction_row(_record(f"vsr_test:{i:04d}"),
                                       _input_row(f"vsr_test:{i:04d}"),
                                       True, "True", _checkpoint("a"), "r", "p", "q", "h")
                  for i in range(3)]
        rows_b = [build_prediction_row(_record(f"vsr_test:{i:04d}"),
                                       _input_row(f"vsr_test:{i:04d}"),
                                       False, "False", _checkpoint("b"), "r", "p", "q", "h")
                  for i in range(3)]
        pa = tmp_path / "a.csv"
        pb = tmp_path / "b.csv"
        write_predictions(pa, rows_a)
        write_predictions(pb, rows_b)
        verify_paired_ids({"a": pa, "b": pb})  # should not raise

    def test_paired_ids_mismatch_raises(self, tmp_path):
        rows_a = [build_prediction_row(_record(f"vsr_test:{i:04d}"),
                                       _input_row(f"vsr_test:{i:04d}"),
                                       True, "True", _checkpoint("a"), "r", "p", "q", "h")
                  for i in range(3)]
        rows_b = [build_prediction_row(_record(f"vsr_test:{i:04d}"),
                                       _input_row(f"vsr_test:{i:04d}"),
                                       True, "True", _checkpoint("b"), "r", "p", "q", "h")
                  for i in range(2)]
        pa = tmp_path / "a.csv"
        pb = tmp_path / "b.csv"
        write_predictions(pa, rows_a)
        write_predictions(pb, rows_b)
        with pytest.raises(RuntimeError):
            verify_paired_ids({"a": pa, "b": pb})
