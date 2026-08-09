"""
Structured Spatial Decomposition Prompt Experiment.

Runs the structured prompt on the full VSR test set and compares
with the baseline minimal prompt.

Usage:
    python scripts/run_structured_prompt.py [--num-examples 2195]
"""

import os
import sys
import csv
import json
import time
import math
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.datasets.vsr import load_vsr
from src.models.smolvlm import SmolVLMClassifier, STRUCTURED_PROMPT
from src.evaluation.parser import parse_true_false
from scripts.run_baseline import (
    RELATION_FAMILIES,
    compute_confidence_interval,
    compute_global_metrics,
    compute_relation_metrics,
    compute_family_metrics,
    prefetch_images,
)


def find_baseline_results(results_dir: str = "results") -> dict:
    """Load the baseline metrics JSON."""
    metrics_files = sorted(Path(results_dir).glob("smolvlm2_metrics_*.json"))
    if not metrics_files:
        print("No baseline metrics found. Run baseline first.")
        return None
    with open(metrics_files[-1]) as f:
        return json.load(f)


def find_baseline_csv(results_dir: str = "results") -> list:
    """Load baseline CSV predictions for paired comparison."""
    csv_files = sorted(Path(results_dir).glob("smolvlm2_baseline_*.csv"))
    if not csv_files:
        return []
    results = []
    with open(csv_files[-1], newline="") as f:
        for row in csv.DictReader(f):
            results.append({
                "id": int(row["id"]),
                "statement": row.get("statement", ""),
                "relation": row.get("relation", ""),
                "prediction": parse_true_false(row["raw_output"]),
                "ground_truth": row["ground_truth"] == "True",
                "correct": row["correct"] == "True",
            })
    return results


