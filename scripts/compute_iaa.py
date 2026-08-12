# -*- coding: utf-8 -*-
"""
Inter-annotator agreement (IAA) for the clean-label audit and the
persistent-failure taxonomy.

Rater 1 = the committed single-annotator audit
  results/orientation_persistent_annotations.csv  (48 cases, eight-class
  taxonomy). The binary clean/ambiguous flag is derived from that taxonomy
  exactly as in scripts/clean_label_orientation.py: only
  "clear_image_model_reasoning_failure" counts as "clean".

Rater 2 = the independent human rater (blind; see results/iaa/README.md):
  results/iaa/rater2_clean_labels.csv      (rating_clean in {clean, ambiguous})
  results/iaa/rater2_taxonomy.csv          (class in the eight-class taxonomy)

Statistics:
  - clean/ambiguous flag : Cohen's kappa + percent agreement
  - eight-class taxonomy : Krippendorff's alpha (nominal, 2 raters)
  - 95% CIs by nonparametric bootstrap over units (percentile method,
    fixed seed for reproducibility)

Outputs (written ONLY when rater-2 data exists; nothing is fabricated):
  results/iaa_results.json
  results/iaa_summary.md

Usage:  python scripts/compute_iaa.py
"""
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
IAA = RESULTS / "iaa"

RATER1_TAXO = RESULTS / "orientation_persistent_annotations.csv"
RATER2_CLEAN = IAA / "rater2_clean_labels.csv"
RATER2_TAXO = IAA / "rater2_taxonomy.csv"

CLEAN_CLASS = "clear_image_model_reasoning_failure"
TAXONOMY_CLASSES = [
    "clear_image_model_reasoning_failure",
    "camera_viewpoint_ambiguity",
    "parallel_perpendicular_geometry",
    "annotation_questionable",
    "intrinsic_orientation_ambiguous",
    "front_back_object_ambiguous",
    "small_occluded_object",
    "subject_reference_inversion",
]
BOOT_SEED = 20260811
N_BOOT = 2000


def read_csv(path, key_col):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[str(r[key_col]).strip()] = r
    return rows


def cohen_kappa(labels_a, labels_b):
    """Cohen's kappa for two equally-ordered label lists."""
    n = len(labels_a)
    if n == 0:
        return None, None, None
    p_o = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    ca, cb = Counter(labels_a), Counter(labels_b)
    p_e = sum((ca[c] / n) * (cb[c] / n) for c in set(ca) | set(cb))
    if p_e >= 1.0:
        return p_o, None, p_e
    return p_o, (p_o - p_e) / (1 - p_e), p_e


def krippendorff_alpha_nominal(labels_a, labels_b):
    """Krippendorff's alpha (nominal) for exactly two raters per unit."""
    units = list(zip(labels_a, labels_b))
    m = len(units)
    if m == 0:
        return None
    # observed disagreement: fraction of units with discordant pair
    do = sum(1 for a, b in units if a != b) / m
    # expected disagreement: chance of a discordant pair drawn from all
    # 2m judgments without replacement
    judgments = [x for pair in units for x in pair]
    n = len(judgments)
    counts = Counter(judgments)
    de = 1.0 - sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))
    if de == 0.0:
        return None if do > 0 else 1.0
    return 1.0 - do / de


def bootstrap_ci(labels_a, labels_b, stat_fn, n_boot=N_BOOT, seed=BOOT_SEED):
    """Percentile bootstrap 95% CI over units. Returns (lo, hi) or None."""
    m = len(labels_a)
    if m == 0:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(m) for _ in range(m)]
        v = stat_fn([labels_a[i] for i in idx], [labels_b[i] for i in idx])
        if v is not None:
            vals.append(v)
    if len(vals) < n_boot * 0.9:
        return None  # statistic undefined in too many resamples
    vals.sort()
    lo = vals[int(0.025 * len(vals))]
    hi = vals[int(0.975 * len(vals)) - 1]
    return lo, hi


def fmt(x, nd=3):
    return None if x is None else round(float(x), nd)


