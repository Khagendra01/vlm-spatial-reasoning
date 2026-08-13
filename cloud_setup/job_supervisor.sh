#!/usr/bin/env bash
# ============================================================================
# job_supervisor.sh — reliable on-machine job daemon for seed-variance runs.
#
# Why this exists: background jobs started through MCP/SSH die with the
# instance, and SSH sessions drop. This daemon runs detached (nohup), owns a
# queue file, and keeps all state on the persistent disk so monitoring is
# always truthful even if every remote handle is lost.
#
# State file ~/job_state.json (written on every event + 30s heartbeat):
#   { "status": staged|running|finishing|done|failed|idle,
#     "job": "<condition> <seed>", "detail": "...", "last_update": ...,
#     "heartbeat": ... }
#
# Heartbeat file ~/heartbeat.ts  (unix seconds, refreshed every 30s)
#
# Usage (after the machine has been staged with setup_machine.sh --stage):
#   echo "general 202"   >> ~/job_queue.txt     # queue a job (any time)
#   nohup bash ~/vlm-spatial-reasoning/cloud_setup/job_supervisor.sh \
#       > ~/supervisor.out 2>&1 &               # start the daemon
#
# Each job runs: training -> (auto) consistency eval -> (auto) zip into
# ~/seed_variance_<condition>_<seed>.zip. A failed job is retried once.
# ============================================================================
set -uo pipefail

REPO="$HOME/vlm-spatial-reasoning"
VENV="$HOME/vlm-venv"
QUEUE="$HOME/job_queue.txt"
STATE="$HOME/job_state.json"
HBT="$HOME/heartbeat.ts"
SLOG="$HOME/supervisor.log"

log() { echo "[$(date '+%F %T')] $*" >> "$SLOG"; }

write_state() {  # $1=status $2=job $3=detail
  python3 - "$1" "$2" "$3" <<'PY'
import json, os, sys, time
p = os.path.expanduser("~/job_state.json")
d = {}
if os.path.exists(p):
    try:
        d = json.load(open(p))
    except Exception:
        d = {}
d["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
d["status"] = sys.argv[1]
d["job"] = sys.argv[2]
d["detail"] = sys.argv[3]
json.dump(d, open(p, "w"), indent=2)
PY
}

# ---------------------------------------------------------------- heartbeat
heartbeat_loop() {
  while true; do
    date +%s > "$HBT"
    python3 - <<'PY'
import json, os, time
p = os.path.expanduser("~/job_state.json")
d = {}
if os.path.exists(p):
    try:
        d = json.load(open(p))
    except Exception:
        d = {}
d["heartbeat"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
json.dump(d, open(p, "w"), indent=2)
PY
    sleep 30
  done
}

# ------------------------------------------------------------------ one job
run_one() {  # $1=condition $2=seed
  local condition="$1" seed="$2"
  local out="$REPO/results/seed_variance/$condition/$seed"
  local runlog="$REPO/run_${condition}_${seed}.log"
  local attempt rcc

  write_state "running" "$condition $seed" "attempt 1"
  for attempt in 1 2; do
    rm -rf "$out"
    mkdir -p "$out"
    log "START $condition $seed attempt $attempt"
    ( cd "$REPO" && "$VENV/bin/python" scripts/run_seed_variance.py \
        --condition "$condition" --seed "$seed" > "$runlog" 2>&1 )
    rcc=$?
    if [ $rcc -eq 0 ] && [ -f "$out/metrics.json" ]; then
      write_state "finishing" "$condition $seed" "training done; consistency + zip"
      log "FINISH $condition $seed (consistency + zip)"
      ( cd "$REPO" && "$VENV/bin/python" scripts/eval_consistency_flips.py \
          --condition seed_checkpoint --lora-path "$out/checkpoint" \
          --orig-csv "$out/predictions.csv" --out-csv "$out/consistency_flips.csv" \
          >> "$runlog" 2>&1 )
      ( cd "$REPO" && zip -qr "$HOME/seed_variance_${condition}_${seed}.zip" \
          "results/seed_variance/$condition/$seed" )
      write_state "done" "$condition $seed" \
        "metrics.json + consistency_flips.csv + seed_variance_${condition}_${seed}.zip"
      log "DONE $condition $seed"
      return 0
    fi
    log "FAILED attempt $attempt (exit=$rcc) $condition $seed — see $runlog"
    write_state "failed" "$condition $seed" "attempt $attempt exit=$rcc"
  done
  return 1
}

# -------------------------------------------------------------------- main
main() {
  [ -d "$REPO" ] || { echo "REPO missing: $REPO (run setup_machine.sh --stage first)"; exit 1; }
  [ -x "$VENV/bin/python" ] || { echo "VENV missing: $VENV"; exit 1; }
  touch "$QUEUE"
  log "supervisor started (queue=$QUEUE)"
  write_state "idle" "" "supervisor started"
  heartbeat_loop &
  local HB_PID=$!
  trap 'kill $HB_PID 2>/dev/null' EXIT

  while true; do
    local line cond seed
    line="$(head -n 1 "$QUEUE" 2>/dev/null)"
    if [ -z "$line" ]; then
      write_state "idle" "" "queue empty"
      sleep 60
      continue
    fi
    tail -n +2 "$QUEUE" > "$QUEUE.tmp" 2>/dev/null && mv "$QUEUE.tmp" "$QUEUE"
    read -r cond seed <<< "$line"
    log "DEQUEUE $cond $seed"
    if ! run_one "$cond" "$seed"; then
      log "JOB FAILED after retries: $cond $seed"
    fi
  done
}

main "$@"
