#!/usr/bin/env python3
"""Seed campaign training launcher - DIAGNOSTIC ARTIFACT (2026-08-12).

Variant of run_seed_campaign.py main() with torch imported at module level
before any training code. Built to test whether the first-backward
autograd/checkpoint deadlock (DECISION_LOG 2026-08-12 entry) was caused by
import timing. Result: NEGATIVE - it deadlocked identically; the cause
remains open. Kept verbatim as part of the incident record.

Same semantics as run_seed_campaign.py main() in every other respect
(identical recipe, seeds, manifest, split, optimizer, and train_2b/train_7b
code paths).

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

import torch  # noqa: E402   module-level, before anything training-related

import argparse  # noqa: E402
from run_seed_campaign import train_2b, train_7b  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", choices=["qwen2vl_7b", "smolvlm2_2b"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    tag = [t for t, s in {"A": 101, "B": 202, "C": 303}.items() if s == args.seed]
    tag = tag[0] if tag else "?"

    if args.backbone == "qwen2vl_7b":
        train_7b(args.seed, args.output)
    else:
        train_2b(args.seed, args.output)
    print(f"DONE backbone={args.backbone} seed={args.seed} tag={tag} output={args.output}")


if __name__ == "__main__":
    main()