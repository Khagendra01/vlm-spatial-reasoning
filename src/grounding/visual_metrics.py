"""Tier-C1 visual metrics (visual axis V, study plan section 12.5).

Candidate-direction metrics for reflected images, ALWAYS reported separately
per protocol section 8: the flip-expected rate (hflip_flip) and the
expected-invariant stability rate (hflip_invariant) are never merged.

For flip-expected transforms (mirrored left/right relations):
  C(m)              = expected flip rate: P(pred == NOT original label)
  wrong_direction   = P(pred == original label)  (spurious flip-adverse)
  change_rate       = P(pred != original label)  (any response change)
  both_correct      = P(normal correct AND pred obeys the expected flip)

For expected-invariant transforms (vertical/depth controls):
  C(m)              = stability rate: P(pred == original label)
  change_rate       = P(pred != original label)  (spurious response change)
  both_correct      = P(normal correct AND stable)

Invalid outputs count as NON-obeying everywhere and the invalid rate is
reported separately.
"""

from .semantic_metrics import _obeys


def direction_summary(rows_t: list, rows_normal: list) -> dict:
    """Direction metrics for one checkpoint x transform (visual axis)."""
    norm_by_id = {r["example_id"]: r for r in rows_normal}
    n = len(rows_t)
    obey = sum(1 for r in rows_t if _obeys(r))
    both = sum(
        1 for r in rows_t
        if _obeys(r) and bool(norm_by_id[r["example_id"]]["correct"])
    )
    wrong = sum(
        1 for r in rows_t
        if r["prediction"] is not None
        and bool(r["prediction"]) == bool(r["ground_truth"])
    )
    inval = sum(1 for r in rows_t if r["prediction"] is None)
    change = sum(1 for r in rows_t if r["prediction"] is not None
                 and bool(r["prediction"]) != bool(r["ground_truth"]))
    return {
        "n": n,
        "law": rows_t[0]["expected_prediction_behavior"] if n else None,
        "C": round(obey / n, 6) if n else 0.0,
        "obey": obey,
        "both_correct": round(both / n, 6) if n else 0.0,
        "wrong_direction": round(wrong / n, 6) if n else 0.0,
        "change_rate": round(change / n, 6) if n else 0.0,
        "invalid": inval,
        "invalid_rate": round(inval / n, 6) if n else 0.0,
    }