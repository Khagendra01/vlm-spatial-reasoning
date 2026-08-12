"""Build the full 2,195-example VSR blind evaluation package for
external vision models (GPT / Gemini), mirroring the frozen MiMo protocol:
same prompt verbatim, one image per request, invalid outputs counted wrong,
no ground truth or prior predictions included.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "mimo" / "mimo_v25_zeroshot_predictions.csv"
FLIPS = ROOT / "results" / "mimo" / "consistency_flips_mimo.csv"
DEST = ROOT / "external_eval" / "vsr_full_v1"

FROZEN_PROMPT = (
    'Look at the image carefully.\n\nStatement: "{statement}"\n\n'
    "Is this statement true or false?\n\n"
    "Answer with exactly one word: True or False."
)

FAMILY_NAMES = {
    "FB": "front/behind",
    "LR": "left/right",
    "FF": "facing/facing-away",
    "PP": "parallel/perpendicular (soft complement, treated separately)",
}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    with SRC.open(encoding="utf-8-sig", newline="") as f:
        vsr = {r["id"]: r for r in csv.DictReader(f)}
    if len(vsr) != 2195:
        raise SystemExit(f"unexpected VSR row count: {len(vsr)}")

    # Blind input sheets (no ground truth, no predictions).
    with (DEST / "vsr_2195.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "relation", "statement", "image_url"])
        for i in sorted(vsr, key=int):
            r = vsr[i]
            w.writerow([i, r["relation"], r["statement"], r["image_url"]])

    with FLIPS.open(encoding="utf-8-sig", newline="") as f:
        flips = list(csv.DictReader(f))
    with (DEST / "consistency_pairs.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "family", "item_id", "statement_a", "statement_b",
                    "image_url"])
        for r in flips:
            i = r["id"]
            orig = vsr[i]["statement"]
            w.writerow([f"{r['family']}-{i}", r["family"], i, orig,
                        r["statement"], r["image_url"]])

    prompts = (
        "# Frozen prompts (verbatim from the MiMo protocol, supplementary App. A)\n\n"
        "## VSR binary audit (vsr_2195.csv)\n\n"
        "For each item, attach the image from `image_url` (or a local copy) and "
        "submit exactly one request. Answer with exactly one word:\n\n"
        "```\n" + FROZEN_PROMPT + "\n```\n\n"
        "`parsed_binary` must be exactly `True`, `False`, or `INVALID`. Any "
        "response that is not an unambiguous single verdict after the provider's "
        "documented normalization is `INVALID` and counts as wrong in aggregate "
        "reporting. Use the lowest available reasoning/thinking setting for the "
        "primary run and record it; freeze image detail/resolution and report it; "
        "record model id, evaluation date, and endpoint.\n\n"
        "## Complementary consistency (consistency_pairs.csv)\n\n"
        "Answer `statement_a` and `statement_b` of each pair in two independent "
        "requests (same image). Do not show the model the other statement. "
        "Consistency is computed later by comparing the two verdicts.\n\n"
        "Families: FB=front/behind, LR=left/right, FF=facing/facing-away, "
        "PP=parallel/perpendicular (soft complement; do not pool with the "
        "strict families).\n"
    )
    (DEST / "prompts.md").write_text(prompts, encoding="utf-8")

    (DEST / "results_template.csv").write_text(
        "run_id,model_id,provider,eval_date_utc,item_id,relation,raw_response,parsed_binary,invalid_reason,latency_ms\n",
        encoding="utf-8",
    )
    (DEST / "consistency_results_template.csv").write_text(
        "run_id,model_id,provider,eval_date_utc,pair_id,family,item_id,part,raw_response,parsed_binary,invalid_reason,latency_ms\n",
        encoding="utf-8",
    )

    report = (
        "# External VSR report: `{model_id}`\n\n"
        "- run_id, model id/version, provider, eval date (UTC), endpoint\n"
        "- reasoning/thinking setting, image-detail setting, temperature, "
        "max output tokens, retries, cost\n\n"
        "## 1. VSR 2,195\n\n"
        "- overall accuracy (with 95% Wilson CI) **after** scoring against the "
        "VSR ground truth on the validator's side; report invalid outputs "
        "separately and count them wrong\n"
        "- per relation family: orientation, depth, horizontal, containment, "
        "topology/contact\n"
        "- per orientation relation: facing (n=64), facing away from (n=39), "
        "parallel to (n=22), perpendicular to (n=12)\n\n"
        "## 2. Consistency (verdicts only; no scoring against ground truth)\n\n"
        "- facing/facing-away (FF): consistency %, both-True %, both-False % "
        "(n=103)\n"
        "- front/behind (FB, n=314) and left/right (LR, n=245): consistency %\n"
        "- parallel/perpendicular (PP, n=34): report separately, soft complement\n\n"
        "## 3. Guardrails\n"
        "- identical prompt/parser/accounting as MiMo (App. A); different "
        "provider settings must be disclosed, not silently equalized\n"
        "- no ground truth, predictions, or rater labels were included in the "
        "input sheets\n"
    )
    (DEST / "REPORT_TEMPLATE.md").write_text(report, encoding="utf-8")

    readme = (
        "# Full VSR blind evaluation package (2,195 items)\n\n"
        "Blind, provider-neutral replay of the full VSR random-split test set "
        "for external vision models, mirroring the frozen MiMo protocol.\n\n"
        "- `vsr_2195.csv`: item_id, relation, statement, image_url (COCO train2017)\n"
        "- `consistency_pairs.csv`: 696 complementary pairs (FB=314, LR=245, "
        "FF=103, PP=34)\n"
        "- `prompts.md`: frozen prompt verbatim (App. A) + run rules\n"
        "- `results_template.csv`, `consistency_results_template.csv`: append "
        "one row per request\n"
        "- `REPORT_TEMPLATE.md`: required per-model report format\n"
        "- `MANIFEST.json`: counts, blindness declaration, prompt hash\n\n"
        "Images are NOT committed (COCO URLs provided in the CSVs; cache locally "
        "and verify against the SHA-256 map in MANIFEST.json if byte-identity "
        "matters). No ground truth, model predictions, or rater labels are "
        "included. Run one item per request; preserve raw responses; count "
        "invalid outputs as wrong; freeze and report provider settings.\n"
    )
    (DEST / "README.md").write_text(readme, encoding="utf-8")

    manifest = {
        "package": "vsr-full-external-evaluation",
        "version": "vsr-full-v1",
        "source": "results/mimo/mimo_v25_zeroshot_predictions.csv (ids/statements/relations/image_urls only)",
        "items": 2195,
        "consistency_pairs": len(flips),
        "consistency_families": {k: n for k, n in sorted(
            {r: sum(1 for x in flips if x["family"] == r) for r in set(x["family"] for x in flips)}.items())},
        "blindness": {
            "ground_truth_included": False,
            "model_predictions_included": False,
            "prior_rater_labels_included": False,
        },
        "frozen_prompt_sha256": hashlib.sha256(FROZEN_PROMPT.encode()).hexdigest(),
        "images": {"committed": False, "source": "image_url column (COCO train2017)"},
    }
    (DEST / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"built {len(vsr)} items + {len(flips)} pairs at {DEST}")


if __name__ == "__main__":
    main()
