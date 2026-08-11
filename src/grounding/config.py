"""Frozen protocol constants for the Tier-A grounding audit.

Single source of run-invariant parameters for the audit. Values mirror
configs/grounding_protocol.yaml and research/GROUNDING_PROTOCOL_FREEZE.md
(pre-result freeze v0.1). Do not edit after results are observed.

Preprocessing cap (MAX_LONG_SIDE=392) is the documented, uniform constant from
docs/TECHNIQUES.md section 4: transformers builds used here ignore `max_pixels`,
so images are pre-resized to <= 392px long side to enforce the patch budget.
It is a constant across examples and conditions (fair by construction) and is
recorded in every run's metadata.
"""

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PROTOCOL_YAML = REPO_ROOT / "configs" / "grounding_protocol.yaml"
PROTOCOL_AUTHORITY = REPO_ROOT / "research" / "GROUNDING_PROTOCOL_FREEZE.md"
DECISION_LOG = REPO_ROOT / "research" / "DECISION_LOG.md"
PARSER_SOURCE = REPO_ROOT / "src" / "evaluation" / "parser.py"

# --- dataset / model identity (frozen) ---
DATASET_ID = "cambridgeltl/vsr_random"
DATASET_SPLIT = "test"
BASE_MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"

# --- frozen prompt (identical to every prior 7B run in this repo) ---
PROMPT_TEMPLATE = (
    'Look at the image carefully.\n\n'
    'Statement: "{statement}"\n\n'
    'Is this statement true or false?\n\n'
    'Answer with exactly one word: True or False.'
)

# --- frozen generation settings (run fairness: identical everywhere) ---
MAX_NEW_TOKENS = 5
DO_SAMPLE = False

# --- frozen intervention parameters (from configs/grounding_protocol.yaml) ---
SHUFFLE_SEED = 20260810            # frozen; never regenerate after results
SHUFFLE_SOURCE_SPLIT = "test"
SHUFFLE_FORBID_SELF_PAIR = True

BLANK_IMAGE_SIZE = 448             # px, square
BLANK_IMAGE_COLOR = (128, 128, 128)  # uniform gray RGB

# Bootstrap resampling seed (frozen pre-result; deterministic CIs).
BOOTSTRAP_SEED = 20260810
BOOTSTRAP_ITERATIONS = 10000

# --- engineering constants (documented, uniform) ---
MAX_LONG_SIDE = 392               # preprocessing cap (docs/TECHNIQUES.md §4)
OOM_SCALE_LADDER = (336, 224, 160, 96)  # docs/TECHNIQUES.md §6
DEFAULT_BATCH_SIZE = 8            # single-image safe batch on A6000 (measured)
MAX_IMAGE_DOWNLOAD_WORKERS = 16

# --- checkpoint matrix (Tier-A primary milestone) ---
# adapter_path None means zero-shot base model.
CHECKPOINTS = {
    "zero_shot": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": None,
        "role": "primary_baseline",
        "label": "7B_zero_shot",
    },
    "general_lora": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "qwen2vl_7b_general_lora" / "final",
        "role": "primary_tuned",
        "label": "7B_general_lora",
    },
    "hardneg_lora": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "qwen2vl_7b_hardneg_lora" / "final",
        "role": "key_diagnostic",
        "label": "7B_hardneg_lora",
    },
    # campaign seeds (retrains of general_lora, seed A=101/B=202/C=303);
    # dirs appear as training completes; predictors load adapters on demand.
    "r1_seedA": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "qwen2vl_7b_general_lora_seedA" / "final",
        "role": "campaign_seed",
        "label": "7B_R1_seedA",
    },
    "r1_seedB": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "qwen2vl_7b_general_lora_seedB" / "final",
        "role": "campaign_seed",
        "label": "7B_R1_seedB",
    },
    "r1_seedC": {
        "model_id": BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "qwen2vl_7b_general_lora_seedC" / "final",
        "role": "campaign_seed",
        "label": "7B_R1_seedC",
    },
}

# --- R1 2B replication checkpoint matrix (frozen Paper-2 contract) ---
# Same keys as CHECKPOINTS so all analyzers/comparisons (P1 zero->general)
# work unchanged; distinct labels/model_id recorded in every row + metadata.
SMOLVLM2_BASE_MODEL_ID = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"
CHECKPOINTS_2B = {
    "zero_shot": {
        "model_id": SMOLVLM2_BASE_MODEL_ID,
        "adapter_path": None,
        "role": "primary_baseline",
        "label": "2B_zero_shot",
    },
    "general_lora": {
        "model_id": SMOLVLM2_BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "general_lora" / "final",
        "role": "primary_tuned",
        "label": "2B_general_lora",
    },
    # campaign seeds (retrains of general_lora, seed A=101/B=202/C=303);
    # dirs appear as training completes; predictors load adapters on demand.
    "r1_seedA": {
        "model_id": SMOLVLM2_BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "smolvlm2_2b_general_lora_seedA" / "final",
        "role": "campaign_seed",
        "label": "2B_R1_seedA",
    },
    "r1_seedB": {
        "model_id": SMOLVLM2_BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "smolvlm2_2b_general_lora_seedB" / "final",
        "role": "campaign_seed",
        "label": "2B_R1_seedB",
    },
    "r1_seedC": {
        "model_id": SMOLVLM2_BASE_MODEL_ID,
        "adapter_path": REPO_ROOT / "checkpoints" / "seed_campaign" / "smolvlm2_2b_general_lora_seedC" / "final",
        "role": "campaign_seed",
        "label": "2B_R1_seedC",
    },
}

