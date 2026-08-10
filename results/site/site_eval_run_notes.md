# SITE Evaluation — Engineering Run Notes

Status: covers the SITE external-validation pipeline (media acquisition →
preregistration → 7B zero-shot image evaluation), the issues encountered,
root causes, and the fixes applied. Committed alongside the results so the
paper trail is reproducible.

---

## 1. Media acquisition: SITE stores all media inside 15 zips (~130 GB)

The official release (`franky-veteran/SITE-Bench`) exposes only two JSON
files (metadata) plus 15 `data_chunked_*.zip` files. There are **no per-file
URLs**; every image/video lives inside a zip. Media root convention:
`data/<source_dataset>/...`.

### Issue 1.1 — single-stream download is ~2 MB/s
A single `curl` of a zip measured ~2 MB/s. At that rate 130 GB ≈ 18 h.

**Fix path explored:** parallel range requests.
- 8 connections ≈ 8 MB/s; 32 ≈ 38 MB/s; 64 ≈ 43 MB/s (per-IP ceiling).
- 43 MB/s made full-zip downloads impractical (~50 min just for the bytes we
  need, before extraction).

### Issue 1.2 — multi-range requests are rejected (HTTP 416)
Attempting `curl -r "a-b,c-d,..."` (multipart/byteranges) returns **416 Range
Not Satisfiable** from the xet-bridge CDN: it only serves single ranges.
This killed the "one request per zip" idea.

### Issue 1.3 — ZIP64 parsing traps
The zips are ZIP64. Pitfalls found:
- EOCD `cd_offset` is the sentinel `0xFFFFFFFF`; real values live in the
  ZIP64 EOCD record (`0x06064b50`), whose offset is in the locator
  (`0x07064b50`) — and that offset is **absolute**, not relative to the
  downloaded tail. Correct approach: the ZIP64 EOCD record ends exactly at
  the locator; parse it at `locator_pos - 56`.
- The central directory sits at the **start** of the file (~4.8 GB in), not
  at the end. The 8 MB tail contains only EOCD + locator. Fetch the CD
  region separately: `curl -r "<cd_offset>-<cd_offset+cd_size-1>"`.

### Issue 1.4 — needed-file list formatting bug
`needed_media.txt` was written via `json.dump(list, indent=0)` → lines like
`"data/...jpg",`. Every path lookup failed (0 hits) until the file was
rewritten as plain newline-separated paths. Fix: regenerate from the frozen
protocol example IDs, `strip('",[]')` per line.

### Issue 1.5 — HTTP 429 rate limiting (the big one)
After ~dozens of parallel range requests, HF began returning **429
rate-limit pages** (191-byte HTML). The range fetcher treated those pages as
file bytes → decompress failures ("invalid block type") everywhere.

**Real fix (order of magnitude):**
1. Add a Hugging Face read token (`~/.cache/huggingface/token`).
2. Install `hf_transfer` + `hf_xet`; use `hf_hub_download(..., repo_type="dataset")`
   with `HF_HUB_ENABLE_HF_TRANSFER=1`.
   - Trap: `hf_hub_download` defaults to `repo_type="model"` → "Repository
     Not Found" for datasets. Must pass `repo_type="dataset"`.
3. Result: **~144 MB/s** (vs 43 MB/s curl ceiling). All 8,086 needed files
   downloaded + extracted in **8.2 minutes** (zips deleted after extraction;
   disk budget respected).

---

## 2. Evaluation script: crashes, stalls, and slow paths

### Issue 2.1 — CUDA OOM on multi-image examples
Batch 8 with SITE's multi-image questions (up to ~9 images per example,
each up to 13,632 patches with the broken max_pixels, see 2.6) → attention
OOM (22–126 GB single allocations).

**Fixes:**
- Batch size: 8 → 1 for multi-image; 4 for single-image (batch 8 with
  padding OOMs on large images and enters an OOM-retry spiral).
- Progressive scale retry: on OOM, retry the batch with images downscaled
  (336 → 224 → 160 → 96 px); skip only if all scales fail.
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

### Issue 2.2 — `torch.cuda.empty_cache()` after every batch
Emptying the CUDA cache per batch forces a GPU sync each time; with batch-1
loops this added ~0.5–2 s per example of pure overhead. Removed from the hot
path (kept only in OOM handlers).

### Issue 2.3 — batch tokenizer failure without `padding=True`
Batch >1 with different prompt lengths requires
`padding=True, truncation=True` in `apply_chat_template`; without it, the
tokenizer raises "Unable to create tensor" and the whole batch is recorded
with `prediction=None` (silently!). This silently produced **1,171 invalid
rows** before detection (rows with empty predictions). Fix: re-add
padding/truncation; validated that rows are identical to the pre-padding
runs; cleaned the CSV (invalid rows re-evaluated).

