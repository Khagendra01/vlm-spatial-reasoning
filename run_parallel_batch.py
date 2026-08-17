"""Launch jobs in parallel batches of BATCH_SIZE with delay between batches.
Modal rate-limits concurrent app creation, but 4-5 at a time works fine.
"""
import subprocess, sys, time, json, ast, os
from pathlib import Path

ARMS = ["original_sft", "augmentation", "output_consistency",
        "latent_invariance", "equiorient", "wrong_geometry"]
SEEDS = [101, 202, 303, 404, 505]
BATCH_SIZE = 4
BATCH_DELAY = 15  # seconds between batches

results_dir = Path("results/phase2_confirmatory")
results_dir.mkdir(exist_ok=True)

# Build list of jobs to run
jobs = []
for seed in SEEDS:
    for arm in ARMS:
        result_file = f"result_{arm}_s{seed}.json"
        if (results_dir / result_file).exists():
            print(f"  SKIP {result_file}", flush=True)
            continue
        jobs.append((arm, seed))

print(f"\nLaunching {len(jobs)} jobs in batches of {BATCH_SIZE}...", flush=True)

# Launch in batches
processes = []
for i in range(0, len(jobs), BATCH_SIZE):
    batch = jobs[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(jobs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} jobs) ---", flush=True)

    for arm, seed in batch:
        cmd = (f'{sys.executable} -m modal run modal/equiorient_phase2.py '
               f'--arm {arm} --seed {seed} --mode confirmatory')

        if os.name == 'nt':
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            proc = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                start_new_session=True,
            )
        processes.append((proc, arm, seed))
        print(f"  Launched {arm} s{seed} (pid={proc.pid})", flush=True)
        time.sleep(3)  # small stagger within batch

    # Wait for all jobs in this batch to finish before launching next
    print(f"  Waiting for batch {batch_num} to complete...", flush=True)
    for proc, arm, seed in processes:
        try:
            stdout, stderr = proc.communicate(timeout=3600)
            output = stdout.decode("utf-8", errors="replace") + "\n" + stderr.decode("utf-8", errors="replace")

            # Parse RESULT line
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
                    eval_key = "test_eval" if "test_eval" in data else "dev_eval"
                    unseen = data.get(eval_key, {}).get("unseen_accuracy", "?")
                    result_file = f"result_{arm}_s{seed}.json"
                    (results_dir / result_file).write_text(
                        json.dumps(data, indent=1), encoding="utf-8")
                    print(f"  DONE {arm} s{seed} unseen={unseen}", flush=True)
                    found = True
                    break
            if not found:
                print(f"  FAIL {arm} s{seed} (rc={proc.returncode})", flush=True)
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  TIMEOUT {arm} s{seed}", flush=True)

    processes = []
    # Count completed
    done = len(list(results_dir.glob("result_*_s*.json")))
    print(f"  Total: {done}/30 done", flush=True)

    # Delay between batches (not after the last one)
    if i + BATCH_SIZE < len(jobs):
        print(f"  Waiting {BATCH_DELAY}s before next batch...", flush=True)
        time.sleep(BATCH_DELAY)

done = len(list(results_dir.glob("result_*_s*.json")))
print(f"\n{'='*50}")
print(f"FINAL: {done}/30 results saved")
