"""Launch all 30 confirmatory runs via Modal CLI with robust parsing."""
import subprocess, sys, time, json, ast
from pathlib import Path

ARMS = ["original_sft", "augmentation", "output_consistency",
        "latent_invariance", "equiorient", "wrong_geometry"]
SEEDS = [101, 202, 303, 404, 505]

results_dir = Path("results/phase2_confirmatory")
results_dir.mkdir(exist_ok=True)

completed = 0
failed = 0
total = len(ARMS) * len(SEEDS)

for seed in SEEDS:
    for arm in ARMS:
        result_file = f"result_{arm}_s{seed}.json"
        if (results_dir / result_file).exists():
            print(f"  SKIP {result_file} (already exists)")
            completed += 1
            continue
        
        print(f"[{time.strftime('%H:%M:%S')}] Running {arm} seed={seed} ({completed}/{total})...", flush=True)
        cmd = [
            sys.executable, "-m", "modal", "run",
            "modal/equiorient_phase2.py",
            "--arm", arm, "--seed", str(seed),
            "--mode", "confirmatory"
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            stdout = p.stdout + "\n" + p.stderr  # Modal mixes stdout/stderr
            
            # Try to parse RESULT line - Modal uses Python repr format
            found = False
            for line in stdout.split("\n"):
                line = line.strip()
                if line.startswith("RESULT: "):
                    raw = line[8:]
                    try:
                        data = json.loads(raw)  # try JSON first
                    except json.JSONDecodeError:
                        try:
                            data = ast.literal_eval(raw)  # Python dict format
                        except Exception:
                            continue
                    
                    # Extract the eval key
                    eval_key = "test_eval" if "test_eval" in data else "dev_eval"
                    unseen = data.get(eval_key, {}).get("unseen_accuracy", "?")
                    
                    # Save with the right key name
                    out = {k: v for k, v in data.items()}
                    out[eval_key] = data.get(eval_key, {})
                    
                    (results_dir / result_file).write_text(
                        json.dumps(out, indent=1), encoding="utf-8")
                    print(f"  DONE {arm} s{seed} unseen={unseen}", flush=True)
                    completed += 1
                    found = True
                    break
            
            if not found:
                print(f"  FAIL {arm} s{seed} — no RESULT line found (rc={p.returncode})", flush=True)
                failed += 1
                # Print last 3 lines of output for debugging
                lines = stdout.strip().split("\n")
                for l in lines[-3:]:
                    print(f"    | {l}", flush=True)
        
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT {arm} s{seed}", flush=True)
            failed += 1
        
        print(f"  Progress: {completed}/{total} done, {failed} failed", flush=True)

print(f"\n{'='*50}")
print(f"COMPLETED: {completed}/{total}")
print(f"FAILED: {failed}")
