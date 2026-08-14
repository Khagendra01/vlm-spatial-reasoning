# EquiOrient — Architecture Criticism Check (Gate 3b, Step 4)

**Question:** would freezing essentially the entire VLM + attaching a
standalone classifier make reviewers say *"this is a new classifier on top
of a pretrained vision encoder, not really training a VLM's internal
spatial representation"?*

**Answer: the criticism is PARTIALLY VALID under a frozen-backbone
implementation — and the fix is to make the backbone trainable + z
answer-path-integrated, which Qwen3's architecture supports cleanly.**

---

## 1. When the criticism is valid (must avoid)

If the pilot froze the ENTIRE Qwen3 model and trained only
`PairEncoder + W_rel` on pooled **merged** `image_embeds`, then:

- The vision features are fixed; training only changes a small head.
- A reviewer's "classifier on a pretrained encoder" attack would hold:
  the model's *internal spatial representation* never moves; only the
  readout does.
- The equivariance loss would still shape *z*, but z would be a function of
  frozen features — the *representation* would not be what's being trained.

**This configuration is NOT EquiOrient's claim** and must not be the
primary result.

## 2. When the criticism is NOT valid (the design that defends it)

The mutated novelty target (Amendment A) requires:
**"z is on the actual answer path"** and the equivariance loss acting on
the same z. It does NOT require freezing the backbone. Three levers, all
available in Qwen3-VL:

### Lever A — train the vision tower (LoRA on fused `qkv`)

Qwen3-VL's vision blocks are trainable; the deepstack features `z` pools
from pass through LoRA adapters (target `self.qkv` + MLP). Then:

```
L_answer -> W_rel^T -> z -> PairEncoder -> V_a,V_b (deepstack) -> Qwen3 vision LoRA
L_eq     -> z(x), z(Tx) -> same PairEncoder -> same deepstack features
```

The equivariance objective now pushes gradient into **Qwen3's own vision
representation** — the internal spatial representation IS what changes.
This is "training the VLM's spatial representation", not a frozen-encoder
classifier.

### Lever B — z on the answer path, not a side branch

The relation token is **forced from W_rel·z** during generation (masked
decode). z is the ONLY route to the relation answer. This is stronger than
"an auxiliary head a model can ignore": the LM literally cannot answer the
relation except through z. (Same as Gate 3 — unchanged.)

### Lever C — the equivariance loss is on the representation, not the answer

`L_eq = || rho(T) z(x) - z(Tx) ||²` shapes z's *geometry*, which the
answer head merely reads. A classifier-only design would have no such
objective — its presence is direct evidence that the *representation* is
the object of training, not the head.

## 3. The honest residual risk (must be stated in the paper)

Even with Levers A-C, a hostile reviewer can still say:

> "The relation decision is a linear head on a pooled vector; the VLM's
> text decoder is only a scaffold."

Answer (paper text): the claim is about **whether answer-relevant spatial
state can be made to obey a transformation algebra and whether that
structure generalizes compositionally** — not about which component of the
pipeline does the final argmax. The forced relation slot means the VLM's
answer *is* `f(z)`; the equivariance constraint demonstrably changes the
representation that feeds it (causal ablation + latent error metrics).
Qwen3's LoRA-trained vision tower ensures the "internal representation"
clause is literal: the backbone adapts.

**Do NOT adopt frozen-backbone + head-only as the primary arm.**

## 4. Decision

**MUTATE_ARCHITECTURE (minor, within existing design):** the Gate-3
`PairEncoder([pool(V)_a; pool(V)_b]) -> z -> W_rel z -> relation` remains
the skeleton, with one strengthening amendment:

1. **Pool from Qwen3 deepstack features** (spatial layout intact) instead
   of merged image_embeds;
2. **LoRA-train the Qwen3 vision tower** (fused `qkv` + MLP) so
   gradients from BOTH objectives reach the backbone representation —
   this is the answer to the "external classifier" criticism;
3. forced relation decoding + mandatory causal ablation unchanged.

This is a **pre-result protocol amendment** (no results seen), consistent
with the orchestrator's Step 4: *"preferred design is one where z is
genuinely integrated into the multimodal answer pathway while still
preventing an LM bypass."*
