"""Intervention + blank-image + pairing unit tests (protocol section 12)."""

import json

import pytest

from src.grounding import config
from src.grounding.images import build_blank_image, preprocess_for_vlm
from src.grounding.interventions import (all_inputs_match_labels,
                                         build_condition_inputs)
from src.grounding.shuffle import build_derangement

RECORDS = [
    {
        "example_id": f"vsr_test:{i:04d}",
        "image_link": f"http://example.invalid/{i}.jpg",
        "statement": f"The cat is on the mat {i}.",
        "label": bool(i % 2),
        "relation": "on" if i % 2 else "under",
        "family": "topology_contact" if i % 2 else "vertical",
        "subject": "cat",
        "object": "mat",
    }
    for i in range(10)
]

SHUFFLE_DOC = {
    "seed": config.SHUFFLE_SEED,
    "file_sha256": "toy",
    "mapping": build_derangement([r["example_id"] for r in RECORDS], config.SHUFFLE_SEED),
}


class TestInterventions:
    def test_normal_keeps_statement_label(self):
        inputs = build_condition_inputs(RECORDS, "normal")
        assert all_inputs_match_labels(inputs, RECORDS)
        for i, r in zip(inputs, RECORDS):
            assert i["transform_name"] == "normal"
            assert i["source_image_id"] == r["image_link"]
            assert i["replacement_image_id"] is None

    def test_shuffle_uses_frozen_mapping_no_self(self):
        inputs = build_condition_inputs(RECORDS, "shuffle", SHUFFLE_DOC)
        for i in inputs:
            repl = i["replacement_image_id"]
            assert repl is not None
            assert repl != i["example_id"]
            assert i["transform_metadata"]["seed"] == config.SHUFFLE_SEED
            assert i["transform_metadata"]["replacement_example_id"] == repl

    def test_shuffle_statement_unchanged(self):
        inputs = build_condition_inputs(RECORDS, "shuffle", SHUFFLE_DOC)
        for i, r in zip(inputs, RECORDS):
            assert i["statement"] == r["statement"]

    def test_blank_uses_deterministic_image(self):
        inputs = build_condition_inputs(RECORDS, "blank")
        for i in inputs:
            assert i["transform_name"] == "blank_image"
            assert i["image"] is not None
            # blank passes through the same 392px cap as real images
            assert i["image"].size == (config.MAX_LONG_SIDE, config.MAX_LONG_SIDE)

    def test_text_only_has_no_image(self):
        inputs = build_condition_inputs(RECORDS, "text_only")
        for i in inputs:
            assert i["image"] is None
            assert i["transform_name"] == "text_only"
            assert i["statement"] != ""

    def test_shuffle_requires_mapping(self):
        with pytest.raises(ValueError):
            build_condition_inputs(RECORDS, "shuffle", None)

    def test_shuffle_subset_uses_global_lookup(self):
        """Pilot subsets must resolve replacements from the FULL eligible set."""
        global_records = RECORDS + [
            {
                "example_id": f"vsr_test:{i:04d}",
                "image_link": f"http://example.invalid/{i}.jpg",
                "statement": f"extra {i}", "label": True,
                "relation": "near", "family": "proximity",
                "subject": "a", "object": "b",
            }
            for i in range(10, 20)
        ]
        global_mapping = build_derangement(
            [r["example_id"] for r in global_records], config.SHUFFLE_SEED)
        doc = {"seed": config.SHUFFLE_SEED, "file_sha256": "toy",
               "mapping": global_mapping}
        lookup = {r["example_id"]: r["image_link"] for r in global_records}
        subset = RECORDS[:5]  # replacements may lie outside the subset
        inputs = build_condition_inputs(subset, "shuffle", doc, link_lookup=lookup)
        for i in inputs:
            repl = i["replacement_image_id"]
            assert repl != i["example_id"]
            assert repl in global_mapping.values()
            assert repl in lookup  # replacement resolves via full set

    def test_link_lookup_must_cover_records(self):
        lookup = {r["example_id"]: r["image_link"] for r in RECORDS[:3]}
        with pytest.raises(ValueError):
            build_condition_inputs(RECORDS, "normal", link_lookup=lookup)

    def test_unknown_condition_rejected(self):
        with pytest.raises(ValueError):
            build_condition_inputs(RECORDS, "nonsense")


class TestBlankReproducibility:
    def test_blank_deterministic_pixels(self):
        a = build_blank_image()
        b = build_blank_image()
        assert list(a.getdata()) == list(b.getdata())

    def test_blank_constant_color(self):
        img = build_blank_image()
        assert all(p == config.BLANK_IMAGE_COLOR for p in img.getdata())

    def test_preprocess_caps_long_side(self):
        big = build_blank_image(1024, (10, 20, 30))
        small = preprocess_for_vlm(big)
        assert max(small.size) <= config.MAX_LONG_SIDE
        assert small.mode == "RGB"

    def test_preprocess_identity_below_cap(self):
        img = build_blank_image(64)
        out = preprocess_for_vlm(img)
        assert out.size == (64, 64)

    def test_preprocess_keeps_aspect_ratio(self):
        from PIL import Image
        img = Image.new("RGB", (800, 400), (1, 2, 3))
        out = preprocess_for_vlm(img)
        assert out.size == (config.MAX_LONG_SIDE, 196)


class TestTransformMetadataDeterminism:
    def test_metadata_json_deterministic(self):
        a = build_condition_inputs(RECORDS, "shuffle", SHUFFLE_DOC)
        b = build_condition_inputs(RECORDS, "shuffle", SHUFFLE_DOC)
        for x, y in zip(a, b):
            assert json.dumps(x["transform_metadata"], sort_keys=True) == \
                   json.dumps(y["transform_metadata"], sort_keys=True)
