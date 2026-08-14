"""Hashing, provenance, and private-hash helpers for the grounding audit.

"Private" hashes (model/checkpoint/config) are written under
results/grounding/private/ which is gitignored: they are recorded for
reproducibility but are not part of the public result artifacts.
"""

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config


def git_commit() -> str:
    """Current git commit (short) or 'unknown' if not available."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=config.REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def git_branch() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=config.REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    return config.sha256_file(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def env_snapshot() -> dict:
    """Minimal environment snapshot for run metadata."""
    try:
        import torch
        torch_version = torch.__version__
        cuda = torch.version.cuda
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        torch_version, cuda, device = "n/a", "n/a", "n/a"
    try:
        import transformers
        tf_version = transformers.__version__
    except Exception:
        tf_version = "n/a"
    try:
        import peft
        peft_version = peft.__version__
    except Exception:
        peft_version = "n/a"
    try:
        import datasets
        ds_version = datasets.__version__
    except Exception:
        ds_version = "n/a"
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch_version,
        "torch_cuda": cuda,
        "device": device,
        "transformers": tf_version,
        "peft": peft_version,
        "datasets": ds_version,
        "cwd": str(config.REPO_ROOT),
        "argv": sys.argv,
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> str:
    """Write JSON (sorted keys, compact hashes) and return file sha256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    return sha256_file(path)


def adapter_hashes(adapter_path: Path) -> dict:
    """SHA-256 of every file in a PEFT adapter directory (small)."""
    if adapter_path is None or not Path(adapter_path).exists():
        return {}
    out = {}
    for p in sorted(Path(adapter_path).rglob("*")):
        if p.is_file():
            out[str(p.relative_to(adapter_path))] = sha256_file(p)
    return out


def model_shard_hashes(model_dir: Path) -> dict:
    """SHA-256 of safetensors/bin shards in a locally cached model dir."""
    if not model_dir.exists():
        return {}
    out = {}
    for p in sorted(model_dir.rglob("*.safetensors")) + sorted(model_dir.rglob("*.bin")):
        out[str(p.relative_to(model_dir))] = sha256_file(p)
    return out


def record_private_hashes(run_id: str, checkpoint: dict) -> dict:
    """Record model/checkpoint/config hashes privately (gitignored)."""
    entry = {
        "run_id": run_id,
        "model_id": checkpoint["model_id"],
        "adapter_path": str(checkpoint["adapter_path"]) if checkpoint["adapter_path"] else None,
        "adapter_hashes": adapter_hashes(checkpoint["adapter_path"]),
        "prompt_hash": config.prompt_hash(),
        "parser_hash": config.parser_hash(),
        "protocol_hash": config.protocol_hash(),
        "recorded_at": utc_now_iso(),
    }
    config.PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.PRIVATE_DIR / f"hashes_{run_id}.json"
    write_json(path, entry)
    return entry
