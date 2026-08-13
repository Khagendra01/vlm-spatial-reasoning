# Cloud seed-variance runbook (Thunder Compute, 4× A6000)

Everything is automated behind ONE command per machine. Your only manual
steps: create the instance, `tnr connect`, paste one line, report back.

## The plan (money-safe: learn once, then parallelize)

```
PHASE 0  (done, free)   provisioner script + complete image downloader +
                        smoke-test flag (--max-steps) committed & pushed
PHASE 1  (~$0.30)       MACHINE 0: provision + 60-step smoke test + FULL
                        run of general/101. Learnings: real step time, VRAM,
                        wall time -> we validate before spending on 3 more.
PHASE 2  (parallel)     MACHINES 1-3: same script -> general/202,
                        hardneg/101, hardneg/202 (launch while m0 finishes).
PHASE 3  (free)         transfer the 4 zips back (tnr scp); I aggregate,
                        update the paper additively, commit.
```

Budget: worst case 4 machines × ~3h × $0.35 ≈ **$4.20**; realistically
~$2.50–3.00. Phase 1 alone ≈ **$0.20–0.35** and that is the entire risk
budget — if the recipe fails (torch/peft version drift, VRAM, HF download),
it fails there, cheaply, and we fix once before touching the other machines.

## Timing (honest estimates; staging confirms them)

| Step (per machine) | Time |
|---|---|
| apt + venv + pip install (torch cu130, ~4 GB) | 10–15 min |
| Qwen2-VL-7B-Instruct download (~16 GB) | 10–20 min (network-bound) |
| vsr_random dataset + image cache (~2,300 files) | 8–15 min |
| 60-step smoke test (incl. model load) | 8–12 min |
| **Full run** general/hardneg 101/202 (2 epochs) | ~60–90 min |
| Consistency eval (660 flipped statements) | ~15–25 min |

Wall time, 4 machines in parallel: **~2.5–3 h** total from first launch.

## What I can and cannot do from here

- I CAN: check `tnr status`, run `tnr scp` transfers, verify logs, aggregate.
- I CANNOT: type inside your interactive `tnr connect` shell. So each
  machine gets one copy-paste command; the script logs everything
  (`setup.log`, `run_*.log`) and resumes instead of redoing work.

## Exact sequence

### Machine 0 (staging + first real job)

```bash
tnr create --gpu a6000 --num-gpus 1 --disk 200     # create (200GB disk: model+venv+logs)
tnr connect 0
```
Then, inside the session, paste:

```bash
export HF_TOKEN=hf_YOUR_TOKEN_HERE        # never commit this
curl -fsSL https://raw.githubusercontent.com/Khagendra01/vlm-spatial-reasoning/paper-draft-v1/cloud_setup/setup_machine.sh -o setup_machine.sh
bash setup_machine.sh --stage
```

Wait for `STAGE COMPLETE`, then start the real job (same session):

```bash
bash setup_machine.sh --run general 101
```

Then **tell me** (paste the `setup.log` tail + `nvidia-smi`). I confirm the
smoke numbers and timing, and we go parallel.

### Machines 1–3 (after Phase 1 validation)

Create 3 more instances (`tnr create --gpu a6000 --num-gpus 1 --disk 200`
×3), connect to each, paste the same two lines with:

| machine | commands |
|---|---|
| 1 | `bash setup_machine.sh --run general 202` |
| 2 | `bash setup_machine.sh --run hardneg 101` |
| 3 | `bash setup_machine.sh --run hardneg 202` |

Each run is backgrounded (nohup) — you can disconnect and reconnect;
`bash setup_machine.sh --finish <condition> <seed>` runs the consistency
eval + zips when `metrics.json` appears. Or just re-connect later and run
`--finish` (the script refuses to rerun finished jobs).

### Collect

```bash
tnr scp 0:$HOME/seed_variance_general_101.zip .
tnr scp 1:$HOME/seed_variance_general_202.zip .
tnr scp 2:$HOME/seed_variance_hardneg_101.zip .
tnr scp 3:$HOME/seed_variance_hardneg_202.zip .
```