def run_structured_evaluation(
    num_examples: int = None,
    split: str = "test",
    output_dir: str = "results",
    model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
    batch_size: int = 8,
):
    """Run structured prompt evaluation."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading VSR {split} split...")
    records = load_vsr(split=split)

    if num_examples and num_examples < len(records):
        records = records[:num_examples]
        print(f"Using {num_examples} examples")
    else:
        print(f"Using all {len(records)} examples")

    images = prefetch_images(records, max_workers=16)

    # Load model with structured prompt
    print(f"Loading SmolVLM2 with STRUCTURED PROMPT (batch_size={batch_size})...")
    classifier = SmolVLMClassifier(
        model_name=model_name,
        prompt_template=STRUCTURED_PROMPT,
    )

    results = []
    start_time = time.time()
    checkpoint_interval = 200
    checkpoint_file = os.path.join(output_dir, "checkpoint_structured.json")

    # Batch processing
    batch_images = []
    batch_statements = []
    batch_records = []
    batch_start_idx = 0

    def flush_batch():
        nonlocal batch_images, batch_statements, batch_records, batch_start_idx
        if not batch_images:
            return

        raw_outputs = classifier.predict_batch(batch_images, batch_statements)

        for j, raw_output in enumerate(raw_outputs):
            record = batch_records[j]
            prediction = parse_true_false(raw_output)
            correct = prediction == record["label"] if prediction is not None else False

            result = {
                "id": batch_start_idx + j,
                "statement": record["statement"],
                "relation": record["relation"],
                "ground_truth": record["label"],
                "prediction": prediction,
                "correct": correct,
                "raw_output": raw_output,
                "image_url": record.get("image", ""),
            }
            results.append(result)

        batch_images = []
        batch_statements = []
        batch_records = []

    for i, record in enumerate(records):
        img = images[i]

        if img is None:
            results.append({
                "id": i,
                "statement": record["statement"],
                "relation": record["relation"],
                "ground_truth": record["label"],
                "prediction": None,
                "correct": False,
                "raw_output": "IMAGE_DOWNLOAD_FAILED",
                "image_url": record.get("image", ""),
            })
            continue

        if not batch_images:
            batch_start_idx = i

        batch_images.append(img)
        batch_statements.append(record["statement"])
        batch_records.append(record)

        if len(batch_images) >= batch_size:
            flush_batch()
            elapsed = time.time() - start_time
            processed = len(results)
            avg = elapsed / max(1, processed)
            remaining = avg * (len(records) - processed)
            print(f"Processed {processed}/{len(records)} "
                  f"(elapsed: {elapsed:.1f}s, remaining: {remaining:.1f}s)")

            if processed % checkpoint_interval < batch_size:
                with open(checkpoint_file, "w") as f:
                    json.dump(results, f, ensure_ascii=False, default=str)

    flush_batch()
    total_time = time.time() - start_time
    print(f"\nEvaluation completed in {total_time:.1f}s ({total_time/len(records):.2f}s/example)")

    # Compute metrics
    global_metrics = compute_global_metrics(results)
    relation_metrics = compute_relation_metrics(results)
    family_metrics = compute_family_metrics(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_file = os.path.join(output_dir, f"smolvlm2_structured_{len(records)}_{timestamp}.csv")
    fieldnames = ["id", "statement", "relation", "ground_truth", "prediction", "correct", "raw_output", "image_url"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    metrics_file = os.path.join(output_dir, f"smolvlm2_structured_metrics_{len(records)}_{timestamp}.json")
    metrics_data = {
        "global": global_metrics,
        "by_relation": relation_metrics,
        "by_family": family_metrics,
        "config": {
            "model": model_name,
            "split": split,
            "num_examples": len(records),
            "total_time_seconds": total_time,
            "prompt": "structured_spatial_v1",
        },
    }
    with open(metrics_file, "w") as f:
        json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    return results, global_metrics, relation_metrics, family_metrics


def mcnemar_test(baseline_correct: list, structured_correct: list) -> dict:
    """
    McNemar's test for paired nominal data.

    baseline_correct[i] = True if baseline got example i correct
    structured_correct[i] = True if structured got example i correct

    Returns dict with b, c, chi2, p_value.
    """
    b = sum(1 for bc, sc in zip(baseline_correct, structured_correct) if bc and not sc)
    c = sum(1 for bc, sc in zip(baseline_correct, structured_correct) if not bc and sc)

    # McNemar's test statistic (with continuity correction)
    if b + c == 0:
        chi2 = 0.0
        p_value = 1.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        # p-value from chi2 distribution with 1 df
        p_value = 1 - _chi2_cdf(chi2, 1)

    return {"b": b, "c": c, "chi2": chi2, "p_value": p_value}


def _chi2_cdf(x: float, k: int) -> float:
    """Approximate chi2 CDF for k degrees of freedom."""
    if x <= 0:
        return 0.0
    # Use incomplete gamma function approximation
    # For k=1, we can use the normal approximation
    if k == 1:
        return _normal_cdf(math.sqrt(x)) - _normal_cdf(-math.sqrt(x))
    # For general k, use series expansion
    s = 0.0
    term = 1.0 / math.gamma(k / 2)
    for n in range(100):
        s += term
        term *= (x / 2) / (n + k / 2)
        if abs(term) < 1e-10:
            break
    return s * math.exp(-x / 2) * (x / 2) ** (k / 2) / math.gamma(k / 2)


def _normal_cdf(x: float) -> float:
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def compare_results(baseline_results: list, structured_results: list, baseline_metrics: dict, structured_metrics: dict):
    """Print comprehensive comparison."""
    # Align by index (both should have same examples in same order)
    baseline_map = {r["id"]: r for r in baseline_results}
    structured_map = {r["id"]: r for r in structured_results}

    common_ids = sorted(set(baseline_map.keys()) & set(structured_map.keys()))
    n = len(common_ids)

    baseline_correct = [baseline_map[i]["correct"] for i in common_ids]
    structured_correct = [structured_map[i]["correct"] for i in common_ids]

    # Paired comparison
    both_right = sum(1 for b, s in zip(baseline_correct, structured_correct) if b and s)
    both_wrong = sum(1 for b, s in zip(baseline_correct, structured_correct) if not b and not s)
    baseline_only = sum(1 for b, s in zip(baseline_correct, structured_correct) if b and not s)
    structured_only = sum(1 for b, s in zip(baseline_correct, structured_correct) if not b and s)

    # McNemar's test
    mcnemar = mcnemar_test(baseline_correct, structured_correct)

    print("\n" + "=" * 80)
    print("STRUCTURED PROMPT vs BASELINE COMPARISON")
    print("=" * 80)

    # Overall accuracy
    bl_acc = baseline_metrics["global"]["accuracy"]
    st_acc = structured_metrics["global"]["accuracy"]
    delta = st_acc - bl_acc

    print(f"\n{'Metric':<35} {'Baseline':<15} {'Structured':<15} {'Delta':<12}")
    print("-" * 77)
    print(f"{'Overall Accuracy':<35} {bl_acc:<15.4f} {st_acc:<15.4f} {delta:+.4f}")

    # Family-level comparison
    print(f"\n{'Family':<25} {'Baseline':<15} {'Structured':<15} {'Delta':<12}")
    print("-" * 67)

    target_families = ["orientation", "depth", "horizontal", "vertical", "containment", "proximity", "topology_contact"]
    for fam in target_families:
        bl = baseline_metrics["by_family"].get(fam, {}).get("accuracy", 0)
        st = structured_metrics["by_family"].get(fam, {}).get("accuracy", 0)
        d = st - bl
        print(f"{fam:<25} {bl:<15.4f} {st:<15.4f} {d:+.4f}")

    # Paired breakdown
    print(f"\n{'Paired Breakdown':<35} {'Count':<10} {'%':<10}")
    print("-" * 55)
    print(f"{'Both correct':<35} {both_right:<10} {both_right/n*100:<10.1f}")
    print(f"{'Both wrong':<35} {both_wrong:<10} {both_wrong/n*100:<10.1f}")
    print(f"{'Baseline correct, Structured wrong':<35} {baseline_only:<10} {baseline_only/n*100:<10.1f}")
    print(f"{'Baseline wrong, Structured correct':<35} {structured_only:<10} {structured_only/n*100:<10.1f}")

    # McNemar's test
    print(f"\nMcNemar's Test:")
    print(f"  b (baseline wrong -> structured right): {mcnemar['b']}")
    print(f"  c (baseline right -> structured wrong): {mcnemar['c']}")
    print(f"  chi2: {mcnemar['chi2']:.4f}")
    print(f"  p-value: {mcnemar['p_value']:.6f}")
    if mcnemar["p_value"] < 0.05:
        print(f"  ** SIGNIFICANT at alpha=0.05 **")
    elif mcnemar["p_value"] < 0.10:
        print(f"  * Marginally significant at alpha=0.10 *")
    else:
        print(f"  Not significant at alpha=0.05")

    # Examples fixed by structured prompt
    if structured_only > 0:
        print(f"\n{'Examples FIXED by Structured Prompt':<35}")
        print("-" * 55)
        fixed_ids = [i for i, (b, s) in enumerate(zip(baseline_correct, structured_correct))
                     if not b and s][:10]
        for idx in fixed_ids:
            cid = common_ids[idx]
            br = baseline_map[cid]
            sr = structured_map[cid]
            print(f"  #{cid}: [{br['relation']}] {br.get('statement', 'N/A')[:50]}")

    # Examples broken by structured prompt
    if baseline_only > 0:
        print(f"\n{'Examples BROKEN by Structured Prompt':<35}")
        print("-" * 55)
        broken_ids = [i for i, (b, s) in enumerate(zip(baseline_correct, structured_correct))
                      if b and not s][:10]
        for idx in broken_ids:
            cid = common_ids[idx]
            br = baseline_map[cid]
            sr = structured_map[cid]
            print(f"  #{cid}: [{br['relation']}] {br.get('statement', 'N/A')[:50]}")

    print("\n" + "=" * 80)

    return {
        "overall_delta": delta,
        "both_right": both_right,
        "both_wrong": both_wrong,
        "baseline_only": baseline_only,
        "structured_only": structured_only,
        "mcnemar": mcnemar,
    }


def main():
    parser = argparse.ArgumentParser(description="Run structured prompt experiment")
    parser.add_argument("--num-examples", type=int, default=None)
    parser.add_argument("--split", default="test")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--model", default="HuggingFaceTB/SmolVLM2-2.2B-Instruct")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    # Run structured prompt evaluation
    results, global_m, relation_m, family_m = run_structured_evaluation(
        num_examples=args.num_examples,
        split=args.split,
        output_dir=args.output_dir,
        model_name=args.model,
        batch_size=args.batch_size,
    )

    # Load baseline for comparison
    baseline_metrics = find_baseline_results(args.output_dir)
    baseline_results = find_baseline_csv(args.output_dir)

    if baseline_metrics and baseline_results:
        comparison = compare_results(baseline_results, results, baseline_metrics, {
            "global": global_m,
            "by_family": family_m,
        })

        # Save comparison
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comp_file = os.path.join(args.output_dir, f"comparison_structured_{timestamp}.json")
        with open(comp_file, "w") as f:
            json.dump(comparison, f, indent=2)
        print(f"\nComparison saved to: {comp_file}")
    else:
        print("\nCould not load baseline results for comparison.")


if __name__ == "__main__":
    main()
