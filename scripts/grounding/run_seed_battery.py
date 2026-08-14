#!/usr/bin/env python3
"""Corrected seed-campaign battery driver (frozen Paper-2 Tier-A/B/C protocol).

Implements the protocol correction recorded in SPATIAL_REASONING_DECISION_LOG
(2026-08-11, "battery drift" entry). The seed campaign is evaluated with the
ALREADY-COMMITTED legacy grounding drivers, not the drifted heavy battery
(results/seed_campaign/rows + src/evaluation/battery.py, preserved as audit
history). This driver is a thin orchestration layer only: every prediction
row and metric is produced by the unmodified legacy code paths.

Battery composition (6 conditions, per the frozen protocol):
  Tier-A:  normal                             (2195 rows)
           wrong_image_shuffle (legacy shuffle derangement, ΔG contrast)
  Tier-B:  relcomp       (strict complement pairs, 0 < semantic dist < 0.3)
           facingcomp    (facing-antonym pairs; runs alone, per its freeze)
  Tier-C:  hflip_flip      (reflection; language held, L/R truth flips)
           hflip_invariant (reflection; vertical/depth truth stable)

Configuration (matches the committed legacy full grids):
  batch-size 8; attn eager for qwen2vl / sdpa for smolvlm2 (R1 2B
  amendment, DECISION_LOG 2026-08-11; verified output-identical 0/32 rows).
  Identities/eligibility come from the frozen IDs + eligibility files; the
  shuffle uses the frozen protocol permutation and verifies it on load.

Usage:
  # campaign grid (default checkpoints = full family registry):
  python scripts/grounding/run_seed_battery.py --model-family qwen2vl
  python scripts/grounding/run_seed_battery.py --model-family smolvlm2

  # restricted subset / tags:
  python scripts/grounding/run_seed_battery.py --model-family qwen2vl \
      --checkpoints zero_shot,general_lora --tag-prefix regress_7b

  # prediction-only (no analyzers), resume-aware:
  python scripts/grounding/run_seed_battery.py --model-family smolvlm2 \
      --tag-prefix regress_2b --skip-analyzers --resume
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.grounding import config

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts" / "grounding"
PY = sys.executable

# attn defaults MUST mirror the committed legacy runs (see module docstring).
FAMILY_ATTN = {"qwen2vl": "eager", "smolvlm2": "sdpa"}

# Tier-A analyzer collects all four conditions; blank/text_only are text-only
# rows (no extra image work) and are part of the frozen tier-a contract.
TIER_A_CONDITIONS = "normal,shuffle,blank,text_only"
TIER_B_RELCOMP = "relcomp"
TIER_B_FACING = "facingcomp"
TIER_C_TRANSFORMS = "hflip_flip,hflip_invariant"


def git(args_list):
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args_list],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def run_step(label, script, *args):
    cmd = [PY, str(SCRIPTS / script), *args]
    print(f"[battery] {label}\n[battery]   $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def write_metadata(family, prefix, attn, batch, checkpoints, resume):
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_branch": git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_commit": git(["rev-parse", "HEAD"]),
        "protocol_hash": config.protocol_hash(),
        "correction": "SPATIAL_REASONING_DECISION_LOG 2026-08-11 battery-drift entry",
        "model_family": family,
        "attn_implementation": attn,
        "batch_size": batch,
        "checkpoints": checkpoints,
        "tier_a_conditions": TIER_A_CONDITIONS.split(","),
        "tier_b_relcomp": [TIER_B_RELCOMP],
        "tier_b_facingcomp": [TIER_B_FACING],
        "tier_c_transforms": TIER_C_TRANSFORMS.split(","),
        "predictions_dir": f"results/grounding/predictions/{prefix}",
        "analysis_files": {
            "tier_a": f"results/grounding/analysis/tier_a_metrics_{prefix}.json",
            "tier_b_relcomp": f"results/grounding/analysis/tier_b_metrics_{prefix}_tierb.json",
            "tier_b_facingcomp": f"results/grounding/analysis/tier_b_metrics_{prefix}_facing.json",
            "tier_c": f"results/grounding/analysis/tier_c_metrics_{prefix}_tierc.json",
        },
        "resume": resume,
    }
    out_dir = config.BATTERY_DIR if hasattr(config, "BATTERY_DIR") else REPO_ROOT / "results" / "seed_campaign" / "battery"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{prefix}_metadata.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
    print(f"[battery] metadata -> {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-family", choices=sorted(config.MODEL_FAMILIES), required=True)
    ap.add_argument("--checkpoints", default=None,
                    help="checkpoint keys to evaluate (default: full family registry)")
    ap.add_argument("--tag-prefix", default=None,
                    help="prediction/analysis tag prefix (default: r1_campaign_<family>)")
    ap.add_argument("--attn", choices=["eager", "sdpa"], default=None,
                    help="defaults: eager (qwen2vl), sdpa (smolvlm2) -- committed-run parity")
    ap.add_argument("--batch-size", type=int, default=config.DEFAULT_BATCH_SIZE)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--skip-analyzers", action="store_true")
    args = ap.parse_args()

    family = args.model_family
    if args.checkpoints:
        checkpoints = [c.strip() for c in args.checkpoints.split(",") if c.strip()]
    else:
        checkpoints = list(config.MODEL_FAMILIES[family]["checkpoints"])
    attn = args.attn or FAMILY_ATTN[family]
    prefix = args.tag_prefix or f"r1_campaign_{family}"
    common = ["--model-family", family, "--checkpoints", ",".join(checkpoints),
              "--attn", attn, "--batch-size", str(args.batch_size)]
    if args.resume:
        common.append("--resume")

    write_metadata(family, prefix, attn, args.batch_size, checkpoints, args.resume)

    # Tier-A: normal + shuffle + (blank, text_only) -- analyzer contract.
    run_step("tier-a grid", "run_tier_a.py",
             "--tag", prefix, "--conditions", TIER_A_CONDITIONS, *common)
    # Tier-B: relcomp (eligible rows included), facingcomp must run alone.
    run_step("tier-b relcomp", "run_tier_b.py",
             "--tag", f"{prefix}_tierb", "--transforms", TIER_B_RELCOMP, *common)
    run_step("tier-b facingcomp (alone)", "run_tier_b.py",
             "--tag", f"{prefix}_facing", "--transforms", TIER_B_FACING, *common)
    # Tier-C: hflip flip + invariant.
    run_step("tier-c hflip", "run_tier_c.py",
             "--tag", f"{prefix}_tierc", "--transforms", TIER_C_TRANSFORMS, *common)

    if args.skip_analyzers:
        return

    run_step("analyze tier-a", "analyze_tier_a.py",
             "--tag", prefix, "--status", "confirmatory",
             "--checkpoints", ",".join(checkpoints))
    run_step("analyze tier-b relcomp", "analyze_tier_b.py",
             "--tag", f"{prefix}_tierb", "--normal-tag", prefix,
             "--status", "confirmatory", "--checkpoints", ",".join(checkpoints),
             "--transforms", TIER_B_RELCOMP, "--out-tag", f"{prefix}_tierb")
    run_step("analyze tier-b facingcomp", "analyze_tier_b.py",
             "--tag", f"{prefix}_facing", "--normal-tag", prefix,
             "--status", "confirmatory", "--checkpoints", ",".join(checkpoints),
             "--transforms", TIER_B_FACING, "--out-tag", f"{prefix}_facing")
    run_step("analyze tier-c", "analyze_tier_c.py",
             "--tag", f"{prefix}_tierc", "--normal-tag", prefix,
             "--status", "confirmatory", "--checkpoints", ",".join(checkpoints))


if __name__ == "__main__":
    main()