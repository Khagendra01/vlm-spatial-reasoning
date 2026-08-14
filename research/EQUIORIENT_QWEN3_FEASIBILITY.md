# EquiOrient — Gate 3b: Qwen3-VL-8B Representation Feasibility

**Date:** 2026-08-14 · **Status:** ANALYSIS (CPU/meta only — no GPU run)
**Scope:** Qwen3-specific compatibility check of the Gate-3 design, per
orchestrator Step 2. Does NOT reopen Gates 1-2 or the 6-arm/held-out design.

---

## 1. Exact model revision / commit

- **Model:** `Qwen/Qwen3-VL-8B-Instruct`
- **HF commit SHA:** `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` (last modified
  2025-10-15)
- **Architecture class:** `Qwen3VLForConditionalGeneration` (`model_type: qwen3_vl`)
- **Config (verified from config.json):**
  - vision: hidden_size **1152**, depth **27** layers, out_hidden_size **4096**
    (patch merger output), intermediate 4304, `gelu_pytorch_tanh`
  - text: hidden_size **4096**, 36 layers, intermediate 12288, `silu`
  - tie_word_embeddings: **False**
  - `deepstack_visual_indexes` + `deepstack_merger_list` present (deep-stack
    visual features, Qwen3-VL novelty) — **this is the key Qwen3 difference**

## 2. Required software versions

| Package | Required | Notes |
|---|---|---|
| transformers | **>= 4.57.0** (README: build from source / `pip install transformers==4.57.0`) | Local env has 4.56.2 — **UPGRADE REQUIRED** |
| torch | 2.x (bf16) | Local has 2.8.0+cu128, CUDA available |
| flash-attn | optional (sdpa fallback) | not required for pilot |
| qwen-vl-utils | recommended (image preprocessing) | can be replaced by manual processor calls |

Local check: `transformers 4.56.2` does **not** have `qwen3_vl` — confirmed
by `from transformers.models import qwen3_vl` → ImportError. Upgrade needed
before any Qwen3 code path runs.

## 3. Processor / image preprocessing contract

- `Qwen3VLProcessor` (from `transformers`), `preprocessor_config.json`
  present in repo.
- Images are resized to a **smart-resize** resolution determined by
  `min_pixels`/`max_pixels` (default 256²–1280²*28²), producing
  `pixel_values` + `image_grid_thw` per image.
- `image_grid_thw`: `(T, H_feat, W_feat)` feature-grid dims **before** merge,
  where `H_feat = h_patches // spatial_merge_size` etc. This is the contract
  the PairEncoder box-mapping uses (see §6).

## 4. Exact tensor produced by the vision stack (object-region source)

`model.visual(pixel_values, grid_thw=image_grid_thw)` returns
**`(image_embeds, deepstack_image_embeds)`**:

- **`image_embeds`** — after all 27 blocks + **patch merger**
  (`Qwen3VLVisionPatchMerger`, out dim **4096**), shape
  `(n_merged_tokens, 4096)` where `n_merged_tokens = prod(grid_thw) // spatial_merge_size²`
  (per image, split via `torch.split` on `grid_thw.prod(-1) // merge_size²`).
  These are the LM-bound embeddings (replacing `<image>` tokens).
- **`deepstack_image_embeds`** — per-block features from
  `deepstack_visual_indexes`, each passed through its own
  `deepstack_merger` (out dim 4096). **Qwen3-specific, richer than Qwen2's
  single-layer output** — these are the natural *mid-stream* feature source
  for `z(a,b)` (they sit before the text model, carry full spatial layout,
  and are not the final answer).

## 5. Tensor shape before/after visual merge / projector

```
pixel_values (B, 3, H_px, W_px)
  -> patch_embed (ViT, patch 28px, spatial_merge 2)     (n_patches, 1152)
  -> 27 vision blocks                                    (n_patches, 1152)
  -> Qwen3VLVisionPatchMerger (out 4096)                 (n_merged, 4096)   <- image_embeds
  -> deepstack mergers (per deepstack index)             (n_merged, 4096)   <- deepstack_image_embeds
  -> text-embedding assembly (image tokens)              (n_merged, 4096)
  -> Qwen3VLTextModel (36 layers, hidden 4096)           (seq, 4096)
  -> lm_head -> logits
```

**Key Qwen3 difference vs Qwen2-VL (NOT assumed — verified from source):**
Qwen2-VL used a single `merger` (2-layer MLP) over the full grid;
Qwen3-VL additionally exposes **deepstack features** at selected vision
layers (`deepstack_visual_indexes`). For EquiOrient, `z(a,b)` should pool
from a **deepstack feature map** (pre-merge, spatial layout intact) rather
than the merged `image_embeds`, so object boxes map cleanly onto grid cells.

