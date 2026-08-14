# EquiOrient — Representation-Feasibility Gate (Gate 3)

**Date:** 2026-08-14 · **Status:** PROPOSAL FOR REVIEW — no GPU used
**Gate question:** can `z(a,b)` be placed on the actual answer path such that
(a) gradients from the answer objective reach it, (b) the equivariance
objective reaches the *same* state, and (c) no path bypasses it?

This document answers the five questions from the execution guide:
where does z live, how does the answer head consume it, can answer gradients
reach it, can the equivariance objective reach the same state, does any path
bypass it.

---

## 0. Design target (from Amendment A + novelty gate)

```
vision features
      ↓
object-pair spatial state z(a,b)          <- typed: [z_h | z_v | z_d | z_orient]
      ↓
answer pathway (relation head)
      ↓
relation prediction / language answer
```

with the equivariance loss acting on that same `z`. `ρ(T)` predeclared,
geometry-derived, never conditioned on the true relation.

---

## 1. Where does z(a,b) live?

**Proposal: a lightweight pair-encoder head on top of the VLM's vision
features, feeding a constrained answer decoder.**

Concretely (SmolVLM2-2B or Qwen2-VL-7B as the single pilot backbone):

- The VLM's vision encoder produces per-patch features `V(x)` for input image `x`.
- Object locations `(a, b)` are KNOWN for synthetic scenes (generator emits
  ground-truth boxes) — grounding is exact, so no detector noise enters the
  pilot. (This is the point of Gate 2's synthetic scenes.)
- `z(a,b)` = a learned function of the visual features restricted to the
  object regions:

  ```
  z(a,b) = PairEncoder( [pool(V(x))_a ; pool(V(x))_b] )
  ```

  where `pool(V(x))_o` pools vision features inside object `o`'s box, and
  `PairEncoder` is an MLP (2-3 layers, dims ~256-512) that outputs a TYPED
  vector `z = [z_h | z_v | z_d | z_orient]`, each block a sub-vector.

  **Typing is structural, not just nominal**: the pair encoder's output
  head is partitioned into 4 blocks; each block is fed ONLY to the relation
  head component for its axis (see §2), and ρ(T) acts block-diagonally.

- **Where it lives in the computation graph**: `z` is produced after the
  vision encoder and before the answer head; it is the *only* input to the
  answer pathway for the relation. The frozen backbone provides `V(x)`; the
  pair encoder + answer head are trainable (LoRA on backbone optional).

Why this placement: it satisfies "answer-path" because the relation answer
is *computed from z*, not from a parallel branch.

---

## 2. How does the answer head consume it?

**Relation head (answer pathway):**

```
rel_logits = W_rel · z + b_rel        # W_rel : 4-relation × dim(z)
answer = argmax(rel_logits)           # left/right/above/below (Phase 1)
```

- The prompt to the VLM is fixed and declarative; the model must output the
  relation word. To guarantee the answer comes from `z` (no LM-side bypass),
  the answer token is produced by the relation head, and the language
  generation is FORCED: the relation slot in the response is filled from
  `rel_logits` (grammar-constrained decoding or a masked token position).
- The backbone still generates subject/object names etc., but the RELATION
  decision is exclusively `f(z)`.

**Invariance-controlled relations (parallel/perpendicular)**: optional Phase-1
extension — same head, fed from `z_orient` block only.

---

## 3. Can gradients from the answer objective reach z?

Yes — by construction:

```
L_ans = CE(rel_logits, y)
∂L_ans/∂z = W_relᵀ · ∂CE/∂rel_logits    # nonzero whenever W_rel active
```

- `z` is a direct function of trainable `PairEncoder` params and (via
  pooling) of the vision features; both receive nonzero gradients from
  `L_ans`.
- If the backbone is LoRA-tuned, gradients additionally flow through the
  vision encoder to the pair-encoder inputs — fine, not required.

---

## 4. Can the equivariance objective reach the same state?

Yes — the equivariance loss is a function of the SAME z computed on the
transformed image:

```
L_eq = || ρ(T) · z(x, a, b) − z(T(x), a', b') ||²      (block-diagonal ρ)
```

where `z(T(x), a', b')` is the pair encoder applied to the transformed
image with the *transformed* boxes `(a', b')` (known from the generator —
Gate 2's `Scene.transformed`).

- Both `z(x,...)` and `z(T(x),...)` pass through the SAME `PairEncoder`
  weights, so `∂L_eq/∂θ_pairEncoder ≠ 0`.
- **ρ never receives the relation label**: ρ(T) is the predeclared
  block-diagonal matrix from `src/equiorient/transforms.py` (RHO_ACTION),
  keyed only on T and the component. The relation label enters only the
  answer loss.

Gradient conflict (answer vs equivariance) is the expected scientific
tension, not a bug — that is exactly what EquiOrient tests.

---

## 5. Does any path bypass z?  (the critical question)

**Bypass risks and the mitigation for each:**

| Bypass path | Risk | Mitigation |
|---|---|---|
| LM generates the relation from its own hidden states | The VLM "knows" left/right from pretraining and answers without z | Relation token is FORCED from `rel_logits`; the decoder slot cannot be filled by the LM head. This is testable at inference: corrupt `z` → answer must change. |
| z ignored because `W_rel` collapses | If the relation head learns a constant, answers don't depend on z | Causal ablation test (mandatory, Amendment A2.1): zero/perturb `z` at inference → relation accuracy must drop; report this in the pilot. |
| Vision features bypass pooling (e.g., LM attends directly to image tokens) | The answer head is a separate path, but the backbone's own attention could "leak" the answer if the LM token is not forced | Only the relation token is forced; the backbone never emits the relation word, so leak is impossible for the answer. Residual risk: information about the relation leaks into other response tokens — acceptable and reportable. |
| PairEncoder ignores geometry (e.g., uses only category information) | z degenerates to "object class pair" | Equivariance loss directly punishes this: if z(x) ≈ z(Tx) for all T while the algebra says they must differ on z_h/z_v, L_eq explodes. This is the structural backstop. |

**Verification plan (pilot, before any claims):**
1. Train with EquiOrient objective; at checkpoint, run inference with
   `z ← z + ε·noise` (ε sweep). If relation accuracy is flat under large ε,
   the answer does not depend on z → EquiOrient is vacuous → STOP.
2. Same check with `z_h` block zeroed vs `z_v` block zeroed — must affect
   only horizontal vs vertical relation accuracy respectively (typed-state
   sanity).

---

## 6. What is NOT decided here (needs pilot-time freeze)

- Exact backbone (SmolVLM2-2B vs Qwen2-VL-7B): pick at pilot freeze from
  `configs/equiorient_protocol.yaml` (max 1 backbone).
- PairEncoder width/depth and whether backbone is LoRA-frozen or
  LoRA-tuned — frozen at pilot freeze; matched across all 6 arms.
- Loss weight λ_eq for `L_eq` — selection rule predeclared (e.g., grid
  {0.1, 1.0, 10.0} on a fixed validation slice, chosen BEFORE comparing
  methods).

## 7. Feasibility verdict (proposed)

**FEASIBLE** under the above design: z is answer-path by forced decoding,
gradient-reachable from both objectives, and bypass is both prevented
(structurally) and detectably auditable (causal ablation). The two open
items are implementation-level (backbone choice, head dims) and are frozen
at pilot time, not now.