MODEL_FAMILIES = {
    "qwen2vl": {"checkpoints": CHECKPOINTS, "classifier": "Qwen2VLClassifier"},
    "smolvlm2": {"checkpoints": CHECKPOINTS_2B, "classifier": "SmolVLM2Classifier"},
}


def family_registry(family: str) -> dict:
    if family not in MODEL_FAMILIES:
        raise ValueError(f"unknown model family {family!r}")
    return MODEL_FAMILIES[family]["checkpoints"]

# --- Tier-A evidence conditions (confirmatory order from the freeze) ---
CONDITIONS = ["normal", "shuffle", "blank", "text_only"]

# transform_name -> canonical condition name (for prediction rows)
TRANSFORM_TO_CONDITION = {
    "normal": "normal",
    "shuffle_image": "shuffle",
    "blank_image": "blank",
    "text_only": "text_only",
}

CONDITION_META = {
    "normal": {"status": "confirmatory_reference", "axis": "evidence"},
    "shuffle": {"status": "confirmatory_primary", "axis": "evidence"},
    "blank": {"status": "confirmatory_secondary", "axis": "evidence"},
    "text_only": {"status": "exploratory_diagnostic", "axis": "evidence"},
}

# --- artifact paths (per configs/grounding_protocol.yaml) ---
PROTOCOL_DIR = REPO_ROOT / "results" / "grounding" / "protocol"
PREDICTIONS_DIR = REPO_ROOT / "results" / "grounding" / "predictions"
ANALYSIS_DIR = REPO_ROOT / "results" / "grounding" / "analysis"
PRIVATE_DIR = REPO_ROOT / "results" / "grounding" / "private"
IMAGE_CACHE_DIR = REPO_ROOT / "data" / "image_cache"

IDS_FILE = PROTOCOL_DIR / "vsr_test_ids.json"
SHUFFLE_MAPPING_FILE = PROTOCOL_DIR / "shuffle_mapping.json"
BLANK_SPEC_FILE = PROTOCOL_DIR / "blank_image_spec.json"
BLANK_IMAGE_FILE = PROTOCOL_DIR / "blank_image.png"
SNAPSHOT_FILE = PROTOCOL_DIR / "run_config_snapshot.json"

# --- Tier-B semantic artifacts (validity table + eligible IDs, frozen pre-result) ---
SEMANTIC_VALIDITY_FILE = PROTOCOL_DIR / "semantic_transform_validity.csv"
SEMANTIC_ELIGIBLE_FILE = PROTOCOL_DIR / "semantic_eligible_ids.json"

# --- facing/facing-away D1 diagnostic (dedicated freeze, pre-result) ---
SEMANTIC_FACING_VALIDITY_FILE = PROTOCOL_DIR / "facing_transform_validity.csv"
SEMANTIC_FACING_ELIGIBLE_FILE = PROTOCOL_DIR / "facing_eligible_ids.json"

# --- Tier-C1 visual artifacts (validity table + eligible IDs, frozen pre-result) ---
VISUAL_VALIDITY_FILE = PROTOCOL_DIR / "visual_transform_validity.csv"
VISUAL_ELIGIBLE_FILE = PROTOCOL_DIR / "visual_eligible_ids.json"
VISUAL_SPOT_DIR = PROTOCOL_DIR / "visual_spot"

TRANSFORM_VERSION = "tier_a_v0.1"
TRANSFORM_VERSION_TIER_B = "tier_b_v0.1"
TRANSFORM_VERSION_TIER_C = "tier_c_v0.1"

# --- comparisons (primary order, frozen) ---
COMPARISONS = {
    "P1": {"from": "zero_shot", "to": "general_lora", "status": "confirmatory_primary"},
    "D1": {"from": "general_lora", "to": "hardneg_lora", "status": "key_diagnostic"},
}


def sha256_file(path: Path) -> str:
    """SHA-256 of a file (streamed)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_hash() -> str:
    return sha256_text(PROMPT_TEMPLATE)


def parser_hash() -> str:
    return sha256_file(PARSER_SOURCE)


def protocol_hash() -> str:
    """Hash of the machine-readable config plus the freeze authority doc."""
    return sha256_text(
        sha256_file(PROTOCOL_YAML) + "|" + sha256_file(PROTOCOL_AUTHORITY)
    )
