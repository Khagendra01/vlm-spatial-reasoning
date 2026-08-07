"""
Baseline evaluation script for VSR dataset using SmolVLM2.

Runs zero-shot classification on held-out examples and saves results.
"""

import os
import sys
import csv
import time
import argparse
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.datasets.vsr import load_vsr, get_relation_frequency
from src.models.smolvlm import SmolVLMClassifier
from src.evaluation.parser import parse_true_false


def run_evaluation(
    num_examples: int = 200,
    split: str = "test",
    output_dir: str = "results",
    model_name: str = "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
):
    """
    Run baseline evaluation on VSR dataset.

    Args:
        num_examples: Number of examples to evaluate (None for all)
        split: Dataset split to use
        output_dir: Directory to save results
        model_name: Model to use
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load dataset
    print(f"Loading VSR {split} split...")
    records = load_vsr(split=split)

    if num_examples and num_examples < len(records):
        records = records[:num_examples]
        print(f"Using {num_examples} examples for smoke test")
    else:
        print(f"Using all {len(records)} examples")

    # Initialize model
    print("Loading SmolVLM2 model...")
    classifier = SmolVLMClassifier(model_name=model_name)

    # Run evaluation
    results = []
    start_time = time.time()

    for i, record in enumerate(records):
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / (i + 1)
            remaining = avg_time * (len(records) - i - 1)
            print(f"Processing {i + 1}/{len(records)} "
                  f"(elapsed: {elapsed:.1f}s, remaining: {remaining:.1f}s)")

        # Get prediction
        raw_output = classifier.predict(record["image"], record["statement"])
        prediction = parse_true_false(raw_output)

        # Determine correctness
        correct = prediction == record["label"] if prediction is not None else False

        result = {
            "id": i,
            "statement": record["statement"],
            "relation": record["relation"],
            "ground_truth": record["label"],
            "prediction": prediction,
            "correct": correct,
            "raw_output": raw_output,
        }
        results.append(result)

    # Calculate metrics
    metrics = calculate_metrics(results)

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        output_dir,
        f"smolvlm2_zero_shot_{len(records)}_{timestamp}.csv"
    )
    save_results(results, output_file)

    # Print results
    print_results(metrics, output_file)

    return metrics


def calculate_metrics(results: list[dict]) -> dict:
    """
    Calculate evaluation metrics.

    Args:
        results: List of result dictionaries

    Returns:
        Dictionary of metrics
    """
    total = len(results)
    valid = [r for r in results if r["prediction"] is not None]
    invalid = [r for r in results if r["prediction"] is None]
    correct = [r for r in results if r["correct"]]

    # Overall metrics
    accuracy = len(correct) / total if total > 0 else 0
    invalid_rate = len(invalid) / total if total > 0 else 0

    # Per-relation metrics
    relation_metrics = defaultdict(lambda: {"total": 0, "correct": 0, "examples": []})
    for r in results:
        relation = r["relation"]
        relation_metrics[relation]["total"] += 1
        if r["correct"]:
            relation_metrics[relation]["correct"] += 1
        relation_metrics[relation]["examples"].append(r)

    # Calculate accuracy per relation
    relation_accuracy = {}
    for relation, stats in relation_metrics.items():
        acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        relation_accuracy[relation] = {
            "accuracy": acc,
            "correct": stats["correct"],
            "total": stats["total"],
        }

    # Sort relations by accuracy
    sorted_relations = sorted(
        relation_accuracy.items(),
        key=lambda x: x[1]["accuracy"],
        reverse=True,
    )

    return {
        "total": total,
        "valid": len(valid),
        "invalid": len(invalid),
        "correct": len(correct),
        "accuracy": accuracy,
        "invalid_rate": invalid_rate,
        "relation_accuracy": dict(sorted_relations),
    }


def save_results(results: list[dict], output_file: str):
    """
    Save results to CSV.

    Args:
        results: List of result dictionaries
        output_file: Output file path
    """
    fieldnames = [
        "id",
        "statement",
        "relation",
        "ground_truth",
        "prediction",
        "correct",
        "raw_output",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {output_file}")


def print_results(metrics: dict, output_file: str):
    """
    Print evaluation results.

    Args:
        metrics: Calculated metrics dictionary
        output_file: Path to saved results file
    """
    print("\n" + "=" * 80)
    print("BASELINE EVALUATION RESULTS")
    print("=" * 80)

    print(f"\nResults saved to: {output_file}")
    print(f"\nTotal examples: {metrics['total']}")
    print(f"Valid predictions: {metrics['valid']}")
    print(f"Invalid predictions: {metrics['invalid']}")
    print(f"Correct predictions: {metrics['correct']}")

    print(f"\nOverall Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"Invalid Output Rate: {metrics['invalid_rate']:.4f} ({metrics['invalid_rate']*100:.2f}%)")

    # Per-relation results
    print("\n" + "-" * 80)
    print("ACCURACY BY SPATIAL RELATION")
    print("-" * 80)

    relation_metrics = metrics["relation_accuracy"]
    sorted_relations = sorted(
        relation_metrics.items(),
        key=lambda x: x[1]["accuracy"],
        reverse=True,
    )

    print(f"\n{'Relation':<30} {'Accuracy':<12} {'Correct':<10} {'Total':<10}")
    print("-" * 62)

    for relation, stats in sorted_relations:
        acc = stats["accuracy"]
        print(f"{relation:<30} {acc:<12.4f} {stats['correct']:<10} {stats['total']:<10}")

    # Top 5 and bottom 5
    print("\n" + "-" * 80)
    print("TOP 5 RELATIONS (HIGHEST ACCURACY)")
    print("-" * 80)
    for relation, stats in sorted_relations[:5]:
        print(f"  {relation}: {stats['accuracy']:.4f} ({stats['correct']}/{stats['total']})")

    print("\n" + "-" * 80)
    print("BOTTOM 5 RELATIONS (LOWEST ACCURACY)")
    print("-" * 80)
    for relation, stats in sorted_relations[-5:]:
        print(f"  {relation}: {stats['accuracy']:.4f} ({stats['correct']}/{stats['total']})")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run VSR baseline evaluation")
    parser.add_argument(
        "--num-examples",
        type=int,
        default=200,
        help="Number of examples to evaluate (default: 200)",
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

    args = parser.parse_args()

    run_evaluation(
        num_examples=args.num_examples,
        split=args.split,
        output_dir=args.output_dir,
        model_name=args.model,
    )


if __name__ == "__main__":
    main()
