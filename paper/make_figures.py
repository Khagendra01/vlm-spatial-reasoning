#!/usr/bin/env python3
"""EquiOrient paper â€” figures for the corrected manuscript.

Reads paper/paper_numbers.json (from extract_numbers.py). Produces:
  paper/figures/fig1_rho.png   (per-transform latent error, correct rho)
  paper/figures/fig2_contrast.png (correct vs wrong rho per arm)
  paper/figures/fig3_probe.png (depth probes full + z_d)
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
D = json.loads((REPO / "paper" / "paper_numbers.json").read_text(encoding="utf-8"))
FIG = REPO / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

V2 = D["V2"]
ARMS = ["augmentation_only", "output_consistency", "latent_invariance",
        "equiorient", "wrong_geometry_equiorient"]
SHORT = ["augment", "out-cons", "lat-inv", "equiorient", "wrong-geo"]
C7, C2, C3 = "#1f77b4", "#d62728", "#2ca02c"

def col(key):
    return [V2["per_arm_val"][a][key] for a in ARMS]

# fig1: per-transform latent error (correct rho), log scale
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
x = np.arange(len(ARMS))
w = 0.27
for i, (tr, lab) in enumerate([("hflip", "rho_H"),
                               ("vflip", "rho_V"),
                               ("v_after_h", "rho_{V o H} (held out)")]):
    vals = [V2["per_arm_val"][a]["rho_per_transform"]["correct"][tr]
            for a in ARMS]
    ax.bar(x + (i - 1) * w, vals, w, label=lab,
           color=[C7, C2, C3][i], alpha=0.9)
ax.set_yscale("log")
ax.set_ylim(1e-3, 60)
ax.set_xticks(x)
ax.set_xticklabels(SHORT, rotation=18, fontsize=7.5)
ax.set_ylabel("mean equivariance error (log)", fontsize=8)
ax.legend(fontsize=7)
ax.set_title("Latent equivariance error under the correct rho â€” EquiOrient "
             "complies, including on the never-seen composition",
             fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "fig1_rho.png", bbox_inches="tight")
plt.close(fig)

# fig2: correct vs wrong rho per arm (on H)
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
corr = [V2["per_arm_val"][a]["rho_per_transform"]["correct"]["hflip"]
        for a in ARMS]
wrong = [V2["per_arm_val"][a]["rho_per_transform"]["wrong"]["hflip"]
         for a in ARMS]
ax.bar(x - w / 2, corr, w, label="error under correct rho (H)",
       color=C7, alpha=0.9)
ax.bar(x + w / 2, wrong, w, label="error under wrong rho (H)",
       color=C2, alpha=0.9)
ax.set_xticks(x)
ax.set_xticklabels(SHORT, rotation=18, fontsize=7.5)
ax.set_ylabel("mean squared error", fontsize=8)
ax.legend(fontsize=7)
ax.set_title("Correct vs wrong rho on the horizontal reflection â€” "
             "specificity of the learned algebra", fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "fig2_contrast.png", bbox_inches="tight")
plt.close(fig)

# fig3: depth probes (full + z_d)
fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=200)
full = col("depth_probe_holdout_acc")
zd = col("depth_probe_z_d_holdout_acc")
ax.bar(x - w / 2, full, w, label="full-z probe", color=C7, alpha=0.9)
ax.bar(x + w / 2, zd, w, label="z_d-only probe", color=C3, alpha=0.9)
ax.axhline(0.5, color="gray", ls="--", lw=0.8)
ax.set_ylim(0.3, 0.8)
ax.set_xticks(x)
ax.set_xticklabels(SHORT, rotation=18, fontsize=7.5)
ax.set_ylabel("hold-out depth accuracy", fontsize=8)
ax.legend(fontsize=7)
ax.set_title("Depth-family transfer probe â€” flat across all arms "
             "(n=60; dashed line = chance 0.5)",
             fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "fig3_probe.png", bbox_inches="tight")
plt.close(fig)

print("figures written:", sorted(p.name for p in FIG.glob("*.png")))
