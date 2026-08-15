#!/usr/bin/env python3
"""EquiOrient paper â€” machine-checked numbers source.

Reads the committed result matrices ONLY (never hand-typed values) and
emits paper/numbers.tex with \\def macros for every headline quantity,
plus paper/paper_numbers.json for figures. Fails loudly on schema drift.

Sources:
  results/equiorient/pilot_run/result_matrix.json        (run #5, v1)
  results/equiorient/pilot_run_v2_modal/result_matrix.json (Amendment D, v2)
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "paper"

SRC_V1 = REPO / "results/equiorient/pilot_run_run5/result_matrix.json"
SRC_V2 = REPO / "results/equiorient/pilot_run_v2_final_matrix.json"
SRC_V1C = REPO / "results/equiorient/pilot_run_v1_corrected_matrix.json"
for p in (SRC_V1, SRC_V2):
    if not p.exists():
        sys.exit(f"missing matrix: {p}")

V1 = json.loads(SRC_V1.read_text(encoding="utf-8"))
V2 = json.loads(SRC_V2.read_text(encoding="utf-8"))
# Regime A corrected (v1 data, corrected harness) â€” optional, fills in
V1C = None
if SRC_V1C.exists():
    V1C = json.loads(SRC_V1C.read_text(encoding="utf-8"))

ARMS = ["ordinary_sft_lora", "augmentation_only", "output_consistency",
        "latent_invariance", "equiorient", "wrong_geometry_equiorient"]
CAUSAL = ARMS[1:]

macros = {}
macros["run_v1_elapsed_s"] = int(V1["elapsed_seconds"])
macros["run_v2_elapsed_s"] = int(V2["elapsed_seconds"])
macros["run_v2_repo_commit"] = V2.get("repo_commit", "?")[:8]

for tag, M in (("V1", V1), ("V2", V2)):
    lam = M["lambda_selected"]
    macros[f"{tag}_lam_oc"] = f"{lam['output_consistency']:g}"
    macros[f"{tag}_lam_li"] = f"{lam['latent_invariance']:g}"
    macros[f"{tag}_lam_eq"] = f"{lam['equiorient']:g}"
    for arm in ARMS:
        a = M["per_arm_val"][arm]
        t = tag + "_" + arm
        macros[f"{t}_val"] = f"{a['val_acc']:.4f}"
        if arm == "ordinary_sft_lora":
            continue
        macros[f"{t}_holdout"] = f"{a['holdout_VoH_accuracy']:.4f}"
        macros[f"{t}_zcorr"] = f"{a['holdout_VoH_accuracy_z_corrupted']:.4f}"
        macros[f"{t}_both"] = f"{a['paired_both_correct_VoH']:.4f}"
        macros[f"{t}_latent"] = f"{a['latent_equivariance_error_VoH']:.3f}"
        macros[f"{t}_probe"] = f"{a['depth_probe_holdout_acc']:.4f}"

# derived: depth probe spread (min/max over causal arms)
for tag, M in (("V1", V1), ("V2", V2)):
    probes = [M["per_arm_val"][a]["depth_probe_holdout_acc"] for a in CAUSAL]
    macros[f"{tag}_probe_min"] = f"{min(probes):.4f}"
    macros[f"{tag}_probe_max"] = f"{max(probes):.4f}"
    macros[f"{tag}_probe_eq"] = (
        f"{M['per_arm_val']['equiorient']['depth_probe_holdout_acc']:.4f}")
    macros[f"{tag}_probe_wrong"] = (
        f"{M['per_arm_val']['wrong_geometry_equiorient']['depth_probe_holdout_acc']:.4f}")

# corrected-regime macros (V2C = v2 corrected FINAL matrix; V1C optional)
for tag, M in (("V2C", V2),):
    lam = M["lambda_selected"]
    macros[f"{tag}_lam_oc"] = f"{lam['output_consistency']:g}"
    macros[f"{tag}_lam_li"] = f"{lam['latent_invariance']:g}"
    macros[f"{tag}_lam_eq"] = f"{lam['equiorient']:g}"
    for arm in ARMS:
        a = M["per_arm_val"][arm]
        t = f"{tag}_{arm}"
        macros[f"{t}_val"] = f"{a['val_acc']:.4f}"
        if arm == "ordinary_sft_lora":
            continue
        rp = a["rho_per_transform"]
        macros[f"{t}_rhoH"] = f"{rp['correct']['hflip']:.4f}"
        macros[f"{t}_rhoV"] = f"{rp['correct']['vflip']:.4f}"
        macros[f"{t}_rhoVH"] = f"{rp['correct']['v_after_h']:.4f}"
        macros[f"{t}_wH"] = f"{rp['wrong']['hflip']:.4f}"
        macros[f"{t}_wV"] = f"{rp['wrong']['vflip']:.4f}"
        macros[f"{t}_wVH"] = f"{rp['wrong']['v_after_h']:.4f}"
        macros[f"{t}_holdout"] = f"{a['holdout_VoH_accuracy']:.4f}"
        macros[f"{t}_zcorr"] = f"{a['holdout_VoH_accuracy_z_corrupted']:.4f}"
        macros[f"{t}_both"] = f"{a['paired_both_correct_VoH']:.4f}"
        macros[f"{t}_latent"] = f"{a['latent_equivariance_error_VoH']:.4f}"
        macros[f"{t}_probe"] = f"{a['depth_probe_holdout_acc']:.4f}"
        macros[f"{t}_probe_zd"] = f"{a['depth_probe_z_d_holdout_acc']:.4f}"
        tl = a["train_loss"]
        macros[f"{t}_ans_epoch_one"] = f"{tl['answer'][0]:.4f}"
        macros[f"{t}_ans_epoch_two"] = f"{tl['answer'][1]:.4f}"
        macros[f"{t}_struct_epoch_one"] = f"{tl['structural'][0]:.6f}"
        macros[f"{t}_struct_epoch_two"] = f"{tl['structural'][1]:.6f}"
    for k in ("V2C_probe_eq", "V2C_probe_wrong"):
        pass
    macros["V2C_probe_eq"] = (
        f"{V2['per_arm_val']['equiorient']['depth_probe_holdout_acc']:.4f}")
    macros["V2C_probe_wrong"] = (
        f"{V2['per_arm_val']['wrong_geometry_equiorient']['depth_probe_holdout_acc']:.4f}")
    macros["V2C_probe_zd_eq"] = (
        f"{V2['per_arm_val']['equiorient']['depth_probe_z_d_holdout_acc']:.4f}")
    macros["V2C_rhoH_eq"] = (
        f"{V2['per_arm_val']['equiorient']['rho_per_transform']['correct']['hflip']:.4f}")
    macros["V2C_rhoH_aug"] = (
        f"{V2['per_arm_val']['augmentation_only']['rho_per_transform']['correct']['hflip']:.4f}")
    macros["V2C_rhoVH_eq"] = (
        f"{V2['per_arm_val']['equiorient']['rho_per_transform']['correct']['v_after_h']:.4f}")
    macros["V2C_rhoVH_aug"] = (
        f"{V2['per_arm_val']['augmentation_only']['rho_per_transform']['correct']['v_after_h']:.4f}")
    # headline ratio macros (computed, not hand-typed)
    r2 = V2['per_arm_val']['augmentation_only']['rho_per_transform']['correct']['v_after_h'] / \
         V2['per_arm_val']['equiorient']['rho_per_transform']['correct']['v_after_h']
    macros["V2C_ratio"] = f"{r2:.0f}"
    if V1C is not None:
        r1 = V1C['per_arm_val']['augmentation_only']['rho_per_transform']['correct']['v_after_h'] / \
             V1C['per_arm_val']['equiorient']['rho_per_transform']['correct']['v_after_h']
        macros["V1C_ratio"] = f"{r1:.0f}"
    macros["V2C_rhoVH_wrong"] = (
        f"{V2['per_arm_val']['wrong_geometry_equiorient']['rho_per_transform']['correct']['v_after_h']:.4f}")
    macros["V2C_wH_eq"] = (
        f"{V2['per_arm_val']['equiorient']['rho_per_transform']['wrong']['hflip']:.4f}")
    macros["V2C_wH_wrong"] = (
        f"{V2['per_arm_val']['wrong_geometry_equiorient']['rho_per_transform']['wrong']['hflip']:.4f}")
if V1C is not None:
    for tag, M in (("V1C", V1C),):
        lam = M["lambda_selected"]
        macros[f"{tag}_lam_eq"] = f"{lam['equiorient']:g}"
        for arm in ["augmentation_only", "equiorient",
                    "wrong_geometry_equiorient"]:
            a = M["per_arm_val"][arm]
            rp = a["rho_per_transform"]
            t = f"{tag}_{arm}"
            macros[f"{t}_rhoH"] = f"{rp['correct']['hflip']:.4f}"
            macros[f"{t}_rhoV"] = f"{rp['correct']['vflip']:.4f}"
            macros[f"{t}_rhoVH"] = f"{rp['correct']['v_after_h']:.4f}"
            macros[f"{t}_wH"] = f"{rp['wrong']['hflip']:.4f}"
            macros[f"{t}_wV"] = f"{rp['wrong']['vflip']:.4f}"
            macros[f"{t}_wVH"] = f"{rp['wrong']['v_after_h']:.4f}"
            macros[f"{t}_probe"] = f"{a['depth_probe_holdout_acc']:.4f}"
            macros[f"{t}_holdout"] = f"{a['holdout_VoH_accuracy']:.4f}"
            macros[f"{t}_val"] = f"{a['val_acc']:.4f}"
            macros[f"{t}_latent"] = f"{a['latent_equivariance_error_VoH']:.4f}"

def camel(name: str) -> str:
    """V1_equiorient_holdout -> VOneEquiorientHoldout (valid control-seq)."""
    out = []
    for p in name.split("_"):
        low = p.lower()
        if low == "v1":
            out.append("VOne")
        elif low == "v2":
            out.append("VTwo")
        elif low == "v1c":
            out.append("VOneC")
        elif low == "v2c":
            out.append("VTwoC")
        else:
            out.append(p[:1].upper() + p[1:])
    return "".join(out)


lines = ["% AUTO-GENERATED by paper/extract_numbers.py â€” do not edit by hand.",
         "% Every value below comes from the committed result matrices.",
         "% Run: python paper/extract_numbers.py",
         ""]
for k in sorted(macros):
    v = macros[k]
    lines.append(f"\\def\\eqn{camel(k)}{{{v}}}")
lines.append("")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "numbers.tex").write_text("\n".join(lines), encoding="utf-8")
(OUT / "paper_numbers.json").write_text(
    json.dumps({**{"V1": V1, "V2": V2}, "macros": macros}, indent=1),
    encoding="utf-8")
print(f"wrote {len(macros)} macros -> paper/numbers.tex")
print(f"V1: holdout eq={macros['V1_equiorient_holdout']} "
      f"probe eq={macros['V1_equiorient_probe']} "
      f"latent eq={macros['V1_equiorient_latent']}")
print(f"V2: holdout eq={macros['V2_equiorient_holdout']} "
      f"probe eq={macros['V2_equiorient_probe']} "
      f"latent eq={macros['V2_equiorient_latent']}")
