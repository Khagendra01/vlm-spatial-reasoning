"""Canonical Tier-A metrics.

Definitions frozen in research/GROUNDING_PROTOCOL_FREEZE.md section 8:
  A(m,c)      = accuracy for model condition m in evaluation condition c
  DeltaA(u->v)= A(v,normal) - A(u,normal)
  G_shuffle(m)= A(m,normal) - A(m,shuffle)   (primary evidence-ablation gap)
  G_blank(m)  = A(m,normal) - A(m,blank)     (secondary)
  G_text(m)   = A(m,normal) - A(m,text_only) (exploratory)
  DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)

Accuracy A = correct / total, counting invalid outputs as incorrect (matches
every prior run in this repo), with the invalid rate always reported
separately. A_valid (accuracy over parseable rows) is also reported for
transparency but is not the primary metric.
"""

from collections import defaultdict


def accuracy(rows: list) -> float:
    if not rows:
        return 0.0
    return sum(1 for r in rows if r["correct"]) / len(rows)


def invalid_rate(rows: list) -> float:
    if not rows:
        return 0.0
    return sum(1 for r in rows if r["prediction"] is None) / len(rows)


def accuracy_valid(rows: list) -> float:
    valid = [r for r in rows if r["prediction"] is not None]
    if not valid:
        return 0.0
    return sum(1 for r in valid if r["correct"]) / len(valid)


def condition_summary(rows: list) -> dict:
    return {
        "n": len(rows),
        "correct": sum(1 for r in rows if r["correct"]),
        "accuracy": accuracy(rows),
        "accuracy_valid": accuracy_valid(rows),
        "invalid": sum(1 for r in rows if r["prediction"] is None),
        "invalid_rate": invalid_rate(rows),
    }


def family_breakdown(rows: list) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[r["relation_family"]].append(r)
    out = {}
    for fam, fam_rows in sorted(groups.items()):
        s = condition_summary(fam_rows)
        out[fam] = s
    return out


def gap(a_normal: float, a_condition: float) -> float:
    return a_normal - a_condition


def transitions_matrix(summaries: dict) -> dict:
    """summaries: {condition: {checkpoint: summary}} -> canonical metrics.

    Conditions available: normal, shuffle, blank, text_only.
    """
    ckpts = list(summaries["normal"].keys())
    out = {"checkpoints": ckpts, "conditions": list(summaries.keys())}

    # A(m,c) table
    table = {}
    for c in summaries:
        table[c] = {m: summaries[c][m]["accuracy"] for m in ckpts}
    out["accuracy_by_checkpoint_condition"] = table

    # invalid rates
    out["invalid_rate_by_checkpoint_condition"] = {
        c: {m: summaries[c][m]["invalid_rate"] for m in ckpts} for c in summaries
    }

    # gaps per checkpoint
    gaps = {}
    for m in ckpts:
        a_norm = table["normal"][m]
        gaps[m] = {
            "G_shuffle": gap(a_norm, table["shuffle"][m]),
            "G_blank": gap(a_norm, table["blank"][m]),
            "G_text": gap(a_norm, table["text_only"][m]),
        }
    out["gaps"] = gaps

    # transitions P1 and D1
    transitions = {}
    for name, cmp in {
        "P1": ("zero_shot", "general_lora"),
        "D1": ("general_lora", "hardneg_lora"),
    }.items():
        u, v = cmp
        if u not in ckpts or v not in ckpts:
            continue
        transitions[name] = {
            "from": u,
            "to": v,
            "delta_A": table["normal"][v] - table["normal"][u],
            "delta_G_shuffle": (gaps[v]["G_shuffle"] - gaps[u]["G_shuffle"]),
            "delta_G_blank": gaps[v]["G_blank"] - gaps[u]["G_blank"],
            "delta_G_text": gaps[v]["G_text"] - gaps[u]["G_text"],
        }
    out["transitions"] = transitions
    return out
