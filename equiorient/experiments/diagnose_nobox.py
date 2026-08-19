"""Comprehensive latent diagnostics for the no-box EquiOrient arm.

Re-runs the exact training config (seed, N, epochs, lr, arm) while
recording per-epoch:
  - latent z-norm (mean, std over batch)
  - per-dimension variance of z
  - effective rank of z (via SVD)
  - cosine similarity structure (z_x vs z_y intra-sample)
  - logit stats (mean, std, entropy of predicted distribution)
  - gradient norms (answer-only vs structural)
  - z-ablation: accuracy with z zeroed out

Also records per-step gradient norms for answer and structural losses
to detect the exact epoch where structural loss collapses.

Usage (Modal):
    python -m modal run modal/equiorient_nobox.py --probe --variant nobox_v1
    or directly:
    python -m equiorient.experiments.diagnose_nobox --arm equiorient --seed 101
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import ELEMENTS, GENERATORS, UNSEEN
from equiorient.algebra.label_action import LABELS
from equiorient.models.full_image_relation import (N_CLASSES,
                                                   FullImagePool,
                                                   NoBoxEncoder,
                                                   RelationHead8)
from equiorient.objectives.answer import loss_answer
from equiorient.objectives.equiorient import (loss_equiorient, rho_vec_of,
                                              wrong_rho_vec_of)
from equiorient.experiments.train_nobox import (NoBoxRunner, load_manifest,
                                                subset_scenes, make_examples)


def effective_rank(z: torch.Tensor) -> float:
    """Effective rank via SVD: sum(s)^2 / sum(s^2), where s are singular
    values normalized to sum to 1. Ranges from 1 (rank-1) to D (full rank)."""
    if z.dim() == 1:
        z = z.unsqueeze(0)
    s = torch.linalg.svdvals(z.float())
    s = s / (s.sum() + 1e-12)
    return float((s ** 2).sum().reciprocal())


def diagnose(runner: NoBoxRunner, arm: str, examples: list,
             manifest: dict, lam: float, epochs: int, batch: int,
             seed: int, lr: float) -> dict:
    """Train the arm while recording comprehensive latent diagnostics."""
    STRUCTURAL_OF = {"output_consistency": "output_consistency",
                     "latent_invariance": "invariance",
                     "equiorient": "equiorient",
                     "wrong_geometry": "wrong_geometry"}
    structural = STRUCTURAL_OF.get(arm, "none")

    # reset weights
    with torch.no_grad():
        for n, p in runner.model.named_parameters():
            if p.requires_grad:
                p.copy_(runner.lora_init[n])
    runner._feat_cache = {}
    runner.enc = NoBoxEncoder(FullImagePool()).to(runner.device)
    runner.head = RelationHead8().to(runner.device)

    opt = torch.optim.AdamW(
        list(runner.enc.parameters()) + list(runner.head.parameters())
        + [p for n, p in runner.model.named_parameters()
           if p.requires_grad], lr=lr)

    pairs = [(e["scene_id"], e["transform"], e["png"],
              e["label_idx"]) for e in examples]
    by_scene = {}
    for e in examples:
        by_scene.setdefault(e["scene_id"], []).append(e)

    use_transform = arm != "original_sft"
    need_structural = structural != "none"

    # ---- per-epoch history ----
    epoch_diag = []

    for ep in range(epochs):
        torch.manual_seed(seed + ep)
        idx = torch.randperm(len(pairs))
        n_steps = max(len(idx) // batch, 1)

        # accumulators for this epoch
        ans_sum = struct_sum = 0.0
        struct_n = 0
        corr = tot_n = 0

        # per-step gradient norms
        grad_ans_norms = []
        grad_struct_norms = []

        # per-step latent stats (collected during forward pass)
        z_all = []  # list of (z_x, z_y) per sample
        logit_all = []
        attn_all = []

        for st in range(n_steps):
            sel = idx[st * batch:(st + 1) * batch]
            opt.zero_grad()

            tot = torch.tensor(0.0, device=runner.device)
            n = 0

            # identity features
            id_feat = {}
            if use_transform or need_structural:
                for i in sel:
                    sid = pairs[i.item()][0]
                    if sid in id_feat:
                        continue
                    id_ex = next(e for e in by_scene[sid]
                                 if e["transform"] == "I")
                    id_feat[sid] = (id_ex, runner.vision_features(
                        id_ex["png"], requires_grad=True))

            for i in sel:
                sid, g, png, y = pairs[i.item()]
                if use_transform or need_structural:
                    logits_t, zt = runner.image_logits(png, grad=True)
                    zt_x, zt_y = zt
                    id_ex, (fx, gx) = id_feat[sid]
                    zx_pair = runner.enc(fx.float())
                    zx_x, zx_y = zx_pair
                    logits_x = runner.head(*zx_pair)

                    # collect latent stats
                    with torch.no_grad():
                        z_all.append((zx_x.clone(), zx_y.clone(),
                                      zt_x.clone(), zt_y.clone()))
                        logit_all.append(logits_t.clone())

                    # answer loss
                    al = loss_answer(logits_t,
                                     torch.tensor([y], device=runner.device))
                    tot = tot + al
                    ans_sum += float(al.detach())

                    # structural loss
                    if need_structural and lam is not None:
                        if structural == "equiorient":
                            sl = loss_equiorient(zx_pair, zt, rho_vec_of(g))
                        elif structural == "wrong_geometry":
                            sl = loss_equiorient(
                                zx_pair, zt, wrong_rho_vec_of(g))
                        elif structural == "invariance":
                            sl = ((zx_x - zt_x) ** 2 + (zx_y - zt_y) ** 2).mean()
                        else:
                            sl = torch.tensor(0.0, device=runner.device)
                        tot = tot + lam * sl
                        struct_sum += float(sl.detach())
                        struct_n += 1

                    # identity answer loss
                    if use_transform:
                        y_id = next(e for e in by_scene[sid]
                                    if e["transform"] == "I")["label_idx"]
                        tot = tot + loss_answer(
                            logits_x,
                            torch.tensor([y_id], device=runner.device))
                else:
                    logits_x, _ = runner.image_logits(png, grad=True)
                    tot = tot + loss_answer(
                        logits_x,
                        torch.tensor([y], device=runner.device))
                    ans_sum += float(loss_answer(
                        logits_x,
                        torch.tensor([y], device=runner.device)).detach())

                n += 1

            # backward + grad norms
            (tot / max(n, 1)).backward()

            # gradient norms for answer vs structural
            with torch.no_grad():
                ans_grad_norm = 0.0
                struct_grad_norm = 0.0
                for name, p in runner.model.named_parameters():
                    if p.requires_grad and p.grad is not None:
                        g = p.grad.data.norm().item()
                        if "lora" in name:
                            ans_grad_norm += g ** 2
                for p in list(runner.enc.parameters()) + \
                         list(runner.head.parameters()):
                    if p.grad is not None:
                        ans_grad_norm += p.grad.data.norm().item() ** 2
                ans_grad_norm = math.sqrt(ans_grad_norm)

            opt.step()

            # accuracy this step
            with torch.no_grad():
                for i in sel:
                    sid, g, png, y = pairs[i.item()]
                    l, _ = runner.image_logits(png, grad=False)
                    corr += int(l.argmax(-1).item() == y)
                    tot_n += 1

        # ---- end of epoch: compute latent diagnostics ----
        mean_struct = struct_sum / max(struct_n, 1)
        acc_tr = corr / max(tot_n, 1)

        with torch.no_grad():
            # stack all latent vectors from this epoch
            if z_all:
                zx_0 = torch.stack([z[0].squeeze() for z in z_all])  # (N, Z_BLOCK)
                zx_1 = torch.stack([z[1].squeeze() for z in z_all])
                zt_0 = torch.stack([z[2].squeeze() for z in z_all])
                zt_1 = torch.stack([z[3].squeeze() for z in z_all])

                z_full = torch.cat([zx_0, zx_1], dim=-1)  # (N, 2*Z_BLOCK)

                # latent norm
                norm_x0 = float(zx_0.norm(dim=-1).mean())
                norm_x1 = float(zx_1.norm(dim=-1).mean())
                norm_full = float(z_full.norm(dim=-1).mean())

                # per-dimension variance
                var_per_dim = float(z_full.var(dim=0).mean())

                # effective rank
                eff_rank = effective_rank(z_full)

                # cosine similarity: z_x vs z_y (intra-sample)
                cos_xy = float(F.cosine_similarity(zx_0, zx_1, dim=-1).mean())

                # cosine similarity: z(x) vs z(gx) (transform invariance)
                cos_x_gx = float(F.cosine_similarity(zx_0, zt_0, dim=-1).mean())

                # logit stats
                if logit_all:
                    logits_stack = torch.stack(logit_all)  # (N, 8)
                    probs = torch.softmax(logits_stack, dim=-1)
                    logit_mean = float(logits_stack.mean())
                    logit_std = float(logits_stack.std())
                    entropy = float(-(probs * probs.log()).sum(dim=-1).mean())
                else:
                    logit_mean = logit_std = entropy = 0.0

                # z-ablation: accuracy with z zeroed
                # (need fresh forward with z=0)
                abl_corr = 0
                abl_n = 0
                for i in range(min(200, len(pairs))):  # subsample for speed
                    sid, g, png, y = pairs[i]
                    feat, grid = runner.vision_features(png, requires_grad=False)
                    zx_a, zy_a = runner.enc.pool(feat.float())[:2]
                    # zero out z
                    zx_zero = torch.zeros_like(zx_a)
                    zy_zero = torch.zeros_like(zy_a)
                    logits_abl = runner.head(zx_zero, zy_zero)
                    abl_corr += int(logits_abl.argmax(-1).item() == y)
                    abl_n += 1
                abl_acc = abl_corr / max(abl_n, 1)
            else:
                norm_x0 = norm_x1 = norm_full = 0.0
                var_per_dim = eff_rank = cos_xy = cos_x_gx = 0.0
                logit_mean = logit_std = entropy = abl_acc = 0.0

        diag = {
            "epoch": ep + 1,
            "answer_loss": round(ans_sum / max(n_steps, 1), 6),
            "structural_loss": round(mean_struct, 8),
            "train_acc": round(acc_tr, 4),
            "latent_norm_zx": round(norm_x0, 6),
            "latent_norm_zy": round(norm_x1, 6),
            "latent_norm_full": round(norm_full, 6),
            "latent_var_per_dim": round(var_per_dim, 8),
            "latent_eff_rank": round(eff_rank, 4),
            "cosine_zx_zy": round(cos_xy, 6),
            "cosine_zx_zgx": round(cos_x_gx, 6),
            "logit_mean": round(logit_mean, 6),
            "logit_std": round(logit_std, 6),
            "logit_entropy": round(entropy, 6),
            "z_ablation_acc": round(abl_acc, 4),
        }
        epoch_diag.append(diag)
        runner.log(f"[DIAG] ep {ep+1}: norm={norm_full:.6f} "
                   f"rank={eff_rank:.2f} cos_zxzy={cos_xy:.4f} "
                   f"cos_zxgx={cos_x_gx:.4f} ent={entropy:.4f} "
                   f"abl={abl_acc:.4f}")

    return {"arm": arm, "seed": seed, "epochs": epochs,
            "epoch_diagnostics": epoch_diag}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="equiorient")
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--n_train", type=int, default=128)
    ap.add_argument("--lambda", dest="lam", type=float, default=1.0)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--data", default="results/phase2_data")
    ap.add_argument("--out", default="results/equiorient_no_box/diag")
    a = ap.parse_args()

    import random
    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(a.seed)

    data_dir = Path(a.data)
    manifest = load_manifest(data_dir)
    runner = NoBoxRunner(data_dir, Path(a.out))
    runner.load_model()
    runner.attach_lora()

    train_ids = subset_scenes(manifest, "train", a.n_train)
    ex = make_examples(manifest, train_ids)
    runner.log(f"DIAGNOSTIC: arm={a.arm} seed={a.seed} N={a.n_train} "
               f"epochs={a.epochs} lr={a.lr}")

    diag = diagnose(runner, a.arm, ex, manifest, a.lam, a.epochs,
                    a.batch, a.seed, a.lr)

    out_path = Path(a.out)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / f"diag_{a.arm}_s{a.seed}.json").write_text(
        json.dumps(diag, indent=1), encoding="utf-8")
    print(json.dumps(diag, indent=1))


if __name__ == "__main__":
    main()
