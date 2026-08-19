"""EquiOrient NO-BOX six-arm training harness (D4, 8-way).

Removes the ground-truth bounding-box shortcut from the Phase-2 study:

  OLD (boxed): pooled(feat, grid, boxes, obj) extracts the exact grid
               cell at each target's GT box center; the model is handed
               both target positions -> displacement -> label.
  NEW (no-box): a learned single-query cross-attention pools over ALL
               visual tokens of the full image; the model must itself
               locate the target pair and read the compass relation.
               NO boxes, NO centers, NO displacement are ever provided.

Arms (matched; only the structural objective differs):
  augmentation | equiorient | wrong_geometry  (primary)
  output_consistency | latent_invariance | original_sft  (secondary if used)

Sparse exposure: each training scene contributes identity + exactly one
generator (H or R, 50/50). Structural losses couple z(x) (identity
image, full-image tokens) with z(gx) (transform image, full-image
tokens).

Deterministic: all seeds fixed before any stochastic init; dataset
noise seeded via SHA-256 (see equiorient.data.manifests).

CLI:
  python -m equiorient.experiments.train_nobox --mode dev \
      --arm equiorient --seed 101 --n_train 128
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from equiorient.algebra.d4 import ELEMENTS, GENERATORS, UNSEEN
from equiorient.algebra.label_action import LABELS
from equiorient.models.full_image_relation import (N_CLASSES,
                                                   FullImagePool,
                                                   NoBoxEncoder,
                                                   RelationHead8)
from equiorient.objectives.answer import loss_answer
from equiorient.objectives.output_consistency import loss_output_consistency
from equiorient.objectives.invariance import loss_invariance
from equiorient.objectives.equiorient import (loss_equiorient, rho_vec_of,
                                              wrong_rho_vec_of)

ARMS = ("original_sft", "augmentation", "output_consistency",
        "latent_invariance", "equiorient", "wrong_geometry")
STRUCTURAL_OF = {"output_consistency": "output_consistency",
                 "latent_invariance": "invariance",
                 "equiorient": "equiorient",
                 "wrong_geometry": "wrong_geometry"}
KNOWN = ("none", "output_consistency", "invariance", "equiorient",
         "wrong_geometry")


def load_manifest(data_dir: Path) -> dict:
    return json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))


def subset_scenes(manifest: dict, split: str, n: int | None):
    ids = []
    for e in manifest["examples"]:
        if e["split"] == split and e["scene_id"] not in ids:
            ids.append(e["scene_id"])
    return set(ids[:n]) if n is not None else set(ids)


class NoBoxRunner:
    """Full-image (no-box) Phase-2 runner. Mirrors Phase2Runner but the
    forward path never reads boxes/centers/displacement."""

    def __init__(self, data_dir: Path, out: Path, tiny: bool = False):
        self.data_dir = data_dir
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        self.device = "cpu" if tiny else "cuda"
        self.tiny = tiny
        self.backbone = "qwen3"
        self.model = None
        self.processor = None
        self.enc = None
        self.head = None
        self._pix_cache: dict = {}
        self._feat_cache: dict = {}
        self._attn_cache: dict = {}
        self._diag_boxes = True
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
        else:
            from transformers import (Qwen3VLForConditionalGeneration,
                                      AutoProcessor)
            bb = "Qwen/Qwen3-VL-8B-Instruct"
            rev = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                bb, revision=rev, torch_dtype=torch.bfloat16,
                attn_implementation="sdpa", device_map="cuda")
            self.processor = AutoProcessor.from_pretrained(
                bb, revision=rev, image_token="<|image_pad|>",
                video_token="<|video_pad|>")
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
    # full-image features (NO boxes anywhere in this path)
    # ------------------------------------------------------------------ #
    def image_input(self, path):
        if path not in self._pix_cache:
            if self.tiny:
                pix = torch.randn(1, 3, 2, 2 * 28, 2 * 28, device=self.device)
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
            _, deep = out
            feat = deep[0]
        if not requires_grad:
            self._feat_cache[path] = (feat, grid)
        return feat, grid

    def image_state(self, path, grad=False):
        """z(x) = Encoder(full-image tokens). NO boxes."""
        feat, grid = self.vision_features(path, requires_grad=grad)
        return self.enc(feat.float())

    def image_logits(self, path, grad=False):
        zx, zy = self.image_state(path, grad)
        return self.head(zx, zy), (zx, zy)

    # ------------------------------------------------------------------ #
    # training
    # ------------------------------------------------------------------ #
    def train(self, arm: str, examples: list, lam: float | None,
              epochs: int, batch: int, seed: int, lr: float = 1e-4) -> dict:
        """examples: list of dicts {scene_id, transform, png, label_idx}.
        NOTE: examples intentionally contain NO boxes/centers/delta."""
        with torch.no_grad():
            for n, p in self.model.named_parameters():
                if p.requires_grad:
                    p.copy_(self.lora_init[n])
        self._feat_cache = {}
        self.enc = NoBoxEncoder(FullImagePool()).to(self.device)
        self.head = RelationHead8().to(self.device)
        structural = STRUCTURAL_OF.get(arm, "none")
        assert structural in KNOWN, f"arm {arm} -> {structural}"
        opt = torch.optim.AdamW(
            list(self.enc.parameters()) + list(self.head.parameters())
            + [p for n, p in self.model.named_parameters()
               if p.requires_grad], lr=lr)
        pairs = [(e["scene_id"], e["transform"], e["png"],
                  e["label_idx"]) for e in examples]
        use_transform = arm != "original_sft"
        need_structural = structural != "none"
        by_scene = {}
        for e in examples:
            by_scene.setdefault(e["scene_id"], []).append(e)
        history = {"answer": [], "structural": [], "train_acc": []}
        for ep in range(epochs):
            torch.manual_seed(seed + ep)
            idx = torch.randperm(len(pairs))
            n_steps = max(len(idx) // batch, 1)
            ans_sum = struct_sum = 0.0
            struct_n = 0
            corr = 0
            tot_n = 0
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
                    sid, g, png, y = pairs[i.item()]
                    if use_transform or need_structural:
                        logits_t, zt = self.image_logits(png, grad=True)
                        id_ex, (fx, gx) = id_feat[sid]
                        zx = self.enc(fx.float())
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
                        if use_transform:
                            y_id = next(e for e in by_scene[sid]
                                        if e["transform"] == "I")["label_idx"]
                            tot = tot + loss_answer(
                                logits_x,
                                torch.tensor([y_id], device=self.device))
                    else:  # original_sft: identity only
                        logits_x, _ = self.image_logits(png, grad=True)
                        tot = tot + loss_answer(
                            logits_x,
                            torch.tensor([y], device=self.device))
                        ans_sum += float(loss_answer(
                            logits_x,
                            torch.tensor([y], device=self.device)).detach())
                    n += 1
                (tot / max(n, 1)).backward()
                opt.step()
            # train-pair accuracy (answer on the transform image).
            # Refresh the feature cache first so the diagnostic is measured
            # under the CURRENT (post-update) LoRA weights, not a stale
            # cache from an earlier epoch's model state.
            self.model.eval()
            self._feat_cache = {}
            with torch.no_grad():
                for i in idx:
                    sid, g, png, y = pairs[i.item()]
                    l, _ = self.image_logits(png, grad=False)
                    corr += int(l.argmax(-1).item() == y)
                    tot_n += 1
            self.model.train()
            acc_tr = corr / max(tot_n, 1)
            mean_struct = struct_sum / max(struct_n, 1)
            self.log(f"[{arm}] epoch {ep + 1}/{epochs} "
                     f"(ans {ans_sum / max(n_steps, 1):.4f}, "
                     f"struct {mean_struct:.6f}, train_acc {acc_tr:.3f})")
            # per-epoch checkpoint: a killed run never loses its curve.
            ckpt = {"arm": arm, "seed": seed, "epoch": ep + 1,
                    "answer": round(ans_sum / max(n_steps, 1), 6),
                    "structural": round(mean_struct, 8),
                    "train_acc": round(acc_tr, 4)}
            ckpt_path = self.out / f"progress_{arm}_s{seed}.jsonl"
            with open(ckpt_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ckpt) + "\n")
            if need_structural and lam is not None and struct_n:
                if mean_struct < 1e-6:
                    raise RuntimeError(
                        f"MANIPULATION CHECK FAILED: structural loss "
                        f"{mean_struct:.3e} for {arm}")
            history["answer"].append(round(ans_sum / max(n_steps, 1), 6))
            history["structural"].append(round(mean_struct, 8))
            history["train_acc"].append(round(acc_tr, 4))
        return history

    # ------------------------------------------------------------------ #
    # evaluation (dev/test scenes, all 8 views) — NO boxes
    # ------------------------------------------------------------------ #
    def evaluate(self, manifest: dict, split: str,
                 collect_attn: bool = False) -> dict:
        self._feat_cache = {}
        self._attn_cache = {}
        self.model.eval()
        per_g: dict[str, dict] = {}
        for g in ELEMENTS:
            per_g[g] = {"correct": 0, "total": 0}
        attn_diag = {"pair_mass": [], "pair_in_top4": []}
        with torch.no_grad():
            for e in manifest["examples"]:
                if e["split"] != split:
                    continue
                g = e["transform"]
                feat, grid = self.vision_features(e["png"], requires_grad=False)
                zx, zy, attn = self.enc.pool(feat.float())
                logits = self.head(zx, zy)
                if collect_attn:
                    self._attn_cache[e["png"]] = attn.detach().cpu()
                if self._diag_boxes:
                    from equiorient.analysis.attn_diagnostic import (
                        attention_mass_diag_from_example)
                    d = attention_mass_diag_from_example(
                        attn, e, int(grid[0][2]), int(grid[0][1]))
                    if d is not None and d.get("pair_mass") is not None:
                        attn_diag["pair_mass"].append(d["pair_mass"])
                        attn_diag["pair_in_top4"].append(d["pair_in_top4"])
                per_g[g]["total"] += 1
                per_g[g]["correct"] += int(
                    logits.argmax(-1).item() == LABELS.index(e["label"]))
        acc = {g: per_g[g]["correct"] / max(per_g[g]["total"], 1)
               for g in ELEMENTS}
        unseen = float(np.mean([acc[g] for g in UNSEEN]))
        worst = float(min(acc[g] for g in UNSEEN))
        out = {"per_transform": {g: round(acc[g], 4) for g in ELEMENTS},
               "unseen_accuracy": round(unseen, 4),
               "worst_unseen_accuracy": round(worst, 4),
               "n_per_transform": {g: per_g[g]["total"] for g in ELEMENTS}}
        if self._diag_boxes and attn_diag["pair_mass"]:
            out["attention_diag"] = {
                "mean_pair_mass": round(
                    float(np.mean(attn_diag["pair_mass"])), 4),
                "pair_in_top4_pct": round(
                    100.0 * float(np.mean(attn_diag["pair_in_top4"])), 1),
                "n": len(attn_diag["pair_mass"])}
        return out

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.log_f.write(line + "\n")
        self.log_f.flush()


def make_examples(manifest: dict, scene_ids: set) -> list:
    """One labeled example per (scene, view) for the given scene ids.
    DELIBERATELY excludes boxes/centers/delta: the no-box path must not
    be able to read ground-truth locations from the example dict."""
    out = []
    for e in manifest["examples"]:
        if e["scene_id"] in scene_ids:
            out.append({
                "scene_id": e["scene_id"],
                "transform": e["transform"],
                "png": e["png"],
                "label_idx": LABELS.index(e["label"]),
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="dev", choices=["tiny", "dev", "confirmatory"])
    ap.add_argument("--arm", default="augmentation", choices=list(ARMS))
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--n_train", type=int, default=128)
    ap.add_argument("--lambda", dest="lam", type=float, default=1.0)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--data", default="results/phase2_data")
    ap.add_argument("--out", default="results/equiorient_no_box/dev")
    ap.add_argument("--eval_split", default="dev")
    a = ap.parse_args()

    import random
    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(a.seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    data_dir = Path(a.data)
    manifest = load_manifest(data_dir)
    runner = NoBoxRunner(data_dir, Path(a.out), tiny=(a.mode == "tiny"))
    runner.load_model()
    runner.attach_lora()

    if a.mode == "tiny":
        train_ids = subset_scenes(manifest, "train", 8)
        ex = make_examples(manifest, train_ids)
        hist = runner.train(a.arm, ex, a.lam, a.epochs, a.batch, a.seed, a.lr)
        ev = runner.evaluate(manifest, "dev")
    else:
        train_ids = subset_scenes(manifest, "train", a.n_train)
        ex = make_examples(manifest, train_ids)
        runner.log(f"train scenes {len(train_ids)} pairs {len(ex)} "
                   f"arm {a.arm} lam {a.lam} lr {a.lr} NO-BOX")
        hist = runner.train(a.arm, ex, a.lam, a.epochs, a.batch, a.seed, a.lr)
        ev = runner.evaluate(manifest, "dev")
        runner.log(f"DEV unseen_accuracy {ev['unseen_accuracy']:.4f} "
                   f"worst {ev['worst_unseen_accuracy']:.4f}")

    eval_split = "test" if a.mode == "confirmatory" else a.eval_split
    ev = runner.evaluate(manifest, eval_split)
    runner.log(f"{eval_split.upper()} unseen_accuracy {ev['unseen_accuracy']:.4f} "
               f"worst {ev['worst_unseen_accuracy']:.4f}")

    import subprocess, hashlib
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=str(REPO), timeout=10).stdout.strip()
    except Exception:
        git_commit = "unknown"
    try:
        manifest_json = (data_dir / "manifest.json").read_bytes()
        dataset_sha = hashlib.sha256(manifest_json).hexdigest()
    except Exception:
        dataset_sha = "unknown"

    result = {"mode": a.mode, "arm": a.arm, "seed": a.seed,
              "n_train": a.n_train, "lambda": a.lam, "lr": a.lr,
              "epochs": a.epochs, "variant": "no_box",
              "train_loss": hist, f"{eval_split}_eval": ev,
              "provenance": {"git_commit": git_commit,
                             "dataset_manifest_sha256": dataset_sha,
                             "backbone": runner.backbone,
                             "torch": torch.__version__}}
    (runner.out / f"result_{a.arm}_s{a.seed}.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