## 6. How synthetic object boxes map onto the visual-token grid

- Generator produces canonical boxes `(cx, cy, size)` in the **320×320**
  canvas → these are the *scene* coordinates.
- Processor smart-resize maps the 320×320 scene to `(H_px, W_px)` with a
  known scale factor `s` (from `image_grid_thw` + patch size + merge):
  `box_px = box_scene * s`, then
  `grid_cell = floor(box_px / (28 * spatial_merge_size))` → feature-grid
  coordinates over `H_feat × W_feat` (matching `image_grid_thw[1:]`).
- **Deterministic mapping** (exact resize = nearest/`F.interpolate`, known
  `s`), no object detection needed — the generator owns ground truth.
- Pool region = the set of merged grid cells intersecting the box;
  guard against empty regions (boxes sized ≥ 2 cells; fallback = nearest cell).

## 7. Where region pooling for objects a and b occurs

Proposal (frozen): pool **deepstack feature** (per-image, before merge) at
the grid cells covered by each box:

```
V_a = mean_pool(deepstack_feat[grid cells of a])   # (4096,)  [or concat of top-k cells]
V_b = mean_pool(deepstack_feat[grid cells of b])   # (4096,)
```

Implementation point: a hook on `model.visual` output (or a custom forward
override in the training wrapper) capturing `deepstack_image_embeds` +
`grid_thw`; the PairEncoder consumes `[V_a; V_b]`. No modification of the
HF modeling file — a wrapper class, keeping Qwen3 code pristine.

## 8. Exact construction of z(a,b)

```
z(a,b) = PairEncoder([V_a ; V_b])                 # MLP 8192 -> 512 -> typed blocks
z = [z_h | z_v | z_d | z_orient]                  # 4 blocks of 128 each
```

- Typed blocks are *structural*: each block feeds only its axis head (§9).
- PairEncoder is small (2 layers) — trainable, shared across arms.
- `z` is **not** an auxiliary probe: it is the sole input to the relation
  head; the relation answer is produced from `z` (§9) and the equivariance
  loss acts on `z` itself (§12).

## 9. z feeds the forced relation head — confirmation

Yes. Architecture:

```
rel_logits = W_rel · z + b_rel        # W_rel: 4 relations x 512 (typed)
answer_token = argmax(rel_logits)     # FORCED decoding:
```

The prompt asks "is the relation left_of / right_of / above / below …?" and
the **relation slot in the generated sequence is filled from `rel_logits`**,
not from the LM's softmax over the full vocab. Implementation: generate with
the Qwen3 LM for the prefix (subject/object names), then overwrite the
relation token position with `rel_logits` (masked/constrained step). This is
identical in spirit to the Gate-3 design — Qwen3's text decoder still
produces the sentence scaffold, but the relation decision is exclusively
`f(z)`.

## 10. No LM relation-answer bypass — confirmation

- The relation token cannot be emitted by the LM head (it is overwritten/
  masked at decode time). The LM cannot answer the relation from its own
  hidden state.
- Residual risk (same as Gate 3): the LM could *leak* relation info into
  other tokens (e.g., wording). Acceptable and reportable; the answer is
  still scored on the forced relation slot.
- **Causal ablation is mandatory (unchanged):** corrupt/zero `z` at eval →
  relation accuracy must collapse. Also required by smoke tests (Step 3).

## 11. Gradient path L_answer -> z -> PairEncoder -> Qwen3 features

```
L_ans = CE(rel_logits, y)
  -> dL/dz      = W_rel^T * dCE/dlogits        (nonzero if W_rel active)
  -> dL/dPairEncoder_theta (nonzero)
  -> dL/dV_a, dL/dV_b  (through pooling, if pooling is differentiable —
     mean-pool IS; box→cell mapping is fixed/detached, geometry not learned)
  -> dL/ddeepstack_feat  (only if deepstack features are trainable)
```

**Qwen3-specific decision:** which Qwen3 params are trainable (§13)
determines whether the *feature producer* itself adapts. If vision tower is
LoRA-tuned (recommended), gradients flow into Qwen3's vision blocks through
the deepstack path — the representation genuinely moves. If the vision
tower is frozen, gradients stop at `V_a` (PairEncoder still trains, but the
*backbone features* do not adapt — weaker scientifically).

## 12. Gradient path L_eq -> z(x), z(Tx) -> same PairEncoder

```
L_eq = || rho(T) z(x, a, b) - z(T(x), a', b') ||^2
  -> dL/dz(x) and dL/dz(Tx) both nonzero
  -> same PairEncoder weights (shared) -> dL/dPairEncoder_theta nonzero
  -> if vision tower LoRA: dL/dQwen3_vision (through both branches)
```

