# VLM Spatial Reasoning — Techniques & Conventions

Empirically-discovered conventions and reusable techniques from this project
(grounding, region pooling, resolution handling, video sampling). Each
technique links to the script that implements it.

---

## 1. Qwen2-VL grounding: bounding-box coordinate convention

**Problem.** Qwen2-VL (native grounding via `<|box_start|>` tokens) outputs
box coordinates in a normalized **per-axis [0, 1000] space**, not original
pixels and not longest-side-normalized:

```
x_norm = x_px * 1000 / width
y_norm = y_px * 1000 / height
```

**How it was discovered (do not trust docs — verify empirically).** A
single-image diagnostic on a known 500×333 image asked the model to locate
objects; the output box was `(1,0),(995,996)`. Longest-side-1000 scaling
would have produced `y` ≤ 667; per-axis scaling produces `y` ≈ 333 px when
rescaled back — matching the image height, proving per-axis [0,1000].

**Rescale to pixels:**

```python
def rescale_1000(box, w, h):
    x1, y1, x2, y2 = box
    return [x1 * w / 1000.0, y1 * h / 1000.0, x2 * w / 1000.0, y2 * h / 1000.0]
```

**Validation:** clamp boxes to image bounds; flag boxes with zero area;
sanity-check area fraction (median ≈ 0.32 of image). Save raw 1000-space
boxes alongside rescaled ones so the convention can be re-verified offline.

Implementation: `scripts/ground_objects.py` (`rescale_1000`).

---

## 2. Reliable grounding: one box per query

**Problem.** Asking Qwen2-VL for *two* boxes in one prompt ("return a box
for the cat and a box for the dog") fails ~50% of the time (single box,
refusals, malformed output). **One box per query** succeeds ~95%.

**Pattern:**

```
Locate the {object} in this image. Return exactly one bounding box in the
format <|box_start|>(x1,y1),(x2,y2)<|box_end|>.
```

Run two batched passes (all subjects, then all references); regex-parse the
box tokens from decoded output (`skip_special_tokens=False`); treat missing
boxes as `None` (typically genuinely absent objects). Batch size 4 keeps the
long prompt sequences memory-safe.

Implementation: `scripts/ground_objects.py`.

---

## 3. Patch-grid region pooling (object-grounded features)

Map a grounding box (original pixels) onto the ViT/merger patch grid, then
pool the patches whose **centers** fall inside the box:

```python
# resized image is grid_h*ps x grid_w*ps (ps=14 ViT, 28 merger);
# scale box by (grid*ps / orig_w, grid*ps / orig_h)
cx = (arange(gw) + 0.5) * ps   # patch center x positions
cy = (arange(gh) + 0.5) * ps
mj = (cx >= x1) & (cx < x2);  mi = (cy >= y1) & (cy < y2)
idx = where(outer(mi, mj))      # row-major: i*gw + j
emb_region = emb[idx].mean(0)   # mean-pooled region embedding
```

- Grid dims come from the processor's `image_grid_thw` per image.
- **Fallback**: if no patch center lands in the box (tiny/degenerate box),
  take the nearest patch to the box center.
- Region features used downstream as `[subj, ref, subj−ref, subj·ref]`.

Implementations: `scripts/run_grounded_probe.py`, `scripts/two_stage_reasoning.py`
(`pool_region`).

---

## 4. Qwen2-VL input resolution: the `max_pixels` regression and the 392 px cap

**Problem.** This transformers build (5.14.1) **ignores `max_pixels`**
(verified on both `processor(images=..., max_pixels=...)` and
`apply_chat_template(processor_kwargs=...)`): a 2000×1335 image yields a
96×142 patch grid = 13,632 vision tokens (2.7 Mpx — above the nominal
1,003,520 budget). Consequence: O(n²) vision attention over 13k+ patches ≈
5 s/batch — the dominant cost on large SITE images (VSR was fast only
because COCO images are small).

**Fix:** pre-resize images to ≤ 392 px long side in the prep step, enforcing
the 28×28 patch grid budget that `max_pixels` is meant to provide. This is a
**constant protocol parameter** (uniform across examples/subsets), recorded
in run metadata — documented, not silent.

**When to re-check:** if you upgrade transformers, verify
`max_pixels` works again and decide whether to lift the cap for full
fidelity (see `results/site/zeroshot_image_report.md` caveats).

Implementation: `scripts/eval_site_zeroshot.py` (`prep_batch`).

---

## 5. Video input: uniform frame sampling with pyav

The transformers video path defaulted to torchvision/torchcodec (both
broken/absent here), so videos are decoded manually:

- Uniformly sample **16 frames** across the clip via `av` seek+decode.
- Resize frames to ≤ 128 px long side (16 frames × ≤81 patches keeps
  attention within memory; 224 px OOMs on real SITE videos).
- Pass the stacked frames as an np array in content:
  `{"type": "video", "video": frames_array}` — the processor accepts arrays
  and emits `pixel_values_videos` + `video_grid_thw`.
- SITE video evaluation is currently **deferred** (secondary extension).

Implementation: `scripts/eval_site_zeroshot.py` (`load_video_frames`).

---

## 6. OOM-safe batched generation

- **Batch sizing**: single-image examples batch 4–8; multi-image batch 1
  (long sequences OOM at larger batches).
- **Progressive scale retry**: on CUDA OOM, retry the batch with images
  downscaled 336 → 224 → 160 → 96 px; skip only if all scales fail.
- **No per-batch `torch.cuda.empty_cache()`**: it forces a GPU sync
  (~0.5–2 s/example overhead at batch 1); call only on OOM.
- **`padding=True, truncation=True` is required** in `apply_chat_template`
  for batches >1; without it the tokenizer fails and batches are silently
  recorded with `prediction=None`.
- **Attention backend**: `_attn_implementation="sdpa"` (torch built-in flash
  on Ampere) is ~2.5× faster than eager on long sequences, no install.

Implementation: `scripts/eval_site_zeroshot.py`.

---

## 7. Long-running job hygiene

- Launch with `setsid nohup env ... python3 -u script > log 2>&1 < /dev/null &`
  so the job survives the controlling session.
- Always use a **fresh log file per launch** (two processes appending to one
  log produces unreadable interleaving).
- Keep GPU work in the **main thread**; only CPU prep (PIL/tokenizer) in
  worker threads (CUDA from executor threads caused stalls).
- Save results **incrementally** (every N examples) and implement **resume**
  (skip done IDs, reload prior rows) so restarts never lose work.

---

## Cross-references

- `results/site/site_eval_run_notes.md` — full issue-by-issue engineering log
- `results/grounded_probe_report.md` — object-grounded probe results using
  techniques 1–3
- `results/site/orientation_subset_definition.md` — heuristic orientation
  subset definition
