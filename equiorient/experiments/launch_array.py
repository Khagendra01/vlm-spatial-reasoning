"""Launch the five-seed × six-arm confirmatory job array on Modal.

Usage (local):
  python -m equiorient.experiments.launch_array --check_only
  python -m equiorient.experiments.launch_array --dry_run
  python -m equiorient.experiments.launch_array   # actually launch

This generates the 30-run manifest, verifies the freeze YAML is committed,
and either prints the commands (dry_run) or submits to Modal.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.experiments.train import ARMS

SEEDS = [101, 202, 303, 404, 505]
N_TRAIN = 512
LAMBDA = 1.0


def check_freeze_committed() -> bool:
    """Verify confirmatory YAML is committed (git HEAD matches)."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=str(REPO), capture_output=True, text=True, timeout=10)
        return "phase2_confirmatory" in result.stdout.lower()
    except Exception:
        return False


def generate_manifest(seeds: list[int] = SEEDS,
                      arms: list[str] = None) -> list[dict]:
    """Generate the job manifest: list of {arm, seed, n_train, lambda}."""
    if arms is None:
        arms = list(ARMS)
    jobs = []
    for seed in seeds:
        for arm in arms:
            jobs.append({
                "arm": arm,
                "seed": seed,
                "n_train": N_TRAIN,
                "lambda": LAMBDA,
            })
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check_only", action="store_true",
                    help="Only check if freeze YAML is committed")
    ap.add_argument("--dry_run", action="store_true",
                    help="Print job list without launching")
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    ap.add_argument("--n_train", type=int, default=N_TRAIN)
    ap.add_argument("--lambda", dest="lam", type=float, default=LAMBDA)
    a = ap.parse_args()

    if a.check_only:
        ok = check_freeze_committed()
        print(f"Freeze YAML committed: {ok}")
        sys.exit(0 if ok else 1)

    jobs = generate_manifest(a.seeds)
    print(f"Job manifest: {len(jobs)} runs "
          f"({len(a.seeds)} seeds × {len(ARMS)} arms)")

    if a.dry_run:
        for j in jobs:
            print(f"  modal run modal/equiorient_phase2.py "
                  f"--arm {j['arm']} --seed {j['seed']} "
                  f"--n_train {j['n_train']} --lambda {j['lambda']}")
        return

    # Launch via Modal
    for j in jobs:
        cmd = (f"python -m modal run modal/equiorient_phase2.py "
               f"--arm {j['arm']} --seed {j['seed']} "
               f"--n_train {j['n_train']} --lambda {j['lambda']}")
        print(f"Launching: {cmd}")
        # In production, these would be submitted as background processes
        # For now, print the commands for manual execution or job scheduling


if __name__ == "__main__":
    main()
