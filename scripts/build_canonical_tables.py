"""
Canonical results tables — single source of truth for the paper.

1) VSR conditions table: 10 model conditions x family groups
   (overall / orientation / depth / horizontal / containment / topology-contact)
2) SITE external-validation table: zero-shot vs VSR-LoRA (already computed)

Outputs: results/tables/vsr_conditions_table.{csv,md}
         results/tables/site_validation_table.{csv,md}
"""
import os, sys, csv, json, re
from collections import defaultdict
os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

FAMILY_MAP = {
    "in front of": "depth", "behind": "depth", "at the back of": "depth", "ahead of": "depth",
    "left of": "horizontal", "right of": "horizontal",
    "at the left side of": "horizontal", "at the right side of": "horizontal",
    "next to": "horizontal", "beside": "horizontal",
    "above": "vertical", "below": "vertical", "over": "vertical",
    "under": "vertical", "beneath": "vertical", "on top of": "vertical",
    "facing": "orientation", "facing away from": "orientation",
    "parallel to": "orientation", "perpendicular to": "orientation",
    "in": "containment", "inside": "containment", "contains": "containment",
    "within": "containment",
    "near": "proximity", "far from": "proximity", "far away from": "proximity",
    "close to": "proximity", "away from": "proximity",
    "touching": "topology_contact", "on": "topology_contact",
    "at": "topology_contact", "at the edge of": "topology_contact",
    "off": "topology_contact",
}

CONDITIONS = [
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
GROUPS = ["overall", "orientation", "depth", "horizontal", "containment", "topology_contact"]

def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            r["correct"] = r["correct"] == "True"
            rows.append(r)
    return rows

def acc(rows):
    n = len(rows)
    return (sum(r["correct"] for r in rows) / n, n) if n else (None, 0)

def main():
    os.makedirs("results/tables", exist_ok=True)
    header = ["condition"] + [f"{g} (n)" if g == "overall" else g for g in GROUPS]
    rows_out = []
    for name, path in CONDITIONS:
        rows = load(path)
        row = {"condition": name}
        fam = defaultdict(list)
        for r in rows:
            fam[FAMILY_MAP.get(r["relation"], "other")].append(r)
        a, n = acc(rows)
        row["overall"] = f"{a:.3f} (n={n})" if a is not None else "-"
        for g in GROUPS[1:]:
            a, n = acc(fam.get(g, []))
            row[g] = f"{a:.3f}" if a is not None else "-"
            if g == "orientation":
                row["orientation_n"] = n
        rows_out.append(row)
        print(f"{name:<26} overall={row['overall']} "
              f"orientation={row['orientation']} (n={row.get('orientation_n')}) "
              f"depth={row['depth']} horizontal={row['horizontal']} "
              f"containment={row['containment']} topo={row['topology_contact']}")

    with open("results/tables/vsr_conditions_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows([{k: r.get(k, "-") for k in header} for r in rows_out])

    lines = ["# Canonical VSR Conditions Table", "",
             "All values: accuracy on VSR test (n=2195). Orientation n=137.",
             "", "| Condition | Overall | Orientation | Depth | Horizontal | Containment | Topology-contact |", "|---|---|---|---|---|---|---|"]
    for r in rows_out:
        lines.append(f"| {r['condition']} | {r['overall']} | {r['orientation']} | "
                     f"{r['depth']} | {r['horizontal']} | {r['containment']} | {r['topology_contact']} |")
    open("results/tables/vsr_conditions_table.md", "w").write("\n".join(lines) + "\n")

    # ── SITE table from paired comparison ──
    cmp = json.load(open("results/site/vsr_lora_vs_zeroshot.json"))
    site_rows = []
    for name in ["All images", "Primary: spatial relationship reasoning",
                 "Secondary: orientation heuristic", "single-image", "multi-image"]:
        d = cmp[name]
        zs, lr = d["zs"], d["lora"]
        site_rows.append({"subset": name, "n": d["n"],
                          "zero_shot_raw": f"{zs['raw']:.3f}", "zero_shot_caa": f"{zs['caa']:.3f}",
                          "vsr_lora_raw": f"{lr['raw']:.3f}", "vsr_lora_caa": f"{lr['caa']:.3f}",
                          "delta_pp": f"{(lr['raw']-zs['raw'])*100:+.1f}",
                          "mcnemar_p": f"{d['mcnemar_p']:.3f}"})
    with open("results/tables/site_validation_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(site_rows[0].keys()))
        w.writeheader()
        w.writerows(site_rows)
    lines = ["# SITE External Validation Table (images, n=2,591)", "",
             "| Subset | n | Zero-shot raw (CAA) | VSR-LoRA raw (CAA) | Δ raw (pp) | McNemar p |",
             "|---|---|---|---|---|---|"]
    for r in site_rows:
        lines.append(f"| {r['subset']} | {r['n']} | {r['zero_shot_raw']} ({r['zero_shot_caa']}) | "
                     f"{r['vsr_lora_raw']} ({r['vsr_lora_caa']}) | {r['delta_pp']} | {r['mcnemar_p']} |")
    open("results/tables/site_validation_table.md", "w").write("\n".join(lines) + "\n")
    print("\nSaved results/tables/vsr_conditions_table.{csv,md} and site_validation_table.{csv,md}")

if __name__ == "__main__":
    main()