### Issue 2.4 — incremental save bug on resume
The resume path skipped already-done IDs but did not load their rows into
the in-memory results list, so the next incremental save **overwrote** the
CSV with only new rows (lost the original 125 rows). Fix: load prior rows
into `results` at startup. (The 50 lost rows were re-evaluated; validation
showed the new ceiling yields identical predictions, so no scientific loss.)

### Issue 2.5 — max_new_tokens 128 → 16 (protocol-neutral efficiency change)
The task only needs an answer letter ("Give me the answer letter directly").
Before changing, **validated on the existing 125 outputs: the parsed answer
letter is identical within the first 16 generated tokens for 125/125**. The
change is a truncation ceiling only (same prompt, decoding, parser);
recorded in `run_metadata.json` with config hash
`28f4cc09887477af`.

### Issue 2.6 — `max_pixels` is ignored by this transformers build (the root speed bug)
`Qwen2VLProcessor` in transformers 5.14.1 (this build) **ignores
`max_pixels` entirely** (tested both `apply_chat_template(processor_kwargs=...)`
and direct `processor(images=..., max_pixels=...)`): a 2000×1335 image
produces a **96×142 patch grid = 13,632 vision tokens** (2.7 Mpx, above the
nominal 1,003,520 budget). This silently made big SITE images ~17× more
expensive in the vision tower (O(n²) attention over 13k+ patches → ~5 s per
batch of 4; VSR was fast only because its COCO images are small).

**Fix:** pre-resize images to ≤ 392 px long side in the prep step (≈ the
28×28 patch grid that `max_pixels` is meant to enforce). Recorded as a
**constant protocol parameter** (uniform across examples and subsets; more
controlled than the status quo of arbitrary per-image native resolutions).
Result: ~0.19 s/example (≈ 10× speedup); single-image pass ~2 min,
multi-image ~30 min.

### Issue 2.7 — attention backend
Eager attention at 2,765-token sequences measured ~6.3 s / batch of 4
(~100× slower than theory). Switching to torch's built-in SDPA
(`_attn_implementation="sdpa"`, flash kernels available on sm_86) gave
~2.5×. Combined with the resolution cap, the total speedup is ~25×.
(flash-attn pip install was attempted; it hung on dependencies and was
killed — not needed after the cap.)

### Issue 2.8 — process management / shell flakiness
- Long-running jobs must be launched with
  `setsid nohup env ... python3 -u script > log 2>&1 < /dev/null &` so they
  survive the controlling shell/session being killed.
- The automation shell's timeout kills the whole process group; chaining
  `pkill && patch && setsid launch && sleep && grep` in one command is
  fragile — the launch often dies with the command. Launch and monitor in
  separate commands.
- Two fetcher instances once wrote to the same log simultaneously, producing
  confusing interleaved output; always use a fresh log file per launch.

### Issue 2.9 — CUDA/threads
Running `model.generate` inside a `ThreadPoolExecutor` worker (for a
prefetch queue) produced stalls (main thread futex-wait, GPU idle). Keep GPU
work in the main thread; do CPU-only prep (PIL, tokenizer) in the worker
thread (safe, and that's the CPU/GPU overlap we need).

---

## 3. Performance summary (RTX A6000, batch sizes as noted)

| Change | Effect |
|---|---|
| 64-way parallel curl ranges | 2 MB/s → 43 MB/s (ceiling) |
| token + hf_transfer (`repo_type="dataset"`) | → 144 MB/s; 8,086 files in 8.2 min |
| batch 8→1 (multi-image) + scale retry | eliminates OOM |
| remove per-batch `empty_cache()` | removes ~0.5–2 s/example sync overhead |
| `padding=True, truncation=True` | fixes silent None-prediction batches |
| eager → sdpa | ~2.5× on long sequences |
| 392 px image cap (constant protocol param) | ~10× on big images (root cause: ignored max_pixels) |
| max_new_tokens 128→16 (validated) | ~1.3× decode savings |

Final measured pace: **~0.19 s/example** single-image (batch 4, prefetch),
~2.5–3 s/example multi-image (batch 1).

## 4. Protocol integrity notes

- All efficiency changes are **protocol-neutral** (ceiling/back-end changes;
  prompt, model, decoding, parser, example ordering unchanged) and recorded
  in `results/site/run_metadata.json` under a config hash
  (`28f4cc09887477af`).
- Truncation equivalence was empirically validated (125/125 identical parses).
- Image resolution cap is a single constant documented as a protocol
  parameter (uniform across subsets; mitigates a transformers regression).
- Resume is safe: `--out <same.csv>` skips completed IDs and preserves rows.
- Images evaluated first, videos deferred (VSR is image-based; video is a
  secondary extension). The 7B VSR-LoRA condition is deferred until the
  zero-shot image results are reviewed.
