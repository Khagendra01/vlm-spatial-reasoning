"""Lightweight visual annotation tool for VSR failure cases.

Usage:
    python scripts/annotate_tool.py [--port 5000]

Opens a web UI where you can visually inspect each failure case,
pick the failure mode from a dropdown, add notes, and submit.
Results accumulate in results/manual_annotations.csv.
"""

import csv
import json
import os
import argparse
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__, template_folder="templates")

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
FAILURE_JSON = RESULTS_DIR / "failure_cases_20260808_214536.csv.json"
ANNOT_CSV = RESULTS_DIR / "manual_annotations.csv"

# Try the timestamped file name, fall back to generic
if not FAILURE_JSON.exists():
    # Find the failure cases file
    for f in RESULTS_DIR.glob("failure_cases_*.json"):
        FAILURE_JSON = f
        break

FAILURE_MODES = [
    "geometric reasoning",
    "viewpoint ambiguity",
    "lexical ambiguity",
    "grounding failure",
    "occlusion",
    "small object",
    "annotation ambiguity",
    "other",
]

CSV_FIELDS = [
    "id", "relation", "family", "gt", "pred",
    "failure_mode", "confidence", "notes",
]

FAMILY_MAP = {
    "in front of": "depth", "behind": "depth", "at the back of": "depth", "ahead of": "depth",
    "left of": "horizontal", "right of": "horizontal",
    "at the left side of": "horizontal", "at the right side of": "horizontal",
    "next to": "horizontal", "beside": "horizontal",
    "above": "vertical", "below": "vertical", "over": "vertical",
    "under": "vertical", "beneath": "vertical", "on top of": "vertical",
    "facing": "orientation", "facing away from": "orientation",
    "parallel to": "orientation", "perpendicular to": "orientation",
    "in": "containment", "inside": "containment", "contains": "containment",
    "within": "containment",
    "near": "proximity", "far from": "proximity", "far away from": "proximity",
    "close to": "proximity", "away from": "proximity",
    "touching": "topology_contact", "on": "topology_contact",
    "at": "topology_contact", "at the edge of": "topology_contact",
    "off": "topology_contact",
}


def load_failures():
    with open(FAILURE_JSON) as f:
        return json.load(f)


def load_annotated():
    """Return set of already-annotated case IDs."""
    annotated = {}
    if ANNOT_CSV.exists():
        with open(ANNOT_CSV, newline="") as f:
            for row in csv.DictReader(f):
                annotated[int(row["id"])] = row
    return annotated


def save_annotation(row):
    """Append one annotation to the CSV."""
    write_header = not ANNOT_CSV.exists()
    with open(ANNOT_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


@app.route("/")
def index():
    """Show the next unannotated case, or summary if all done."""
    cases = load_failures()
    annotated = load_annotated()

    # Find next unannotated
    next_case = None
    for c in cases:
        if c["id"] not in annotated:
            next_case = c
            break

    total = len(cases)
    done = len(annotated)

    if next_case is None:
        return render_template("annotate.html",
            done=True, total=total, cases=cases, annotated=annotated,
            failure_modes=FAILURE_MODES)

    family = FAMILY_MAP.get(next_case["relation"], "unknown")
    gt_str = "TRUE" if next_case["ground_truth"] else "FALSE"
    pred_str = "TRUE" if next_case["prediction"] else "FALSE"

    return render_template("annotate.html",
        case=next_case, family=family,
        gt=gt_str, pred=pred_str,
        progress=f"{done}/{total}",
        done=False, failure_modes=FAILURE_MODES,
        remaining=total - done)


@app.route("/submit", methods=["POST"])
def submit():
    """Save annotation and go to next case."""
    case_id = int(request.form["case_id"])
    failure_mode = request.form["failure_mode"]
    confidence = request.form.get("confidence", "0.7")
    notes = request.form.get("notes", "")

    cases = load_failures()
    case = next(c for c in cases if c["id"] == case_id)
    family = FAMILY_MAP.get(case["relation"], "unknown")

    row = {
        "id": case_id,
        "relation": case["relation"],
        "family": family,
        "gt": "true" if case["ground_truth"] else "false",
        "pred": "true" if case["prediction"] else "false",
        "failure_mode": failure_mode,
        "confidence": confidence,
        "notes": notes,
    }
    save_annotation(row)
    return redirect(url_for("index"))


@app.route("/skip")
def skip():
    """Skip current case without annotating."""
    return redirect(url_for("index"))


@app.route("/api/progress")
def progress():
    """JSON endpoint for progress tracking."""
    annotated = load_annotated()
    cases = load_failures()
    return jsonify({
        "annotated": len(annotated),
        "total": len(cases),
        "remaining": len(cases) - len(annotated),
    })


@app.route("/back/<int:case_id>")
def back(case_id):
    """Go back to a specific case to re-annotate."""
    cases = load_failures()
    case = next(c for c in cases if c["id"] == case_id)
    family = FAMILY_MAP.get(case["relation"], "unknown")
    gt_str = "TRUE" if case["ground_truth"] else "FALSE"
    pred_str = "TRUE" if case["prediction"] else "FALSE"
    annotated = load_annotated()
    total = len(cases)
    existing = annotated.get(case_id)

    return render_template("annotate.html",
        case=case, family=family,
        gt=gt_str, pred=pred_str,
        progress=f"{len(annotated)}/{total}",
        done=False, failure_modes=FAILURE_MODES,
        remaining=total - len(annotated),
        existing=existing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VSR Failure Annotation Tool")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print(f"\n  VSR Failure Annotation Tool")
    print(f"  Open http://localhost:{args.port}")
    print(f"  Results saved to: {ANNOT_CSV}\n")

    app.run(host=args.host, port=args.port, debug=False)
