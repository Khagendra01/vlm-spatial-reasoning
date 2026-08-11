#!/usr/bin/env python3
"""Tier-C analyzer: canonical visual-direction metrics + frozen report.

Usage:
  python scripts/grounding/analyze_tier_c.py --tag tierc_smoke10 --status engineering
  python scripts/grounding/analyze_tier_c.py --tag tierc_pilot200 --status engineering
  python scripts/grounding/analyze_tier_c.py --tag tierc_full --status confirmatory

Requires the corresponding Tier-A normal predictions for both-correct rates
(--normal-tag full by default; the normal rows of the SAME examples).

Outputs:
  results/grounding/analysis/tier_c_metrics_<tag>.json
  results/grounding/analysis/tier_c_report_<tag>.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.grounding import config
from src.grounding.predictions import read_predictions, verify_paired_ids
from src.grounding.semantic_metrics import (family_breakdown, relation_breakdown,
                                            transitions_matrix, transform_summary)
from src.grounding.visual import TRANSFORMS, BEHAVIOR_NAMES
from src.grounding.visual_metrics import direction_summary
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
        directions = {c: direction_summary(rows[c], normal_rows[c]) for c in ckpts}
        all_metrics["transforms"][t] = {
            "law": BEHAVIOR_NAMES[t],
            "n_eligible": summaries[ckpts[0]]["n"],
            "summary_by_checkpoint": summaries,
            "direction_by_checkpoint": directions,
            "transitions": trans,
            "family_breakdown": {c: family_breakdown(rows[c]) for c in ckpts},
            "relation_breakdown": {c: relation_breakdown(rows[c]) for c in ckpts},
        }
        print(f"[{t}] law={BEHAVIOR_NAMES[t]} n={summaries[ckpts[0]]['n']}")
        for c in ckpts:
            s = summaries[c]
            d = directions[c]
            print(f"  {c}: C={s['C']:.4f} both_correct={s['both_correct']:.4f} "
                  f"wrong_dir={d['wrong_direction']:.4f} "
                  f"change={d['change_rate']:.4f} invalid={s['invalid_rate']:.4f}")
        for name, tr in trans.items():
            if name in ("checkpoints",):
                continue
            ci = tr["delta_c_ci"]
            print(f"  {name}: deltaC={tr['delta_C']:.4f} "
                  f"CI=[{ci['ci_lower']:.4f},{ci['ci_upper']:.4f}] "
                  f"mcnemar_p={tr['mcnemar']['exact_p']}")

    metrics_path = out_dir / f"tier_c_metrics_{args.tag}.json"
    write_json(metrics_path, all_metrics)
    report_path = out_dir / f"tier_c_report_{args.tag}.md"
    write_report(report_path, all_metrics, args)
    print(f"metrics: {metrics_path}")
    print(f"report : {report_path}")
    print(f"sha256 : {config.sha256_file(report_path)}")


def write_report(path, m, args):
    lines = [
        "# Tier-C1 Visual-Counterfactual Audit Report (horizontal reflection)",
        "",
        f"- **Protocol:** v0.1 (`configs/grounding_protocol.yaml`, hash "
        f"{config.protocol_hash()[:16]}...)",
        f"- **Run tag:** {m['tag']}  |  **Status label:** {m['status']}",
        f"- **Git commit:** {m['git_commit']}  |  branch {m['git_branch']}",
        f"- **Generated:** {m['generated_at']}",
        f"- **Normal-condition baseline:** tag {m['normal_tag']}",
        "",
        "> Interpretation guardrails (protocol section 8/16): reflected-image "
        "behavior is about causal sensitivity to the visual layout. Flip "
        "rates and expected-invariant stability rates are reported SEPARATELY "
        "and never merged. A model can flip coherently and still be wrong on "
        "the scene, so C is ALWAYS reported together with both-correct. No "
        "internal mechanism is inferred, and consistency alone is not proof "
        "of grounding.",
        "",
        "## Definitions",
        "",
        "- `C(m)` = expected-behavior rate: P(prediction equals the expected "
        "transformed label) under the image transform; invalid outputs count "
        "as non-obeying, and the invalid rate is reported separately.",
        "- For `hflip_flip` (mirrored left/right relations): C = expected "
        "flip rate, `wrong_direction` = P(pred == original label), "
        "`change_rate` = any response change, `both_correct` = normal-correct "
        "AND obeys the flip.",
        "- For `hflip_invariant` (vertical/depth controls): C = stability "
        "rate, `change_rate` = spurious response change, `both_correct` = "
        "normal-correct AND stable.",
        "- `DeltaC(u->v)` = C(v) - C(u) with paired bootstrap CI "
        "(n=10000, seed 20260810) and exact McNemar on the obey indicator.",
        "",
        "## Transform definitions (frozen pre-result)",
        "",
        "| transform | law | image change | language | expected behavior |",
        "|---|---|---|---|---|",
        "| hflip_flip | flip_expected | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = NOT original label (left/right relations) |",
        "| hflip_invariant | expected_invariant | horizontal mirror (PIL FLIP_LEFT_RIGHT) | fixed | expected = original label (vertical/depth relations) |",
        "",
        "Validity table: `results/grounding/protocol/visual_transform_validity.csv` "
        "(all 61 relations classified; flip-expected strictly only for "
        "mirrored-axis left/right relations; invariant controls kept "
        "separate). Eligible IDs: "
        "`results/grounding/protocol/visual_eligible_ids.json`. "
        "Spot-check image pairs: `results/grounding/protocol/visual_spot/`.",
        "",
    ]
    for t, data in m["transforms"].items():
        lines += [
            f"## Transform: {t} (law: {data['law']}, n_eligible={data['n_eligible']})",
            "",
            "| checkpoint | C | both_correct | wrong_dir | change | invalid% |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for c in data["summary_by_checkpoint"]:
            s = data["summary_by_checkpoint"][c]
            d = data["direction_by_checkpoint"][c]
            lines.append(
                f"| {c} | {s['C']:.4f} | {s['both_correct']:.4f} | "
                f"{d['wrong_direction']:.4f} | {d['change_rate']:.4f} | "
                f"{s['invalid_rate']:.4f} |"
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
        "*Report generated from frozen protocol v0.1; visual transforms frozen "
        "in visual_transform_validity.csv before any Tier-C result was "
        "inspected.*",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()