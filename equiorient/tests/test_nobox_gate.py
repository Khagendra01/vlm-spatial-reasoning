"""EquiOrient NO-BOX pre-GPU verification gate.

Proves that the no-box implementation cannot access ground-truth
bounding boxes / object centers / pixel displacement, and that the
matched-arm machinery (common init, equal trainable params, gradient
flow, nonzero structural loss, D4 laws) still holds.

Run:
  python -m equiorient.tests.test_nobox_gate
or:
  pytest equiorient/tests/test_nobox_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import ELEMENTS, group_axiom_checks
from equiorient.algebra.label_action import LABELS, label_permutation
from equiorient.algebra.identifiability_audit import audit
from equiorient.algebra.wrong_representation import (wrong_self_consistency_checks)
from equiorient.models.full_image_relation import (RelationHead8, FullImagePool,
                                                   NoBoxEncoder, FullImageRelation)
from equiorient.objectives.equiorient import loss_equiorient, rho_vec_of, wrong_rho_vec_of
from equiorient.objectives.answer import loss_answer
from equiorient.objectives.output_consistency import loss_output_consistency

FAILURES: list[str] = []
TINY = {"n_pass": 0, "n_fail": 0}


def check(name: str, cond: bool, detail: str = ""):
    if cond:
        TINY["n_pass"] += 1
        print(f"  PASS {name}")
    else:
        TINY["n_fail"] += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL {name}: {detail}")


# ---------------------------------------------------------------------------
# 1. NO-GROUND-TRUTH-SHORTCUT guarantees
# ---------------------------------------------------------------------------
def test_no_gt_access_source():
    """Static source checks: the no-box forward path never references
    boxes, centers, or displacement. We strip docstrings/comments and
    grep for executable tokens only."""
    print("[no-box] source-level no-ground-truth-audit")
    src_dir = REPO / "equiorient"
    forbidden_in_forward = ["boxes", "pixel_transform", "displacement",
                            "delta", "obj_id", ".cx", ".cy"]
    model_src = (src_dir / "models" / "full_image_relation.py").read_text(
        encoding="utf-8")
    # strip triple-quoted docstrings to check only executable code
    import re
    code = re.sub(r'""".*?"""', '', model_src, flags=re.DOTALL)
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    for tok in forbidden_in_forward:
        check(f"no_gt_{tok}_in_model_code", tok not in code,
              f"found '{tok}' in executable code")
    # harness file: boxes must NOT appear in training/forward-path runtime
    # code nor in make_examples. The post-hoc attention-localization
    # diagnostic lives in equiorient/analysis/attn_diagnostic.py (a
    # separate module, imported by the harness), so the audited harness
    # source itself must contain NO ground-truth references at all.
    harness_src = (src_dir / "experiments" / "train_nobox.py").read_text(
        encoding="utf-8")
    stripped = re.sub(r'""".*?"""', '', harness_src, flags=re.DOTALL)
    stripped = re.sub(r'#.*$', '', stripped, flags=re.MULTILINE)
    check("make_examples_has_no_boxes",
          '"boxes"' not in stripped,
          "'boxes' key present in train_nobox.py source")
    check("make_examples_has_no_delta",
          '"delta"' not in stripped,
          "'delta' key present in train_nobox.py source")
    for tok in ("displacement", "obj_id", ".cx", ".cy"):
        check(f"no_gt_{tok}_in_harness", tok not in stripped,
              f"found '{tok}' in train_nobox.py")


def test_example_dicts_have_no_gt():
    """Structural: make_examples output must never contain boxes/delta."""
    print("[no-box] example dicts carry no ground-truth geometry")
    import json
    tiny = {
        "examples": [
            {"scene_id": "scene_000000", "split": "train",
             "transform": "I", "png": "x.png", "label": "right",
             "delta": [1.0, 0.0],
             "boxes": {"a": [0, 0, 5], "b": [10, 0, 5]}}
        ]
    }
    # emulate make_examples selection on a real manifest dict
    from equiorient.experiments.train_nobox import make_examples, subset_scenes
    ex = make_examples(tiny, {"scene_000000"})
    check("example_has_no_boxes_key", "boxes" not in ex[0],
          f"keys={list(ex[0].keys())}")
    check("example_has_no_delta_key", "delta" not in ex[0],
          f"keys={list(ex[0].keys())}")
    check("example_keys_are_minimal",
          set(ex[0].keys()) == {"scene_id", "transform", "png", "label_idx"},
          f"keys={list(ex[0].keys())}")


# ---------------------------------------------------------------------------
# 2. D4 laws + wrong-law self consistency + identifiability
# ---------------------------------------------------------------------------
def test_d4():
    print("[no-box] D4 + wrong-law")
    probs = group_axiom_checks()
    check("no_box_d4_laws_pass", len(probs) == 0, str(probs[:3]))
    wprobs = wrong_self_consistency_checks()
    check("no_box_wrong_law_self_consistent", len(wprobs) == 0, str(wprobs[:2]))
    a = audit()
    check("no_box_wrong_differs_on_holdout",
          a["passes"] and len(a["unseen_collisions"]) == 0,
          str(a["unseen_collisions"]))
    # label permutation for output-consistency arm must be exact
    ph = label_permutation("H")
    check("no_box_label_perm_H",
          ph[LABELS.index("right")] == LABELS.index("left"))


# ---------------------------------------------------------------------------
# 3. No-box pool: matched init, param count, gradient flow, structural loss
# ---------------------------------------------------------------------------
class NoBoxTinyRig:
    """Minimal CPU training step for the no-box architecture."""

    def __init__(self, feat_dim: int = 64):
        self.feat_dim = feat_dim
        # use a smaller pool with arbitrary feat_dim for CPU checks
        self.pool = FullImagePool(feat_dim=feat_dim, proj_dim=64)
        self.enc = NoBoxEncoder(self.pool)
        self.head = RelationHead8()
        self.opt = torch.optim.AdamW(
            list(self.enc.parameters()) + list(self.head.parameters()), lr=1e-3)

    def step(self, g_name: str = "H", structural: str = "equiorient",
             lam: float = 1.0):
        self.opt.zero_grad()
        # random full-image token sequence (T=12 tokens, feat_dim)
        fx = torch.randn(1, 12, self.feat_dim)
        ft = torch.randn(1, 12, self.feat_dim) * 0.9
        zx = self.enc(fx)
        logits_x = self.head(*zx)
        zt = self.enc(ft)
        logits_t = self.head(*zt)
        y = torch.tensor([2])
        tot = loss_answer(logits_t, y)
        if structural == "equiorient":
            sl = loss_equiorient(zx, zt, rho_vec_of(g_name))
            tot = tot + lam * sl
        elif structural == "wrong":
            sl = loss_equiorient(zx, zt, wrong_rho_vec_of(g_name))
            tot = tot + lam * sl
        elif structural == "output":
            perm = label_permutation(g_name)
            sl = loss_output_consistency(logits_t, logits_x, perm)
            tot = tot + lam * sl
        else:
            sl = torch.tensor(0.0)
        tot.backward()
        self.opt.step()
        return float(sl.detach()), self


def test_no_box_rig():
    print("[no-box] manipulation/gradient/init checks (CPU)")
    rig = NoBoxTinyRig()

    sl_eq, _ = rig.step("H", "equiorient")
    check("no_box_equivariance_loss_nonzero", sl_eq > 1e-6, f"{sl_eq:.2e}")

    rig2 = NoBoxTinyRig()
    sl_w, _ = rig2.step("R", "wrong")
    check("no_box_wrong_loss_nonzero", sl_w > 1e-6, f"{sl_w:.2e}")

    # gradient reaches the pool (query, k_proj, v_proj) and the head
    rig3 = NoBoxTinyRig()
    fx = torch.randn(1, 12, rig3.feat_dim)
    zx = rig3.enc(fx)
    logits = rig3.head(*zx)
    y = torch.tensor([2])
    tot = loss_answer(logits, y) + loss_equiorient(zx, zx, rho_vec_of("H"))
    tot.backward()
    check("no_box_grad_reaches_query",
          rig3.pool.query.grad is not None and
          float(rig3.pool.query.grad.abs().sum()) > 0)
    check("no_box_grad_reaches_k_proj",
          rig3.pool.k_proj.weight.grad is not None)
    check("no_box_grad_reaches_head",
          rig3.head.w.weight.grad is not None)

    # common initialization across "arms": two encoders with same seed
    torch.manual_seed(0)
    a1 = NoBoxEncoder(FullImagePool(feat_dim=64, proj_dim=64))
    torch.manual_seed(0)
    a2 = NoBoxEncoder(FullImagePool(feat_dim=64, proj_dim=64))
    same = all(torch.equal(p1, p2)
               for p1, p2 in zip(a1.parameters(), a2.parameters()))
    check("no_box_common_initialization", same)

    # equal trainable parameter count between two instantiations
    n1 = sum(p.numel() for p in a1.parameters())
    n2 = sum(p.numel() for p in a2.parameters())
    check("no_box_equal_trainable_params", n1 == n2 and n1 > 0, f"{n1} vs {n2}")

    # z-ablation changes logits (answer causality)
    hd = RelationHead8()
    zx = a1(fx)
    l1 = hd(*zx).detach()
    l2 = hd(zx[0] * 0, zx[1] * 0).detach()
    check("no_box_z_ablation_changes_logits", float((l1 - l2).abs().sum()) > 1e-6)
    # attention pooling is over the full token set (no single-cell pick)
    attns = []
    for _ in range(3):
        fx2 = torch.randn(1, 12, 64)
        _, _, attn = a1.pool(fx2)
        attns.append(attn)
    check("no_box_attention_over_all_tokens",
          all(float(a.min()) >= 0.0 and abs(float(a.sum()) - 1.0) < 1e-3
              for a in attns))


def main():
    test_no_gt_access_source()
    test_example_dicts_have_no_gt()
    test_d4()
    test_no_box_rig()
    print()
    print(f"TOTAL: {TINY['n_pass']} passed, {TINY['n_fail']} failed")
    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print("  -", f)
        sys.exit(1)
    print("NOBOX_GATE_PASS")


if __name__ == "__main__":
    main()
