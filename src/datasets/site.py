"""
SITE (Spatial Intelligence Thorough Evaluation, ICCV 2025) dataset loader.

EXTERNAL VALIDATION benchmark — evaluation-only. No training or fine-tuning
is performed on SITE.

Official source:
  Paper:    SITE: towards Spatial Intelligence Thorough Evaluation (ICCV 2025)
            https://arxiv.org/abs/2505.05456
  Dataset:  https://huggingface.co/datasets/franky-veteran/SITE-Bench
  Code:     https://github.com/wenqi-wang20/SITE-Bench
  License:  CC-BY-4.0

Official organization (preserved here):
  - Two official configs, both official "test" split:
      image_test  (4449 examples, single-/multi-image questions)
      video_test  (3619 examples, video questions)
  - Official fields per example: question, options, category (SI factor),
    answer (letter), dataset (source benchmark), visual (media paths).

Normalized record:
  {
      "id": "image_test-00000",          # config + index (official release has no id)
      "split": "test",                   # official split
      "config": "image_test",            # official config
      "modality": "single-image" | "multi-image" | "video",   # derived
      "question": ...,
      "options": [...],                  # official
      "answer": "C",                     # official (letter)
      "answer_index": 2,                 # derived (A=0)
      "category": ...,                   # official SI factor
      "si_factor": ...,                  # normalized alias of category
      "source_dataset": ...,             # official source benchmark
      "visual": [...],                   # official media paths (relative)
      "intrinsic_extrinsic": None,       # NOT provided in the official release
      "orientation": {...},              # heuristic flag (documented, not official)
  }

NOTE: media files are hosted in ~130GB chunks on Hugging Face and are NOT
downloaded by this loader; only metadata is read. Media download is deferred
until model evaluation.
"""

import re
from typing import Dict, List, Optional

from datasets import load_dataset

SITE_DATASET = "franky-veteran/SITE-Bench"
SITE_CONFIGS = ["image_test", "video_test"]

# SI factors used by the official benchmark (paper taxonomy, 6 categories).
SI_FACTORS = [
    "counting & existence",
    "object localization & positioning",
    "3d information understanding",
    "multi-view & cross-image reasoning",
    "spatial relationship reasoning",
    "movement prediction & navigation",
]

# Keyword heuristic for orientation-related questions.
# CLEARLY NOT OFFICIAL METADATA: the official release does not tag
# orientation examples; this is an indicative filter for inspection only.
ORIENTATION_KEYWORDS = [
    "orientation", "oriented", "orient",
    "facing", "face", "faces",
    "direction", "directional",
    "view", "viewpoint", "view angle",
    "angle", "turned", "rotate", "rotated", "rotation",
    "toward", "towards", "away from",
    "left", "right", "front", "behind", "in front of",
    "parallel", "perpendicular",
    "clockwise", "counterclockwise",
]


def _detect_modality(config: str, options: List[str], visual: List[str]) -> str:
    """Derive modality from the official config and structure."""
    if config == "video_test":
        return "video"
    has_image_option = any("<image>" in (o or "") for o in options)
    n_visual = len(visual or [])
    if has_image_option or n_visual > 1:
        return "multi-image"
    return "single-image"


def _orientation_flags(question: str, options: List[str]) -> Dict:
    """Heuristic orientation relevance (NOT official metadata)."""
    text = (question or "").lower() + " " + " ".join(
        o.lower() for o in (options or []) if o and "<image>" not in o)
    hits = sorted({kw for kw in ORIENTATION_KEYWORDS if re.search(rf"\b{kw}", text)})
    return {"orientation_relevant": bool(hits), "keywords": hits}


def _normalize(example, config: str, index: int) -> Dict:
    answer = str(example.get("answer", "")).strip().upper()
    try:
        answer_index = ord(answer) - ord("A")
    except (TypeError, ValueError):
        answer_index = None
    question = example.get("question", "")
    options = list(example.get("options", []) or [])
    visual = list(example.get("visual", []) or [])
    category = str(example.get("category", "")).strip()
    return {
        "id": f"{config}-{index:05d}",
        "split": "test",
        "config": config,
        "modality": _detect_modality(config, options, visual),
        "question": question,
        "options": options,
        "answer": answer,
        "answer_index": answer_index,
        "category": category,
        "si_factor": category.lower() if category else None,
        "source_dataset": str(example.get("dataset", "")).strip(),
        "visual": visual,
        "intrinsic_extrinsic": None,  # not provided in official release
        "orientation": _orientation_flags(question, options),
    }


def load_site(
    config: Optional[str] = None,
    dataset_name: str = SITE_DATASET,
) -> List[Dict]:
    """
    Load SITE examples.

    Args:
        config: Official config ("image_test" or "video_test"); if None,
                both configs are loaded and concatenated.
        dataset_name: Hugging Face dataset name.

    Returns:
        List of normalized records.
    """
    configs = [config] if config else SITE_CONFIGS
    records: List[Dict] = []
    for cfg in configs:
        ds = load_dataset(dataset_name, cfg, split="test")
        records.extend(_normalize(ex, cfg, i) for i, ex in enumerate(ds))
    return records


def load_site_splits(
    dataset_name: str = SITE_DATASET,
) -> Dict[str, List[Dict]]:
    """
    Load SITE organized by official config/split.
    Returns {"image_test": [...], "video_test": [...], "all": [...]}.
    """
    image = load_site("image_test", dataset_name)
    video = load_site("video_test", dataset_name)
    return {"image_test": image, "video_test": video, "all": image + video}


def get_orientation_subset(records: List[Dict]) -> List[Dict]:
    """Heuristic orientation subset for inspection (NOT an official split)."""
    return [r for r in records if r["orientation"]["orientation_relevant"]]


if __name__ == "__main__":
    print("Loading SITE...")
    records = load_site()
    print(f"Loaded {len(records)} examples")
    if records:
        print("\nFirst record:")
        for k, v in records[0].items():
            print(f"  {k}: {v}")
