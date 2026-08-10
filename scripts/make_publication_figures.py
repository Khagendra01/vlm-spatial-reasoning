"""
Five publication figures for the VLM spatial reasoning paper.

1. fig1_scale_conditions.png — 10 conditions, overall vs orientation acc
2. fig2_orientation_interventions.png — 7B intervention ladder, orientation
   (full + clean) + per-relation
3. fig3_probes.png — representation probes (ungrounded/grounded vs majority)
4. fig4_consistency.png — logical consistency (facing pairs) across conditions
5. fig5_site_external.png — SITE zero-shot vs VSR-LoRA (CAA)
"""
import os, sys, csv, json, re
os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "results/figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 300})

ORIENT = {"facing", "facing away from", "parallel to", "perpendicular to"}
CONDS = [
    ("2B zero-shot", "results/smolvlm2_baseline_2195_20260808_214536.csv"),
    ("2B structured", "results/smolvlm2_structured_2195_20260808_225009.csv"),
    ("2B General LoRA", "results/general_lora_predictions_20260809_054915.csv"),
    ("2B Targeted LoRA", "results/targeted_lora_predictions_20260809_061231.csv"),
    ("7B zero-shot", "results/qwen2vl_7b_predictions_20260809_064919.csv"),
    ("7B General LoRA", "results/7B_general_lora_predictions_20260809_094930.csv"),
    ("7B Targeted LoRA", "results/7B_targeted_lora_predictions_20260809_095926.csv"),
    ("7B Hard-Neg LoRA", "results/7B_hardneg_lora_predictions_20260809_164619.csv"),
    ("7B Projector LoRA", "results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv"),
    ("7B Vision+Projector LoRA", "results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv"),
]

def load(path):
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            out.append(r)
    return out

def acc(rows):
    return sum(1 for r in rows if r["correct"] == "True") / len(rows) if rows else 0.0

def orientation_stats(rows):
    o = [r for r in rows if r["relation"] in ORIENT]
    per = {}
    for rel in ["facing", "facing away from", "parallel to", "perpendicular to"]:
        rs = [r for r in o if r["relation"] == rel]
        if rs:
            per[rel] = acc(rs)
    return acc(o), per

# ═══ FIG 1: scale + fine-tuning family ═══
fig, ax = plt.subplots(figsize=(10, 4.6))
names = [c[0] for c in CONDS]
overall = []
orientation = []
for _, p in CONDS:
    rows = load(p)
    oa, per = orientation_stats(rows)
    overall.append(acc(rows))
    orientation.append(oa)
x = np.arange(len(names))
w = 0.38
b1 = ax.bar(x - w / 2, overall, w, label="Overall", color="#4C72B0")
b2 = ax.bar(x + w / 2, orientation, w, label="Orientation (4 relations)", color="#C44E52")
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=35, ha="right", fontsize=9)
ax.set_ylabel("Accuracy")
ax.set_ylim(0, 1.0)
ax.axvline(4.5 - 0.5, color="0.4", ls="--", lw=0.8)
ax.text(2.2, 0.95, "2B (SmolVLM2)", ha="center", fontsize=10)
ax.text(6.7, 0.95, "7B (Qwen2-VL)", ha="center", fontsize=10)
ax.legend(frameon=False)
ax.set_title("Spatial reasoning accuracy by model scale and fine-tuning condition")
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_scale_conditions.png", bbox_inches="tight")
plt.close(fig)

# ═══ FIG 2: orientation intervention ladder (7B) ═══
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
interv = [("Zero-shot", "results/qwen2vl_7b_predictions_20260809_064919.csv"),
          ("LM-only LoRA", "results/7B_general_lora_predictions_20260809_094930.csv"),
          ("Targeted LoRA", "results/7B_targeted_lora_predictions_20260809_095926.csv"),
          ("Hard-neg LoRA", "results/7B_hardneg_lora_predictions_20260809_164619.csv"),
          ("Projector LoRA", "results/qwen2vl_7b_projector_lora_predictions_20260809_221720.csv"),
          ("Vis+Proj LoRA", "results/qwen2vl_7b_vision_proj_lora_predictions_20260809_222845.csv")]
ann = {}
with open("results/orientation_persistent_annotations.csv") as f:
    for r in csv.DictReader(f):
        ann[int(r["id"])] = r["annotation"]
strict_ex = {i for i, a in ann.items() if a in {
    "annotation_questionable", "camera_viewpoint_ambiguity",
    "intrinsic_orientation_ambiguous", "front_back_object_ambiguous",
    "small_occluded_object", "subject_reference_inversion",
    "parallel_perpendicular_geometry"}}
names_i = [c[0] for c in interv]
full, clean = [], []
for _, p in interv:
    rows = {int(r["id"]): r for r in load(p)}
    o = [rows[i] for i in rows if rows[i]["relation"] in ORIENT]
    full.append(acc(o))
    oc = [rows[i] for i in rows if i not in strict_ex and rows[i]["relation"] in ORIENT]
    clean.append(acc(oc))
ax = axes[0]
x = np.arange(len(names_i))
ax.bar(x - 0.18, full, 0.36, label="Full (n=137)", color="#4C72B0")
ax.bar(x + 0.18, clean, 0.36, label="Strict-clean (n=107)", color="#55A868")
ax.set_xticks(x); ax.set_xticklabels(names_i, rotation=25, ha="right", fontsize=8.5)
ax.set_ylabel("Orientation accuracy")
ax.set_ylim(0, 1.0); ax.legend(frameon=False, fontsize=9)
ax.set_title("Orientation: intervention ladder (7B)")

per_rel = {}
for name_i, p in interv:
    rows = load(p)
    oa, per = orientation_stats(rows)
    per_rel[name_i] = per