(one per machine, or use `--collect` on each machine first to build a single
`seed_variance_all.zip`).

## Ready for 2B AND 7B

The provisioner downloads **both** base models, so the same machines can run
any canonical workload:

| Workload | Model | Command (in `$REPO`, using the venv) |
|---|---|---|
| Seed variance (reviewer P3) | 7B | `python scripts/run_seed_variance.py --condition general --seed 101` |
| 2B zero-shot baseline | 2B | `python scripts/run_baseline.py` (SmolVLM2 wrapper) |
| 2B structured prompt | 2B | `python scripts/run_structured_prompt.py` |
| 2B/7B LoRA eval | both | `python scripts/eval_lora.py --base-model ...` |

Both wrappers use the same modern API (`AutoProcessor` /
`AutoModelForImageTextToText`, bf16, eager attention), so ONE venv serves
both. The `--stage` smoke test now also loads the 2B model to prove the venv
works for both before you launch anything. (Historical note: the canonical 2B
runs happened on an old python3.10/conda environment; we deliberately run
both on the current pinned stack here. If SmolVLM2 ever fails to load on
transformers 5.14.1, the fallback is a second venv pinned to transformers
4.5x — staging will catch it before any real run.)

SITE evaluation is intentionally NOT part of this setup: it needs the ~130 GB
`data/site_media/` bundle and stays on the original GPU box.

## Gotchas learned the hard way (read before touching anything)

These are the problems we hit in earlier sessions; the provisioner and
recipes already encode the fixes, but knowing them saves debugging time:

1. **Never install flash-attn on these machines.** It fails to build on
   CUDA 13. Every recipe in this repo uses `_attn_implementation="eager"`
   by design — that is not an oversight.
2. **transformers 5.14.1 ignores `max_pixels`.** Verified empirically: a
   2000×1335 image yields a 96×142 patch grid (13,632 vision tokens). The
   SITE evaluator pre-resizes to ≤392 px long side as a constant protocol
   parameter. VSR COCO images are small, so VSR runs are unaffected — do not
   "fix" the resizing if you run SITE later.
3. **datasets v5 renamed the split:** it is `"validation"`, not `"dev"`.
   The seed runner only uses `split="test"`, so nothing to do — just don't
   copy old `dev`-based snippets.
4. **Qwen2-VL grounding boxes are per-axis [0, 1000], not pixels** (only
   relevant to the two-stage/probe scripts, not the seed runner).
5. **The runner silently skips images missing from `data/image_cache`**
   (train batches and eval statements both). That is why provisioning runs
   `pre_download_all.py` and checks counts BEFORE launching — never skip
   that step.
6. **HF token hygiene:** the token is in this chat's history, so treat it as
   exposed — rotate it on Hugging Face after these runs. On the machines it
   lives only in the session env var; nothing writes it to disk.

## Token safety

- `HF_TOKEN` lives only in the session environment; the provisioner reads it
  via `snapshot_download(token=...)`. Nothing writes it to disk or logs.
- It was shared in chat, so treat it as **potentially exposed**: rotate it
  on Hugging Face after the runs, and reuse it only for these 4 machines.
- If a machine is returned/deleted, the token dies with the session.

## Failure playbook

- `pip install torch` fails → staging catches it; we pin the cu130 wheel URL
  once and re-push (cost: ~15 min on machine 0 only).
- HF download stalls → re-run the script (idempotent, resumes).
- Image cache incomplete → `python scripts/pre_download_all.py` re-runs and
  retries only the missing files (the runner never silently skips: the
  provisioner verifies cache counts before launching).
- Job dies mid-run → `results/seed_variance/<c>/<s>/metrics.json` absent →
  re-run `--run` (refuses only if metrics.json exists, so resumes are safe).
- Everything is logged; paste any log tail to me and I debug from here.
