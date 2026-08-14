"""Tier-C1 visual metrics (visual axis V, study plan section 12.5).

Candidate-direction metrics for reflected images, ALWAYS reported separately
per protocol section 8: the flip-expected rate (hflip_flip) and the
expected-invariant stability rate (hflip_invariant) are never merged.

For flip-expected transforms (mirrored left/right relations):
  A_transform(m)   = P(pred_mirror == NOT original label)  (transformed accuracy)
  response_flip    = P(pred_mirror != pred_normal)          (literal response change)
  wrong_direction  = P(pred_mirror == original label)
  both_correct     = P(normal correct AND transformed correct)

For expected-invariant transforms (vertical/depth controls):
  A_transform(m)   = P(pred_mirror == original label)  (transformed accuracy)
  response_stability = P(pred_mirror == pred_normal)   (literal response stability)
  both_correct     = P(normal correct AND stable)

Invalid outputs count as NON-obeying everywhere and the invalid rate is
reported separately. Per decision log 2026-08-11 the response rates compare
the model's TWO answers (mirror vs normal prediction), not predictions vs
ground truth.
"""

from .semantic_metrics import _obeys


def response_indicators(rows_t: list, rows_normal: list) -> dict:
    """Literal response-change/stability flags vs the NORMAL prediction.

    Returns {"flip": [...]} / {"stability": [...]} keyed by the transform's
    expected behavior; flags are True when the answer CHANGED (flip) or
    STAYED (stability). None on either side -> False.
    """
    norm_by_id = {r["example_id"]: r for r in rows_normal}
    flip, stability = [], []
    for rt in rows_t:
        law = rt.get("expected_prediction_behavior")
        pt = rt["prediction"]
        pn = norm_by_id[rt["example_id"]]["prediction"]
        changed = pt is not None and pn is not None and bool(pt) != bool(pn)
        if law == "flip_expected":
            flip.append(changed)
            stability.append(None)
        elif law == "expected_invariant":
            stability.append(not changed)
            flip.append(None)
        else:
            flip.append(None)
            stability.append(None)
    return {"flip": [f for f in flip if f is not None],
            "stability": [s for s in stability if s is not None]}


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
    resp = response_indicators(rows_t, rows_normal)
    law = rows_t[0]["expected_prediction_behavior"] if n else None
    resp_rate = None
    if law == "flip_expected":
        resp_rate = round(sum(resp["flip"]) / len(resp["flip"]), 6) if resp["flip"] else None
    elif law == "expected_invariant":
        resp_rate = round(sum(resp["stability"]) / len(resp["stability"]), 6) if resp["stability"] else None
    return {
        "n": n,
        "law": law,
        "A_transform": round(obey / n, 6) if n else 0.0,
        "C": round(obey / n, 6) if n else 0.0,  # legacy alias
        "response_flip": round(sum(resp["flip"]) / len(resp["flip"]), 6) if resp["flip"] else None,
        "response_stability": round(sum(resp["stability"]) / len(resp["stability"]), 6) if resp["stability"] else None,
        "response_rate": resp_rate,
        "both_correct": round(both / n, 6) if n else 0.0,
        "wrong_direction": round(wrong / n, 6) if n else 0.0,
        "change_rate": round(change / n, 6) if n else 0.0,  # GT-based, legacy
        "invalid": inval,
        "invalid_rate": round(inval / n, 6) if n else 0.0,
    }