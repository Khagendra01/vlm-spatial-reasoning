"""
Comprehensive baseline evaluation script for VSR dataset using SmolVLM2.

Runs zero-shot classification on the full held-out test split and produces:
- Global metrics (accuracy, confusion matrix, prediction distribution)
- Relation-level metrics (n, correct, accuracy, 95% CI)
- Relation family analysis
- Failure case analysis
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
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.datasets.vsr import load_vsr, get_relation_frequency
from src.models.smolvlm import SmolVLMClassifier
from src.evaluation.parser import parse_true_false


# Relation family definitions
RELATION_FAMILIES = {
    "horizontal": [
        "left of", "right of", "at the left side of", "at the right side of",
        "at the side of", "beside", "next to", "alongside", "across from",
    ],
    "vertical": [
        "above", "below", "over", "under", "beneath", "on top of",
    ],
    "depth": [
        "in front of", "behind", "at the back of", "ahead of",
    ],
    "orientation": [
        "facing", "facing away from", "parallel to", "perpendicular to",
    ],
    "containment": [
        "in", "inside", "contains", "within", "enclosed by",
    ],
    "proximity": [
        "near", "far from", "far away from", "close to", "away from",
    ],
    "topology_contact": [
        "touching", "on", "at", "at the edge of", "against", "attached to",
        "connected to", "detached from",
    ],
    "compositional": [
        "part of", "has as a part", "consists of", "surrounding",
        "in the middle of", "among",
    ],
}


def compute_confidence_interval(n_correct: int, n_total: int, confidence: float = 0.95) -> tuple:
    """
    Compute Wilson score interval for binomial proportion.

    Args:
        n_correct: Number of correct predictions
        n_total: Total number of examples
        confidence: Confidence level (default 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n_total == 0:
        return (0.0, 0.0)

    p_hat = n_correct / n_total
    z = 1.96  # For 95% CI

    denominator = 1 + z**2 / n_total
    center = (p_hat + z**2 / (2 * n_total)) / denominator
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_total)) / n_total) / denominator

    lower = max(0, center - spread)
    upper = min(1, center + spread)

    return (lower, upper)


def compute_global_metrics(results: list) -> dict:
    """
    Compute global evaluation metrics.

    Args:
        results: List of result dictionaries

    Returns:
        Dictionary of global metrics
    """
    total = len(results)
    valid = [r for r in results if r["prediction"] is not None]
    invalid = [r for r in results if r["prediction"] is None]
    correct = [r for r in results if r["correct"]]

    # True/False class accuracy
    true_class = [r for r in results if r["ground_truth"] is True]
    false_class = [r for r in results if r["ground_truth"] is False]
    true_correct = [r for r in true_class if r["correct"]]
    false_correct = [r for r in false_class if r["correct"]]

    # Prediction distribution
    predicted_true = [r for r in results if r["prediction"] is True]
    predicted_false = [r for r in results if r["prediction"] is False]

    # Confusion matrix
    tp = len([r for r in results if r["ground_truth"] is True and r["prediction"] is True])
    fp = len([r for r in results if r["ground_truth"] is False and r["prediction"] is True])
    tn = len([r for r in results if r["ground_truth"] is False and r["prediction"] is False])
    fn = len([r for r in results if r["ground_truth"] is True and r["prediction"] is False])

    # Precision and recall
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "total": total,
        "valid": len(valid),
        "invalid": len(invalid),
        "correct": len(correct),
        "accuracy": len(correct) / total if total > 0 else 0,
        "invalid_rate": len(invalid) / total if total > 0 else 0,
        "true_class": {
            "total": len(true_class),
            "correct": len(true_correct),
            "accuracy": len(true_correct) / len(true_class) if len(true_class) > 0 else 0,
        },
        "false_class": {
            "total": len(false_class),
            "correct": len(false_correct),
            "accuracy": len(false_correct) / len(false_class) if len(false_class) > 0 else 0,
        },
        "prediction_distribution": {
            "predicted_true": len(predicted_true),
            "predicted_false": len(predicted_false),
            "true_ratio": len(predicted_true) / total if total > 0 else 0,
        },
        "confusion_matrix": {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        },
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def compute_relation_metrics(results: list) -> dict:
    """
    Compute per-relation metrics with confidence intervals.

    Args:
        results: List of result dictionaries

    Returns:
        Dictionary mapping relation names to their metrics
    """
    relation_stats = defaultdict(lambda: {"total": 0, "correct": 0, "true_total": 0, "false_total": 0})
    for r in results:
        relation = r["relation"]
        relation_stats[relation]["total"] += 1
        if r["correct"]:
            relation_stats[relation]["correct"] += 1
        if r["ground_truth"] is True:
            relation_stats[relation]["true_total"] += 1
        else:
            relation_stats[relation]["false_total"] += 1

    relation_metrics = {}
    for relation, stats in relation_stats.items():
        n = stats["total"]
        correct = stats["correct"]
        accuracy = correct / n if n > 0 else 0
        ci_lower, ci_upper = compute_confidence_interval(correct, n)

        relation_metrics[relation] = {
            "n": n,
            "correct": correct,
            "accuracy": accuracy,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "true_total": stats["true_total"],
            "false_total": stats["false_total"],
        }

    # Sort by sample count (descending)
    return dict(sorted(relation_metrics.items(), key=lambda x: x[1]["n"], reverse=True))