`rho(T)` = predeclared block-diagonal from `src/equiorient/transforms.py`
(RHO_ACTION); receives only `(T, component)`, **never** the true relation
(unchanged from Gate 1; smoke-tested in Step 3).

## 13. Qwen3 parameters: frozen vs LoRA-trained (proposal)

| Params | Status | Reason |
|---|---|---|
| Vision tower (27 blocks) | **LoRA** (r=16, alpha=32, on q/k/v/o + MLP) | features must adapt; Qwen3 deepstack path benefits |
| Patch embed + pos embed | frozen | low-level, no benefit |
| Patch merger / deepstack mergers | **LoRA or trainable small** | they transform features z pools from |
| Text model (36 layers) | **LoRA** (r=16) | sentence scaffold generation |
| lm_head | frozen | relation slot forced; not needed |
| PairEncoder + relation head | **fully trainable** | the EquiOrient machinery |

Pilot does NOT use flash-attn; sdpa. bf16. gradient checkpointing on.

## 14. LoRA target modules (Qwen3 names, verified from source)

- Vision: `Qwen3VLVisionBlock` submodules — `qkv` (the class uses a fused
  `qkv` projection: `self.qkv = nn.Linear(...)` inside
  `Qwen3VLVisionAttention`) and MLP (`Qwen3VLVisionMLP`).
- Text: `Qwen3VLTextAttention` — `q_proj, k_proj, v_proj, o_proj`;
  `Qwen3VLTextMLP` — `gate_proj, up_proj, down_proj`.
- **Note (Qwen3 vs Qwen2 — NOT assumed):** Qwen2-VL vision used separate
  `qkv` per head class with `q_proj/k_proj/v_proj` names; Qwen3-VL vision
  attention uses a **fused `qkv`** linear — LoRA config must target `qkv`
  (or fall back to training only the text-side LoRA + PairEncoder, which
  also works and keeps vision frozen — a documented arm-level choice).
  Verified from `modeling_qwen3_vl.py` source (`self.qkv = nn.Linear`).

## 15. Estimated VRAM for one training arm (Qwen3-VL-8B, bf16, LoRA)

| Component | VRAM (est.) |
|---|---|
| Base weights (8B, bf16) | ~16 GB |
| LoRA adapters + PairEncoder + head + optimizer | ~2–3 GB |
| Activations (grad checkpointing, batch 8, 320px) | ~6–8 GB |
| **Total** | **~24–27 GB → fits single A6000 (48 GB); tight on 24 GB GPUs** |

Recommend A6000 (48 GB) for headroom; batch 8 with grad checkpointing.
If 24 GB only: batch 4 + `gradient_accumulation 2` keeps matched budget.

## 16. Six-arm matched parameter/optimization budget

| Arm | Trainable params | Same budget? |
|---|---|---|
| ordinary_sft_lora | LoRA (vision+text) + head | yes |
| augmentation_only | LoRA (vision+text) + head (data aug only) | yes |
| output_consistency | LoRA (vision+text) + head (+consistency loss) | yes |
| latent_invariance | LoRA (vision+text) + head (rho=I) | yes |
| equiorient | LoRA (vision+text) + head + PairEncoder | yes |
| wrong_geometry_equiorient | identical to equiorient, wrong rho only | **yes — only the action matrix differs** |

- Same optimizer (AdamW 1e-4), epochs 2, batch 8, same scenes, same
  transforms (H/V seen; V∘H never), same max examples/epoch (2048).
- **Only structural difference:** EquiOrient arms add the tiny PairEncoder
  (~1–2M params) + equivariance loss term; wrong-geometry arm differs ONLY
  in the rho matrix (zero added params). The PairEncoder param delta is
  reported explicitly (protocol: "unavoidable method-specific tiny
  structural parameters must be explicitly reported").

---

## Summary of Qwen3-specific findings (not assumed, source-verified)

1. transformers **4.57.0 required** (local 4.56.2 — must upgrade).
2. Vision stack emits **deepstack features** (Qwen3-specific) — better
   region-pooling source than Qwen2's merged output; spatial layout intact.
3. Vision attention uses **fused `qkv`** (Qwen2 used separate q/k/v) —
   LoRA target names differ; must target `qkv` or accept frozen-vision arm.
4. Box→grid mapping is deterministic via `image_grid_thw` + patch/merge
   sizes (28 px, merge 2); no detector needed (synthetic ground truth).
5. `z(a,b)` typed 4-block construction unchanged; forced relation decoding
   unchanged; causal ablation mandatory.
6. VRAM ~24–27 GB → A6000 48 GB single-GPU pilot feasible.

**No blockers found for the Qwen3 answer-path design.**
