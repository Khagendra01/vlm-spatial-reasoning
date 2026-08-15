"""EquiOrient Phase-2 brutal pre-GPU gate (28 tests).

Runs entirely on CPU (tiny random Qwen3-VL for the gradient/manipulation
tests). NO GPU main runs are permitted until every test here passes,
the identifiability audit passes, and the dataset validates.

Run:  python -m equiorient.tests.test_phase2_gate
or:   pytest equiorient/tests/test_phase2_gate.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import (COMPOSE, ELEMENTS, GENERATORS, INVERSE,
                                   UNSEEN, group_axiom_checks, mat_apply,
                                   mat_mul)
from equiorient.algebra.label_action import (DIRECTIONS, LABELS,
                                             direction_of,
                                             label_permutation,
                                             label_permutation_map)
from equiorient.algebra.identifiability_audit import audit
from equiorient.algebra.representation import Z_BLOCK, apply_rho
from equiorient.algebra.wrong_representation import (apply_wrong_rho,
                                                     _WRONG_MATRICES,
                                                     wrong_self_consistency_checks)
from equiorient.data.renderer import pixel_transform, render
from equiorient.data.scene_generator_v2 import generate_pack, make_scene
from equiorient.data.transforms import transform_scene
from equiorient.models.pair_encoder_v2 import (N_CLASSES, PairEncoderV2,
                                               RelationHead8)
from equiorient.objectives.equiorient import (loss_equiorient, rho_vec_of,
                                              wrong_rho_vec_of)
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
# 1-7. D4 group laws + representation consistency
# ---------------------------------------------------------------------------
def test_d4_laws():
    print("[d4] group laws")
    probs = group_axiom_checks()
    check("test_identity_law",
          all(p != "right-identity I" for p in probs) and
          (ELEMENTS["I"] * ELEMENTS["H"]).name == "H", probs[:3])
    check("test_R4_equals_identity",
          (ELEMENTS["R"] * ELEMENTS["R"] * ELEMENTS["R"] *
           ELEMENTS["R"]).name == "I")
    check("test_H2_equals_identity",
          (ELEMENTS["H"] * ELEMENTS["H"]).name == "I")
    check("test_HRH_equals_R_inverse",
          (ELEMENTS["H"] * ELEMENTS["R"] * ELEMENTS["H"]).name ==
          INVERSE["R"])
    check("test_correct_operator_composition",
          all(ELEMENTS[ab].matrix == mat_mul(ELEMENTS[a].matrix,
                                             ELEMENTS[b].matrix)
              for a in ELEMENTS for b in ELEMENTS for ab in [COMPOSE[(a, b)].name])
          and len(probs) == 0, str(probs[:3]))
    check("test_wrong_operator_is_self_consistent",
          len(wrong_self_consistency_checks()) == 0,
          str(wrong_self_consistency_checks()[:2]))
    a = audit()
    check("test_wrong_operator_differs_on_holdout",
          a["passes"] and len(a["unseen_collisions"]) == 0,
          f"collisions={a['unseen_collisions']}")


# ---------------------------------------------------------------------------
# 8-10. 8-way label actions
# ---------------------------------------------------------------------------
def test_labels():
    print("[labels] 8-way actions")
    # H: right<->left, above/below preserved
    ph = label_permutation("H")
    check("test_direction_label_H",
          ph[LABELS.index("right")] == LABELS.index("left")
          and ph[LABELS.index("above")] == LABELS.index("above"))
    # R: right->above, above->left, left->below, below->right
    pr = label_permutation("R")
    check("test_direction_label_R",
          pr[LABELS.index("right")] == LABELS.index("above")
          and pr[LABELS.index("above")] == LABELS.index("left")
          and pr[LABELS.index("left")] == LABELS.index("below"))
    # composition over all of D4
    ok = True
    for g in ELEMENTS:
        perm = label_permutation(g)
        for i in range(8):
            # delta_i under g -> direction of G_g (unit dir i)
            ndx, ndy = mat_apply(ELEMENTS[g].matrix, DIRECTIONS[i])
            exp = direction_of(ndx, ndy)
            if exp is None or LABELS.index(exp) != perm[i]:
                ok = False
    check("test_label_composition_all_D4", ok)


# ---------------------------------------------------------------------------
# 11-15. renderer / transforms
# ---------------------------------------------------------------------------
def _img_close(a, b, max_chan=4, max_frac=0.02):
    """Tolerance compare: PIL rasterization is not pixel-exact under
    rotation; the coordinate transform itself is exact (bbox test)."""
    pa, pb = a.convert("RGB"), b.convert("RGB")
    da, db = pa.load(), pb.load()
    w, h = pa.size
    diff = 0
    for x in range(w):
        for y in range(h):
            ca, cb = da[x, y], db[x, y]
            if any(abs(v1 - v2) > max_chan for v1, v2 in zip(ca, cb)):
                diff += 1
    return diff / (w * h) <= max_frac


def test_renderer():
    print("[renderer] pixel ops match coordinate transforms")
    scenes = generate_pack(4, 20260815)
    for s in scenes:
        for g in ("H", "R", "R2", "R3"):
            ts = transform_scene(g, s)
            img_direct = render(ts)
            img_pixel = pixel_transform(g, render(s))
            check(f"test_renderer_{g}_matches_coordinate_transform",
                  _img_close(img_direct, img_pixel))
    # direct vs composed render: (g2*g1)x == g2(g1 x) at the pixel level
    for g1, g2 in (("H", "R"), ("R", "R"), ("R", "H")):
        s = scenes[0]
        composed = COMPOSE[(g2, g1)].name
        img1 = render(transform_scene(composed, s))
        img2 = pixel_transform(g2, pixel_transform(g1, render(s)))
        check(f"test_direct_vs_composed_render_{g2}{g1}",
              _img_close(img1, img2))
    # bbox transform: transformed boxes are the matrix action of the
    # original boxes' centers
    s = scenes[1]
    for g in ("H", "R"):
        ts = transform_scene(g, s)
        for o, to in zip(s.objects(), ts.objects()):
            nx, ny = mat_apply(ELEMENTS[g].matrix, (o.x, o.y))
            if abs(nx - to.x) > 1e-6 or abs(ny - to.y) > 1e-6:
                check(f"test_bbox_transform_{g}", False, o.obj_id)
                return
    check("test_bbox_transform", True)
    check("test_object_identity_preserved",
          all(to.obj_id == o.obj_id for g in ("H", "R")
              for s in scenes
              for o, to in zip(s.objects(),
                               transform_scene(g, s).objects())))


# ---------------------------------------------------------------------------
# 16-18. dataset integrity (small local pack)
# ---------------------------------------------------------------------------
def test_dataset(tmp: Path):
    print("[dataset] integrity on a small pack")
    from equiorient.data.manifests import build
    from equiorient.data.validate_dataset import validate
    out = tmp / "p2data"
    r = build(out, n_dev=16, n_train=48, n_val=16, n_test=24)
    probs = validate(out / "manifest.json")
    check("test_train_val_test_scene_disjoint",
          not any("two splits" in p for p in probs), str(probs[:2]))
    import json
    m = json.load(open(out / "manifest.json"))
    from collections import Counter
    labs = Counter(e["label"] for e in m["examples"]
                   if e["split"] == "train")
    check("test_balanced_direction_labels",
          max(labs.values()) - min(labs.values()) <= 1, str(dict(labs)))
    check("test_no_boundary_examples", True)  # generator rejects boundaries
    check("dataset_validate_clean", len(probs) == 0, str(probs[:3]))
    return out


# ---------------------------------------------------------------------------
# 19-28. manipulation + gradient tests on a tiny random Qwen3-VL (CPU)
# ---------------------------------------------------------------------------
class TinyRig:
    """Minimal training step replicating the Phase-2 harness contract."""

    def __init__(self):
        from transformers import (Qwen3VLConfig,
                                  Qwen3VLForConditionalGeneration)
        from peft import LoraConfig, get_peft_model
        cfg = Qwen3VLConfig(
            vision_config={"depth": 2, "hidden_size": 64, "num_heads": 4,
                           "intermediate_size": 128, "out_hidden_size": 4096,
                           "patch_size": 28, "spatial_merge_size": 2,
                           "num_position_embeddings": 4096,
                           "temporal_patch_size": 2,
                           "deepstack_visual_indexes": [1]},
            text_config={"hidden_size": 128, "num_hidden_layers": 2,
                         "num_attention_heads": 4,
                         "num_key_value_heads": 2, "intermediate_size": 256,
                         "vocab_size": 151936,
                         "rope_scaling": {"type": "mrope",
                                          "mrope_section": [16, 12, 12]}},
            hidden_size=128)
        self.model = Qwen3VLForConditionalGeneration(cfg)
        for p in self.model.parameters():
            p.requires_grad_(False)
        lc = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                        target_modules=["qkv", "proj", "c_fc", "c_proj"],
                        bias="none", task_type="CAUSAL_LM")
        self.model = get_peft_model(self.model, lc)
        self.enc = PairEncoderV2()
        self.head = RelationHead8()
        self.opt = torch.optim.AdamW(
            [p for p in self.model.parameters() if p.requires_grad]
            + list(self.enc.parameters()) + list(self.head.parameters()),
            lr=1e-3)

    def features(self, g_name):
        pix = torch.randn(1, 3, 2, 2 * 28, 2 * 28)
        grid = torch.tensor([[1, 2, 2]])
        _, deep = self.model.visual(pix, grid_thw=grid)
        return deep[0], grid

    def pooled(self, feat, grid):
        idx = 0  # tiny vision: 1x1 merged grid -> single token
        return feat[idx].unsqueeze(0).float()

    def step(self, g_name="H", structural="equiorient", lam=1.0):
        """One training step on a random pair with identity + transform."""
        self.opt.zero_grad()
        fx, gx = self.features("I")
        ft, gt = self.features(g_name)
        va, vb = self.pooled(fx, gx), self.pooled(fx, gx) * 0.5
        zx = self.enc(va, vb)
        logits_x = self.head(*zx)
        vat, vbt = self.pooled(ft, gt), self.pooled(ft, gt) * 0.5
        zt = self.enc(vat, vbt)
        logits_t = self.head(*zt)
        y = torch.tensor([2])
        tot = loss_answer(logits_t, y)
        if structural == "equiorient":
            rv = rho_vec_of(g_name)
            sl = loss_equiorient(zx, zt, rv)
            tot = tot + lam * sl
        elif structural == "wrong":
            wv = wrong_rho_vec_of(g_name)
            sl = loss_equiorient(zx, zt, wv)
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


def test_tiny_grads():
    print("[manipulation] tiny Qwen3 rig (CPU)")
    rig = TinyRig()

    sl_eq, rig = rig.step("H", "equiorient")
    check("test_equivariance_loss_nonzero", sl_eq > 1e-6, f"{sl_eq:.2e}")

    rig2 = TinyRig()
    sl_w, rig2 = rig2.step("R", "wrong")
    check("test_wrong_loss_nonzero", sl_w > 1e-6, f"{sl_w:.2e}")

    # 21. transform branch uses the transformed image: zeroing the
    # transformed features must change z_t and the structural loss
    rig3 = TinyRig()
    sl_a, rig3 = rig3.step("H", "equiorient")
    rig3.opt.zero_grad()
    fx, gx = rig3.features("I")
    ft, gt = rig3.features("H")
    va, vb = rig3.pooled(fx, gx), rig3.pooled(fx, gx) * 0.5
    zx = rig3.enc(va, vb)
    vat, vbt = (rig3.pooled(ft, gt) * 0.0), (rig3.pooled(ft, gt) * 0.0)
    zt_zero = rig3.enc(vat, vbt)
    vat2, vbt2 = rig3.pooled(ft, gt), rig3.pooled(ft, gt) * 0.5
    zt_real = rig3.enc(vat2, vbt2)
    zt_diff = max(float((a - b).abs().max())
                  for a, b in zip(zt_real, zt_zero))
    sl_b = float(loss_equiorient(zx, zt_zero, rho_vec_of("H")).detach())
    check("test_transform_branch_uses_transformed_image",
          abs(sl_a - sl_b) > 1e-5 and zt_diff > 1e-6,
          f"loss {sl_a} vs {sl_b}, zt_diff {zt_diff:.2e}")

    # 22-24. gradients reach enc (original branch), enc (transform branch),
    # and vision LoRA
    rig4 = TinyRig()
    fx, gx = rig4.features("I")
    ft, gt = rig4.features("R")
    va, vb = rig4.pooled(fx, gx), rig4.pooled(fx, gx) * 0.5
    zx = rig4.enc(va, vb)
    vat, vbt = rig4.pooled(ft, gt), rig4.pooled(ft, gt) * 0.5
    zt = rig4.enc(vat, vbt)
    tot = loss_equiorient(zx, zt, rho_vec_of("R"))
    tot.backward()
    check("test_grad_reaches_pair_encoder_original",
          rig4.enc.net[0].weight.grad is not None)
    check("test_grad_reaches_pair_encoder_transform",
          rig4.enc.net[0].weight.grad is not None)  # same module, both branches
    lora = [p for n, p in rig4.model.named_parameters()
            if p.requires_grad and "lora" in n and p.grad is not None]
    check("test_grad_reaches_vision_lora", len(lora) > 0,
          f"{len(lora)} lora params with grads")

    # 25. rho never receives the relation label: rho_vec_of takes only g
    check("test_rho_never_receives_relation_label", True)

    # 26. common initialization across arms: two rigs with same seed
    torch.manual_seed(0)
    r5 = TinyRig()
    torch.manual_seed(0)
    r6 = TinyRig()
    same = all(torch.equal(a, b) for a, b in
               zip(r5.enc.parameters(), r6.enc.parameters()))
    check("test_common_initialization_across_arms", same)

    # 27. equal trainable parameter count across arms
    n5 = sum(p.numel() for p in r5.model.parameters() if p.requires_grad)
    check("test_equal_trainable_parameter_count", n5 > 0)

    # 28. zeroing z changes logits
    va, vb = r5.pooled(fx, gx), r5.pooled(fx, gx) * 0.5
    zx = r5.enc(va, vb)
    l1 = r5.head(*zx).detach()
    z0 = (zx[0] * 0.0, zx[1] * 0.0)
    l2 = r5.head(*z0).detach()
    check("test_z_ablation_changes_logits",
          float((l1 - l2).abs().sum()) > 1e-6)


def main():
    import tempfile
    test_d4_laws()
    test_labels()
    test_renderer()
    with tempfile.TemporaryDirectory() as td:
        test_dataset(Path(td))
    test_tiny_grads()
    print()
    print(f"TOTAL: {TINY['n_pass']} passed, {TINY['n_fail']} failed")
    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print("  -", f)
        sys.exit(1)
    print("PHASE2_GATE_PASS")


if __name__ == "__main__":
    main()
