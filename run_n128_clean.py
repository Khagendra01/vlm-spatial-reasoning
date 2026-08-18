"""Clean confirmatory N=128 rerun with 15 matched seeds.
4 arms (augmentation, output_consistency, equiorient, wrong_geometry) x 15 seeds
= 60 runs. Same seed -> same init -> same dataset; only objective differs.
Batched 10 at a time (Modal GPU concurrency = 10), L40S only.
"""
import subprocess, sys, time, json, ast, os
from pathlib import Path

BATCH_SIZE = 10
BATCH_DELAY = 10
results_dir = Path("results/n128_clean")
results_dir.mkdir(parents=True, exist_ok=True)

ARMS = ["augmentation", "output_consistency", "equiorient", "wrong_geometry"]
SEEDS = [101, 202, 303, 404, 505,
         606, 707, 808, 909, 1010,
         1111, 1212, 1313, 1414, 1515]

jobs = []
for seed in SEEDS:
    for arm in ARMS:
        rf = results_dir / f"result_{arm}_s{seed}.json"
        if rf.exists():
            print(f"  SKIP {arm} s{seed}", flush=True)
            continue
        jobs.append((arm, seed))

print(f"\nTotal N=128 clean jobs: {len(jobs)}", flush=True)
for arm in ARMS:
    count = sum(1 for j in jobs if j[0] == arm)
    print(f"  {arm}: {count} seeds", flush=True)

completed = 0
failed = 0

for i in range(0, len(jobs), BATCH_SIZE):
    batch = jobs[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n--- Batch {batch_num}/{total_batches} ---", flush=True)

    procs = []
    for arm, seed in batch:
        cmd = (f'{sys.executable} -m modal run modal/equiorient_phase2.py '
               f'--arm {arm} --seed {seed} --n-train 128 --mode confirmatory')

        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            proc = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent), start_new_session=True)
        procs.append((proc, arm, seed))
        print(f"  Launched {arm} s{seed}", flush=True)
        time.sleep(2)

    for proc, arm, seed in procs:
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
                    out_file = results_dir / f"result_{arm}_s{seed}.json"
                    out_file.write_text(json.dumps(data, indent=1), encoding="utf-8")
                    ek = "test_eval" if "test_eval" in data else "dev_eval"
                    unseen = data.get(ek, {}).get("unseen_accuracy", "?")
                    print(f"  DONE {arm} s{seed} unseen={unseen}", flush=True)
                    completed += 1
                    found = True
                    break
            if not found:
                print(f"  FAIL {arm} s{seed} (rc={proc.returncode})", flush=True)
                failed += 1
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  TIMEOUT {arm} s{seed}", flush=True)
            failed += 1

    if i + BATCH_SIZE < len(jobs):
        print(f"  Waiting {BATCH_DELAY}s...", flush=True)
        time.sleep(BATCH_DELAY)

print(f"\n{'='*50}")
print(f"N=128 CLEAN COMPLETED: {completed}/{len(jobs)}")
print(f"FAILED: {failed}")
