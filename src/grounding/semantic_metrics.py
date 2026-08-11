"""Canonical Tier-B metrics (semantic axis S, study plan section 12.4).

Definitions:
  C_t(m)     = proportion of examples where the model obeys the expected
               linked-answer law for transform t on checkpoint m.
               Invalid outputs count as NON-obeying (matches the Tier-A
               accuracy convention); the invalid rate is always reported
               separately. C_valid is reported for transparency.
  both_correct(m, t) = proportion where the NORMAL prediction is correct AND
               the transformed prediction obeys the expected law.
  DeltaC(u->v) = C_t(v) - C_t(u), with paired bootstrap CI and exact
               McNemar on the per-example obey indicator.

Protocol section 8: 'Always report pair both-correct separately from
consistency.' Consistency can increase by becoming coherently wrong, so
both-correct is never collapsed into C.
"""

from collections import defaultdict

from .statistics import paired_bootstrap_ci


def obey_indicator(rows_t: list, rows_normal: list) -> list:
    """Per-example obey flags aligned to rows_t order.

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


def transform_summary(rows_t: list, rows_normal: list) -> dict:
    """rows_t: transformed rows; rows_normal: same examples, normal condition."""
    pairs = obey_indicator(rows_t, rows_normal)
    n = len(pairs)
    obey = sum(o for o, _ in pairs)
    both = sum(b for _, b in pairs)
    invalid = sum(1 for r in rows_t if r["prediction"] is None)
    return {
        "n": n,
        "obey": obey,
        "C": round(obey / n, 6) if n else 0.0,
        "both_correct": round(both / n, 6) if n else 0.0,
        "invalid": invalid,
        "invalid_rate": round(invalid / n, 6) if n else 0.0,
        "C_valid": round(
            obey / (n - invalid), 6) if n > invalid else 0.0,
    }


def transitions_matrix(rows_by_checkpoint: dict, alpha: float = 0.05) -> dict:
    """rows_by_checkpoint: {checkpoint: rows_t (example-aligned)} -> transitions.

    Pairs are example-aligned (same IDs in the same order across checkpoints,
    guaranteed by the runner's frozen eligibility). delta_C uses the paired
    bootstrap; McNemar uses the per-example obey indicator.
    """
    ckpts = list(rows_by_checkpoint.keys())
    out = {"checkpoints": ckpts}
    for name, (u, v) in {
        "P1": ("zero_shot", "general_lora"),
        "D1": ("general_lora", "hardneg_lora"),
    }.items():
        if u not in ckpts or v not in ckpts:
            continue
        ru, rv = rows_by_checkpoint[u], rows_by_checkpoint[v]
        ou = [1 if _obeys(r) else 0 for r in ru]
        ov = [1 if _obeys(r) else 0 for r in rv]
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