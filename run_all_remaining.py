"""Launch ALL remaining experiments: data-scale + second backbone.
Batch 4 at a time to avoid Modal rate limits.
"""
import subprocess, sys, time, json, ast, os
from pathlib import Path

BATCH_SIZE = 6  # Modal task limit is 10; leave headroom
BATCH_DELAY = 15
results_dir = Path("results")

# ============================================================
# Experiment 1: Data-scale N=128 (4 arms x 5 seeds = 20 runs)
# Experiment 2: Data-scale N=2048 (4 arms x 5 seeds = 20 runs)
# Experiment 3: Backbone Qwen2-VL-7B (4 arms x 3 seeds = 12 runs)
# ============================================================
SCALE_ARMS = ["augmentation", "output_consistency", "equiorient", "wrong_geometry"]
SCALE_SEEDS = [101, 202, 303, 404, 505]
BB_SEEDS = [101, 202, 303]

jobs = []

# Data-scale jobs
for n in [128, 2048]:
    d = results_dir / f"phase2_scale_{n}"
    d.mkdir(exist_ok=True)
    for seed in SCALE_SEEDS:
        for arm in SCALE_ARMS:
            rf = d / f"result_{arm}_s{seed}.json"
            if rf.exists():
                print(f"  SKIP scale-{n} {arm} s{seed}", flush=True)
                continue
            jobs.append(("scale", n, arm, seed, "qwen3"))

# Backbone jobs
bb_dir = results_dir / "phase2_backbone_qwen2vl"
bb_dir.mkdir(exist_ok=True)
for seed in BB_SEEDS:
    for arm in SCALE_ARMS:
        rf = bb_dir / f"result_{arm}_s{seed}.json"
        if rf.exists():
            print(f"  SKIP backbone {arm} s{seed}", flush=True)
            continue
        jobs.append(("backbone", 512, arm, seed, "qwen2vl"))

print(f"\nTotal jobs: {len(jobs)}", flush=True)
print(f"  N=128: {sum(1 for j in jobs if j[0]=='scale' and j[1]==128)}", flush=True)
print(f"  N=2048: {sum(1 for j in jobs if j[0]=='scale' and j[1]==2048)}", flush=True)
print(f"  Qwen2-VL: {sum(1 for j in jobs if j[0]=='backbone')}", flush=True)

completed = 0
failed = 0

for i in range(0, len(jobs), BATCH_SIZE):
    batch = jobs[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n--- Batch {batch_num}/{total_batches} ---", flush=True)

    procs = []
    for experiment, n_train, arm, seed, bb in batch:
        cmd = (f'{sys.executable} -m modal run modal/equiorient_phase2.py '
               f'--arm {arm} --seed {seed} --n-train {n_train} '
               f'--backbone {bb} --mode confirmatory')

        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            proc = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent), start_new_session=True)
        procs.append((proc, experiment, n_train, arm, seed, bb))
        print(f"  Launched {experiment} {arm} s{seed} n={n_train} bb={bb}", flush=True)
        time.sleep(3)

    for proc, experiment, n_train, arm, seed, bb in procs:
        try:
            stdout, stderr = proc.communicate(timeout=3600)
            output = stdout.decode("utf-8", errors="replace") + "\n" + stderr.decode("utf-8", errors="replace")
            found = False
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("RESULT: "):
                    raw = line[8:]
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        try:
                            data = ast.literal_eval(raw)
                        except Exception:
                            continue
                    if experiment == "scale":
                        out_dir = results_dir / f"phase2_scale_{n_train}"
                    else:
                        out_dir = bb_dir
                    out_dir.mkdir(exist_ok=True)
                    out_file = out_dir / f"result_{arm}_s{seed}.json"
                    out_file.write_text(json.dumps(data, indent=1), encoding="utf-8")
                    ek = "test_eval" if "test_eval" in data else "dev_eval"
                    unseen = data.get(ek, {}).get("unseen_accuracy", "?")
                    print(f"  DONE {experiment} {arm} s{seed} n={n_train} unseen={unseen}", flush=True)
                    completed += 1
                    found = True
                    break
            if not found:
                print(f"  FAIL {experiment} {arm} s{seed} n={n_train} (rc={proc.returncode})", flush=True)
                failed += 1
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  TIMEOUT {experiment} {arm} s{seed} n={n_train}", flush=True)
            failed += 1

    if i + BATCH_SIZE < len(jobs):
        print(f"  Waiting {BATCH_DELAY}s...", flush=True)
        time.sleep(BATCH_DELAY)

print(f"\n{'='*50}")
print(f"COMPLETED: {completed}/{len(jobs)}")
print(f"FAILED: {failed}")
