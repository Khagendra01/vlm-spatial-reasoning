"""Frozen Tier-A report generation.

Produces results/grounding/analysis/tier_a_metrics.json and a markdown report
using the protocol's allowed interpretation language. A larger visual-ablation
gap is labeled "visual-evidence dependence" / "evidence consistent with
stronger visual dependence" -- never asserted as proof of grounding.
"""

import json
from datetime import datetime, timezone

from . import config
from .hashing import utc_now_iso, write_json


def build_report(analysis: dict, predictions: list, metadata: dict) -> str:
    """analysis: dict from analyze_tier_a; predictions: prediction file paths."""
    lines = []
    A = lines.append
    A("# Tier-A Evidence-Dependence Audit Report")
    A("")
    A(f"- **Protocol:** v0.1 (`{config.PROTOCOL_YAML.relative_to(config.REPO_ROOT)}`, hash "
      f"{metadata.get('protocol_hash', '')[:12]}...)")
    A(f"- **Run tag:** {metadata.get('tag', '?')}  |  **Status label:** "
      f"{metadata.get('status_label', 'engineering')}")
    A(f"- **Git commit:** {metadata.get('git_commit', '?')}  |  branch "
      f"{metadata.get('git_branch', '?')}")
    A(f"- **Generated:** {utc_now_iso()}")
    A(f"- **Prediction files:** {len(predictions)}")
    A("")
    A("> Interpretation guardrails (protocol section 16): larger ablation gaps are "
      "reported as **visual-evidence dependence** or **evidence consistent with "
      "stronger visual dependence**. They are not asserted as proof of internal "
      "grounding, geometric reasoning, or memorization.")
    A("")

    # accuracy table
    A("## Accuracy by checkpoint and condition")
    A("")
    A("| Checkpoint | normal | shuffle | blank | text_only | invalid% |")
    A("|---|---:|---:|---:|---:|---:|")
    tbl = analysis.get("accuracy_by_checkpoint_condition", {})
    inv = analysis.get("invalid_rate_by_checkpoint_condition", {})
    for ckpt in analysis.get("checkpoints", []):
        A(f"| {ckpt} | {tbl['normal'].get(ckpt, float('nan')):.4f} | "
          f"{tbl['shuffle'].get(ckpt, float('nan')):.4f} | "
          f"{tbl['blank'].get(ckpt, float('nan')):.4f} | "
          f"{tbl['text_only'].get(ckpt, float('nan')):.4f} | "
          f"{inv.get('normal', {}).get(ckpt, float('nan')):.4f} |")
    A("")
    A("Accuracy `A(m,c)` = correct / total (invalid outputs count as incorrect, "
      "matching prior repo convention); invalid rates are always reported "
      "separately.")
    A("")

    # gaps
    A("## Visual-evidence dependence gaps")
    A("")
    A("| Checkpoint | G_shuffle | G_blank | G_text |")
    A("|---|---:|---:|---:|")
    for ckpt, g in analysis.get("gaps", {}).items():
        A(f"| {ckpt} | {g['G_shuffle']:.4f} | {g['G_blank']:.4f} | {g['G_text']:.4f} |")
    A("")
    A("`G_shuffle(m) = A(m,normal) - A(m,shuffle)` is the primary evidence-ablation "
      "gap. Blank and text-only gaps are secondary/diagnostic; text-only behavior "
      "is exploratory and not the strongest grounding evidence (evidence "
      "hierarchy, protocol section 7).")
    A("")

    # transitions
    A("## Transitions (paired, normal condition)")
    A("")
    A("| Transition | DeltaA | DeltaG_shuffle | DeltaG_blank | DeltaG_text |")
    A("|---|---:|---:|---:|---:|")
    for name, t in analysis.get("transitions", {}).items():
        A(f"| {name} {t['from']} -> {t['to']} | {t['delta_A']:.4f} | "
          f"{t['delta_G_shuffle']:.4f} | {t['delta_G_blank']:.4f} | "
          f"{t['delta_G_text']:.4f} |")
    A("")
    A("`DeltaG_shuffle(u->v) = G_shuffle(v) - G_shuffle(u)`. A positive value is "
      "evidence consistent with greater dependence on the correct image; it is "
      "not by itself proof of grounding.")
    A("")

    # paired tests
    stats = analysis.get("paired_stats", {})
    if stats:
        A("## Paired tests and CIs")
        A("")
        for tname, s in stats.items():
            A(f"### {tname}: {s['from']} vs {s['to']}")
            A("")
            m = s.get("mcnemar", {})
            if m:
                A(f"- Exact McNemar (normal): b={m['b']} c={m['c']} "
                  f"p={m['exact_p']} OR={m['mcnemar_odds_ratio']:.4g}")
            for key in ("delta_a_ci", "did_ci"):
                ci = s.get(key)
                if ci:
                    A(f"- {key}: mean={ci['mean']} 95% CI "
                      f"[{ci['ci_lower']}, {ci['ci_upper']}] (bootstrap n={ci['n']})")
            for key in sorted(s.keys()):
                if key.startswith("g_shuffle_") and key.endswith("_ci"):
                    ci = s[key]
                    A(f"- {key}: mean={ci['mean']} 95% CI "
                      f"[{ci['ci_lower']}, {ci['ci_upper']}] (bootstrap n={ci['n']})")
            if s.get("effect_sizes"):
                A(f"- Effect sizes: {s['effect_sizes']}")
            A("")

    # family breakdown
    fam = analysis.get("family_breakdown", {})
    if fam:
        A("## Relation-family breakdown (descriptive; relation-level inference is secondary)")
        A("")
        for cond in ("normal", "shuffle", "blank", "text_only"):
            if cond not in fam:
                continue
            A(f"### {cond}")
            A("")
            for ckpt in analysis.get("checkpoints", []):
                fam_rows = fam[cond].get(ckpt, {})
                if not fam_rows:
                    continue
                A(f"**{ckpt}**")
                A("")
                A("| Family | n | accuracy | invalid |")
                A("|---|---:|---:|---:|")
                for fname, s in fam_rows.items():
                    A(f"| {fname} | {s['n']} | {s['accuracy']:.4f} | {s['invalid']} |")
                A("")
            A("")
    A("")
    A(f"*Report generated from frozen protocol v0.1; predictions: "
      f"{len(predictions)} files.*")
    return "\n".join(lines)


def write_analysis(analysis: dict, predictions: list, metadata: dict) -> dict:
    config.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "predictions": predictions, "analysis": analysis}
    metrics_path = config.ANALYSIS_DIR / f"tier_a_metrics_{metadata.get('tag', 'run')}.json"
    write_json(metrics_path, payload)
    md = build_report(analysis, predictions, metadata)
    report_path = config.ANALYSIS_DIR / f"tier_a_report_{metadata.get('tag', 'run')}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(md, encoding="utf-8")
    return {
        "metrics_file": str(metrics_path.relative_to(config.REPO_ROOT)),
        "report_file": str(report_path.relative_to(config.REPO_ROOT)),
        "sha256": config.sha256_file(metrics_path),
    }
