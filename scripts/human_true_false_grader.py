#!/usr/bin/env python3
"""
Human orientation True/False grader — Flask version (same framework as iaa_tool.py).

Usage:  python scripts/human_true_false_grader.py
        → http://localhost:5100
"""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, send_file

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "results" / "iaa" / "blind_clean_label_sheet.csv"
IMGDIR = ROOT / "results" / "iaa" / "images"
PROGRESS = ROOT / "results" / ".grader_progress.json"
OUT_CSV = ROOT / "results" / "human_orientation_gt.csv"
GT_CSV = ROOT / "results" / "smolvlm2_baseline_2195_20260808_214536.csv"
PORT = 5100

app = Flask(__name__)

with open(SHEET, encoding="utf-8") as f:
    EXAMPLES = list(csv.DictReader(f))
TOTAL = len(EXAMPLES)

gt = {}
with open(GT_CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        gt[r["id"]] = r["ground_truth"]


def load_progress():
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"answers": {}, "current": 0}


def save_progress(state):
    PROGRESS.write_text(json.dumps(state), encoding="utf-8")


@app.route("/img/<rid>")
def serve_image(rid):
    p = IMGDIR / f"id{rid}.jpg"
    if not p.exists() or p.stat().st_size == 0:
        return "not found", 404
    return send_file(str(p), mimetype="image/jpeg")


@app.route("/", methods=["GET"])
def index():
    state = load_progress()
    current = state["current"]
    if current >= TOTAL:
        return show_results(state)
    ex = EXAMPLES[current]
    answered = len(state["answers"])
    pct = answered / TOTAL * 100
    return render_template_string("""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Grader ({{answered}}/{{total}})</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
  .card { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }
  .progress { height: 6px; background: #e0e0e0; border-radius: 3px; margin-bottom: 20px; overflow: hidden; }
  .progress-fill { height: 100%; background: #4caf50; transition: width 0.3s; }
  .statement { font-size: 20px; font-weight: 600; margin: 15px 0; line-height: 1.4; }
  .relation { color: #666; margin: 5px 0 20px; font-size: 14px; }
  img { max-width: 100%; max-height: 400px; border-radius: 8px; margin: 15px 0; border: 1px solid #ddd; }
  .buttons { display: flex; gap: 16px; justify-content: center; margin-top: 20px; }
  .btn { padding: 16px 48px; font-size: 18px; font-weight: 600; border: 2px solid #ccc; border-radius: 8px; cursor: pointer; transition: all 0.2s; text-decoration: none; color: inherit; display: inline-block; }
  .btn:hover { transform: scale(1.05); }
  .btn-true { background: #e8f5e9; border-color: #4caf50; color: #2e7d32; }
  .btn-true:hover { background: #4caf50; color: white; }
  .btn-false { background: #ffebee; border-color: #f44336; color: #c62828; }
  .btn-false:hover { background: #f44336; color: white; }
  .skip { margin-top: 12px; font-size: 13px; color: #999; cursor: pointer; text-decoration: underline; display: inline-block; }
</style></head><body>
<div class="card">
  <div class="progress"><div class="progress-fill" style="width:{{pct}}%"></div></div>
  <div style="font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1px">Example {{current}} of {{total}}</div>
  <div class="relation">Relation: {{relation}}</div>
  <div class="statement">{{statement}}</div>
  <img src="/img/{{img_id}}" alt="image">
  <div class="buttons">
    <form method="POST" action="/answer" style="display:inline">
      <input type="hidden" name="id" value="{{current}}">
      <input type="hidden" name="answer" value="True">
      <button class="btn btn-true" type="submit">True</button>
    </form>
    <form method="POST" action="/answer" style="display:inline">
      <input type="hidden" name="id" value="{{current}}">
      <input type="hidden" name="answer" value="False">
      <button class="btn btn-false" type="submit">False</button>
    </form>
  </div>
  <a class="skip" href="/skip">skip</a>
</div></body></html""",
        answered=answered, total=TOTAL, pct=pct,
        current=current+1, relation=ex["relation"],
        statement=ex["statement"], img_id=ex["id"])


def show_results(state):
    answered = len(state["answers"])
    correct = sum(1 for k, v in state["answers"].items() if gt.get(k) == v)
    accuracy = correct / answered if answered else 0
    rel_stats = defaultdict(lambda: [0, 0])
    for k, v in state["answers"].items():
        rel = EXAMPLES[int(k)]["relation"]
        rel_stats[rel][1] += 1
        if gt.get(k) == v:
            rel_stats[rel][0] += 1
    rows = ""
    for rel in sorted(rel_stats):
        c, t = rel_stats[rel]
        rows += f"<tr><td>{rel}</td><td>{c}/{t}</td><td>{c/t*100:.1f}%</td></tr>\n"
    return render_template_string("""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Results</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
  .card { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .big { font-size: 48px; font-weight: 700; color: #2e7d32; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { color: #666; font-size: 12px; text-transform: uppercase; }
  .note { color: #999; font-size: 13px; margin-top: 20px; }
</style></head><body>
<div class="card">
  <h1>Your Human Performance</h1>
  <div class="big">{{accuracy}}</div>
  <p>{{correct}}/{{answered}} correct out of {{total}}</p>
  <table><tr><th>Relation</th><th>Correct/Total</th><th>Accuracy</th></tr>
  {{rows|safe}}</table>
  <p class="note">Saved to results/human_orientation_gt.csv</p>
</div></body></html""",
        accuracy=f"{accuracy*100:.1f}%", correct=correct,
        answered=answered, total=TOTAL, rows=rows)


@app.route("/skip")
def skip():
    state = load_progress()
    state["current"] += 1
    save_progress(state)
    return redirect("/")


@app.route("/answer", methods=["POST"])
def answer():
    idx = int(request.form["id"])
    answer = request.form["answer"]
    state = load_progress()
    state["answers"][str(idx)] = answer
    state["current"] = idx + 1
    save_progress(state)
    return redirect("/")


if __name__ == "__main__":
    print(f"\n=== Human Orientation True/False Grader ===")
    print(f"Open http://localhost:{PORT} in your browser")
    print(f"Rate each of the {TOTAL} orientation statements as True or False")
    print(f"Results saved on completion\n")
    app.run(host="127.0.0.1", port=PORT, debug=False)
