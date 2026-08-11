#!/usr/bin/env python3
"""Tier-B analyzer: canonical semantic-consistency metrics + frozen report.

Usage:
  python scripts/grounding/analyze_tier_b.py --tag tierb_smoke10 --status engineering
  python scripts/grounding/analyze_tier_b.py --tag tierb_pilot200 --status engineering
  python scripts/grounding/analyze_tier_b.py --tag tierb_full --status confirmatory

Requires the corresponding Tier-A normal predictions for both-correct rates
(--normal-tag full by default; the normal rows of the SAME examples).

Outputs:
  results/grounding/analysis/tier_b_metrics_<tag>.json
  results/grounding/analysis/tier_b_report_<tag>.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config
from src.grounding.predictions import read_predictions, verify_paired_ids
from src.grounding.semantic import TRANSFORMS, LAW_NAMES
from src.grounding.semantic_metrics import (family_breakdown, relation_breakdown,
                                            transitions_matrix, transform_summary)
from src.grounding.hashing import git_branch, git_commit, utc_now_iso, write_json


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--status", choices=["engineering", "confirmatory"],
                   default="engineering")
    p.add_argument("--normal-tag", default="full")
    p.add_argument("--checkpoints", default=",".join(config.CHECKPOINTS))
    return p.parse_args()


def main():
    args = parse_args()
    ckpts = [c.strip() for c in args.checkpoints.split(",") if c.strip()]
    out_dir = config.ANALYSIS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    normal_dir = config.PREDICTIONS_DIR / args.normal_tag
    normal_rows = {c: read_predictions(normal_dir / f"{c}_normal.csv") for c in ckpts}

    all_metrics = {
        "tag": args.tag,
        "status": args.status,
        "normal_tag": args.normal_tag,
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "generated_at": utc_now_iso(),
        "transforms": {},
    }

    for t in TRANSFORMS:
        files = {c: config.PREDICTIONS_DIR / args.tag / f"{c}_{t}.csv" for c in ckpts}
        missing = [str(p) for p in files.values() if not p.exists()]
        if missing:
            raise SystemExit(f"missing prediction files: {missing}")
        verify_paired_ids(files)
        rows = {c: read_predictions(files[c]) for c in ckpts}

        summaries = {c: transform_summary(rows[c], normal_rows[c]) for c in ckpts}
        trans = transitions_matrix(rows)
        all_metrics["transforms"][t] = {
            "law": LAW_NAMES[t],
            "n_eligible": summaries[ckpts[0]]["n"],
            "summary_by_checkpoint": summaries,
            "transitions": trans,
            "family_breakdown": {c: family_breakdown(rows[c]) for c in ckpts},
            "relation_breakdown": {c: relation_breakdown(rows[c]) for c in ckpts},
        }
        print(f"[{t}] law={LAW_NAMES[t]} n={summaries[ckpts[0]]['n']}")
        for c in ckpts:
            s = summaries[c]
            print(f"  {c}: C={s['C']:.4f} both_correct={s['both_correct']:.4f} "
                  f"invalid={s['invalid_rate']:.4f}")
        for name, tr in trans.items():
            if name in ("checkpoints",):
                continue
            ci = tr["delta_c_ci"]
            print(f"  {name}: deltaC={tr['delta_C']:.4f} "
                  f"CI=[{ci['ci_lower']:.4f},{ci['ci_upper']:.4f}] "
                  f"mcnemar_p={tr['mcnemar']['exact_p']}")

    metrics_path = out_dir / f"tier_b_metrics_{args.tag}.json"
    write_json(metrics_path, all_metrics)
    report_path = out_dir / f"tier_b_report_{args.tag}.md"
    write_report(report_path, all_metrics, args)
    print(f"metrics: {metrics_path}")
    print(f"report : {report_path}")
    print(f"sha256 : {config.sha256_file(report_path)}")


def write_report(path, m, args):
    lines = [
        "# Tier-B Semantic-Consistency Audit Report",
        "",
        f"- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash "
        f"{config.protocol_hash()[:16]}...)",
        f"- **Run tag:** {m['tag']}  |  **Status label:** {m['status']}",
        f"- **Git commit:** {m['git_commit']}  |  branch {m['git_branch']}",
        f"- **Generated:** {m['generated_at']}",
        f"- **Normal-condition baseline:** tag {m['normal_tag']}",
        "",
        "> Interpretation guardrails (protocol section 16): a model can obey a "
        "semantic law while being wrong on the scene. C (obeying the expected "
        "linked-answer law) is therefore ALWAYS reported together with "
        "both-correct (obey AND normal-correct). Consistency alone is not "
        "asserted as proof of grounding, and no internal mechanism is inferred.",
        "",
        "## Definitions",
        "",
        "- `C_t(m)` = P(model prediction equals the expected transformed label "
        "under transform `t` for checkpoint `m`); invalid outputs count as "
        "non-obeying, and the invalid rate is reported separately.",
        "- `both_correct(m,t)` = P(normal prediction correct AND transformed "
        "prediction obeys the law).",
        "- `DeltaC(u->v) = C_t(v) - C_t(u)` with paired bootstrap CI "
        "(n=10000, seed 20260810) and exact McNemar on the obey indicator.",
        "",
        "## Transform definitions (frozen pre-result)",
        "",
        "| transform | law | expected behavior |",
        "|---|---|---|",
        "| relcomp | flip_law | expected = NOT original label (strict complement pairs only) |",
        "| sorev | stability_law | expected = original label (symmetric relations, subject/object swap) |",
        "| continv | paraphrase_law | expected = original label (in/inside/within <-> contains) |",
        "",
        "Validity table: `results/grounding/protocol/semantic_transform_validity.csv` "
        "(all 61 relations classified; strict/soft/unsafe/not_in_scope with "
        "reasons). Eligible IDs: `results/grounding/protocol/semantic_eligible_ids.json`.",
        "",
    ]
    for t, data in m["transforms"].items():
        lines += [
            f"## Transform: {t} (law: {data['law']}, n_eligible={data['n_eligible']})",
            "",
            "| checkpoint | C | both_correct | invalid% |",
            "|---|---:|---:|---:|",
        ]
        for c in data["summary_by_checkpoint"]:
            s = data["summary_by_checkpoint"][c]
            lines.append(
                f"| {c} | {s['C']:.4f} | {s['both_correct']:.4f} | {s['invalid_rate']:.4f} |"
            )
        lines += ["", "| transition | deltaC | 95% CI | McNemar p |", "|---|---:|---:|---:|"]
        for name, tr in data["transitions"].items():
            if name in ("checkpoints",):
                continue
            ci = tr["delta_c_ci"]
            lines.append(
                f"| {name} ({tr['from']}->{tr['to']}) | {tr['delta_C']:.4f} | "
                f"[{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}] | "
                f"{tr['mcnemar']['exact_p']} |"
            )
        lines += ["", "### Relation-family breakdown (descriptive; relation-level inference is secondary)", ""]
        for c in data["family_breakdown"]:
            lines += [f"**{c}**", "",
                      "| family | n | C | invalid% |", "|---|---:|---:|---:|"]
            for fam, fb in data["family_breakdown"][c].items():
                lines.append(f"| {fam} | {fb['n']} | {fb['C']:.4f} | {fb['invalid_rate']:.4f} |")
            lines += [""]
    lines += [
        "*Report generated from frozen protocol v0.1; semantic transforms frozen "
        "in semantic_transform_validity.csv before any Tier-B result was "
        "inspected.*",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()