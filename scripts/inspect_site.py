"""
Inspect the SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025)
benchmark: structure, SI-factor distribution, orientation subset, modality
counts, and representative examples.

EXTERNAL VALIDATION benchmark: inspection only, no model evaluation.

Writes results/site/site_dataset_report.md.
"""
import os, sys, json
from pathlib import Path
from collections import Counter

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

from src.datasets.site import (load_site, load_site_splits,
                               get_orientation_subset, SI_FACTORS)

OUT = Path("results/site")
OUT.mkdir(parents=True, exist_ok=True)


def fmt_pct(n, total):
    return f"{100.0 * n / total:.1f}%"


def main():
    splits = load_site_splits()
    image, video, all_records = splits["image_test"], splits["video_test"], splits["all"]
    total = len(all_records)

    print("=" * 72)
    print("SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025)")
    print("External-validation benchmark — inspection only (no model eval)")
    print("=" * 72)
    print(f"Total examples: {total}")
    print(f"  image_test: {len(image)}  |  video_test: {len(video)}")

    # ── SI factor counts ──
    cat_counts = Counter(r["category"] for r in all_records)
    print("\n-- Counts by SI factor (official category) --")
    for factor in SI_FACTORS:
        n = cat_counts.get(factor, 0)
        print(f"  {factor:<42} {n:>5}  {fmt_pct(n, total)}")

    # ── Orientation subset (heuristic) ──
    orient = get_orientation_subset(all_records)
    print("\n-- Spatial orientation (HEURISTIC keyword subset, NOT official) --")
    print(f"  orientation-relevant examples: {len(orient)}  {fmt_pct(len(orient), total)}")
    print("  keyword hits (question/option text):")
    kw_counts = Counter(kw for r in orient for kw in r["orientation"]["keywords"])
    for kw, n in kw_counts.most_common(20):
        print(f"    {kw:<20} {n}")
    print("  orientation subset by category:")
    oc = Counter(r["category"] for r in orient)
    for factor in SI_FACTORS:
        n = oc.get(factor, 0)
        if n:
            print(f"    {factor:<42} {n:>5}")
    print("  orientation subset by modality:")
    for m, n in Counter(r["modality"] for r in orient).most_common():
        print(f"    {m:<14} {n}")
    print("  orientation subset by source dataset (top 15):")
    for ds, n in Counter(r["source_dataset"] for r in orient).most_common(15):
        print(f"    {ds:<24} {n}")

    # ── Intrinsic vs extrinsic ──
    print("\n-- Intrinsic vs extrinsic --")
    print("  NOT AVAILABLE: the official SITE-Bench release does not include")
    print("  intrinsic/extrinsic annotations. The paper's top-down taxonomy")
    print("  (intrinsic/extrinsic) is not exposed per example in the dataset.")

    # ── Modality counts ──
    print("\n-- Modality counts (derived: config + visual structure) --")
    mod_counts = Counter(r["modality"] for r in all_records)
    for m in ["single-image", "multi-image", "video"]:
        n = mod_counts.get(m, 0)
        print(f"  {m:<14} {n:>5}  {fmt_pct(n, total)}")
    print("\n  modality x SI factor:")
    for m in ["single-image", "multi-image", "video"]:
        row = Counter(r["category"] for r in all_records if r["modality"] == m)
        parts = ", ".join(f"{f.split(' & ')[0]}:{row.get(f, 0)}" for f in SI_FACTORS if row.get(f, 0))
        print(f"    {m:<14} {parts}")

    # ── Source datasets ──
    print("\n-- Source benchmarks (official 'dataset' field, top 20) --")
    for ds, n in Counter(r["source_dataset"] for r in all_records).most_common(20):
        print(f"  {ds:<28} {n:>5}")

    # ── Options / answer stats ──
    print("\n-- Question structure --")
    opt_counts = Counter(len(r["options"]) for r in all_records)
    print("  options per question:", dict(sorted(opt_counts.items())))
    bad = [r for r in all_records if r["answer_index"] is None or not (0 <= r["answer_index"] < len(r["options"]))]
    print(f"  examples with answer outside option range: {len(bad)}")
    n_image_opts = sum(1 for r in all_records if any("<image>" in (o or "") for o in r["options"]))
    print(f"  examples with <image> placeholders in options: {n_image_opts}")

    # ── 10 representative examples ──
    print("\n-- 10 representative examples --")
    shown = set()
    for r in all_records:
        key = (r["config"], r["category"])
        if key in shown:
            continue
        shown.add(key)
        print("  " + "-" * 68)
        print(f"  id: {r['id']} | config: {r['config']} | modality: {r['modality']}")
        print(f"  category: {r['category']} | source: {r['source_dataset']}")
        print(f"  orientation-relevant (heuristic): {r['orientation']['orientation_relevant']}"
              f" {r['orientation']['keywords'][:6] if r['orientation']['orientation_relevant'] else ''}")
        print(f"  question: {r['question'][:180]}")
        print(f"  options ({len(r['options'])}): "
              + " | ".join(o[:40] for o in r["options"]))
        print(f"  answer: {r['answer']} (index {r['answer_index']})")
        print(f"  visual: {r['visual'][:2]}")
        if len(shown) >= 10:
            break

    # ── Report ──
    report_lines = [
        "# SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025) — Dataset Inspection",
        "",
        "## Source",
        "",
        "- Paper: *SITE: towards Spatial Intelligence Thorough Evaluation* (ICCV 2025), "
        "arXiv:2505.05456",
        "- Dataset (official): https://huggingface.co/datasets/franky-veteran/SITE-Bench "
        "(CC-BY-4.0)",
        "- Code: https://github.com/wenqi-wang20/SITE-Bench",
        "",
        "## Purpose",
        "",
        "SITE is an **external-validation** benchmark for our VSR orientation finding. "
        "It is evaluation-only in this project: no training or fine-tuning on SITE.",
        "This report documents which SITE subsets can serve as an independent test of "
        "the VSR orientation weakness.",
        "",
        f"## Overview: {total} examples (official test splits only)",
        "",
        f"| Config | Count | Modality |",
        f"|---|---|---|",
        f"| image_test | {len(image)} | single-image / multi-image questions |",
        f"| video_test | {len(video)} | video questions |",
        "",
        "## Counts by SI factor (official `category`)",
        "",
        "| SI factor | Count | % |",
        "|---|---|---|",
    ]
    for factor in SI_FACTORS:
        n = cat_counts.get(factor, 0)
        report_lines.append(f"| {factor} | {n} | {fmt_pct(n, total)} |")

    report_lines += [
        "",
        "## Spatial orientation",
        "",
        f"Heuristic orientation-relevant subset (keyword match on question/options; "
        f"**not an official tag**): **{len(orient)} examples ({fmt_pct(len(orient), total)})**.",
        "",
        "By category:",
    ]
    for factor in SI_FACTORS:
        n = oc.get(factor, 0)
        if n:
            report_lines.append(f"- {factor}: {n}")
    report_lines.append("")
    report_lines.append("By modality:")
    for m, n in Counter(r["modality"] for r in orient).most_common():
        report_lines.append(f"- {m}: {n}")
    report_lines.append("")
    report_lines.append("Top source datasets in the orientation subset:")
    for ds, n in Counter(r["source_dataset"] for r in orient).most_common(15):
        report_lines.append(f"- {ds}: {n}")
    report_lines += [
        "",
        "Top orientation keywords (question/option text):",
    ]
    for kw, n in kw_counts.most_common(20):
        report_lines.append(f"- `{kw}`: {n}")
    report_lines += [
        "",
        "## Intrinsic vs extrinsic",
        "",
        "**Not available.** The official SITE-Bench release exposes only "
        "`question`, `options`, `category`, `answer`, `dataset`, `visual`. The "
        "intrinsic/extrinsic axis of the paper's taxonomy is not released per "
        "example; `intrinsic_extrinsic` is therefore `None` in normalized records.",
        "",
        "## Modality counts",
        "",
        "| Modality | Count | % |",
        "|---|---|---|",
    ]
    for m in ["single-image", "multi-image", "video"]:
        n = mod_counts.get(m, 0)
        report_lines.append(f"| {m} | {n} | {fmt_pct(n, total)} |")
    report_lines += [
        "",
        "## Which subsets can test our VSR orientation findings",
        "",
        "1. **Spatial Relationship Reasoning** category "
        f"({cat_counts.get('spatial relationship reasoning', 0)} examples): "
        "closest analogue to VSR statements (relative relations between objects), "
        "including left/right, front/behind, facing-type relations.",
        f"2. **Orientation-relevant heuristic subset** ({len(orient)} examples): "
        "questions containing orientation vocabulary (facing, direction, view, "
        "rotation, left/right, parallel/perpendicular...). Largest contributors: "
        + ", ".join(f"{ds} ({n})" for ds, n in
                    Counter(r["source_dataset"] for r in orient).most_common(5)) + ".",
        f"3. **Movement Prediction & Navigation** category "
        f"({cat_counts.get('movement prediction & navigation', 0)} examples): "
        "dynamic direction/orientation reasoning (video), a distinct extension "
        "beyond static VSR orientation.",
        "",
        "Note: per-example ground truth in SITE is **multiple-choice**, so "
        "comparisons with VSR (True/False) require chance-adjustment "
        "(official metric: Chance-Adjusted Accuracy).",
    ]
    (OUT / "site_dataset_report.md").write_text("\n".join(report_lines))
    print(f"\nSaved: {OUT / 'site_dataset_report.md'}")

    summary = {
        "total": total,
        "image_test": len(image),
        "video_test": len(video),
        "si_factors": dict(cat_counts),
        "orientation_heuristic": len(orient),
        "modality": dict(mod_counts),
    }
    (OUT / "site_inspection.json").write_text(json.dumps(summary, indent=2))
    print(f"Saved: {OUT / 'site_inspection.json'}")


if __name__ == "__main__":
    main()
