#!/usr/bin/env python3
"""Regression harness: corrected battery MUST reproduce committed legacy outputs.

Reruns the corrected battery driver (run_seed_battery.py) on the EXISTING
legacy adapters and compares every produced metric against the already-
committed legacy analysis JSONs, cell by cell. This is the gate that must
pass before any fresh-seed battery evaluation (DECISION_LOG 2026-08-11,
battery-drift entry).

Committed targets:
  7B: tier_a_metrics_full.json, tier_b_metrics_tierb_full.json (relcomp),
      tier_b_metrics_facing_full.json, tier_c_metrics_tierc_full.json
  2B: tier_a_metrics_r1_2b_full.json, tier_b_metrics_r1_2b_tierb.json,
      tier_b_metrics_r1_2b_facing.json, tier_c_metrics_r1_2b_full.json

Comparison: greedy decoding + per-family attn contract is deterministic, so
metrics must match the committed values. Pass = every shared checkpoint-cell
is close (rel_tol 1e-8); every condition/transform cell present in the
committed files must exist in the fresh output and match.

Usage:
  python scripts/grounding/regress_seed_battery.py --model-family smolvlm2
  python scripts/grounding/regress_seed_battery.py --model-family qwen2vl

Exit code 0 on full PASS, 1 on any mismatch (missing files, drifted cells).
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PY = sys.executable

LEGACY_CHECKPOINTS = {
    "qwen2vl": ["zero_shot", "general_lora", "hardneg_lora"],
    "smolvlm2": ["zero_shot", "general_lora"],
}

COMMITTED_TARGETS = {
    "qwen2vl": {
        "tier_a": "tier_a_metrics_full.json",
        "tier_b_relcomp": "tier_b_metrics_tierb_full.json",
        "tier_b_facingcomp": "tier_b_metrics_facing_full.json",
        "tier_c": "tier_c_metrics_tierc_full.json",
    },
    "smolvlm2": {
        "tier_a": "tier_a_metrics_r1_2b_full.json",
        "tier_b_relcomp": "tier_b_metrics_r1_2b_tierb.json",
        "tier_b_facingcomp": "tier_b_metrics_r1_2b_facing.json",
        "tier_c": "tier_c_metrics_r1_2b_full.json",
    },
}

ANALYSIS_DIR = REPO_ROOT / "results" / "grounding" / "analysis"


def load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def close(a, b) -> bool:
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-8)
    return a == b


def cell_mismatches(label, committed, fresh):
    """Recursively compare scalar leaves; return list of mismatch strings."""
    out = []
    if isinstance(committed, dict) and isinstance(fresh, dict):
        for k, v in committed.items():
            if k not in fresh:
                out.append(f"{label}.{k}: MISSING in fresh output")
            else:
                out.extend(cell_mismatches(f"{label}.{k}", v, fresh[k]))
    elif isinstance(committed, (int, float)) and isinstance(fresh, (int, float)):
        if not close(committed, fresh):
            out.append(f"{label}: {committed!r} != {fresh!r}")
    elif committed != fresh:
        out.append(f"{label}: {committed!r} != {fresh!r}")
    return out


def compare_tier_a(fresh, committed, label):
    # tier-a: analysis.accuracy_by_checkpoint_condition[cond][ckpt]
    fc = fresh.get("analysis", {}).get("accuracy_by_checkpoint_condition", {})
    cc = committed.get("analysis", {}).get("accuracy_by_checkpoint_condition", {})
    if not cc:
        return [f"{label}: committed file has no accuracy_by_checkpoint_condition"]
    cells = []
    for cond, ckpts in cc.items():
        if cond not in fc:
            cells.append(f"{label}:{cond}: MISSING condition in fresh output")
            continue
        for ckpt, val in ckpts.items():
            if ckpt not in fc[cond]:
                cells.append(f"{label}:{cond}:{ckpt}: MISSING checkpoint in fresh output")
                continue
            cells.extend(cell_mismatches(f"{label}:{cond}:{ckpt}", val, fc[cond][ckpt]))
    return cells


def compare_transform_summary(fresh, committed, transform, label):
    ct = committed.get("transforms", {}).get(transform)
    ft = fresh.get("transforms", {}).get(transform)
    if not ct:
        return [f"{label}: committed file has no transforms.{transform}"]
    if not ft:
        return [f"{label}: fresh output has no transforms.{transform}"]
    cs, fs = ct.get("summary_by_checkpoint", {}), ft.get("summary_by_checkpoint", {})
    cells = []
    for ckpt, summary in cs.items():
        if ckpt not in fs:
            cells.append(f"{label}:{transform}:{ckpt}: MISSING checkpoint in fresh output")
            continue
        cells.extend(cell_mismatches(f"{label}:{transform}:{ckpt}", summary, fs[ckpt]))
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-family", choices=sorted(LEGACY_CHECKPOINTS), required=True)
    ap.add_argument("--skip-runs", action="store_true",
                    help="skip prediction/analysis generation (compare existing fresh outputs)")
    args = ap.parse_args()

    family = args.model_family
    checkpoints = LEGACY_CHECKPOINTS[family]
    prefix = f"regress_{family}"

    if not args.skip_runs:
        subprocess.run(
            [PY, str(REPO_ROOT / "scripts" / "grounding" / "run_seed_battery.py"),
             "--model-family", family, "--checkpoints", ",".join(checkpoints),
             "--tag-prefix", prefix],
            cwd=REPO_ROOT, check=True,
        )

    targets = COMMITTED_TARGETS[family]
    fresh_paths = {
        "tier_a": f"tier_a_metrics_{prefix}.json",
        "tier_b_relcomp": f"tier_b_metrics_{prefix}_tierb.json",
        "tier_b_facingcomp": f"tier_b_metrics_{prefix}_facing.json",
        "tier_c": f"tier_c_metrics_{prefix}_tierc.json",
    }

    failures = []
    for tier, committed_name in targets.items():
        committed_path = ANALYSIS_DIR / committed_name
        fresh_path = ANALYSIS_DIR / fresh_paths[tier]
        label = f"{family}:{tier}"
        if not committed_path.exists():
            failures.append(f"{label}: committed target missing: {committed_path}")
            continue
        if not fresh_path.exists():
            failures.append(f"{label}: fresh output missing: {fresh_path}")
            continue
        c, f = load(committed_path), load(fresh_path)
        if tier == "tier_a":
            failures.extend(compare_tier_a(f, c, label))
        elif tier == "tier_b_relcomp":
            failures.extend(compare_transform_summary(f, c, "relcomp", label))
        elif tier == "tier_b_facingcomp":
            failures.extend(compare_transform_summary(f, c, "facingcomp", label))
        else:
            failures.extend(compare_transform_summary(f, c, "hflip_flip", label))
            failures.extend(compare_transform_summary(f, c, "hflip_invariant", label))

    print(f"[regress] {family}: {len(failures)} mismatches")
    for m in failures:
        print(f"[regress]   FAIL {m}")
    if failures:
        sys.exit(1)
    print(f"[regress] {family}: PASS -- corrected battery reproduces committed "
          f"legacy {list(targets)} outputs")


if __name__ == "__main__":
    main()