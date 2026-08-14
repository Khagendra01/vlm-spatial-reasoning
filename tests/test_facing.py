"""Unit tests for the dedicated facing/facing-away D1 diagnostic (facingcomp).

Decision log 2026-08-11: the Tier-B relcomp table soft-excludes
facing/facing-away (oblique orientations), so a dedicated transform measures
the Paper-1 D1 construct directly. Covers scope, flip law, parse/reconstruct,
validity rows, eligible doc, and no mutation of the Tier-B artifacts.
"""

import json

import pytest

from src.grounding import config, semantic


class TestFacingScope:
    def test_pair_is_symmetric(self):
        assert semantic.FACING_COMPLEMENT_PAIRS["facing"] == "facing away from"
        assert semantic.FACING_COMPLEMENT_PAIRS["facing away from"] == "facing"

    def test_no_self_pairs(self):
        for rel, comp in semantic.FACING_COMPLEMENT_PAIRS.items():
            assert rel != comp

    def test_disjoint_from_tier_b_strict_pairs(self):
        assert not (set(semantic.FACING_COMPLEMENT_PAIRS)
                    & set(semantic.STRICT_COMPLEMENT_PAIRS))

    def test_facing_transform_not_in_canonical_transforms(self):
        # Tier-B TRANSFORMS list stays frozen: facingcomp is a dedicated
        # diagnostic with its own freeze files
        assert semantic.FACING_TRANSFORM not in semantic.TRANSFORMS

    def test_law_name(self):
        assert semantic.LAW_NAMES[semantic.FACING_TRANSFORM] == "flip_law"


class TestFacingParse:
    def test_parse_facing(self):
        assert semantic.parse_subject_object(
            "The dog is facing the cat", "facing") == ("dog", "cat")

    def test_parse_facing_away(self):
        assert semantic.parse_subject_object(
            "The dog is facing away from the cat", "facing away from") == ("dog", "cat")

    def test_reconstruct_flip(self):
        s, o = semantic.parse_subject_object(
            "The dog is facing away from the cat", "facing away from")
        assert semantic.reconstruct_statement(s, "facing", o) == \
            "The dog is facing the cat"


class TestFacingTransform:
    @pytest.fixture()
    def records(self):
        payload = json.load(open(config.IDS_FILE))
        records = [r for r in payload["examples"] if r["image_available"]]
        semantic.audit_parser(records)
        return records

    def test_flip_law_and_scope(self, records):
        seen = set()
        for row in semantic.eligible_rows(records, semantic.FACING_TRANSFORM):
            assert row["expected_prediction_behavior"] == "flip_law"
            assert row["expected_transformed_label"] == (not row["label"])
            assert row["relation"] in semantic.FACING_COMPLEMENT_PAIRS
            assert row["statement"] != row["original_statement"]
            seen.add(row["relation"])
        assert seen == set(semantic.FACING_COMPLEMENT_PAIRS)

    def test_eligibility_deterministic(self, records):
        a = [r["example_id"] for r in semantic.eligible_rows(records, semantic.FACING_TRANSFORM)]
        b = [r["example_id"] for r in semantic.eligible_rows(records, semantic.FACING_TRANSFORM)]
        assert a == b
        assert len(a) > 0


class TestFacingFreezeArtifacts:
    @pytest.fixture()
    def records(self):
        payload = json.load(open(config.IDS_FILE))
        return [r for r in payload["examples"] if r["image_available"]]

    def test_validity_rows_cover_all_relations(self, records):
        rows = semantic.build_facing_validity_table(records)
        relations = {r["relation"] for r in records}
        by_rel = {r["relation"]: r for r in rows}
        assert set(by_rel) == relations
        for rel in semantic.FACING_COMPLEMENT_PAIRS:
            assert by_rel[rel]["status"] == "strict_included"
            assert by_rel[rel]["eligible_n"] > 0

    def test_doc_counts_match_rows(self):
        records = [r for r in json.load(open(config.IDS_FILE))["examples"]
                   if r["image_available"]]
        doc = semantic.build_facing_eligible_doc(records)
        rows = semantic.eligible_rows(records, semantic.FACING_TRANSFORM)
        assert doc["transforms"][semantic.FACING_TRANSFORM]["n_eligible"] == len(rows)
        assert len(doc["transforms"][semantic.FACING_TRANSFORM]["entries"]) == len(rows)

    def test_tier_b_files_untouched_by_facing_builders(self):
        # builders must not write anything; the frozen Tier-B files' hashes
        # are the authority and are checked by the runner
        assert config.SEMANTIC_FACING_ELIGIBLE_FILE != config.SEMANTIC_ELIGIBLE_FILE
        assert config.SEMANTIC_FACING_VALIDITY_FILE != config.SEMANTIC_VALIDITY_FILE