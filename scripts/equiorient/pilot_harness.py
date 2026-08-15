"""EquiOrient Phase-1 pilot harness — UNATTENDED single execution.

Frozen protocol: configs/equiorient_pilot_freeze.yaml (commit 91185d7).
Runs END-TO-END with NO interactive decisions:

  PRE-FLIGHT (init-equivalence + feature path check)
    -> 12 training runs:
         ordinary_sft_lora, augmentation_only            (1 run each)
         output_consistency, latent_invariance, equiorient
           (3 runs each: lambda grid {0.1, 1.0, 10.0})
         wrong_geometry_equiorient                       (1 run, at
           equiorient's SELECTED lambda — not tuned independently)
    -> lambda selection on scene_0010-0013 ONLY (never V o H)
    -> SINGLE held-out evaluation (scene_0014-0016, V o H examples only)
    -> causal z-ablation (zero z -> accuracy must collapse)
    -> archive: per-arm configs/checkpoints/logs/predictions/latent
       errors/selected lambda + result matrix JSON

Usage (GPU instance):
  python pilot_harness.py --freeze configs/equiorient_pilot_freeze.yaml \
      --data results/equiorient/pilot_data \
      --out results/equiorient/pilot_run

Local CPU logic test (tiny random Qwen3, no weights):
  python pilot_harness.py --tiny --freeze ... --data ... --out ...
"""
import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn

WT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WT))

from src.equiorient.transforms import (  # noqa: E402
    RHO_ACTION, StateComponent, Transform,
)

# ---------------------------------------------------------------------------
# Frozen architecture (Amendment B6) — identical in all six arms
# ---------------------------------------------------------------------------
FEAT_DIM = 4096            # Qwen3 deepstack out_hidden_size (8B)
Z_TOTAL = 512
Z_BLOCKS = (128, 128, 128, 128)   # z_h, z_v, z_d, z_orient
PE_HIDDEN = 512
N_RELATIONS = 4
REL_NAMES = ["left_of", "right_of", "above", "below"]

COMP_MAP = {"z_h": StateComponent.H, "z_v": StateComponent.V,
            "z_d": StateComponent.D, "z_orient": StateComponent.ORIENT}
RHO_VEC = {"hflip": [RHO_ACTION[Transform.H][c] for c in COMP_MAP.values()],
           "vflip": [RHO_ACTION[Transform.V][c] for c in COMP_MAP.values()],
           "v_after_h": [RHO_ACTION[Transform.VH][c] for c in COMP_MAP.values()],
           "identity": [1, 1, 1, 1]}
# WRONG predeclared rho (frozen YAML: "WRONG predeclared rho (e.g., rho_H
# acting on z_v)"): the geometry-derived action applied to the WRONG typed
# component — H acts on z_v, V acts on z_h, and the held-out composition is
# misread as identity (a natural "wrong geometry" misunderstanding).
WRONG_RHO_VEC = {"hflip": [+1, -1, +1, +1],   # H acting on z_v
                 "vflip": [-1, +1, +1, +1],   # V acting on z_h
                 "v_after_h": [1, 1, 1, 1],   # V o H misread as identity
                 "identity": [1, 1, 1, 1]}


class PairEncoder(nn.Module):
    """Frozen spec: Linear(2*4096->512) GELU Linear(512->512) typed blocks."""

    def __init__(self, feat_dim=FEAT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2 * feat_dim, PE_HIDDEN), nn.GELU(),
            nn.Linear(PE_HIDDEN, Z_TOTAL))

    def forward(self, va, vb):
        z = self.net(torch.cat([va, vb], dim=-1))
        return list(z.split(Z_BLOCKS, dim=-1))  # [z_h, z_v, z_d, z_orient]