ax = axes[1]
for i, rel in enumerate(["facing", "facing away from", "parallel to", "perpendicular to"]):
    vals = [per_rel[n][rel] for n in names_i]
    ax.plot(names_i, vals, marker="o", label=rel, linewidth=1.6)
ax.set_xticks(range(len(names_i)))
ax.set_xticklabels(names_i, rotation=25, ha="right", fontsize=8.5)
ax.set_ylim(0, 1.0); ax.legend(frameon=False, fontsize=8.5, loc="lower left")
ax.set_title("Orientation: per-relation")
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_orientation_interventions.png", bbox_inches="tight")
plt.close(fig)

# ═══ FIG 3: representation probes ═══
fig, axes = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
probe = json.load(open("results/probe/grounded_probe_results.json"))
tasks = [("T1 facing vs facing-away", "T1_facing_vs_facingaway", 0.637),
         ("T2 parallel vs perp", "T2_parallel_vs_perp", 0.570),
         ("T3 4-way orientation", "T3_4way", 0.499)]
for ax, (title, task, maj) in zip(axes, tasks):
    cells = []
    for lv in ["vit", "merger"]:
        for featset in ["visual", "visual_geometry"]:
            k = f"{lv}::{task}::{featset}"
            if k in probe:
                cells.append((probe[k]["linear"]["test_acc"], f"{lv} linear"))
                cells.append((probe[k]["mlp"]["test_acc"], f"{lv} mlp"))
    vals = [c[0] for c in cells]
    labels = [c[1] for c in cells]
    x = np.arange(len(cells))
    ax.bar(x, vals, 0.6, color="#8172B2")
    ax.axhline(maj, color="#C44E52", ls="--", lw=1.2)
    ax.text(len(cells) - 0.4, maj + 0.015, f"majority {maj:.2f}", fontsize=8.5, color="#C44E52", ha="right")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7.5)
    ax.set_title(title, fontsize=10)
    ax.set_ylim(0, 1.0)
axes[0].set_ylabel("Test accuracy (object-grounded probe)")
fig.suptitle("Orientation decodability from frozen vision features (linear/MLP)", y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_probes.png", bbox_inches="tight")
plt.close(fig)

# ═══ FIG 4: logical consistency (facing pairs) ═══
fig, ax = plt.subplots(figsize=(8.6, 4.0))
cons = {}
for cond, f in [("Zero-shot", "results/consistency_stats_7B_zero_shot.json"),
                ("LM-only LoRA", "results/consistency_stats_LM_only_LoRA.json"),
                ("Hard-neg LoRA", "results/consistency_stats_hardneg_LoRA.json"),
                ("Projector LoRA", "results/consistency_stats_projector_LoRA.json"),
                ("Vis+Proj LoRA", "results/consistency_stats_vision_proj_LoRA.json")]:
    d = json.load(open(f))
    s = d["FF"]
    cons[cond] = {"consistent": s["consistent"] / s["n"], "contradiction": s["contradiction"] / s["n"]}
names_c = list(cons)
x = np.arange(len(names_c))
w = 0.36
ax.bar(x - w / 2, [cons[n]["consistent"] for n in names_c], w, label="Self-consistent (opposite verdicts)", color="#55A868")
ax.bar(x + w / 2, [cons[n]["contradiction"] for n in names_c], w, label="Self-contradiction (same verdict)", color="#C44E52")
ax.axhline(0.5, color="0.4", ls="--", lw=1)
ax.text(len(names_c) - 0.4, 0.52, "chance", fontsize=9, color="0.3", ha="right")
ax.set_xticks(x); ax.set_xticklabels(names_c, rotation=20, ha="right")
ax.set_ylabel("Rate on facing↔facing-away pairs (n=103)")
ax.set_ylim(0, 1.0); ax.legend(frameon=False, fontsize=9)
ax.set_title("Logical consistency: complementary orientation statements")
fig.tight_layout()
fig.savefig(f"{OUT}/fig4_consistency.png", bbox_inches="tight")
plt.close(fig)

# ═══ FIG 5: SITE external validation ═══
fig, ax = plt.subplots(figsize=(8.6, 4.2))
cmp = json.load(open("results/site/vsr_lora_vs_zeroshot.json"))
order = [("All images", "All images"), ("Primary: spatial relationship reasoning", "Official spatial-relationship"),
         ("Secondary: orientation heuristic", "Orientation heuristic (non-official)"),
         ("single-image", "single-image"), ("multi-image", "multi-image")]
names_s = [o[1] for o in order]
zs = [cmp[o[0]]["zs"]["caa"] for o in order]
lr = [cmp[o[0]]["lora"]["caa"] for o in order]
x = np.arange(len(names_s))
w = 0.36
ax.bar(x - w / 2, zs, w, label="Zero-shot", color="#4C72B0")
ax.bar(x + w / 2, lr, w, label="VSR-trained LoRA", color="#DD8452")
ax.axhline(0, color="0.3", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(names_s, rotation=18, ha="right", fontsize=9)
ax.set_ylabel("Chance-adjusted accuracy (CAA)")
ax.set_ylim(-0.1, 0.75)
ax.legend(frameon=False)
ax.set_title("SITE external validation (2,591 image examples): zero-shot vs VSR-trained LoRA")
for i in range(len(names_s)):
    p = cmp[order[i][0]]["mcnemar_p"]
    if p < 0.05:
        ax.text(i, max(zs[i], lr[i]) + 0.02, "*", ha="center", fontsize=13)
fig.tight_layout()
fig.savefig(f"{OUT}/fig5_site_external.png", bbox_inches="tight")
plt.close(fig)

print("Figures saved to", OUT)
for f in sorted(os.listdir(OUT)):
    print(" ", f)
