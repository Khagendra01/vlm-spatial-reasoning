"""Metric toy-case tests (protocol section 12: metric toy cases)."""

from src.grounding.metrics import (accuracy, accuracy_valid, condition_summary,
                                   family_breakdown, gap, invalid_rate,
                                   transitions_matrix)


def _row(example_id, correct, prediction=None, family="horizontal"):
    return {
        "example_id": example_id,
        "correct": correct,
        "prediction": prediction,
        "relation_family": family,
    }


class TestAccuracy:
    def test_all_correct(self):
        rows = [_row("a", True, True), _row("b", True, True)]
        assert accuracy(rows) == 1.0

    def test_invalid_counts_incorrect(self):
        rows = [_row("a", True, True), _row("b", False, None)]
        assert accuracy(rows) == 0.5
        assert invalid_rate(rows) == 0.5
        assert accuracy_valid(rows) == 1.0

    def test_empty(self):
        assert accuracy([]) == 0.0
        assert invalid_rate([]) == 0.0

    def test_summary_fields(self):
        rows = [_row("a", True, True), _row("b", False, None), _row("c", False, False)]
        s = condition_summary(rows)
        assert s["n"] == 3
        assert s["correct"] == 1
        assert s["invalid"] == 1
        assert s["accuracy"] == 1 / 3
        assert s["invalid_rate"] == 1 / 3


class TestGaps:
    def test_gap_definition(self):
        assert gap(0.9, 0.5) == 0.4
        assert gap(0.5, 0.5) == 0.0


class TestFamilyBreakdown:
    def test_families_separated(self):
        rows = [
            _row("a", True, True, "horizontal"),
            _row("b", False, None, "horizontal"),
            _row("c", True, True, "vertical"),
        ]
        fam = family_breakdown(rows)
        assert fam["horizontal"]["accuracy"] == 0.5
        assert fam["vertical"]["accuracy"] == 1.0
        assert fam["horizontal"]["invalid"] == 1


class TestTransitionsMatrix:
    def _summaries(self):
        # toy: zero-shot 0.80/0.60/0.70/0.65, general 0.85/0.55/0.60/0.70
        def accs(ckpt):
            return {"normal": {"accuracy": ckpt[0], "invalid_rate": 0.0},
                    "shuffle": {"accuracy": ckpt[1], "invalid_rate": 0.0},
                    "blank": {"accuracy": ckpt[2], "invalid_rate": 0.0},
                    "text_only": {"accuracy": ckpt[3], "invalid_rate": 0.0}}

        zero = accs((0.80, 0.60, 0.70, 0.65))
        gen = accs((0.85, 0.55, 0.60, 0.70))
        hn = accs((0.84, 0.56, 0.62, 0.72))
        return {
            "normal": {"zero_shot": zero["normal"], "general_lora": gen["normal"],
                       "hardneg_lora": hn["normal"]},
            "shuffle": {"zero_shot": zero["shuffle"], "general_lora": gen["shuffle"],
                        "hardneg_lora": hn["shuffle"]},
            "blank": {"zero_shot": zero["blank"], "general_lora": gen["blank"],
                      "hardneg_lora": hn["blank"]},
            "text_only": {"zero_shot": zero["text_only"], "general_lora": gen["text_only"],
                          "hardneg_lora": hn["text_only"]},
        }

    def test_transition_values(self):
        out = transitions_matrix(self._summaries())
        t = out["transitions"]["P1"]
        assert abs(t["delta_A"] - 0.05) < 1e-9
        # G_shuffle: zero=0.20, gen=0.30 -> delta=0.10
        assert abs(t["delta_G_shuffle"] - 0.10) < 1e-9
        assert abs(out["gaps"]["zero_shot"]["G_shuffle"] - 0.20) < 1e-9
        assert abs(out["gaps"]["general_lora"]["G_shuffle"] - 0.30) < 1e-9
        assert abs(out["gaps"]["general_lora"]["G_text"] - 0.15) < 1e-9
