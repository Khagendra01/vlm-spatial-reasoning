"""Canonical Tier-B metrics (semantic axis S, study plan section 12.4).

Definitions:
  A_transform(m, t) = P(transformed prediction equals the expected
                transformed label) for transform t on checkpoint m. This is
                accuracy on the transformed statement. Invalid outputs count
                as incorrect; the invalid rate is always reported separately.
  C_pair(m, t) = P(pair consistency): the model's two answers obey the
                linked-answer law — flip-law transforms: P(pred_transformed
                != pred_normal); stability/paraphrase transforms: P(
                pred_transformed == pred_normal). Invalid outputs count as
                non-consistent.
  both_correct(m, t) = P(normal prediction correct AND transformed
                prediction correct).
  DeltaC_pair(u->v) = C_pair(v) - C_pair(u), with paired bootstrap CI and
                exact McNemar on the per-example pair-consistency indicator.

Protocol section 8: 'Always report pair both-correct separately from
consistency.' Consistency can increase by becoming coherently wrong, so
both-correct is never collapsed into C_pair, and A_transform (transformed
accuracy) is reported separately from C_pair (pair consistency) per decision
log 2026-08-11.
"""

from collections import defaultdict

from .statistics import paired_bootstrap_ci

FLIP_BEHAVIORS = {"flip_law", "flip_expected"}
STABLE_BEHAVIORS = {"stability_law", "paraphrase_law", "expected_invariant"}


def obey_indicator(rows_t: list, rows_normal: list) -> list:
    """Per-example transformed-accuracy flags aligned to rows_t order.

    rows_t carries expected_transformed_label; rows_normal is joined by
    example_id for both-correct computation. Predictions are None-safe.
    """
    norm_by_id = {r["example_id"]: r for r in rows_normal}
    out = []
    for rt in rows_t:
        pred = rt["prediction"]
        expected = rt["expected_transformed_label"]
        obey = pred is not None and bool(pred) == bool(expected)
        both = obey and bool(norm_by_id[rt["example_id"]]["correct"])
        out.append((obey, both))
    return out


def pair_consistency_indicator(rows_t: list, rows_normal: list) -> list:
    """Per-example linked-answer consistency flags (decision log 2026-08-11).

    flip-law transforms: consistent iff the model CHANGES its answer.
    stability/paraphrase transforms: consistent iff the model KEEPS its
    answer. Any invalid output (either side) counts as non-consistent.
    """
    norm_by_id = {r["example_id"]: r for r in rows_normal}
    out = []
    for rt in rows_t:
        law = rt.get("expected_prediction_behavior")
        pt = rt["prediction"]
        pn = norm_by_id[rt["example_id"]]["prediction"]
        if pt is None or pn is None:
            out.append(False)
        elif law in FLIP_BEHAVIORS:
            out.append(bool(pt) != bool(pn))
        elif law in STABLE_BEHAVIORS:
            out.append(bool(pt) == bool(pn))
        else:
            out.append(False)
    return out


def transform_summary(rows_t: list, rows_normal: list) -> dict:
    """rows_t: transformed rows; rows_normal: same examples, normal condition."""
    pairs = obey_indicator(rows_t, rows_normal)
    cons = pair_consistency_indicator(rows_t, rows_normal)
    n = len(pairs)
    obey = sum(o for o, _ in pairs)
    both = sum(b for _, b in pairs)
    c_pair = sum(1 for c in cons if c)
    invalid = sum(1 for r in rows_t if r["prediction"] is None)
    return {
        "n": n,
        "obey": obey,
        "A_transform": round(obey / n, 6) if n else 0.0,
        "C": round(obey / n, 6) if n else 0.0,   # legacy alias (transformed accuracy)
        "C_pair": round(c_pair / n, 6) if n else 0.0,
        "both_correct": round(both / n, 6) if n else 0.0,
        "invalid": invalid,
        "invalid_rate": round(invalid / n, 6) if n else 0.0,
        "C_valid": round(
            obey / (n - invalid), 6) if n > invalid else 0.0,
    }


