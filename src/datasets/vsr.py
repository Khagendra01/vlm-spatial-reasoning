"""
VSR (Visual Spatial Reasoning) dataset loader.

Loads the VSR dataset from Hugging Face and returns records in a consistent format:
{
    "image": ...,
    "statement": "The car is behind the suitcase.",
    "label": True,
    "relation": "behind",
    "subject": "car",
    "object": "suitcase"
}
"""

from datasets import load_dataset
from typing import Dict, List, Optional


def load_vsr(
    split: str = "train",
    dataset_name: str = "cambridgeltl/vsr_random",
) -> List[Dict]:
    """
    Load VSR dataset from Hugging Face.

    Args:
        split: Dataset split to load ("train", "dev", or "test")
        dataset_name: Hugging Face dataset name

    Returns:
        List of records in consistent format
    """
    # Map split names for different datasets
    split_map = {
        "train": "train",
        "validation": "dev",
        "dev": "dev",
        "test": "test",
    }
    actual_split = split_map.get(split, split)

    # Load dataset from Hugging Face
    dataset = load_dataset(dataset_name, split=actual_split)

    records = []
    for example in dataset:
        # Extract fields from the Hugging Face dataset
        # The cambridgeltl dataset has: image, caption, label, relation
        image = example.get("image")
        caption = example.get("caption", "")
        label = example.get("label", False)
        relation = example.get("relation", "")

        # Try to extract subject and object from caption
        # Caption format: "The {subject} is {relation} the {object}."
        subject = ""
        obj = ""
        if caption:
            # Simple parsing - look for "the X is/are" pattern
            parts = caption.lower().split(" is ")
            if len(parts) >= 2:
                # Get subject (remove "the " prefix)
                subject_part = parts[0].strip()
                if subject_part.startswith("the "):
                    subject_part = subject_part[4:]
                subject = subject_part

                # Get object (remove "the " prefix and period)
                obj_part = parts[1].strip()
                # Remove relation and get object
                relation_words = relation.split()
                for word in relation_words:
                    obj_part = obj_part.replace(word, "", 1).strip()
                if obj_part.startswith("the "):
                    obj_part = obj_part[4:]
                if obj_part.endswith("."):
                    obj_part = obj_part[:-1]
                obj = obj_part

        # Convert label to boolean if needed
        if isinstance(label, int):
            label = bool(label)

        record = {
            "image": image,
            "statement": caption,
            "label": label,
            "relation": relation,
            "subject": subject,
            "object": obj,
        }
        records.append(record)

    return records


def load_vsr_splits(
    dataset_name: str = "cambridgeltl/vsr_random",
) -> Dict[str, List[Dict]]:
    """
    Load all VSR splits.

    Args:
        dataset_name: Hugging Face dataset name

    Returns:
        Dictionary with "train", "dev", "test" splits
    """
    splits = {}
    for split_name in ["train", "dev", "test"]:
        try:
            splits[split_name] = load_vsr(split=split_name, dataset_name=dataset_name)
        except Exception as e:
            print(f"Warning: Could not load {split_name} split: {e}")
            splits[split_name] = []

    return splits


def get_relation_frequency(records: List[Dict]) -> Dict[str, int]:
    """
    Count frequency of each spatial relation in the dataset.

    Args:
        records: List of VSR records

    Returns:
        Dictionary mapping relation names to their counts
    """
    relation_counts = {}
    for record in records:
        relation = record["relation"]
        relation_counts[relation] = relation_counts.get(relation, 0) + 1

    return dict(sorted(relation_counts.items(), key=lambda x: x[1], reverse=True))


if __name__ == "__main__":
    # Quick test
    print("Loading VSR dataset...")
    records = load_vsr(split="train")
    print(f"Loaded {len(records)} records")

    if records:
        print("\nFirst record:")
        print(records[0])
