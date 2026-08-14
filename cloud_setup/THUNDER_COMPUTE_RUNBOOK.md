# Thunder Compute startup runbook (one machine at a time)

> Distilled from the operational session (`session-ses_008a.md`, 2026-08-13) and
> the committed provisioner (`cloud_setup/setup_machine.sh`,
> `cloud_setup/job_supervisor.sh`). This is the exact procedure used for the
> 4×A6000 seed-variance campaign — follow it machine by machine.
>
> **Current status (from `session-ses_006f.md`):** GPU compute is **frozen**.
> Steps 1–7 of the Paper-2 post-compute pipeline are complete and audited. Any
> future GPU start requires an **explicit unlock** (only pending item: optional
> 1-GPU-hr VisualFLIP validation if the dataset releases, weekly re-check).

---

## 0. Pre-flight (free, do once)

1. **Push the tooling branch.** All cloud scripts must be committed on the
   working branch (`paper-draft-v1` used in the campaign):
   - `cloud_setup/setup_machine.sh` — one-command provisioner
   - `cloud_setup/job_supervisor.sh` — on-machine job daemon (queue + heartbeat
     + auto `--finish` + one retry)
2. **HF token.** `HF_TOKEN=hf_...` is required on every machine. It lives in
   chat history → treat as **exposed and rotate after runs**. Never commit it;
   nothing writes it to disk on the machines (session env only).
3. **SSH key saved** on the Thunder Compute org (key name used:
   `gsd-desktop`).

Machine spec used for every instance:
`gpu_type: a6000`, `template: base`, `num_gpus: 1`, `disk_size_gb: 200`,
`ssh_key_name: gsd-desktop`.

---

## 1. Create an instance

Via the MCP tools (one call per machine) — or manually with the `tnr` CLI:

```bash
tnr create --gpu a6000 --num-gpus 1 --disk 200
tnr connect 0
```

MCP `create_instance` returns:
- `instance_id` — the **integer** (0, 1, 2, 3). Use it for all subsequent tool
  calls (`run_command`, `start_command`, `get_command_output`…).
- `uuid` — the alphanumeric name (e.g. `sl8wcy6r`). Used for **snapshots**
  (see step 7 — snapshot tool takes the UUID, not the integer).

Wait ~30 s, then verify with `list_instances` → status must be `RUNNING`.
(Transient `instance_not_found` during platform restores is normal — retry.)

**Do this one machine at a time.** Do not launch multiple concurrent jobs on a
machine you have not verified — duplicate concurrent staging jobs raced and
broke the venv in the campaign (`No module named pip`), requiring a full wipe.

---

## 2. Provision + stage (`--stage`, ~10–25 min)

One `start_command` per machine (runs detached; poll with
`get_command_output`):

```bash
export HF_TOKEN=hf_YOUR_TOKEN_HERE; cd ~ && git clone --quiet --depth 1 --filter=blob:none --sparse --branch paper-draft-v1 https://github.com/Khagendra01/vlm-spatial-reasoning.git vlm-spatial-reasoning 2>&1; cd ~/vlm-spatial-reasoning && git sparse-checkout set src scripts configs data cloud_setup docs requirements.txt .gitignore README.md SEED_VARIANCE_JOB.md; echo "CLONE_OK"; cd ~ && bash ~/vlm-spatial-reasoning/cloud_setup/setup_machine.sh --stage 2>&1 | tail -20
```

`--stage` runs (idempotent — re-running resumes, never redoes completed work):
1. `provision_system` — apt: git, python3-venv, zip
2. `provision_venv` — venv, pip, `torch==2.12.1+cu130` + `torchvision==0.27.1+cu130`
   (cu130 index only — PyPI has no `+cu130` wheels), then `requirements.txt`
3. `provision_repo` — sparse clone (cone keeps the ~1.2 GB tree to a few MB;
   full clone times out)
4. `provision_hf` — download Qwen2-VL-7B-Instruct + SmolVLM2-2.2B-Instruct
   (~24 GB) + preload `cambridgeltl/vsr_random` test split
5. `provision_images` — `scripts/pre_download_all.py` fills `data/image_cache`
6. `smoke_test` — 60-step training run (scratch seed 9999, ~1 min of training)
   + 2B model load check

**Wait for `STAGE COMPLETE` in the log** before doing anything else:
`tail -3 ~/vlm-spatial-reasoning/cloud_setup/setup.log`

---

## 3. Launch a job

Two supported flows:

### A. Direct (`--run`, machine 0 style)

```bash
export HF_TOKEN=hf_YOUR_TOKEN_HERE
bash setup_machine.sh --run general 101
```

- Trains in background (nohup); log at `~/run_<condition>_<seed>.log`.
- Refuses to rerun if `results/seed_variance/<c>/<s>/metrics.json` exists
  (safe resumes: no `metrics.json` = died mid-run = rerun).
- After the run finishes: `bash setup_machine.sh --finish <condition> <seed>`
  → consistency eval + zip to `~/seed_variance_<c>_<s>.zip`.

