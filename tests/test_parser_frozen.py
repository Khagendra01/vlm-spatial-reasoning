"""Frozen parser semantics unit tests.

The parser (src/evaluation/parser.py) is frozen pre-result; these tests pin
its exact behavior so a change can never slip in silently.
"""

import pytest

from src.evaluation.parser import parse_true_false, parse_batch


class TestParserSemantics:
    def test_exact_true(self):
        assert parse_true_false("True") is True
        assert parse_true_false("true") is True

    def test_exact_false(self):
        assert parse_true_false("False") is False
        assert parse_true_false("false") is False

    def test_yes_no(self):
        assert parse_true_false("Yes") is True
        assert parse_true_false("no") is False

    def test_harmless_wrappers(self):
        assert parse_true_false("The answer is True") is True
        assert parse_true_false("The answer is False") is False
        assert parse_true_false("Answer: True") is True
        assert parse_true_false("Response: false") is False
        assert parse_true_false("Output: True") is True

    def test_statement_phrases(self):
        assert parse_true_false("The statement is true") is True
        assert parse_true_false("this statement is false") is False
        assert parse_true_false("it is true") is True
        assert parse_true_false("it's false") is False
        assert parse_true_false("not true") is False
        assert parse_true_false("not correct") is False

    def test_leading_assistant_prefix(self):
        assert parse_true_false("Assistant: True") is True
        assert parse_true_false("assistant: false") is False

    def test_case_and_padding(self):
        assert parse_true_false("  TRUE  ") is True
        assert parse_true_false("true.") is True
        assert parse_true_false("False.") is False

    def test_both_words_present_is_invalid(self):
        # "true" and "false" both present -> ambiguous -> None
        assert parse_true_false("true false") is None
        assert parse_true_false("True or False") is None

    def test_empty_output_invalid(self):
        assert parse_true_false("") is None
        assert parse_true_false("   ") is None

    def test_malformed_output_invalid(self):
        assert parse_true_false("maybe") is None
        assert parse_true_false("I cannot determine this") is None
        assert parse_true_false("42") is None
        assert parse_true_false("tru") is None
        assert parse_true_false("fals") is None

    def test_non_string_invalid(self):
        assert parse_true_false(None) is None
        assert parse_true_false(True) is None

    def test_contains_fallback_single_word(self):
        # substring fallback: "true" alone anywhere -> True
        assert parse_true_false("It is definitely true that...") is True
        assert parse_true_false("This is false indeed") is False

    def test_batch(self):
        assert parse_batch(["True", "false", "garbage", ""]) == [True, False, None, None]