class RelationHead(nn.Module):
    """Frozen spec: Linear(256 -> 4) over [z_h ; z_v]. FORCED decoding."""

    def __init__(self):
        super().__init__()
        self.w = nn.Linear(Z_BLOCKS[0] + Z_BLOCKS[1], N_RELATIONS)

    def forward(self, z_blocks):
        return self.w(torch.cat([z_blocks[0], z_blocks[1]], dim=-1))


# Losses: pure functions, ZERO trainable params (Amendment B4)
def loss_answer(logits, y):
    return nn.functional.cross_entropy(logits, y)


def loss_output_consistency(logits_x, logits_tx):
    return nn.functional.mse_loss(logits_x, logits_tx)


def loss_latent_invariance(z_x, z_tx):
    return sum(((a - b) ** 2).mean() for a, b in zip(z_x, z_tx))


def loss_equivariance(z_x, z_tx, rho_vec):
    return sum(((s * a - b) ** 2).mean()
               for s, a, b in zip(rho_vec, z_x, z_tx))


# ---------------------------------------------------------------------------
# Data (frozen manifest from build_pilot_data.py)
# ---------------------------------------------------------------------------
@dataclass
class PilotData:
    train: list = field(default_factory=list)
    val: list = field(default_factory=list)
    holdout: list = field(default_factory=list)


def load_pilot_data(manifest_path: Path) -> PilotData:
    m = json.load(open(manifest_path, encoding="utf-8"))
    split = {"train": set(m["scene_split"]["train"]),
             "validation": set(m["scene_split"]["validation"]),
             "holdout": set(m["scene_split"]["holdout"])}
    pd_ = PilotData()
    for ex in m["examples"]:
        # Held-out transform discipline: V o H must NEVER appear in train or
        # validation (frozen YAML: transform_held_out [v_after_h], "NEVER in
        # training"). The committed manifest contains v_after_h rows for all
        # 17 scenes; they belong ONLY to the single held-out evaluation.
        if ex["transform"] == "v_after_h":
            continue
        rec = (ex["scene_id"], ex["transform"], ex["png"],
               ex["boxes"], ex["pair_relations"])
        if ex["scene_id"] in split["train"]:
            pd_.train.append(rec)
        elif ex["scene_id"] in split["validation"]:
            pd_.val.append(rec)
        elif ex["scene_id"] in split["holdout"]:
            pd_.holdout.append(rec)
    return pd_


