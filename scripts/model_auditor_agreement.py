"""Aggregate model-auditor agreement statistics (GPT-5.6 / Gemini vs humans).

Computes per-pair agreement and Cohen's kappa for the 137-item binary
clean/ambiguous flag and per-pair exact-class agreement for the 48-item
taxonomy, and writes results/iaa/model_auditor_agreement.json.
"""

from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IAA = ROOT / "results" / "iaa"

BINARY = {
    "human_a": IAA / "rater2_clean_labels.csv",
    "human_b": IAA / "rater3_clean_labels.csv",
    "gpt56": IAA / "gpt56_clean_137.csv",
    "gemini": IAA / "gemini_clean_137.csv",
}
TAXONOMY = {
    "human_a": IAA / "rater2_taxonomy.csv",
    "human_b": IAA / "rater3_taxonomy.csv",
    "gpt56": IAA / "gpt56_taxo_48.csv",
    "gemini": IAA / "gemini_taxo_48.csv",
}


def load(path: Path, id_key: str, label_key: str) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {
            (row.get("item_id") or row.get("id") or row.get(id_key)):
            (row.get(label_key) or row.get("parsed_clean") or row.get("parsed_taxonomy") or row.get("rating_clean") or row.get("class") or "").strip().upper()
            for row in csv.DictReader(f)
        }


def kappa(a: dict[str, str], b: dict[str, str]) -> tuple[int, float, float]:
    keys = sorted(set(a) & set(b))
    n = len(keys)
    po = sum(a[k] == b[k] for k in keys) / n
    ca = collections.Counter(a[k] for k in keys)
    cb = collections.Counter(b[k] for k in keys)
    pe = sum(ca[x] * cb[x] for x in set(ca) | set(cb)) / (n * n)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return n, round(po, 3), round(k, 3)


def main() -> None:
    bin_data = {k: load(p, "id", "rating_clean") for k, p in BINARY.items()}
    tax_data = {k: load(p, "id", "class") for k, p in TAXONOMY.items()}

    binary_pairs = {}
    for a, b in [
        ("human_a", "human_b"), ("gpt56", "human_a"), ("gpt56", "human_b"),
        ("gemini", "human_a"), ("gemini", "human_b"), ("gpt56", "gemini"),
    ]:
        n, agree, kap = kappa(bin_data[a], bin_data[b])
        binary_pairs[f"{a}__{b}"] = {
            "n": n,
            "agreement": agree,
            "kappa": kap,
        }

    clean_rates = {k: round(sum(v == "CLEAN" for v in d.values()) / len(d), 4)
                   for k, d in bin_data.items()}

    taxonomy_pairs = {}
    for a, b in [
        ("human_a", "human_b"), ("gpt56", "human_a"), ("gpt56", "human_b"),
        ("gemini", "human_a"), ("gemini", "human_b"), ("gpt56", "gemini"),
    ]:
        n, agree, _ = kappa(tax_data[a], tax_data[b])
        taxonomy_pairs[f"{a}__{b}"] = {"n": n, "agreement": agree}

    tax_dist = {k: dict(collections.Counter(d.values()))
                for k, d in tax_data.items()}

    out = {
        "resource": "model auditor agreement vs human re-audits",
        "version": "iaa-v3",
        "binary_clean_ambiguity_137": {
            "clean_rates": clean_rates,
            "pairs": binary_pairs,
        },
        "taxonomy_48_exact_class": {
            "pairs": taxonomy_pairs,
            "distributions": tax_dist,
        },
        "protocol_notes": {
            "gpt56": "Corrected one-item-per-request CLEAN/AMBIGUOUS run "
                     "(run_id gpt56sol_clean_ambiguity_137_20260812); original "
                     "interactive run was contact-sheet batched and is "
                     "retained separately as exploratory only.",
            "gemini": "One-item-per-request run "
                      "(run_id run_gemini_spark_clean_137_001, latency_ms 150).",
        },
    }
    (IAA / "model_auditor_agreement.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("wrote results/iaa/model_auditor_agreement.json")
    print(json.dumps(binary_pairs, indent=1))
    print("clean_rates:", clean_rates)
    print("taxonomy_pairs:", json.dumps(taxonomy_pairs))


if __name__ == "__main__":
    main()
