"""Build the blind 137/48 flagship-model evaluation package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "iaa"
DEST = ROOT / "external_eval" / "flagship_v1"
IMAGE_SOURCE = SOURCE / "images"
IMAGE_DEST = DEST / "images"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_input(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["item_id", "relation", "statement", "image_file"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "item_id": row["id"],
                    "relation": row["relation"],
                    "statement": row["statement"],
                    "image_file": f"images/id{row['id']}.jpg",
                }
            )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    IMAGE_DEST.mkdir(parents=True, exist_ok=True)

    binary = read_rows(SOURCE / "blind_clean_label_sheet.csv")
    taxonomy = read_rows(SOURCE / "blind_failure_taxonomy_sheet.csv")
    if len(binary) != 137 or len(taxonomy) != 48:
        raise SystemExit(f"unexpected source sizes: binary={len(binary)}, taxonomy={len(taxonomy)}")

    write_input(DEST / "orientation_137.csv", binary)
    write_input(DEST / "taxonomy_48.csv", taxonomy)

    ids = {row["id"] for row in binary} | {row["id"] for row in taxonomy}
    missing = []
    for item_id in sorted(ids, key=int):
        source = IMAGE_SOURCE / f"id{item_id}.jpg"
        if not source.exists():
            missing.append(str(source))
            continue
        shutil.copy2(source, IMAGE_DEST / source.name)
    if missing:
        raise SystemExit("missing images:\n" + "\n".join(missing))

    files = {}
    for path in sorted(DEST.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json":
            files[str(path.relative_to(DEST)).replace("\\", "/")] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }

    manifest = {
        "package": "flagship-model-external-evaluation",
        "version": "flagship-v1",
        "purpose": "Blind provider-neutral replay of the 137-item clean/ambiguous and 48-item taxonomy audit used for MiMo and independent human raters.",
        "source": {
            "binary_sheet": "results/iaa/blind_clean_label_sheet.csv",
            "taxonomy_sheet": "results/iaa/blind_failure_taxonomy_sheet.csv",
            "binary_items": 137,
            "taxonomy_items": 48,
            "unique_images": len(ids),
        },
        "blindness": {
            "ground_truth_included": False,
            "model_predictions_included": False,
            "prior_rater_labels_included": False,
        },
        "files": files,
    }
    (DEST / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"built {len(binary)} binary items, {len(taxonomy)} taxonomy items, {len(ids)} images")


if __name__ == "__main__":
    main()