def transitions_matrix(rows_by_checkpoint: dict, alpha: float = 0.05,
                       indicator: "callable | dict | None" = None) -> dict:
    """rows_by_checkpoint: {checkpoint: rows_t (example-aligned)} -> transitions.

    Pairs are example-aligned (same IDs in the same order across checkpoints,
    guaranteed by the runner's frozen eligibility). delta_C uses the paired
    bootstrap; McNemar uses the per-example indicator. `indicator` is a
    per-row bool builder: either a single callable row -> bool (default:
    transformed-accuracy obey; checkpoint-independent), or a dict
    {checkpoint: row -> bool} for indicators that depend on that checkpoint's
    own normal prediction (e.g. pair consistency, decision log 2026-08-11).
    """
    if indicator is None:
        indicator = {c: _obeys for c in rows_by_checkpoint}
    elif callable(indicator):
        indicator = {c: indicator for c in rows_by_checkpoint}

    def flags(ckpt, rows):
        fn = indicator.get(ckpt, _obeys)
        return [1 if fn(r) else 0 for r in rows]

    ckpts = list(rows_by_checkpoint.keys())
    out = {"checkpoints": ckpts}
    for name, (u, v) in {
        "P1": ("zero_shot", "general_lora"),
        "D1": ("general_lora", "hardneg_lora"),
    }.items():
        if u not in ckpts or v not in ckpts:
            continue
        ru, rv = rows_by_checkpoint[u], rows_by_checkpoint[v]
        ou, ov = flags(u, ru), flags(v, rv)
        cu, cv = sum(ou) / len(ou), sum(ov) / len(ov)
        out[name] = {
            "from": u,
            "to": v,
            "n": len(ru),
            "C_u": round(cu, 6),
            "C_v": round(cv, 6),
            "delta_C": round(cv - cu, 6),
            "delta_c_ci": paired_bootstrap_ci(
                [x - y for x, y in zip(ov, ou)], alpha=alpha),
            "mcnemar": _mcnemar(
                b=sum(1 for x, y in zip(ou, ov) if x == 0 and y == 1),
                c=sum(1 for x, y in zip(ou, ov) if x == 1 and y == 0),
            ),
        }
    return out


def _obeys(r) -> bool:
    pred = r["prediction"]
    return pred is not None and bool(pred) == bool(r["expected_transformed_label"])


def pair_consistency_indicators(rows_by_checkpoint: dict,
                                normal_by_checkpoint: dict) -> dict:
    """Per-checkpoint dict {checkpoint: row -> bool} of linked-answer
    consistency vs that checkpoint's own normal prediction (decision log
    2026-08-11). Flip laws: changed answer; stability/paraphrase laws:
    kept answer; invalid either side -> False.
    """
    out = {}
    for ckpt, rows in rows_by_checkpoint.items():
        norm = normal_by_checkpoint.get(ckpt, [])
        norm_by_id = {r["example_id"]: r["prediction"] for r in norm}
        def ind(r, _norm_by_id=norm_by_id):
            law = r.get("expected_prediction_behavior")
            pt = r["prediction"]
            pn = _norm_by_id.get(r["example_id"])
            if pt is None or pn is None:
                return False
            if law in FLIP_BEHAVIORS:
                return bool(pt) != bool(pn)
            if law in STABLE_BEHAVIORS:
                return bool(pt) == bool(pn)
            return False
        out[ckpt] = ind
    return out


def _mcnemar(b: int, c: int) -> dict:
    from scipy.stats import binom
    n_disc = b + c
    if n_disc == 0:
        p = 1.0
    else:
        k = min(b, c)
        p = min(1.0, 2.0 * binom.cdf(k, n_disc, 0.5))
    return {
        "b": b, "c": c, "discordant_n": n_disc,
        "exact_p": round(float(p), 6),
        "mcnemar_odds_ratio": float("inf") if c == 0 else (b / c if b else 0.0),
    }


def single_checkpoint_summary(rows_t: list, rows_normal: list) -> dict:
    """Rows: {example_id: row} dicts or lists joined by example_id."""
    return transform_summary(rows_t, rows_normal)


def paired_delta_c(rows_u, rows_v, alpha: float = 0.05) -> dict:
    """Paired bootstrap CI for DeltaC over per-example obey diffs."""
    diffs = [
        (1 if _obeys(ru) else 0) - (1 if _obeys(rv) else 0)
        for ru, rv in zip(rows_u, rows_v)
    ]
    return paired_bootstrap_ci(diffs, alpha=alpha)


def family_breakdown(rows_t: list) -> dict:
    groups = defaultdict(list)
    for r in rows_t:
        groups[r["relation_family"]].append(r)
    out = {}
    for fam, fam_rows in sorted(groups.items()):
        n = len(fam_rows)
        obey = sum(
            1 for r in fam_rows
            if r["prediction"] is not None
            and bool(r["prediction"]) == bool(r["expected_transformed_label"])
        )
        invalid = sum(1 for r in fam_rows if r["prediction"] is None)
        out[fam] = {
            "n": n,
            "obey": obey,
            "C": round(obey / n, 6) if n else 0.0,
            "invalid": invalid,
            "invalid_rate": round(invalid / n, 6) if n else 0.0,
        }
    return out


def relation_breakdown(rows_t: list) -> dict:
    groups = defaultdict(list)
    for r in rows_t:
        groups[r["relation"]].append(r)
    out = {}
    for rel, rel_rows in sorted(groups.items()):
        n = len(rel_rows)
        obey = sum(
            1 for r in rel_rows
            if r["prediction"] is not None
            and bool(r["prediction"]) == bool(r["expected_transformed_label"])
        )
        out[rel] = {"n": n, "C": round(obey / n, 6) if n else 0.0}
    return out