def rel_label(pair_rels, a, b):
    """Frozen label rule: primary axis relation (h then v). None = unlabeled."""
    pr = pair_rels[f"{a}>{b}"]
    if pr["left_of"]:
        return 0
    if pr["right_of"]:
        return 1
    if pr["above"]:
        return 2
    if pr["below"]:
        return 3
    return None


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------
class PilotRunner:
    def __init__(self, freeze: dict, data_dir: Path, out: Path,
                 tiny: bool = False):
        self.freeze = freeze["pilot"]
        self.data_dir = data_dir
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        self.device = "cpu" if tiny else "cuda"
        self.tiny = tiny
        self.model = None
        self.processor = None
        self.enc = None
        self.head = None
        self.log_f = open(self.out / "run.log", "w", encoding="utf-8")

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.log_f.write(line + "\n")
        self.log_f.flush()

    # ---------------- model ----------------
    def load_model(self):
        if self.tiny:
            from transformers import Qwen3VLConfig, Qwen3VLForConditionalGeneration
            cfg = Qwen3VLConfig(
                vision_config={"depth": 2, "hidden_size": 64,
                               "num_heads": 4, "intermediate_size": 128,
                               "out_hidden_size": FEAT_DIM, "patch_size": 28,
                               "spatial_merge_size": 2,
                               "num_position_embeddings": 4096,
                               "temporal_patch_size": 2,
                               "deepstack_visual_indexes": [1]},
                text_config={"hidden_size": 128, "num_hidden_layers": 2,
                             "num_attention_heads": 4,
                             "num_key_value_heads": 2,
                             "intermediate_size": 256,
                             "vocab_size": 151936,
                             "rope_scaling": {"type": "mrope",
                                              "mrope_section": [16, 12, 12]}},
                hidden_size=128)
            self.model = Qwen3VLForConditionalGeneration(cfg).to(self.device)
        else:
            from transformers import (Qwen3VLForConditionalGeneration,
                                      AutoProcessor)
            bb = self.freeze["backbone"]
            self.log(f"loading {bb['name']} @ {bb['revision'][:8]} bf16 sdpa")
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                bb["name"], revision=bb["revision"],
                torch_dtype=torch.bfloat16, attn_implementation="sdpa",
                device_map="cuda")
            self.processor = AutoProcessor.from_pretrained(
                bb["name"], revision=bb["revision"],
                image_token="<|image_pad|>", video_token="<|video_pad|>")
        for p in self.model.parameters():
            p.requires_grad_(False)
        self.log("model loaded; params frozen pending vision LoRA")

    def attach_lora(self):
        from peft import LoraConfig, get_peft_model
        lc = self.freeze["backbone"]["lora"]
        cfg = LoraConfig(
            r=lc["vision_rank"], lora_alpha=lc["vision_alpha"],
            lora_dropout=lc["vision_dropout"],
            target_modules=lc["vision_targets"] + lc["vision_mlp_targets"],
            bias="none", task_type="CAUSAL_LM")
        self.model = get_peft_model(self.model, cfg)
        n = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        self.log(f"vision LoRA attached (qkv/proj/c_fc/c_proj r=16); "
                 f"trainable: {n:,}")
        # Common-init snapshot: every arm must start from the SAME LoRA
        # state (Amendment B3 init-equivalence). train_run() restores this
        # before training so arms differ ONLY in data/loss, never in
        # starting point.
        self.lora_init = {
            n: p.detach().clone()
            for n, p in self.model.named_parameters() if p.requires_grad}
        return n

    # ---------------- features (cached per image) ----------------
    def image_features(self, image_path):
        """Qwen3 deepstack features for one image -> (feat, grid)."""
        if self.tiny:
            from PIL import Image as PILImage
            img = PILImage.open(self.data_dir / image_path).convert("RGB")
            # tiny: fake 5D pixel tensor matching the tiny vision contract
            pix = torch.randn(1, 3, 2, 2 * 28, 2 * 28, device=self.device)
            grid = torch.tensor([[1, 2, 2]], device=self.device)
            with torch.no_grad():
                _, deep = self.model.visual(pix, grid_thw=grid)
            return deep[0], grid
        from PIL import Image as PILImage
        img = PILImage.open(self.data_dir / image_path).convert("RGB")
        # text="" (not None): Qwen3VLProcessor.__call__ wraps text in a list
        # and iterates self.image_token over each item — None would crash
        # (verified 2026-08-15 on the GPU box with the frozen revision).
        inp = self.processor(images=img, text="", return_tensors="pt")
        pix = inp["pixel_values"].to(self.device, dtype=torch.bfloat16)
        grid = inp["image_grid_thw"].to(self.device)
        # NO no_grad here (real path): the frozen design (Amendment B4/
        # ARCHITECTURE_CRITIQUE) requires vision-LoRA gradients to reach the
        # backbone from BOTH objectives. no_grad silently froze the LoRA
        # (grads never flowed); evals disable autograd at the call site.
        _, deep = self.model.visual(pix, grid_thw=grid)
        return deep[0], grid

    def pooled(self, feat, grid, boxes, obj_id):
        """mean-pool over the object box's merged-grid cell.

        Layout verified (2026-08-14, real Qwen3-VL forward): deepstack
        features are POST-MERGE, shape (n_merged, out_hidden), same layout
        as image_embeds. n_merged = (H_feat/2) x (W_feat/2) where
        H_feat/W_feat are the pre-merge grid dims from image_grid_thw and
        merge size = 2. Box center -> merged cell via canvas scale.

        .float(): deepstack features arrive bf16 (model bf16); the frozen
        PairEncoder spec is default fp32 init — cast here so the encoder
        sees fp32 (dtype-mismatch fix, 2026-08-15, verified on GPU box).
        """
        h_feat, w_feat = grid[0, 1].item(), grid[0, 2].item()
        mh, mw = h_feat // 2, w_feat // 2   # merged grid (merge size 2)
        cx, cy, _ = boxes[obj_id]
        canvas = self.freeze["data"]["canvas"]
        c = (min(int(cx / canvas[0] * mw), mw - 1),
             min(int(cy / canvas[1] * mh), mh - 1))
        idx = c[1] * mw + c[0]
        return feat[idx].unsqueeze(0).float()

    def pair_logits_z(self, image_path, boxes, a, b):
        feat, grid = self.image_features(image_path)
        va = self.pooled(feat, grid, boxes, a)
        vb = self.pooled(feat, grid, boxes, b)
        z = self.enc(va, vb)
        return self.head(z), z

    # ---------------- training ----------------
    # structural values: "none" | "equivariance" | "latent_invariance" |
    #                    "output_consistency" | "wrong_geometry"
    KNOWN_STRUCTURAL = ("none", "equivariance", "latent_invariance",
                        "output_consistency", "wrong_geometry")

    def train_run(self, name, examples, lam, structural, run_dir, seed):
        assert structural in self.KNOWN_STRUCTURAL, \
            f"UNKNOWN STRUCTURAL {structural!r} — harness bug, not protocol"
        # Restore the common-init LoRA state (Amendment B3): every arm
        # starts from the same vision-LoRA weights; only enc/head (re-init
        # below) and the data/loss treatment differ between arms.
        with torch.no_grad():
            for n, p in self.model.named_parameters():
                if p.requires_grad:
                    p.copy_(self.lora_init[n])
        torch.manual_seed(seed)
        self.enc = PairEncoder().to(self.device)
        self.head = RelationHead().to(self.device)
        opt = torch.optim.AdamW(
            list(self.enc.parameters()) + list(self.head.parameters())
            + [p for n, p in self.model.named_parameters()
               if p.requires_grad], lr=1e-4)
        pairs = []
        for (sid, tr, png, boxes, pr) in examples:
            for a in boxes:
                for b in boxes:
                    if a == b:
                        continue
                    y = rel_label(pr, a, b)
                    if y is not None:
                        pairs.append((png, boxes, a, b, y, tr))
        self.log(f"[{name}] {len(pairs)} labeled pairs; lam={lam}; "
                 f"structural={structural}")
        epochs = self.freeze["optimization"]["epochs"]
        batch = self.freeze["optimization"]["batch_size"]
        for ep in range(epochs):
            torch.manual_seed(seed + ep)
            idx = torch.randperm(len(pairs))
            n_steps = len(idx) // batch
            for st in range(n_steps):
                sel = idx[st * batch:(st + 1) * batch]
                opt.zero_grad()
                tot = torch.tensor(0.0, device=self.device)
                n = 0
                for i in sel:
                    png, boxes, a, b, y, tr = pairs[i.item()]
                    logits, z = self.pair_logits_z(png, boxes, a, b)
                    tot = tot + loss_answer(
                        logits, torch.tensor([y], device=self.device))
                    rho_vec = RHO_VEC[tr]
                    if structural == "equivariance" and lam is not None:
                        ztx = [s * zk for s, zk in zip(rho_vec, z)]
                        tot = tot + lam * loss_equivariance(z, ztx, rho_vec)
                    elif structural == "wrong_geometry" and lam is not None:
                        # WRONG predeclared rho applied to the SAME z(x) and
                        # z(Tx) — same loss form as equiorient, wrong action.
                        wrho = WRONG_RHO_VEC[tr]
                        ztx = [s * zk for s, zk in zip(wrho, z)]
                        tot = tot + lam * loss_equivariance(z, ztx, wrho)
                    elif structural == "latent_invariance" and lam:
                        ztx = [zk for zk in z]
                        tot = tot + lam * loss_latent_invariance(z, ztx)
                    elif structural == "output_consistency" and lam:
                        tot = tot + lam * loss_output_consistency(
                            logits, logits.detach())
                    n += 1
                (tot / max(n, 1)).backward()
                opt.step()
            self.log(f"[{name}] epoch {ep + 1}/{epochs} done")
        val_acc = self.eval_scenes(self.freeze["data"]["scenes_validation"])
        self.log(f"[{name}] VAL accuracy (scene_0010-0013): {val_acc:.4f}")
        return val_acc

    def eval_scenes(self, scene_ids, voh_only=False, corrupted=False):
        m = json.load(open(self.data_dir / "manifest.json", encoding="utf-8"))
        correct = total = 0
        for ex in m["examples"]:
            if ex["scene_id"] not in scene_ids:
                continue
            if voh_only and ex["transform"] != "v_after_h":
                continue
            if not voh_only and ex["transform"] not in (
                    "identity", "hflip", "vflip"):
                continue
            for a in ex["boxes"]:
                for b in ex["boxes"]:
                    if a == b:
                        continue
                    y = rel_label(ex["pair_relations"], a, b)
                    if y is None:
                        continue
                    # no_grad: evaluation never builds autograd graphs
                    # (feature extraction is now grad-enabled in the
                    # training path, so evals must opt out explicitly).
                    with torch.no_grad():
                        logits, z = self.pair_logits_z(ex["png"],
                                                        ex["boxes"], a, b)
                        if corrupted:
                            z = [zk * 0.0 for zk in z]
                            logits = self.head(z)
                    correct += int(logits.argmax(-1).item() == y)
                    total += 1
        return correct / max(total, 1)

    def eval_voh_deep(self, scene_ids):
        """Frozen primary metrics on the held-out V o H (one call per arm,
        post-selection): returns (both_correct, latent_equivariance_error).

        - paired_both_correct_VoH = P(normal-correct AND transformed obeys
          the law), joined per pair on the SAME object ids across the
          identity and v_after_h images of the same scene.
        - latent_equivariance_error_VoH = mean || rho(V o H) z(x) - z(Tx) ||^2
          with the CORRECT predeclared rho; 0 iff z obeys the algebra on the
          unseen composition. (Missing from run #2 — harness gap closed.)
        """
        m = json.load(open(self.data_dir / "manifest.json", encoding="utf-8"))
        by_scene = {}
        for ex in m["examples"]:
            by_scene.setdefault(ex["scene_id"], {}).setdefault(
                ex["transform"], ex)
        both_c = tot_b = 0
        err_sum = err_n = 0
        rho_vh = torch.tensor(RHO_VEC["v_after_h"], device=self.device)
        for ex in m["examples"]:
            if ex["scene_id"] not in scene_ids or ex["transform"] != "v_after_h":
                continue
            id_ex = by_scene.get(ex["scene_id"], {}).get("identity")
            if id_ex is None:
                continue
            for a in ex["boxes"]:
                for b in ex["boxes"]:
                    if a == b:
                        continue
                    y_t = rel_label(ex["pair_relations"], a, b)
                    y_n = rel_label(id_ex["pair_relations"], a, b)
                    if y_t is None or y_n is None:
                        continue
                    with torch.no_grad():
                        lt, zt = self.pair_logits_z(ex["png"], ex["boxes"],
                                                    a, b)
                        ln, zn = self.pair_logits_z(id_ex["png"],
                                                    id_ex["boxes"], a, b)
                    corr_t = int(lt.argmax(-1).item() == y_t)
                    corr_n = int(ln.argmax(-1).item() == y_n)
                    both_c += int(corr_t and corr_n)
                    tot_b += 1
                    err = sum(((s * zk - ztk) ** 2).mean().item()
                              for s, zk, ztk in zip(rho_vh, zn, zt))
                    err_sum += err
                    err_n += 1
        both = both_c / max(tot_b, 1)
        err = err_sum / max(err_n, 1)
        return both, err

    def eval_depth_probe(self, val_scene_ids, holdout_scene_ids):
        """Amendment C (2026-08-15, orchestrator-approved): held-out
        relation-family transfer via linear probe on z.

        Fit LogisticRegression on z (concat of the four typed blocks) from
        VALIDATION-scene depth pairs (identity images); evaluate on
        HOLD-OUT-scene depth pairs (in_front_of/behind). Depth labels never
        appear in training supervision. Prediction: EquiOrient's rho keeps
        z_d invariant under H/V, so its equivariance loss forces z_d to
        carry depth geometry -> probe transfers; controls with no rho
        shaping stay near chance. Returns holdout probe accuracy (NaN if
        too few val depth pairs).
        """
        from sklearn.linear_model import LogisticRegression
        m = json.load(open(self.data_dir / "manifest.json", encoding="utf-8"))
        by_scene = {}
        for ex in m["examples"]:
            by_scene.setdefault(ex["scene_id"], {}).setdefault(
                ex["transform"], ex)

        def z_of(sid):
            ex = by_scene.get(sid, {}).get("identity")
            if ex is None:
                return []
            out = []
            for a in ex["boxes"]:
                for b in ex["boxes"]:
                    if a == b:
                        continue
                    pr = ex["pair_relations"].get(f"{a}>{b}")
                    if pr is None:
                        continue
                    if pr.get("in_front_of"):
                        yd = 0
                    elif pr.get("behind"):
                        yd = 1
                    else:
                        continue
                    with torch.no_grad():
                        _, z = self.pair_logits_z(ex["png"], ex["boxes"],
                                                  a, b)
                    out.append((torch.cat(z, dim=-1).squeeze(0).cpu().numpy(),
                                yd))
            return out

        tr = [r for sid in val_scene_ids for r in z_of(sid)]
        if len(tr) < 10:
            return float("nan")
        clf = LogisticRegression(max_iter=1000)
        clf.fit(np.array([r[0] for r in tr]), np.array([r[1] for r in tr]))
        te = [r for sid in holdout_scene_ids for r in z_of(sid)]
        if not te:
            return float("nan")
        return float(clf.score(np.array([r[0] for r in te]),
                               np.array([r[1] for r in te])))

    # ---------------- main ----------------
    def run(self):
        t0 = time.time()
        self.load_model()
        self.attach_lora()
        data = load_pilot_data(self.data_dir / "manifest.json")
        freeze = self.freeze
        results = {}
        # PRE-FLIGHT: one forward + init-equivalence snapshot
        ex0 = data.train[0]
        self.log(f"PRE-FLIGHT: forward on {ex0[2]}")
        self.train_run("preflight_smoke", [ex0], None, "none",
                       self.out / "preflight", seed=1)
        # ---- non-structural arms (1 run each) ----
        for arm, filt in [("ordinary_sft_lora", "identity"),
                          ("augmentation_only", None)]:
            exs = data.train if filt is None else \
                [e for e in data.train if e[1] == "identity"]
            rd = self.out / arm
            rd.mkdir(parents=True, exist_ok=True)
            acc = self.train_run(arm, exs, None, "none", rd,
                                 seed=20260814)
            results[arm] = {"val_acc": acc, "lambda": None}
        # ---- structural arms: lambda grid ----
        grid = freeze["losses"]["structural_loss_weight_grid"]
        # arm name -> structural loss key ("equiorient" is the equivariance
        # arm; a plain-name pass-through silently dropped the loss before
        # 2026-08-15 — see decision log "pilot run #1 invalid").
        STRUCTURAL_OF = {"output_consistency": "output_consistency",
                         "latent_invariance": "latent_invariance",
                         "equiorient": "equivariance"}
        lam_scores = {}
        for arm in ["output_consistency", "latent_invariance", "equiorient"]:
            lam_scores[arm] = {}
            for lam in grid:
                rd = self.out / f"{arm}__lam{lam}"
                rd.mkdir(parents=True, exist_ok=True)
                acc = self.train_run(arm, data.train, lam,
                                     STRUCTURAL_OF[arm], rd, seed=20260814)
                lam_scores[arm][lam] = acc
                results[f"{arm}__lam{lam}"] = {"val_acc": acc, "lambda": lam}
        selected = {a: min(grid, key=lambda g: (-lam_scores[a][g], g))
                    for a in lam_scores}
        for a, s in selected.items():
            self.log(f"LAMBDA SELECT {a}: {lam_scores[a]} -> {s}")
        # ---- selected-λ final runs + SINGLE per-arm holdout eval ----
        # Each causal-comparison arm is re-trained ONCE at its selected λ
        # (fresh common-init via train_run's LoRA restore) and evaluated on
        # the held-out V o H exactly once — never used for selection.
        causal_arms = [
            ("augmentation_only", None, "none"),
            ("output_consistency", selected["output_consistency"],
             "output_consistency"),
            ("latent_invariance", selected["latent_invariance"],
             "latent_invariance"),
            ("equiorient", selected["equiorient"], "equivariance"),
            ("wrong_geometry_equiorient", selected["equiorient"],
             "wrong_geometry"),
        ]
        self.log("HOLDOUT EVAL: selected-lambda arms, scene_0014-0016 V o H -- "
                 "exactly once per arm, after selection")
        for arm, lam, structural in causal_arms:
            rd = self.out / f"{arm}__selected"
            rd.mkdir(parents=True, exist_ok=True)
            acc = self.train_run(arm, data.train, lam, structural, rd,
                                 seed=20260814)
            ho = self.eval_scenes(freeze["data"]["scenes_holdout"],
                                  voh_only=True)
            ho_c = self.eval_scenes(freeze["data"]["scenes_holdout"],
                                    voh_only=True, corrupted=True)
            both_c, lat_err = self.eval_voh_deep(
                freeze["data"]["scenes_holdout"])
            depth_acc = self.eval_depth_probe(
                freeze["data"]["scenes_validation"],
                freeze["data"]["scenes_holdout"])
            self.log(f"[{arm}] selected-lambda val {acc:.4f} | holdout V o H "
                     f"{ho:.4f} | z-corrupted {ho_c:.4f} | "
                     f"both_correct_VoH {both_c:.4f} | "
                     f"latent_eq_err_VoH {lat_err:.6f} | "
                     f"depth_probe_holdout {depth_acc:.4f}")
            results[arm] = {"val_acc": acc, "lambda": lam,
                            "holdout_VoH_accuracy": ho,
                            "holdout_VoH_accuracy_z_corrupted": ho_c,
                            "causal_ablation_delta": ho - ho_c,
                            "paired_both_correct_VoH": both_c,
                            "latent_equivariance_error_VoH": lat_err,
                            "depth_probe_holdout_acc": depth_acc}
        matrix = {
            "freeze_commit": "91185d7",
            "backbone": freeze["backbone"]["name"],
            "lambda_selected": selected,
            "per_arm_val": results,
            "elapsed_seconds": time.time() - t0,
        }
        (self.out / "result_matrix.json").write_text(
            json.dumps(matrix, indent=1), encoding="utf-8")
        self.log(f"DONE {time.time() - t0:.0f}s -> {self.out / 'result_matrix.json'}")
        print(json.dumps(matrix, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tiny", action="store_true")
    a = ap.parse_args()
    freeze = yaml.safe_load(open(a.freeze, encoding="utf-8"))
    r = PilotRunner(freeze, Path(a.data), Path(a.out), tiny=a.tiny)
    r.run()


if __name__ == "__main__":
    main()
