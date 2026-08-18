"""EquiOrient Phase-2 six-arm training harness (D4, 8-way).

Modes:
  --tiny            CPU smoke on a tiny random Qwen3-VL (no weights)
  --dev             one-seed development run (augmentation + equiorient,
                    primary N=512) with the full dev-split evaluation
  (--confirmatory later, five-seed job array)

CLI:
  python -m equiorient.experiments.train --mode dev --arm augmentation --seed 101
  python -m equiorient.experiments.train --mode dev --arm equiorient --seed 101

Matched-arms contract (identical in every arm): Qwen3 deepstack ->
region pooling -> PairEncoderV2 -> z=[z_x;z_y] -> RelationHead8 (forced);
vision LoRA qkv/proj/c_fc/c_proj; text backbone + lm_head frozen;
common-init LoRA restore per arm; identical optimizer budget on the
same image pairs; the only difference is the structural objective.

Sparse exposure: each training scene contributes identity + exactly one
generator (H or R, 50/50). Structural losses couple z(x) (identity
image) with z(gx) (transform image) on the same object pair.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import ELEMENTS, GENERATORS, UNSEEN
from equiorient.algebra.label_action import LABELS
from equiorient.models.pair_encoder_v2 import (N_CLASSES, PairEncoderV2,
                                               RelationHead8)
from equiorient.objectives.answer import loss_answer
from equiorient.objectives.output_consistency import loss_output_consistency
from equiorient.objectives.invariance import loss_invariance
from equiorient.objectives.equiorient import (loss_equiorient, rho_vec_of,
                                              wrong_rho_vec_of)

ARMS = ("original_sft", "augmentation", "output_consistency",
        "latent_invariance", "equiorient", "wrong_geometry")
# structural key per arm (used to select the loss branch)
STRUCTURAL_OF = {"output_consistency": "output_consistency",
                 "latent_invariance": "invariance",
                 "equiorient": "equiorient",
                 "wrong_geometry": "wrong_geometry"}
KNOWN = ("none", "output_consistency", "invariance", "equiorient",
         "wrong_geometry")


def load_manifest(data_dir: Path) -> dict:
    return json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))


def subset_scenes(manifest: dict, split: str, n: int | None):
    """First n scene ids of a split (or all if n is None)."""
    ids = []
    for e in manifest["examples"]:
        if e["split"] == split and e["scene_id"] not in ids:
            ids.append(e["scene_id"])
    return set(ids[:n]) if n is not None else set(ids)


class Phase2Runner:
    def __init__(self, data_dir: Path, out: Path, tiny: bool = False,
                 backbone: str = "qwen3"):
        self.data_dir = data_dir
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        self.device = "cpu" if tiny else "cuda"
        self.tiny = tiny
        self.backbone = backbone
        self.model = None
        self.processor = None
        self.enc = None
        self.head = None
        self._pix_cache: dict = {}
        self._feat_cache: dict = {}
        self.log_f = open(self.out / "run.log", "w", encoding="utf-8")

    # ------------------------------------------------------------------ #
    # model
    # ------------------------------------------------------------------ #
    def load_model(self):
        if self.tiny:
            from transformers import (Qwen3VLConfig,
                                      Qwen3VLForConditionalGeneration)
            cfg = Qwen3VLConfig(
                vision_config={"depth": 2, "hidden_size": 64,
                               "num_heads": 4, "intermediate_size": 128,
                               "out_hidden_size": 4096, "patch_size": 28,
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
            self.feat_dim = 4096
        elif self.backbone == "qwen2vl":
            from transformers import (Qwen2VLForConditionalGeneration,
                                      AutoProcessor)
            bb = "Qwen/Qwen2-VL-7B-Instruct"
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                bb, torch_dtype=torch.bfloat16,
                attn_implementation="sdpa", device_map="cuda")
            self.processor = AutoProcessor.from_pretrained(bb)
            self.feat_dim = 3584
        else:
            from transformers import (Qwen3VLForConditionalGeneration,
                                      AutoProcessor)
            bb = "Qwen/Qwen3-VL-8B-Instruct"
            rev = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                bb, revision=rev, torch_dtype=torch.bfloat16,
                attn_implementation="sdpa", device_map="cuda")
            self.processor = AutoProcessor.from_pretrained(
                bb, revision=rev, image_token="โฆ",
                video_token="圐")
            self.feat_dim = 4096
        for p in self.model.parameters():
            p.requires_grad_(False)

    def attach_lora(self):
        from peft import LoraConfig, get_peft_model
        lc = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                        target_modules=["qkv", "proj", "c_fc", "c_proj"],
                        bias="none", task_type="CAUSAL_LM")
        self.model = get_peft_model(self.model, lc)
        self.lora_init = {n: p.detach().clone()
                          for n, p in self.model.named_parameters()
                          if p.requires_grad}

    # ------------------------------------------------------------------ #
    # features (cached; Phase-1 optimizations carried over)
    # ------------------------------------------------------------------ #
    def image_input(self, path):
        if path not in self._pix_cache:
            if self.tiny:
                pix = torch.randn(1, 3, 2, 2 * 28, 2 * 28,
                                  device=self.device)
                grid = torch.tensor([[1, 2, 2]], device=self.device)
            else:
                from PIL import Image
                img = Image.open(self.data_dir / path).convert("RGB")
                inp = self.processor(images=img, text="",
                                     return_tensors="pt")
                pix = inp["pixel_values"].to(self.device,
                                             dtype=torch.bfloat16)
                grid = inp["image_grid_thw"].to(self.device)
            self._pix_cache[path] = (pix, grid)
        return self._pix_cache[path]

    def vision_features(self, path, requires_grad):
        if not requires_grad and path in self._feat_cache:
            return self._feat_cache[path]
        pix, grid = self.image_input(path)
        with torch.no_grad() if not requires_grad else torch.enable_grad():
            out = self.model.visual(pix, grid_thw=grid)
            if self.backbone == "qwen2vl":
                # Qwen2-VL returns (features,) tuple
                feat = out[0] if isinstance(out, tuple) else out
            else:
                # Qwen3-VL returns (last_hidden, deepstack_features)
                _, deep = out
                feat = deep[0]
        if not requires_grad:
            self._feat_cache[path] = (feat, grid)
        return feat, grid

    def pooled(self, feat, grid, boxes, obj_id):
        hf, wf = grid[0, 1].item(), grid[0, 2].item()
        mh, mw = hf // 2, wf // 2
        cx, cy, _ = boxes[obj_id]
        canvas = [192, 192]
        c = (min(int(cx / canvas[0] * mw), mw - 1),
             min(int(cy / canvas[1] * mh), mh - 1))
        return feat[c[1] * mw + c[0]].unsqueeze(0).float()

    def pair_state(self, path, boxes, a, b, grad):
        feat, grid = self.vision_features(path, requires_grad=grad)
        va = self.pooled(feat, grid, boxes, a)
        vb = self.pooled(feat, grid, boxes, b)
        return self.enc(va, vb)

    def pair_logits(self, path, boxes, a, b, grad=False):
        zx, zy = self.pair_state(path, boxes, a, b, grad)
        return self.head(zx, zy), (zx, zy)

    # ------------------------------------------------------------------ #
    # training
    # ------------------------------------------------------------------ #
    def train(self, arm: str, examples: list, lam: float | None,
              epochs: int, batch: int, seed: int) -> dict:
        """examples: list of dicts {scene_id, transform, png, boxes,
        label_idx} — one labeled pair per example."""
        with torch.no_grad():
            for n, p in self.model.named_parameters():
                if p.requires_grad:
                    p.copy_(self.lora_init[n])
        self._feat_cache = {}
        self.enc = PairEncoderV2(feat_dim=self.feat_dim).to(self.device)
        self.head = RelationHead8().to(self.device)
        structural = STRUCTURAL_OF.get(arm, "none")
        assert structural in KNOWN, f"arm {arm} -> {structural}"
        opt = torch.optim.AdamW(
            list(self.enc.parameters()) + list(self.head.parameters())
            + [p for n, p in self.model.named_parameters()
               if p.requires_grad], lr=1e-4)
        pairs = [(e["scene_id"], e["transform"], e["png"], e["boxes"],
                  e["label_idx"]) for e in examples]
        use_transform = arm != "original_sft"
        need_structural = structural != "none"
        by_scene = {}
        for e in examples:
            by_scene.setdefault(e["scene_id"], []).append(e)
        history = {"answer": [], "structural": []}
        for ep in range(epochs):
            torch.manual_seed(seed + ep)
            idx = torch.randperm(len(pairs))
            n_steps = max(len(idx) // batch, 1)
            ans_sum = struct_sum = 0.0
            struct_n = 0
            for st in range(n_steps):
                sel = idx[st * batch:(st + 1) * batch]
                opt.zero_grad()
                tot = torch.tensor(0.0, device=self.device)
                n = 0
                # identity features per scene per step (structural arms)
                id_feat = {}
                if use_transform or need_structural:
                    for i in sel:
                        sid = pairs[i.item()][0]
                        if sid in id_feat:
                            continue
                        id_ex = next(e for e in by_scene[sid]
                                     if e["transform"] == "I")
                        id_feat[sid] = (id_ex, self.vision_features(
                            id_ex["png"], requires_grad=True))
                for i in sel:
                    sid, g, png, boxes, y = pairs[i.item()]
                    boxes = {k: v for k, v in boxes.items()}
                    a, b = "a", "b"
                    if use_transform or need_structural:
                        logits_t, zt = self.pair_logits(
                            png, boxes, a, b, grad=True)
                        id_ex, (fx, gx) = id_feat[sid]
                        ib = id_ex["boxes"]
                        vax = self.pooled(fx, gx, ib, "a")
                        vbx = self.pooled(fx, gx, ib, "b")
                        zx = self.enc(vax, vbx)
                        logits_x = self.head(*zx)
                        tot = tot + loss_answer(
                            logits_t, torch.tensor([y], device=self.device))
                        ans_sum += float(loss_answer(
                            logits_t,
                            torch.tensor([y], device=self.device)).detach())
                        if need_structural and lam is not None:
                            if structural == "equiorient":
                                sl = loss_equiorient(
                                    zx, zt, rho_vec_of(g))
                            elif structural == "wrong_geometry":
                                sl = loss_equiorient(
                                    zx, zt, wrong_rho_vec_of(g))
                            elif structural == "invariance":
                                sl = loss_invariance(zx, zt)
                            else:  # output_consistency
                                from equiorient.algebra.label_action import (
                                    label_permutation)
                                perm = label_permutation(g)
                                sl = loss_output_consistency(
                                    logits_t, logits_x, perm)
                            tot = tot + lam * sl
                            struct_sum += float(sl.detach())
                            struct_n += 1
                        # also answer on the identity image (all arms
                        # except original_sft see both views)
                        if use_transform:
                            y_id = next(e for e in by_scene[sid]
                                        if e["transform"] == "I")["label_idx"]
                            tot = tot + loss_answer(
                                logits_x,
                                torch.tensor([y_id], device=self.device))
                    else:  # original_sft: identity only
                        logits_x, _ = self.pair_logits(
                            png, boxes, a, b, grad=True)
                        tot = tot + loss_answer(
                            logits_x,
                            torch.tensor([y], device=self.device))
                        ans_sum += float(loss_answer(
                            logits_x,
                            torch.tensor([y], device=self.device)).detach())
                    n += 1
                (tot / max(n, 1)).backward()
                opt.step()
            mean_struct = struct_sum / max(struct_n, 1)
            self.log(f"[{arm}] epoch {ep + 1}/{epochs} "
                     f"(ans {ans_sum / max(n_steps, 1):.4f}, "
                     f"struct {mean_struct:.6f})")
            if need_structural and lam is not None and struct_n:
                if mean_struct < 1e-6:
                    raise RuntimeError(
                        f"MANIPULATION CHECK FAILED: structural loss "
                        f"{mean_struct:.3e} for {arm}")
            history["answer"].append(round(ans_sum / max(n_steps, 1), 6))
            history["structural"].append(round(mean_struct, 8))
        return history

    # ------------------------------------------------------------------ #
    # evaluation (dev/test scenes, all 8 views)
    # ------------------------------------------------------------------ #
    def evaluate(self, manifest: dict, split: str) -> dict:
        self._feat_cache = {}
        scenes = subset_scenes(manifest, split, None)
        per_g: dict[str, dict] = {}
        for g in ELEMENTS:
            per_g[g] = {"correct": 0, "total": 0}
        with torch.no_grad():
            for e in manifest["examples"]:
                if e["split"] != split:
                    continue
                g = e["transform"]
                logits, _ = self.pair_logits(e["png"], e["boxes"], "a", "b")
                per_g[g]["total"] += 1
                per_g[g]["correct"] += int(
                    logits.argmax(-1).item() == LABELS.index(e["label"]))
        acc = {g: per_g[g]["correct"] / max(per_g[g]["total"], 1)
               for g in ELEMENTS}
        unseen = float(np.mean([acc[g] for g in UNSEEN]))
        worst = float(min(acc[g] for g in UNSEEN))
        return {"per_transform": {g: round(acc[g], 4) for g in ELEMENTS},
                "unseen_accuracy": round(unseen, 4),
                "worst_unseen_accuracy": round(worst, 4),
                "n_per_transform": {g: per_g[g]["total"] for g in ELEMENTS}}

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.log_f.write(line + "\n")
        self.log_f.flush()


def make_examples(manifest: dict, scene_ids: set) -> list:
    """One labeled example per (scene, view) for the given scene ids."""
    out = []
    for e in manifest["examples"]:
        if e["scene_id"] in scene_ids:
            out.append({
                "scene_id": e["scene_id"],
                "transform": e["transform"],
                "png": e["png"],
                "boxes": e["boxes"],
                "label_idx": LABELS.index(e["label"]),
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="dev", choices=["tiny", "dev", "confirmatory"])
    ap.add_argument("--arm", default="augmentation",
                    choices=list(ARMS))
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--n_train", type=int, default=512)
    ap.add_argument("--lambda", dest="lam", type=float, default=1.0)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--data", default="results/phase2_data")
    ap.add_argument("--out", default="results/phase2_dev")
    ap.add_argument("--eval_split", default="dev",
                    help="Split to evaluate on (dev for dev mode, test for confirmatory)")
    ap.add_argument("--backbone", default="qwen3",
                    choices=["qwen3", "qwen2vl"],
                    help="VLM backbone: qwen3 (Qwen3-VL-8B) or qwen2vl (Qwen2-VL-7B)")
    a = ap.parse_args()

    # CRITICAL: Set ALL seeds BEFORE any stochastic initialization
    # (model, LoRA, PairEncoder, optimizer). Same seed must produce the
    # same starting parameters for every arm.
    import random, numpy as np
    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(a.seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    data_dir = Path(a.data)
    manifest = load_manifest(data_dir)
    runner = Phase2Runner(data_dir, Path(a.out), tiny=(a.mode == "tiny"),
                          backbone=a.backbone)
    runner.load_model()
    runner.attach_lora()

    if a.mode == "tiny":
        # tiny: 8 train scenes, eval on 4 dev scenes
        train_ids = subset_scenes(manifest, "train", 8)
        ex = make_examples(manifest, train_ids)
        hist = runner.train(a.arm, ex, a.lam, a.epochs, a.batch, a.seed)
        ev = runner.evaluate(manifest, "dev")
    else:
        train_ids = subset_scenes(manifest, "train", a.n_train)
        ex = make_examples(manifest, train_ids)
        runner.log(f"train scenes {len(train_ids)} pairs {len(ex)} "
                   f"arm {a.arm} lam {a.lam}")
        hist = runner.train(a.arm, ex, a.lam, a.epochs, a.batch, a.seed)
        ev = runner.evaluate(manifest, "dev")
        runner.log(f"DEV unseen_accuracy {ev['unseen_accuracy']:.4f} "
                   f"worst {ev['worst_unseen_accuracy']:.4f}")

    eval_split = "test" if a.mode == "confirmatory" else a.eval_split
    ev = runner.evaluate(manifest, eval_split)
    runner.log(f"{eval_split.upper()} unseen_accuracy {ev['unseen_accuracy']:.4f} "
               f"worst {ev['worst_unseen_accuracy']:.4f}")

    # ---- Provenance metadata embedded in every result JSON ----
    import subprocess, hashlib
    # git commit (if available)
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=str(REPO), timeout=10).stdout.strip()
    except Exception:
        git_commit = "unknown"
    # dataset manifest sha
    try:
        manifest_json = (data_dir / "manifest.json").read_bytes()
        dataset_sha = hashlib.sha256(manifest_json).hexdigest()
    except Exception:
        dataset_sha = "unknown"

    result = {"mode": a.mode, "arm": a.arm, "seed": a.seed,
              "n_train": a.n_train, "lambda": a.lam,
              "train_loss": hist, f"{eval_split}_eval": ev,
              "provenance": {
                  "git_commit": git_commit,
                  "dataset_manifest_sha256": dataset_sha,
                  "backbone": runner.backbone,
                  "torch": torch.__version__,
              }}
    (runner.out / f"result_{a.arm}_s{a.seed}.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