### B. Queued + supervised (machines 1–3 style, recommended)

The supervisor owns a queue file, keeps disk-truthful state, auto-runs
`--finish` (consistency + zip) per job, and **retries once on failure**:

```bash
echo "hardneg 101" >> ~/job_queue.txt
cd ~ && nohup bash ~/vlm-spatial-reasoning/cloud_setup/job_supervisor.sh > ~/supervisor.out 2>&1 & echo "SUPERVISOR_PID=$!"; sleep 3; cat ~/job_state.json
```

Supervisor artifacts:
- `~/job_queue.txt` — one `"<condition> <seed>"` per line; append anytime
- `~/job_state.json` — `{status: staged|running|finishing|done|failed|idle,
  job, detail, last_update, heartbeat}` refreshed every 30 s on persistent disk
- `~/heartbeat.ts` — unix-seconds heartbeat
- `~/supervisor.log` / `~/supervisor.out` — daemon logs
- Zip output: `~/seed_variance_<condition>_<seed>.zip`

Background jobs are NOT captured by snapshots and die with the instance — the
supervisor's disk state is the truth even when every MCP job handle is lost.

Campaign job assignments:

| Machine | Job |
|---|---|
| 0 | `general 101` (then `general 303`) |
| 1 | `general 202` |
| 2 | `hardneg 101` |
| 3 | `hardneg 202` |

(Bonus: `targeted 101/202`. Machines 4–6 belonged to the other agent — don't
touch them.)

---

## 4. Monitor

Per machine, poll:

```bash
cat ~/job_state.json 2>/dev/null | head -6
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
tail -2 ~/vlm-spatial-reasoning/run_<c>_<s>.log 2>/dev/null | tr '\r' '\n' | tail -2
```

Rules:
- **Heartbeat stale > 3 min → investigate** (platform restores can kill
  jobs; disk state tells you what happened).
- `status: failed` + `detail: attempt 1 exit=1` → supervisor retry is
  running; if attempt 2 fails, read the run log tail for the cause
  (campaign example: `ArrowInvalid: Could not convert '171_hn'` = manifest
  data bug, fixed in `data/manifests/hardneg_train.jsonl`).
- GPU at 0 % early = model loading; training ramp follows.

---

## 5. Collect results

```bash
tnr scp 0:$HOME/seed_variance_general_101.zip .
tnr scp 1:$HOME/seed_variance_general_202.zip .
tnr scp 2:$HOME/seed_variance_hardneg_101.zip .
tnr scp 3:$HOME/seed_variance_hardneg_202.zip .
```

(Or MCP `get_scp_command`; or on-machine `bash setup_machine.sh --collect` →
single `seed_variance_all.zip`.) Unzip locally, then aggregate/commit.

---

## 6. Snapshot & teardown

- **Snapshot before teardown** — `create_snapshot` takes the **UUID**, not the
  integer id (integer id → `instance_not_found`; verified in session):
  `instance_id: "jx9x5w8c"` (the uuid), `name: a6000-seed-provisioned`.
- **Delete instances when done** (`delete_instance`) — billing stops. The
  campaign teardown was completed 2026-08-13; no instances should be running
  without a purpose.

---

## 7. Failure playbook

| Symptom | Fix |
|---|---|
| `pip install torch` fails | Re-run staging (idempotent); check the cu130 wheel index pin once, re-push |
| HF download stalls | Re-run the script — resumes |
| Image cache incomplete | Re-run `scripts/pre_download_all.py` (retries only missing) |
| Venv broken / `No module named pip` (duplicate provisioning race) | `pkill -f setup_machine; pkill -f "pip install"; rm -rf ~/vlm-venv ~/run_*.log ~/job_state.json ~/heartbeat.ts ~/supervisor.out`, then re-run ONE clean staging job |
| Job dies mid-run | `metrics.json` absent → rerun `--run` (safe resume) |
| `instance_not_found` | Platform restore in progress — wait and retry |

---

## 8. Gotchas (all encoded in the scripts — read before touching anything)

1. **Never install flash-attn.** Fails on CUDA 13; every recipe uses
   `_attn_implementation="eager"` by design.
2. **transformers 5.14.1 ignores `max_pixels`.** SITE evaluator pre-resizes to
   ≤392 px long side as a constant protocol parameter; do not "fix" it.
3. **datasets v5 split is `"validation"`, not `"dev"`.** Seed runner only uses
   `split="test"` — no action, just don't copy old snippets.
4. **Runner silently skips images missing from `data/image_cache`** — never
   skip `provision_images` / `pre_download_all.py`.
5. **HF token hygiene:** token appeared in chat → rotate after use; machines
   keep it in session env only.
6. **K8s containers can't reboot** (`sudo reboot` doesn't work, no systemd, no
   MCP restart tool) — recover via snapshot restore / recreate from snapshot
   rather than reboot attempts.
7. **Hardware metrics vary by GPU config** — compare workloads with
   application-level metrics (iterations/sec), not temperature/wattage.