def compute_family_metrics(results: list) -> dict:
    """
    Compute accuracy for each relation family.

    Args:
        results: List of result dictionaries

    Returns:
        Dictionary mapping family names to their metrics
    """
    family_metrics = {}

    for family_name, relations in RELATION_FAMILIES.items():
        family_results = [r for r in results if r["relation"] in relations]
        if not family_results:
            continue

        total = len(family_results)
        correct = sum(1 for r in family_results if r["correct"])
        accuracy = correct / total if total > 0 else 0
        ci_lower, ci_upper = compute_confidence_interval(correct, total)

        # Per-relation breakdown within family
        relation_breakdown = defaultdict(lambda: {"total": 0, "correct": 0})
        for r in family_results:
            relation_breakdown[r["relation"]]["total"] += 1
            if r["correct"]:
                relation_breakdown[r["relation"]]["correct"] += 1

        family_metrics[family_name] = {
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "relations_included": list(relation_breakdown.keys()),
            "relation_breakdown": dict(relation_breakdown),
        }

    return dict(sorted(family_metrics.items(), key=lambda x: x[1]["accuracy"], reverse=True))


def save_failure_cases(results: list, output_dir: str, num_cases: int = 50) -> str:
    """
    Save incorrect examples for manual inspection.

    Args:
        results: List of result dictionaries
        output_dir: Directory to save results
        num_cases: Number of failure cases to save

    Returns:
        Path to saved file
    """
    incorrect = [r for r in results if not r["correct"] and r["prediction"] is not None]

    # Stratified sampling: try to get a mix of relations
    relation_groups = defaultdict(list)
    for r in incorrect:
        relation_groups[r["relation"]].append(r)

    # Prioritize relations with more failures
    sorted_relations = sorted(relation_groups.keys(), key=lambda x: len(relation_groups[x]), reverse=True)

    sampled = []
    for relation in sorted_relations:
        if len(sampled) >= num_cases:
            break
        # Take up to 2 from each relation
        samples = relation_groups[relation][:2]
        sampled.extend(samples)

    # Fill remaining with random samples
    remaining = [r for r in incorrect if r not in sampled]
    np.random.seed(42)
    np.random.shuffle(remaining)
    sampled.extend(remaining[:num_cases - len(sampled)])

    # Save failure cases
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"failure_cases_{timestamp}.csv")

    fieldnames = ["id", "statement", "relation", "ground_truth", "prediction", "raw_output"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sampled[:num_cases]:
            writer.writerow({k: r[k] for k in fieldnames})

    print(f"Saved {min(num_cases, len(sampled))} failure cases to {output_file}")
    return output_file


def save_failure_cases_json(results: list, output_dir: str, num_cases: int = 50) -> str:
    """
    Save failure cases as JSON with image URLs for manual inspection.

    Args:
        results: List of result dictionaries
        output_dir: Directory to save results
        num_cases: Number of failure cases to save

    Returns:
        Path to saved file
    """
    incorrect = [r for r in results if not r["correct"] and r["prediction"] is not None]

    # Stratified sampling
    relation_groups = defaultdict(list)
    for r in incorrect:
        relation_groups[r["relation"]].append(r)

    sorted_relations = sorted(relation_groups.keys(), key=lambda x: len(relation_groups[x]), reverse=True)

    sampled = []
    for relation in sorted_relations:
        if len(sampled) >= num_cases:
            break
        samples = relation_groups[relation][:2]
        sampled.extend(samples)

    remaining = [r for r in incorrect if r not in sampled]
    np.random.seed(42)
    np.random.shuffle(remaining)
    sampled.extend(remaining[:num_cases - len(sampled)])

    # Save as JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"failure_cases_{timestamp}.json")

    failure_data = []
    for r in sampled[:num_cases]:
        failure_data.append({
            "id": r["id"],
            "statement": r["statement"],
            "relation": r["relation"],
            "ground_truth": r["ground_truth"],
            "prediction": r["prediction"],
            "raw_output": r["raw_output"],
            "image_url": r.get("image_url", ""),
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(failure_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(failure_data)} failure cases to {output_file}")
    return output_file


def prefetch_images(records: list, max_workers: int = 8) -> list:
    """
    Download all images in parallel to avoid network delays during inference.

    Args:
        records: List of VSR records with image URLs
        max_workers: Number of parallel download threads

    Returns:
        List of PIL Images (same order as records)
    """
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from io import BytesIO

    def download_image(idx_url):
        idx, url = idx_url
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            img = Image.open(BytesIO(data)).convert("RGB")
            return idx, img
        except Exception as e:
            print(f"  Warning: Failed to download image {idx} ({url}): {e}")
            return idx, None

    urls = [(i, r["image"]) for i, r in enumerate(records)]
    images = [None] * len(records)

    print(f"Prefetching {len(urls)} images with {max_workers} threads...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_image, u): u for u in urls}
        done = 0
        for future in as_completed(futures):
            idx, img = future.result()
            images[idx] = img
            done += 1
            if done % 200 == 0:
                print(f"  Downloaded {done}/{len(urls)} images")

    # Count failures
    failures = sum(1 for img in images if img is None)
    if failures:
        print(f"  Warning: {failures} images failed to download")

    print(f"Prefetch complete: {len(urls) - failures}/{len(urls)} images ready")
    return images


def run_evaluation(
    num_examples: int = None,
    split: str = "test",
    output_dir: str = "results",
    model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
    resume: bool = False,
    batch_size: int = 8,
):
    """
    Run comprehensive baseline evaluation on VSR dataset.
    Uses batch inference and image prefetching for speed.

    Args:
        num_examples: Number of examples to evaluate (None for all)
        split: Dataset split to use
        output_dir: Directory to save results
        model_name: Model to use
        resume: If True, load existing checkpoint and continue from there
        batch_size: Number of examples to process at once
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load dataset
    print(f"Loading VSR {split} split...")
    records = load_vsr(split=split)

    if num_examples and num_examples < len(records):
        records = records[:num_examples]
        print(f"Using {num_examples} examples")
    else:
        print(f"Using all {len(records)} examples")

    # Prefetch all images upfront (parallel downloads)
    images = prefetch_images(records, max_workers=16)

    # Checkpoint file for resume
    checkpoint_file = os.path.join(output_dir, f"checkpoint_{split}_{len(records)}.json")
    results = []

    # Resume from checkpoint if requested
    if resume and os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"Resumed from checkpoint: {len(results)} examples already evaluated")
        if len(results) >= len(records):
            print("All examples already evaluated. Computing metrics...")
        else:
            print(f"Continuing from example {len(results) + 1}")

    # Initialize model
    print(f"Loading SmolVLM2 model (batch_size={batch_size})...")
    classifier = SmolVLMClassifier(model_name=model_name)

    # Run evaluation in batches
    start_idx = len(results)
    start_time = time.time()
    checkpoint_interval = 200

    # Process in batches
    batch_images = []
    batch_statements = []
    batch_records = []

    def flush_batch():
        """Process current batch and store results."""
        nonlocal batch_images, batch_statements, batch_records

        if not batch_images:
            return

        # Run batch inference
        raw_outputs = classifier.predict_batch(batch_images, batch_statements)

        # Store results
        for j, raw_output in enumerate(raw_outputs):
            record = batch_records[j]
            prediction = parse_true_false(raw_output)
            correct = prediction == record["label"] if prediction is not None else False

            global_idx = start_idx + len(results)
            result = {
                "id": global_idx,
                "statement": record["statement"],
                "relation": record["relation"],
                "ground_truth": record["label"],
                "prediction": prediction,
                "correct": correct,
                "raw_output": raw_output,
                "image_url": record.get("image", ""),
            }
            results.append(result)

        # Clear batch
        batch_images = []
        batch_statements = []
        batch_records = []

    for i in range(start_idx, len(records)):
        record = records[i]
        img = images[i]

        # Skip failed downloads
        if img is None:
            result = {
                "id": i,
                "statement": record["statement"],
                "relation": record["relation"],
                "ground_truth": record["label"],
                "prediction": None,
                "correct": False,
                "raw_output": "IMAGE_DOWNLOAD_FAILED",
                "image_url": record.get("image", ""),
            }
            results.append(result)
            continue

        # Add to batch
        batch_images.append(img)
        batch_statements.append(record["statement"])
        batch_records.append(record)

        # Flush when batch is full
        if len(batch_images) >= batch_size:
            flush_batch()

            # Progress report
            elapsed = time.time() - start_time
            processed = len(results) - start_idx
            avg_time = elapsed / max(1, processed)
            remaining = avg_time * (len(records) - start_idx - processed)
            print(f"Processed {len(results)}/{len(records)} "
                  f"(elapsed: {elapsed:.1f}s, remaining: {remaining:.1f}s)")

            # Checkpoint
            if len(results) % checkpoint_interval < batch_size:
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                print(f"  Checkpoint saved ({len(results)} examples)")

    # Flush remaining examples
    flush_batch()

    total_time = time.time() - start_time
    print(f"\nEvaluation completed in {total_time:.1f}s ({total_time/len(records):.2f}s per example)")

    # Compute metrics
    global_metrics = compute_global_metrics(results)
    relation_metrics = compute_relation_metrics(results)
    family_metrics = compute_family_metrics(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save full results CSV
    csv_file = os.path.join(output_dir, f"smolvlm2_baseline_{len(records)}_{timestamp}.csv")
    fieldnames = ["id", "statement", "relation", "ground_truth", "prediction", "correct", "raw_output", "image_url"]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Save metrics JSON
    metrics_file = os.path.join(output_dir, f"smolvlm2_metrics_{len(records)}_{timestamp}.json")
    metrics_data = {
        "global": global_metrics,
        "by_relation": relation_metrics,
        "by_family": family_metrics,
        "config": {
            "model": model_name,
            "split": split,
            "num_examples": len(records),
            "total_time_seconds": total_time,
        },
    }
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    # Save failure cases
    failure_csv = save_failure_cases(results, output_dir, num_cases=50)
    failure_json = save_failure_cases_json(results, output_dir, num_cases=50)

    # Print comprehensive results
    print_results(global_metrics, relation_metrics, family_metrics, csv_file)

    return global_metrics, relation_metrics, family_metrics


def print_results(global_metrics: dict, relation_metrics: dict, family_metrics: dict, csv_file: str):
    """
    Print comprehensive evaluation results.

    Args:
        global_metrics: Global metrics dictionary
        relation_metrics: Relation-level metrics dictionary
        family_metrics: Family-level metrics dictionary
        csv_file: Path to saved results file
    """
    print("\n" + "=" * 80)
    print("COMPREHENSIVE BASELINE EVALUATION RESULTS")
    print("=" * 80)

    print(f"\nResults saved to: {csv_file}")

    # Global metrics
    print("\n" + "-" * 80)
    print("GLOBAL METRICS")
    print("-" * 80)
    print(f"  Total examples:     {global_metrics['total']}")
    print(f"  Valid predictions:  {global_metrics['valid']}")
    print(f"  Invalid predictions:{global_metrics['invalid']}")
    print(f"  Correct predictions:{global_metrics['correct']}")
    print(f"\n  Overall Accuracy:   {global_metrics['accuracy']:.4f} ({global_metrics['accuracy']*100:.2f}%)")
    print(f"  Invalid Rate:       {global_metrics['invalid_rate']:.4f} ({global_metrics['invalid_rate']*100:.2f}%)")
    print(f"  Precision:          {global_metrics['precision']:.4f}")
    print(f"  Recall:             {global_metrics['recall']:.4f}")
    print(f"  F1 Score:           {global_metrics['f1']:.4f}")

    # True/False class accuracy
    print("\n  True-class Accuracy:", f"{global_metrics['true_class']['accuracy']:.4f} "
          f"({global_metrics['true_class']['correct']}/{global_metrics['true_class']['total']})")
    print("  False-class Accuracy:", f"{global_metrics['false_class']['accuracy']:.4f} "
          f"({global_metrics['false_class']['correct']}/{global_metrics['false_class']['total']})")

    # Prediction distribution
    print("\n  Prediction Distribution:")
    print(f"    Predicted True:  {global_metrics['prediction_distribution']['predicted_true']} "
          f"({global_metrics['prediction_distribution']['true_ratio']*100:.1f}%)")
    print(f"    Predicted False: {global_metrics['prediction_distribution']['predicted_false']} "
          f"({(1-global_metrics['prediction_distribution']['true_ratio'])*100:.1f}%)")

    # Confusion matrix
    cm = global_metrics['confusion_matrix']
    print("\n  Confusion Matrix:")
    print(f"    TP: {cm['tp']:4d}  FP: {cm['fp']:4d}")
    print(f"    FN: {cm['fn']:4d}  TN: {cm['tn']:4d}")

    # Family-level metrics
    print("\n" + "-" * 80)
    print("RELATION FAMILY ANALYSIS")
    print("-" * 80)
    print(f"\n{'Family':<25} {'Accuracy':<12} {'95% CI':<20} {'N':<8} {'Correct':<10}")
    print("-" * 75)

    for family, metrics in family_metrics.items():
        ci_str = f"[{metrics['ci_lower']:.3f}, {metrics['ci_upper']:.3f}]"
        print(f"{family:<25} {metrics['accuracy']:<12.4f} {ci_str:<20} {metrics['total']:<8} {metrics['correct']:<10}")

    # Relation-level metrics (sorted by sample count)
    print("\n" + "-" * 80)
    print("RELATION-LEVEL METRICS (sorted by sample count)")
    print("-" * 80)
    print(f"\n{'Relation':<30} {'N':<6} {'Correct':<10} {'Accuracy':<12} {'95% CI':<20}")
    print("-" * 78)

    for relation, metrics in relation_metrics.items():
        ci_str = f"[{metrics['ci_lower']:.3f}, {metrics['ci_upper']:.3f}]"
        print(f"{relation:<30} {metrics['n']:<6} {metrics['correct']:<10} "
              f"{metrics['accuracy']:<12.4f} {ci_str:<20}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Find best/worst families
    sorted_families = sorted(family_metrics.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    best_family = sorted_families[0]
    worst_family = sorted_families[-1]

    print(f"\n  Best family:  {best_family[0]} ({best_family[1]['accuracy']:.4f})")
    print(f"  Worst family: {worst_family[0]} ({worst_family[1]['accuracy']:.4f})")

    # Find relations with enough samples
    sufficient_sample_relations = {r: m for r, m in relation_metrics.items() if m["n"] >= 10}
    if sufficient_sample_relations:
        best_relation = max(sufficient_sample_relations.items(), key=lambda x: x[1]["accuracy"])
        worst_relation = min(sufficient_sample_relations.items(), key=lambda x: x[1]["accuracy"])
        print(f"\n  Best relation (n>=10):  {best_relation[0]} ({best_relation[1]['accuracy']:.4f}, n={best_relation[1]['n']})")
        print(f"  Worst relation (n>=10): {worst_relation[0]} ({worst_relation[1]['accuracy']:.4f}, n={worst_relation[1]['n']})")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive VSR baseline evaluation")
    parser.add_argument(
        "--num-examples",
        type=int,
        default=None,
        help="Number of examples to evaluate (None for all)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "dev", "test"],
        help="Dataset split to use (default: test)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory (default: results)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="HuggingFaceTB/SmolVLM2-2.2B-Instruct",
        help="Model to use",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint if available",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for inference (default: 8)",
    )

    args = parser.parse_args()

    run_evaluation(
        num_examples=args.num_examples,
        split=args.split,
        output_dir=args.output_dir,
        model_name=args.model,
        resume=args.resume,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
