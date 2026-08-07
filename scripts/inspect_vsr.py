"""
Inspect VSR dataset: print examples and frequency table of spatial relations.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.datasets.vsr import load_vsr, get_relation_frequency


def print_examples(records, num_examples=10):
    """Print sample records from the dataset."""
    print("=" * 80)
    print(f"SAMPLE RECORDS (showing {min(num_examples, len(records))} of {len(records)})")
    print("=" * 80)

    for i, record in enumerate(records[:num_examples]):
        print(f"\n--- Example {i + 1} ---")
        print(f"  Statement: {record['statement']}")
        print(f"  Label:     {record['label']}")
        print(f"  Relation:  {record['relation']}")
        print(f"  Subject:   {record['subject']}")
        print(f"  Object:    {record['object']}")
        print(f"  Image:     {type(record['image']).__name__}")


def print_frequency_table(records):
    """Print frequency table of spatial relations."""
    relation_freq = get_relation_frequency(records)

    print("\n" + "=" * 80)
    print("SPATIAL RELATIONS FREQUENCY TABLE")
    print("=" * 80)
    print(f"{'Relation':<30} {'Count':<10} {'Percentage':<10}")
    print("-" * 50)

    total = len(records)
    for relation, count in relation_freq.items():
        percentage = (count / total) * 100
        print(f"{relation:<30} {count:<10} {percentage:.1f}%")

    print("-" * 50)
    print(f"{'TOTAL':<30} {total:<10} {'100.0%':<10}")
    print(f"\nUnique relations: {len(relation_freq)}")


def print_label_distribution(records):
    """Print distribution of True/False labels."""
    true_count = sum(1 for r in records if r["label"])
    false_count = len(records) - true_count

    print("\n" + "=" * 80)
    print("LABEL DISTRIBUTION")
    print("=" * 80)
    print(f"  True:  {true_count} ({true_count/len(records)*100:.1f}%)")
    print(f"  False: {false_count} ({false_count/len(records)*100:.1f}%)")


def main():
    """Main inspection function."""
    print("Loading VSR dataset (train split)...")
    records = load_vsr(split="train")

    if not records:
        print("ERROR: No records loaded. Check dataset name and connectivity.")
        sys.exit(1)

    print(f"Successfully loaded {len(records)} records\n")

    # Print examples
    print_examples(records, num_examples=10)

    # Print frequency table
    print_frequency_table(records)

    # Print label distribution
    print_label_distribution(records)

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
