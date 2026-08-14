#!/usr/bin/env python3
"""Tier-A canonical analysis from prediction CSVs (paired, frozen protocol).

Reads results/grounding/predictions/<tag>/*.csv (one file per
checkpoint x condition), verifies exact example-ID equality across all files,
then computes and writes:

  results/grounding/analysis/tier_a_metrics_<tag>.json
  results/grounding/analysis/tier_a_report_<tag>.md

Usage:
  python scripts/grounding/analyze_tier_a.py --tag smoke10   # engineering
  python scripts/grounding/analyze_tier_a.py --tag pilot200  # engineering
  python scripts/grounding/analyze_tier_a.py --tag full      # confirmatory

--status label controls the report header only (engineering vs confirmatory);
metrics are identical either way.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config
from src.grounding.hashing import git_branch, git_commit
from src.grounding.metrics import (condition_summary, family_breakdown,
                                   transitions_matrix)
from src.grounding.predictions import read_predictions, verify_paired_ids
from src.grounding.report import write_analysis
from src.grounding.statistics import (bootstrap_did_ci, cohens_h,
                                      exact_mcnemar, paired_bootstrap_ci)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--status", default="engineering",
                   choices=["engineering", "confirmatory"],
                   help="engineering for smoke/pilot, confirmatory for full run")
    p.add_argument("--checkpoints", default=",".join(config.CHECKPOINTS))
    return p.parse_args()


def collect(pred_dir: Path, checkpoints, conditions) -> dict:
    """Return {condition: {checkpoint: rows}}."""
    files = {}
    data = {}
    for cond in conditions:
        data[cond] = {}
        for ckpt in checkpoints:
            path = pred_dir / f"{ckpt}_{cond}.csv"
            if not path.exists():
                raise SystemExit(f"missing predictions: {path}")
            files[f"{ckpt}_{cond}"] = path
            data[cond][ckpt] = read_predictions(path)
    verify_paired_ids(files)
    return data


def run_analysis(args):
    pred_dir = config.PREDICTIONS_DIR / args.tag
    checkpoints = [c.strip() for c in args.checkpoints.split(",") if c.strip()]
    conditions = config.CONDITIONS
    data = collect(pred_dir, checkpoints, conditions)

    # summaries
    summaries = {c: {m: condition_summary(data[c][m]) for m in checkpoints}
                 for c in conditions}
    analysis = transitions_matrix(summaries)
    analysis["family_breakdown"] = {
        c: {m: family_breakdown(data[c][m]) for m in checkpoints}
        for c in conditions
    }

    # paired statistics
    paired_stats = {}
    for name, cmp in config.COMPARISONS.items():
        u, v = cmp["from"], cmp["to"]
        if u not in checkpoints or v not in checkpoints:
            continue
        s = {"from": u, "to": v, "status": config.COMPARISONS[name]["status"]}

        # aligned rows (normal) for u and v
        by_id_u = {r["example_id"]: r for r in data["normal"][u]}
        by_id_v = {r["example_id"]: r for r in data["normal"][v]}
        ids = sorted(set(by_id_u) & set(by_id_v))
        uc = [bool(by_id_u[i]["correct"]) for i in ids]
        vc = [bool(by_id_v[i]["correct"]) for i in ids]
        s["mcnemar"] = exact_mcnemar(uc, vc)
        s["effect_sizes"] = {"cohens_h_deltaA": round(
            cohens_h(summaries["normal"][u]["accuracy"],
                     summaries["normal"][v]["accuracy"]), 4)}

        # paired bootstrap CI for DeltaA
        s["delta_a_ci"] = paired_bootstrap_ci(
            [int(a) - int(b) for a, b in zip(vc, uc)])

        # G_shuffle CIs per checkpoint (paired normal-vs-shuffle)
        shuf_u = {r["example_id"]: r for r in data["shuffle"][u]}
        shuf_v = {r["example_id"]: r for r in data["shuffle"][v]}
        for m, shuf_map, by_id_m in ((u, shuf_u, by_id_u), (v, shuf_v, by_id_v)):
            s[f"g_shuffle_{m}_ci"] = paired_bootstrap_ci(
                [int(by_id_m[i]["correct"]) - int(shuf_map[i]["correct"])
                 for i in ids])

        # DID bootstrap: DeltaG_shuffle(u->v), example-level quadruples
        quads = [
            (int(by_id_u[i]["correct"]), int(shuf_u[i]["correct"]),
             int(by_id_v[i]["correct"]), int(shuf_v[i]["correct"]))
            for i in ids
        ]
        s["did_ci"] = bootstrap_did_ci(quads)
        paired_stats[name] = s
    analysis["paired_stats"] = paired_stats

    meta = {
        "tag": args.tag,
        "status_label": args.status,
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "protocol_hash": config.protocol_hash(),
        "prediction_dir": str(pred_dir.relative_to(config.REPO_ROOT)),
    }
    out = write_analysis(analysis, sorted(str(p.relative_to(config.REPO_ROOT))
                                          for p in pred_dir.glob("*.csv")), meta)
    print(f"metrics: {out['metrics_file']}")
    print(f"report : {out['report_file']}")
    print(f"sha256 : {out['sha256']}")
    # quick console summary
    for c in conditions:
        row = "  ".join(f"{m}={summaries[c][m]['accuracy']:.4f}" for m in checkpoints)
        print(f"[{c}] {row}")
    for name, t in analysis["transitions"].items():
        print(f"{name}: deltaA={t['delta_A']:.4f} "
              f"deltaG_shuffle={t['delta_G_shuffle']:.4f} "
              f"CI=[{paired_stats[name]['did_ci']['ci_lower']}, "
              f"{paired_stats[name]['did_ci']['ci_upper']}]")


if __name__ == "__main__":
    run_analysis(parse_args())