def main():
    if not (RATER2_CLEAN.exists() and RATER2_TAXO.exists()):
        print("=" * 70)
        print("IAA computation skipped: rater-2 files not found.")
        print("Expected (exported by scripts/export_iaa_sheets.py):")
        print(f"  {RATER2_CLEAN.relative_to(ROOT)}")
        print(f"  {RATER2_TAXO.relative_to(ROOT)}")
        print("The second rater must be an independent HUMAN rater; the blind")
        print("rating protocol is in results/iaa/README.md. No results are")
        print("written when rater-2 data is absent (nothing is fabricated).")
        print("=" * 70)
        return

    # ---- rater 1 (committed audit) ----
    r1_rows = read_csv(RATER1_TAXO, "id")
    r1_ids = sorted(r1_rows, key=int)
    r1_taxo = [r1_rows[i]["annotation"].strip() for i in r1_ids]
    r1_bin = ["clean" if t == CLEAN_CLASS else "ambiguous" for t in r1_taxo]

    # ---- rater 2 (blind) ----
    r2_clean = read_csv(RATER2_CLEAN, "id")
    r2_taxo = read_csv(RATER2_TAXO, "id")

    # ---- binary clean/ambiguous (n = intersection of doubly rated units) ----
    clean_ids = sorted(set(r1_ids) & set(r2_clean), key=int)
    c_a = [r1_bin[r1_ids.index(i)] for i in clean_ids]
    c_b = [r2_clean[i]["rating_clean"].strip() for i in clean_ids]
    valid = all(v in {"clean", "ambiguous"} for v in c_b)
    if not valid:
        sys.exit("ERROR: rater2_clean_labels.csv contains invalid ratings; "
                 "allowed values: clean, ambiguous")
    p_o, kappa, p_e = cohen_kappa(c_a, c_b)
    ci_k = bootstrap_ci(c_a, c_b, lambda x, y: cohen_kappa(x, y)[1])

    # ---- eight-class taxonomy (n = intersection) ----
    taxo_ids = sorted(set(r1_ids) & set(r2_taxo), key=int)
    t_a = [r1_taxo[r1_ids.index(i)] for i in taxo_ids]
    t_b = [r2_taxo[i]["class"].strip() for i in taxo_ids]
    invalid = sorted(set(t_b) - set(TAXONOMY_CLASSES))
    if invalid:
        sys.exit(f"ERROR: rater2_taxonomy.csv contains invalid classes: {invalid}")
    alpha = krippendorff_alpha_nominal(t_a, t_b)
    ci_a = bootstrap_ci(t_a, t_b, krippendorff_alpha_nominal)
    pct_taxo = sum(1 for a, b in zip(t_a, t_b) if a == b) / len(t_a)

    # ---- confusion matrices (nested dicts for JSON serialization) ----
    def matrix(a_labels, b_labels, classes):
        return {a: {b: sum(1 for x, y in zip(a_labels, b_labels)
                           if x == a and y == b) for b in classes}
                for a in classes}

    conf_clean = matrix(c_a, c_b, ("clean", "ambiguous"))
    conf_taxo = matrix(t_a, t_b, TAXONOMY_CLASSES)

    out = {
        "schema_version": "iaa-v1",
        "method": {
            "rater1": "committed single-annotator audit "
                      "(results/orientation_persistent_annotations.csv)",
            "rater2": "independent blind human rater "
                      "(results/iaa/rater2_clean_labels.csv, "
                      "results/iaa/rater2_taxonomy.csv)",
            "binary_flag": "clean vs ambiguous derived from rater1 taxonomy "
                           "(only clear_image_model_reasoning_failure = clean)",
            "statistics": {
                "clean_flag": "Cohen's kappa, percent agreement",
                "taxonomy": "Krippendorff's alpha (nominal, two raters)",
                "ci": "nonparametric bootstrap over units, percentile 95% CI, "
                      f"{N_BOOT} resamples, seed {BOOT_SEED}",
            },
        },
        "clean_flag": {
            "n": len(clean_ids),
            "percent_agreement": fmt(p_o),
            "cohens_kappa": fmt(kappa),
            "kappa_95ci": [fmt(ci_k[0]), fmt(ci_k[1])],
            "p_e": fmt(p_e),
            "confusion_matrix": conf_clean,
        },
        "taxonomy": {
            "n": len(taxo_ids),
            "percent_agreement": fmt(pct_taxo),
            "krippendorff_alpha": fmt(alpha),
            "alpha_95ci": [fmt(ci_a[0]), fmt(ci_a[1])],
            "confusion_matrix": conf_taxo,
        },
        "caveats": [
            "n is the intersection of units rated by both annotators "
            "(48 persistent-failure cases)",
            "kappa/alpha are undefined or unstable when one class dominates; "
            "CIs are bootstrap approximations at this sample size",
            "these statistics are ADDITIVE evidence for the single-annotator "
            "audit; they do not replace or alter any reported clean-label "
            "accuracy in the paper (Table 2 main / Table 7 supplementary)",
        ],
    }

    with open(IAA / "iaa_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    pct_ag = sum(1 for a, b in zip(c_a, c_b) if a == b) / len(c_a)
    kappa_s = "n/a" if kappa is None else f"{kappa:.3f}"
    ci_k_s = ("n/a" if ci_k is None
              else f"[{ci_k[0]:.3f}, {ci_k[1]:.3f}]")
    p_e_s = "n/a" if p_e is None else f"{p_e:.3f}"
    alpha_s = "n/a" if alpha is None else f"{alpha:.3f}"
    ci_a_s = ("n/a" if ci_a is None
              else f"[{ci_a[0]:.3f}, {ci_a[1]:.3f}]")

    summary = f"""# Inter-Annotator Agreement (IAA)

Additive reliability evidence for the single-annotator audits. Computed by
`scripts/compute_iaa.py` from the committed rater-1 audit
(`results/orientation_persistent_annotations.csv`) and the blind rater-2
sheets (`results/iaa/rater2_clean_labels.csv`,
`results/iaa/rater2_taxonomy.csv`).

## Clean/ambiguous flag (clean-label sensitivity audit)

- n = {len(clean_ids)} (48 persistent-failure cases rated by both annotators)
- Percent agreement: {pct_ag:.1%}
- Cohen's kappa: {kappa_s} (95% bootstrap CI {ci_k_s})
- Chance-expected agreement (p_e): {p_e_s}

Rater-1 binary flag derived from the eight-class taxonomy exactly as in
`scripts/clean_label_orientation.py` (only
`clear_image_model_reasoning_failure` counts as clean).

## Eight-class failure taxonomy

- n = {len(taxo_ids)}
- Percent agreement (exact class match): {pct_taxo:.1%}
- Krippendorff's alpha (nominal, two raters): {alpha_s} (95% bootstrap CI {ci_a_s})

## Reading

These are additive results. They do not replace or alter any reported
accuracy number (Table 2 main text / Table 7 supplementary), and the clean-label
analysis remains explicitly a single-annotator exploratory audit if IAA is
not yet available. Per standard conventions (e.g., Landis & Koch 1977 for
kappa), values below 0.41 are commonly read as slight-to-fair agreement and
should be reported as such; at n = {len(clean_ids)} the bootstrap CIs are wide.
"""
    (IAA / "iaa_summary.md").write_text(summary, encoding="utf-8")

    print("=" * 70)
    print("IAA results")
    print("=" * 70)
    print(f"clean/ambiguous flag  n={len(clean_ids)}  "
          f"agreement={pct_ag:.1%}  kappa={kappa_s}  "
          f"95% CI {ci_k_s}")
    print(f"eight-class taxonomy  n={len(taxo_ids)}  "
          f"agreement={pct_taxo:.1%}  alpha={alpha_s}  "
          f"95% CI {ci_a_s}")
    print(f"\nwrote {IAA / 'iaa_results.json'}")
    print(f"wrote {IAA / 'iaa_summary.md'}")


if __name__ == "__main__":
    main()
