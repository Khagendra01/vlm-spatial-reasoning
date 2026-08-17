"""Launch data-scale experiments: N=128 and N=2048.
4 arms x 5 seeds x 2 scales = 40 runs total.
Uses parallel batches of 4 to avoid Modal rate limits.
"""
import subprocess, sys, time, json, ast, os
from pathlib import Path

BATCH_SIZE = 4
BATCH_DELAY = 15
results_dir = Path("results")

SCALE_ARMS = ["augmentation", "output_consistency", "equiorient", "wrong_geometry"]
SCALE_SEEDS = [101, 202, 303, 404, 505]
N_VALUES = [128, 2048]

jobs = []
for n in N_VALUES:
    d = results_dir / f"phase2_scale_{n}"
    d.mkdir(exist_ok=True)
    for seed in SCALE_SEEDS:
        for arm in SCALE_ARMS:
            rf = d / f"result_{arm}_s{seed}.json"
            if rf.exists():
                print(f"  SKIP scale-{n} {arm} s{seed}", flush=True)
                continue
            jobs.append((n, arm, seed))

print(f"\nTotal jobs: {len(jobs)}", flush=True)
for n in N_VALUES:
    count = sum(1 for j in jobs if j[0] == n)
    print(f"  N={n}: {count} jobs", flush=True)

completed = 0
failed = 0

for i in range(0, len(jobs), BATCH_SIZE):
    batch = jobs[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n--- Batch {batch_num}/{total_batches} ---", flush=True)

    procs = []
    for n_train, arm, seed in batch:
        cmd = (f'{sys.executable} -m modal run modal/equiorient_phase2.py '
               f'--arm {arm} --seed {seed} --n-train {n_train} --mode confirmatory')

        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            proc = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent), start_new_session=True)
        procs.append((proc, n_train, arm, seed))
        print(f"  Launched {arm} s{seed} n={n_train}", flush=True)
        time.sleep(3)

    for proc, n_train, arm, seed in procs:
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
                    out_dir = results_dir / f"phase2_scale_{n_train}"
                    out_dir.mkdir(exist_ok=True)
                    out_file = out_dir / f"result_{arm}_s{seed}.json"
                    out_file.write_text(json.dumps(data, indent=1), encoding="utf-8")
                    ek = "test_eval" if "test_eval" in data else "dev_eval"
                    unseen = data.get(ek, {}).get("unseen_accuracy", "?")
                    print(f"  DONE {arm} s{seed} n={n_train} unseen={unseen}", flush=True)
                    completed += 1
                    found = True
                    break
            if not found:
                print(f"  FAIL {arm} s{seed} n={n_train} (rc={proc.returncode})", flush=True)
                failed += 1
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  TIMEOUT {arm} s{seed} n={n_train}", flush=True)
            failed += 1

    if i + BATCH_SIZE < len(jobs):
        print(f"  Waiting {BATCH_DELAY}s...", flush=True)
        time.sleep(BATCH_DELAY)

print(f"\n{'='*50}")
print(f"COMPLETED: {completed}/{len(jobs)}")
print(f"FAILED: {failed}")
