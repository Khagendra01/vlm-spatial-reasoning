# -*- coding: utf-8 -*-
"""
BLIND annotation tool for the second, independent human rater (IAA study).

Serves the two blind sheets exported by scripts/export_iaa_sheets.py and lets
the rater assign, per example:
  - sheet 1 (n=137): a binary clean/ambiguous flag  (clean-label audit)
  - sheet 2 (n=48):  one of the eight failure-taxonomy classes

The UI shows ONLY: id, relation, statement, and the image. Ground truth,
model predictions, and the first annotator's labels are never loaded, so they
cannot leak through the UI or the saved files.

Usage:
    python scripts/iaa_tool.py [--port 5000]

Ratings accumulate in:
    results/iaa/rater2_clean_labels.csv
    results/iaa/rater2_taxonomy.csv
"""
import argparse
import csv
import os
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

ROOT = Path(__file__).resolve().parent.parent
IAA = ROOT / "results" / "iaa"
IMGDIR = IAA / "images"

SHEET_CLEAN = IAA / "blind_clean_label_sheet.csv"
SHEET_TAXO = IAA / "blind_failure_taxonomy_sheet.csv"
OUT_CLEAN = IAA / "rater2_clean_labels.csv"
OUT_TAXO = IAA / "rater2_taxonomy.csv"

BINARY_OPTIONS = ["clean", "ambiguous"]
TAXONOMY_OPTIONS = [
    "clear_image_model_reasoning_failure",
    "camera_viewpoint_ambiguity",
    "parallel_perpendicular_geometry",
    "annotation_questionable",
    "intrinsic_orientation_ambiguous",
    "front_back_object_ambiguous",
    "small_occluded_object",
    "subject_reference_inversion",
]

app = Flask(__name__)


def load_sheet(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_done(path):
    done = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["id"]] = row
    return done


def save_row(path, row, fieldnames):
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow(row)


def img_src(entry):
    """Local image if present, else remote URL (rendered directly)."""
    local = IMGDIR / f"id{entry['id']}.jpg"
    if local.exists() and local.stat().st_size > 0:
        return "/img/%s" % entry["id"]
    return entry.get("image_url", "")


def render_sheet(sheet, out_path, options, rating_col, fieldnames):
    cases = load_sheet(sheet)
    done = load_done(out_path)
    remaining = [c for c in cases if c["id"] not in done]
    case = remaining[0] if remaining else None

    html = """
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Blind annotation</title>
    <style>
      body { font-family: Arial; margin: 24px auto; max-width: 720px; background:#fafafa; }
      .card { background:#fff; border:1px solid #ddd; border-radius:8px; padding:20px; margin-bottom:16px; }
      img { max-width:100%; max-height:420px; border-radius:6px; }
      .stmt { font-size:17px; margin:12px 0; }
      .rel { color:#666; font-size:13px; }
      .opt { display:block; margin:6px 0; }
      textarea { width:100%; height:52px; }
      button { background:#1f3d7a; color:#fff; border:none; padding:10px 22px;
               border-radius:6px; font-size:15px; cursor:pointer; }
      .progress { color:#666; font-size:13px; margin-bottom:8px; }
      .done { color:#2e6f40; font-size:18px; }
    </style></head><body>
    <h3>Blind rating &mdash; independent second annotator</h3>
    <p class="progress">{{ done }}/{{ total }} rated ({{ left }} left)</p>
    {% if not case %}
      <p class="done">All examples in this sheet are rated. Thank you.</p>
    {% else %}
      <div class="card">
        <div class="rel">id {{ case.id }} &middot; relation: {{ case.relation }}</div>
        <div class="stmt">&ldquo;{{ case.statement }}&rdquo;</div>
        <img src="{{ img }}" onerror="this.style.display='none'">
        <form method="post" action="/rate">
          <input type="hidden" name="sheet" value="{{ sheet }}">
          <input type="hidden" name="case_id" value="{{ case.id }}">
          {% for opt in options %}
          <label class="opt"><input type="radio" name="rating" value="{{ opt }}" required> {{ opt }}</label>
          {% endfor %}
          <textarea name="notes" placeholder="Notes (optional)..."></textarea><br>
          <button type="submit">Save &amp; next</button>
        </form>
      </div>
    {% endif %}
    </body></html>
    """
    return render_template_string(
        html, case=case, done=len(done), total=len(cases),
        left=len(remaining), options=options, sheet=sheet.name,
        img=img_src(case) if case else "")


@app.route("/")
def index():
    return """
    <h3>Blind IAA annotation</h3>
    <ul>
      <li><a href="/clean">Sheet 1: clean/ambiguous flag (n=137)</a></li>
      <li><a href="/taxonomy">Sheet 2: failure taxonomy (n=48)</a></li>
    </ul>
    <p style="color:#666">Read results/iaa/README.md before starting.</p>
    """


@app.route("/clean")
def clean_sheet():
    return render_sheet(SHEET_CLEAN, OUT_CLEAN, BINARY_OPTIONS,
                        "rating_clean",
                        ["id", "relation", "statement", "image_path",
                         "image_url", "rating_clean", "notes"])


@app.route("/taxonomy")
def taxonomy_sheet():
    return render_sheet(SHEET_TAXO, OUT_TAXO, TAXONOMY_OPTIONS, "class",
                        ["id", "relation", "statement", "image_path",
                         "image_url", "class", "notes"])


@app.route("/rate", methods=["POST"])
def rate():
    sheet = request.form["sheet"]
    case_id = request.form["case_id"]
    rating = request.form["rating"]
    notes = request.form.get("notes", "").strip()

    if sheet == "blind_clean_label_sheet.csv":
        src, out, col = SHEET_CLEAN, OUT_CLEAN, "rating_clean"
        if rating not in BINARY_OPTIONS:
            return "invalid rating", 400
    else:
        src, out, col = SHEET_TAXO, OUT_TAXO, "class"
        if rating not in TAXONOMY_OPTIONS:
            return "invalid rating", 400

    entry = next(c for c in load_sheet(src) if c["id"] == case_id)
    row = {"id": case_id, "relation": entry["relation"],
           "statement": entry["statement"],
           "image_path": entry["image_path"], "image_url": entry["image_url"],
           col: rating, "notes": notes}
    save_row(out, row, list(row.keys()))
    return "ok"


@app.route("/img/<case_id>")
def image(case_id):
    p = IMGDIR / f"id{case_id}.jpg"
    if not p.exists():
        return "not found", 404
    return app.send_file(str(p), mimetype="image/jpeg")


@app.route("/api/progress")
def progress():
    c_done = len(load_done(OUT_CLEAN))
    t_done = len(load_done(OUT_TAXO))
    return jsonify({"clean": c_done, "clean_total": len(load_sheet(SHEET_CLEAN)),
                    "taxonomy": t_done, "taxonomy_total": len(load_sheet(SHEET_TAXO))})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blind IAA annotation tool")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    for req in (SHEET_CLEAN, SHEET_TAXO):
        if not req.exists():
            raise SystemExit(
                f"Missing blind sheet {req}. Run scripts/export_iaa_sheets.py first.")

    print("\n  Blind IAA annotation tool (second rater)")
    print(f"  Open http://{args.host}:{args.port}")
    print(f"  Ratings saved to {OUT_CLEAN.name} / {OUT_TAXO.name}\n")
    app.run(host=args.host, port=args.port, debug=False)
