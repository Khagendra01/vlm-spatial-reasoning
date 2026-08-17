"""Figure generation for Paper 3 Phase 2.

All figures use matplotlib with a clean academic style.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def setup_style():
    """Minimal academic plotting style."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    })


def fig_unseen_accuracy_by_arm(agg: dict, out_dir: Path,
                               title: str = "Unseen-Group Accuracy by Arm"):
    """Bar chart: per-arm unseen accuracy with error bars."""
    import matplotlib.pyplot as plt
    setup_style()

    arms = list(agg.keys())
    means = [agg[a]["mean"] for a in arms]
    stds = [agg[a]["std"] for a in arms]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2",
              "#CCB974", "#64B5CD"]
    bars = ax.bar(arms, means, yerr=stds, capsize=4,
                  color=colors[:len(arms)], edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Unseen-Group Accuracy")
    ax.set_title(title)
    ax.set_ylim(0, 1.05)
    ax.axhline(y=0.125, color="gray", linestyle="--", alpha=0.5,
               label="chance (12.5%)")
    ax.legend()
    plt.xticks(rotation=30, ha="right")
    fig.savefig(out_dir / "unseen_accuracy_by_arm.png")
    plt.close(fig)


def fig_per_transform_heatmap(agg: dict, out_dir: Path,
                              title: str = "Per-Transform Accuracy"):
    """Heatmap: rows = arms, columns = D4 elements."""
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    setup_style()

    arms = list(agg.keys())
    elements = ["I", "R", "R2", "R3", "H", "RH", "R2H", "R3H"]
    data = np.array([
        [agg[a]["per_transform_mean"].get(e, 0) for e in elements]
        for a in arms
    ])

    fig, ax = plt.subplots(figsize=(10, max(3, len(arms) * 0.8)))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "acc", ["#C44E52", "#F5E6CC", "#55A868"])
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(elements)))
    ax.set_xticklabels(elements)
    ax.set_yticks(range(len(arms)))
    ax.set_yticklabels(arms)
    for i in range(len(arms)):
        for j in range(len(elements)):
            ax.text(j, i, f"{data[i, j]:.3f}", ha="center", va="center",
                    fontsize=8, color="black" if data[i, j] > 0.5 else "white")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Accuracy")
    fig.savefig(out_dir / "per_transform_heatmap.png")
    plt.close(fig)


def fig_structural_error(agg: dict, out_dir: Path,
                         title: str = "Normalized Equivariance Error"):
    """Bar chart: per-arm E_rho and E_rho_wrong (if available)."""
    import matplotlib.pyplot as plt
    setup_style()

    arms = list(agg.keys())
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2",
              "#CCB974", "#64B5CD"]
    # Placeholder: actual values come from evaluation output
    ax.bar(arms, [0] * len(arms), color=colors[:len(arms)],
           edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Normalized Equivariance Error")
    ax.set_title(title)
    plt.xticks(rotation=30, ha="right")
    fig.savefig(out_dir / "structural_error.png")
    plt.close(fig)


def fig_sample_efficiency(scale_results: dict, out_dir: Path):
    """Line plot: accuracy vs N (train size) for each arm."""
    import matplotlib.pyplot as plt
    setup_style()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2",
              "#CCB974", "#64B5CD"]
    for i, (arm, data) in enumerate(sorted(scale_results.items())):
        ns = sorted(int(k) for k in data.keys())
        accs = [data[str(n)]["mean"] for n in ns]
        stds = [data[str(n)].get("std", 0) for n in ns]
        ax.errorbar(ns, accs, yerr=stds, marker="o", label=arm,
                    color=colors[i % len(colors)], capsize=3)
    ax.set_xlabel("Training Scenes (N)")
    ax.set_ylabel("Unseen-Group Accuracy")
    ax.set_title("Sample Efficiency")
    ax.set_xscale("log")
    ax.legend()
    ax.axhline(y=0.125, color="gray", linestyle="--", alpha=0.5)
    fig.savefig(out_dir / "sample_efficiency.png")
    plt.close(fig)
