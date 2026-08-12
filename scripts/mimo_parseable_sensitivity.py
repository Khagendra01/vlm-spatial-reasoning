# -*- coding: utf-8 -*-
"""
MiMo-V2.5 format-sensitivity analysis (additive, no new API calls).

Primary results count non-conforming outputs as wrong (canonical policy:
"invalid outputs are counted wrong, never guessed"). This script reports the
sensitivity counterpart: accuracy on parseable outputs only (prediction is
exactly True or False after the canonical parser).

Outputs:
  results/mimo/mimo_parseable_sensitivity.json
  results/mimo/mimo_parseable_sensitivity.md
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "results" / "mimo" / "mimo_v25_zeroshot_predictions.csv"

ORIENT = {"facing", "facing away from", "parallel to", "perpendicular to"}


def main():
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
    parseable = [r for r in rows if (r["prediction"] or "").strip() in ("True", "False")]
    unparsed = [r for r in rows if (r["prediction"] or "").strip() not in ("True", "False")]

    def acc(sub):
        n = len(sub)
        c = sum(1 for r in sub if r["correct"] == "True")
        return c, n, (100.0 * c / n if n else float("nan"))

    full_overall = acc(rows)
    par_overall = acc(parseable)
    full_orient = acc([r for r in rows if r["relation"] in ORIENT])
    par_orient = acc([r for r in parseable if r["relation"] in ORIENT])

    # per-relation on parseable vs full
    per_rel = {}
    for rel in sorted(ORIENT):
        full_r = acc([r for r in rows if r["relation"] == rel])
        par_r = acc([r for r in parseable if r["relation"] == rel])
        per_rel[rel] = {"full": full_r, "parseable": par_r}

    out = {
        "note": "Canonical policy counts invalid outputs as wrong (never guessed); "
                "this file adds the parseable-only sensitivity.",
        "n_total": len(rows),
        "n_unparsed": len(unparsed),
        "unparsed_rate_pct": round(100.0 * len(unparsed) / len(rows), 2),
        "overall": {
            "full_counted_wrong": {"correct": full_overall[0], "n": full_overall[1],
                                   "accuracy_pct": round(full_overall[2], 2)},
            "parseable_only": {"correct": par_overall[0], "n": par_overall[1],
                               "accuracy_pct": round(par_overall[2], 2)},
        },
        "orientation": {
            "full_counted_wrong": {"correct": full_orient[0], "n": full_orient[1],
                                   "accuracy_pct": round(full_orient[2], 2)},
            "parseable_only": {"correct": par_orient[0], "n": par_orient[1],
                               "accuracy_pct": round(par_orient[2], 2)},
        },
        "per_relation": {
            rel: {"full": {"correct": v["full"][0], "n": v["full"][1],
                           "accuracy_pct": round(v["full"][2], 2)},
                  "parseable": {"correct": v["parseable"][0], "n": v["parseable"][1],
                                "accuracy_pct": round(v["parseable"][2], 2)}}
            for rel, v in per_rel.items()
        },
    }

    (ROOT / "results" / "mimo" / "mimo_parseable_sensitivity.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    md = [
        "# MiMo-V2.5 format sensitivity (parseable-only)",
        "",
        f"Total {out['n_total']} outputs; {out['n_unparsed']} non-conforming "
        f"({out['unparsed_rate_pct']}%) counted wrong under the canonical policy.",
        "",
        "| subset | full (invalid counted wrong) | parseable only |",
        "|---|---|---|",
        f"| overall | {full_overall[2]:.1f}% ({full_overall[0]}/{full_overall[1]}) | "
        f"{par_overall[2]:.1f}% ({par_overall[0]}/{par_overall[1]}) |",
        f"| orientation | {full_orient[2]:.1f}% ({full_orient[0]}/{full_orient[1]}) | "
        f"{par_orient[2]:.1f}% ({par_orient[0]}/{par_orient[1]}) |",
        "",
        "| relation | full | parseable |",
        "|---|---|---|",
    ]
    for rel, v in per_rel.items():
        md.append(f"| {rel} | {v['full'][2]:.1f}% ({v['full'][0]}/{v['full'][1]}) | "
                  f"{v['parseable'][2]:.1f}% ({v['parseable'][0]}/{v['parseable'][1]}) |")
    (ROOT / "results" / "mimo" / "mimo_parseable_sensitivity.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")

    print(f"overall:     full {full_overall[2]:.1f}% ({full_overall[0]}/{full_overall[1]}) | "
          f"parseable {par_overall[2]:.1f}% ({par_overall[0]}/{par_overall[1]})")
    print(f"orientation: full {full_orient[2]:.1f}% ({full_orient[0]}/{full_orient[1]}) | "
          f"parseable {par_orient[2]:.1f}% ({par_orient[0]}/{par_orient[1]})")
    for rel, v in per_rel.items():
        print(f"  {rel:<18} full {v['full'][2]:.1f}% | parseable {v['parseable'][2]:.1f}%")
    print("wrote results/mimo/mimo_parseable_sensitivity.json/.md")


if __name__ == "__main__":
    main()
