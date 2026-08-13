"""Score external full-VSR runs (GPT-5.6 Sol, Gemini Spark) against official
VSR ground truth, with the canonical family map and Wilson 95% CIs.

Usage:  python scripts/score_external_vsr.py
Output: results/external_models/external_vsr_scores.json (+ printed table)
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GT = ROOT / "results" / "mimo" / "mimo_v25_zeroshot_predictions.csv"
OUT_DIR = ROOT / "results" / "external_models"

FAMILY = {
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
ORIENT_RELS = ["facing", "facing away from", "parallel to", "perpendicular to"]
GROUPS = ["overall", "orientation", "depth", "horizontal", "containment",
          "topology_contact", "vertical", "proximity"]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    z = 1.96
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(100 * (center - half), 1), round(100 * (center + half), 1)


def parse_binary(raw: str) -> str | None:
    v = raw.strip().strip('"').strip(".").lower()
    return "True" if v in ("true", "true.") else ("False" if v in ("false", "false.") else None)


def load_gt() -> dict[str, dict]:
    with GT.open(encoding="utf-8-sig", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def score(gt: dict[str, dict], verdicts: dict[str, str | None]) -> dict:
    groups: dict[str, list[bool]] = {g: [] for g in GROUPS}
    per_rel: dict[str, list[bool]] = {r: [] for r in ORIENT_RELS}
    invalid = 0
    for i, r in gt.items():
        v = verdicts.get(i)
        if v is None:
            invalid += 1
            correct = False
        else:
            correct = (v.lower() == r["ground_truth"].strip().lower())
        groups["overall"].append(correct)
        fam = FAMILY.get(r["relation"], "other")
        if fam in groups:
            groups[fam].append(correct)
        if r["relation"] in per_rel:
            per_rel[r["relation"]].append(correct)

    out = {"invalid": invalid}
    for g in GROUPS:
        k, n = sum(groups[g]), len(groups[g])
        out[g] = {"n": n, "accuracy": round(100 * k / n, 1) if n else None,
                  "ci": wilson(k, n) if n else None}
    out["orientation_per_relation"] = {
        r: {"n": len(per_rel[r]),
            "accuracy": round(100 * sum(per_rel[r]) / len(per_rel[r]), 1),
            "ci": wilson(sum(per_rel[r]), len(per_rel[r]))}
        for r in ORIENT_RELS
    }
    return out


def load_gemini(path: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            v = r.get("parsed_binary", "").strip()
            out[r["item_id"]] = v if v.upper() in ("TRUE", "FALSE") else None
    return out


def load_gpt(path: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            out[r["item_id"]] = parse_binary(r["raw_response"])
    return out


def consistency_stats(path: Path) -> dict:
    """Per-family consistency from a consistency results CSV (rows = parts)."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_pair: dict[str, dict] = {}
    for r in rows:
        v = r["parsed_binary"].strip()
        v = "True" if v.upper() == "TRUE" else ("False" if v.upper() == "FALSE" else "INVALID")
        by_pair.setdefault(r["pair_id"], {"family": r["family"], "a": None, "b": None})
        by_pair[r["pair_id"]][r["part"]] = v

    families = {}
    for pid, p in by_pair.items():
        fam = p["family"]
        f = families.setdefault(fam, {"pairs": 0, "comp": 0, "both_true": 0,
                                      "both_false": 0, "invalid_pair": 0})
        f["pairs"] += 1
        a, b = p["a"], p["b"]
        if a == "INVALID" or b == "INVALID":
            f["invalid_pair"] += 1
        elif a == b:
            if a == "True":
                f["both_true"] += 1
            else:
                f["both_false"] += 1
        else:
            f["comp"] += 1

    out = {}
    for fam, f in sorted(families.items()):
        n = f["pairs"]
        strict = f["pairs"] - f["invalid_pair"]
        out[fam] = {
            "pairs": n,
            "complementary": round(100 * f["comp"] / strict, 1) if strict else None,
            "both_true": round(100 * f["both_true"] / strict, 1) if strict else None,
            "both_false": round(100 * f["both_false"] / strict, 1) if strict else None,
            "invalid_pairs": f["invalid_pair"],
        }
    out["_total"] = {"pairs": len(by_pair)}
    return out


def main() -> None:
    gt = load_gt()
    gemini_v1 = score(gt, load_gemini(ROOT / "gemini_vsr_2195_results - Untitled.csv"))
    gemini_v2 = score(gt, load_gemini(ROOT / "gemini_vsr_2195_results_v2 - Untitled.csv"))
    gpt = score(gt, load_gpt(ROOT / "vsr_full_gpt56sol_complete.csv"))

    # Gemini consistency degeneracy check (v1) + stats for v2 and GPT.
    pairs = list(csv.DictReader(
        (ROOT / "gemini_consistency_pairs_results - Untitled.csv").open(encoding="utf-8-sig")))
    pattern = {}
    by_pair: dict[str, dict] = {}
    for r in pairs:
        by_pair.setdefault(r["pair_id"], {})[r["part"]] = r["parsed_binary"]
    for pid, v in by_pair.items():
        pattern[f"{v.get('a')}__{v.get('b')}"] = pattern.get(f"{v.get('a')}__{v.get('b')}", 0) + 1
    gemini_consistency_v1 = {
        "rows": len(pairs),
        "pairs": len(by_pair),
        "verdict_patterns": pattern,
        "degenerate": len(set(pattern)) == 2,
        "note": "Every pair answered with opposite verdicts; statement_b was negated "
                "rather than independently evaluated \u2014 not usable as consistency evidence.",
    }

    out = {
        "ground_truth": str(GT),
        "gemini_spark": {
            "score_v1": gemini_v1,
            "score_v2": gemini_v2,
            "consistency_v1": gemini_consistency_v1,
            "consistency_v2": consistency_stats(ROOT / "gemini_consistency_pairs_results_v2 - Untitled.csv"),
        },
        "gpt56sol": {
            "score": gpt,
            "consistency": consistency_stats(ROOT / "gpt56sol_consistency_pairs_results.csv"),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "external_vsr_scores.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")

    for name, d in [("Gemini Spark v1", gemini_v1), ("Gemini Spark v2", gemini_v2),
                    ("GPT-5.6 Sol", gpt)]:
        print(f"=== {name} (n=2195; invalid={d['invalid']}) ===")
        for g in ["overall", "orientation", "depth", "horizontal", "containment",
                  "topology_contact", "vertical", "proximity"]:
            s = d[g]
            print(f"  {g:16s} {s['accuracy']}%  CI {s['ci']}  (n={s['n']})")
        for rel, s in d["orientation_per_relation"].items():
            print(f"    {rel:18s} {s['accuracy']}%  CI {s['ci']}  (n={s['n']})")
    print("gemini consistency v1:", json.dumps(gemini_consistency_v1))
    print("gemini consistency v2:", json.dumps(out["gemini_spark"]["consistency_v2"], indent=1))
    print("gpt consistency:", json.dumps(out["gpt56sol"]["consistency"], indent=1))


if __name__ == "__main__":
    main()
