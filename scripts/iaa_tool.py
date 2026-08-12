# -*- coding: utf-8 -*-
"""
BLIND annotation web server for the second, independent human rater (IAA).

Auto-saves everything: every rating click and every note edit is persisted
immediately to results/iaa/rater2_clean_labels.csv / rater2_taxonomy.csv
(upsert — re-rating a case overwrites its row, never duplicates). You can
close the browser or reboot and resume exactly where you left off.

Sheets (exported by scripts/export_iaa_sheets.py):
  - clean:    137 orientation test examples, binary clean/ambiguous flag
  - taxonomy: 48 persistent-failure examples, eight-class failure taxonomy

Blind by construction: the UI shows ONLY id, relation, statement, and the
image. Ground truth, model predictions, and the first annotator's labels are
never loaded into this server.

Usage:
    python scripts/iaa_tool.py [--port 5000] [--host 127.0.0.1]
    open http://127.0.0.1:5000

Keyboard shortcuts (annotation page):
    1..N  select option (1-2 for clean sheet, 1-8 for taxonomy)
    N     next case        P     previous case
    R     jump to next UNRATED case
    Alt+1 .. Alt+N  also select option
Notes textarea autosaves ~0.8 s after you stop typing ("Saved" indicator).
"""
import argparse
import csv
import json
import os
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file

ROOT = Path(__file__).resolve().parent.parent
IAA = ROOT / "results" / "iaa"
IMGDIR = IAA / "images"

SHEETS = {
    "clean": {
        "title": "Clean / ambiguous flag (n=137)",
        "sheet": IAA / "blind_clean_label_sheet.csv",
        "out": IAA / "rater2_clean_labels.csv",
        "rating_col": "rating_clean",
        "options": ["clean", "ambiguous"],
    },
    "taxonomy": {
        "title": "Failure taxonomy (n=48)",
        "sheet": IAA / "blind_failure_taxonomy_sheet.csv",
        "out": IAA / "rater2_taxonomy.csv",
        "rating_col": "class",
        "options": [
            "clear_image_model_reasoning_failure",
            "camera_viewpoint_ambiguity",
            "parallel_perpendicular_geometry",
            "annotation_questionable",
            "intrinsic_orientation_ambiguous",
            "front_back_object_ambiguous",
            "small_occluded_object",
            "subject_reference_inversion",
        ],
    },
}

app = Flask(__name__)

# in-memory state per sheet: {id: {col: value}} — rebuilt from the output CSV
# on every request so external edits are picked up too.
_lock = threading.Lock()


def load_sheet_rows(name):
    cfg = SHEETS[name]
    rows = {}
    with open(cfg["sheet"], newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = r
    return rows


def load_done(name):
    cfg = SHEETS[name]
    done = {}
    if cfg["out"].exists():
        with open(cfg["out"], newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done[r["id"]] = r
    return done


def upsert(name, row):
    """Update-or-insert one row in the output CSV (safe under lock)."""
    cfg = SHEETS[name]
    fieldnames = ["id", "relation", "statement", "image_path", "image_url",
                  cfg["rating_col"], "notes"]
    with _lock:
        rows = load_done(name)
        rows[row["id"]] = row
        tmp = cfg["out"].with_suffix(".csv.tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for rid in sorted(rows, key=int):
                w.writerow(rows[rid])
        tmp.replace(cfg["out"])


def progress(name):
    done = load_done(name)
    total = len(load_sheet_rows(name))
    return {"done": len(done), "total": total,
            "pct": round(100.0 * len(done) / total, 1) if total else 100.0,
            "done_ids": sorted(done, key=int)}


def next_unrated(name, after=None):
    cfg = SHEETS[name]
    done = load_done(name)
    ids = sorted(load_sheet_rows(name), key=int)
    after_idx = ids.index(str(after)) if after in ids else -1
    for rid in ids[after_idx + 1:]:
        if rid not in done:
            return rid
    return None


def case_payload(name, rid):
    cfg = SHEETS[name]
    rows = load_sheet_rows(name)
    if rid not in rows:
        return None
    r = rows[rid]
    local = IMGDIR / f"id{rid}.jpg"
    img = (f"/img/{rid}" if local.exists() and local.stat().st_size > 0
           else r.get("image_url", ""))
    done = load_done(name)
    saved = done.get(rid, {})
    return {"id": rid, "relation": r["relation"], "statement": r["statement"],
            "img": img,
            "rating": saved.get(cfg["rating_col"], ""),
            "notes": saved.get("notes", "")}


INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Blind IAA annotation</title>
<style>
 body{font-family:Arial;margin:24px auto;max-width:760px;background:#fafafa;color:#222}
 h1{font-size:20px} h2{font-size:16px}
 .card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:18px;margin:14px 0}
 .bar{height:10px;background:#e5e5e5;border-radius:5px;overflow:hidden;margin:6px 0 14px}
 .bar>div{height:100%;background:#2e6f40;width:0%}
 a.btn{display:inline-block;background:#1f3d7a;color:#fff;text-decoration:none;
       padding:10px 18px;border-radius:6px;margin:4px 6px 4px 0}
 .muted{color:#666;font-size:13px}
</style></head><body>
<h1>Blind IAA annotation — independent second rater</h1>
<p class="muted">Read <b>results/iaa/README.md</b> before starting. Everything
autosaves; you can close the tab and resume later.</p>
{% for name, cfg in sheets.items() %}
<div class="card">
  <h2>{{ cfg.title }}</h2>
  <div class="bar"><div style="width:{{ prog[name].pct }}%"></div></div>
  <p class="muted">{{ prog[name].done }} / {{ prog[name].total }} rated
     ({{ prog[name].pct }}%)</p>
  <a class="btn" href="/sheet/{{ name }}">Resume / start</a>
</div>
{% endfor %}
</body></html>
"""

SHEET_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Blind annotation — {{ cfg.title }}</title>
<style>
 body{font-family:Arial;margin:20px auto;max-width:760px;background:#fafafa;color:#222}
 .top{position:sticky;top:0;background:#fafafa;padding:8px 0;border-bottom:1px solid #ddd}
 .bar{height:10px;background:#e5e5e5;border-radius:5px;overflow:hidden}
 .bar>div{height:100%;background:#2e6f40}
 .meta{font-size:13px;color:#666;margin-top:6px}
 .card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:18px;margin:14px 0}
 img{max-width:100%;max-height:440px;border-radius:6px;display:block;margin:8px 0}
 .stmt{font-size:17px;margin:10px 0}
 .opt{display:block;margin:7px 0;padding:8px 10px;border:1px solid #ddd;border-radius:6px;cursor:pointer}
 .opt:hover{background:#f0f4ff}
 .opt.sel{background:#dbe7ff;border-color:#1f3d7a}
 .opt input{margin-right:8px}
 textarea{width:100%;height:54px;box-sizing:border-box;margin-top:6px}
 .nav{margin:12px 0}
 button{background:#1f3d7a;color:#fff;border:none;padding:9px 16px;border-radius:6px;
        font-size:14px;cursor:pointer;margin-right:6px}
 button.ghost{background:#fff;color:#1f3d7a;border:1px solid #1f3d7a}
 .saved{color:#2e6f40;font-weight:bold;font-size:13px;margin-left:10px}
 .hint{font-size:12px;color:#999}
</style></head><body>
<div class="top">
  <div class="bar"><div id="pbar"></div></div>
  <div class="meta"><b id="doneN">0</b> / <span id="totalN">0</span> rated
    (<span id="pctN">0</span>%) &mdash; <span id="status"></span></div>
</div>

<div class="card" id="caseCard">
  <div class="meta" id="caseMeta"></div>
  <div class="stmt" id="caseStmt"></div>
  <img id="caseImg" onerror="this.style.display='none'">
  <div id="options"></div>
  <textarea id="notes" placeholder="Notes (optional)..."></textarea>
  <div class="hint" id="hint"></div>
</div>

<div class="nav">
  <button class="ghost" onclick="goPrev()">&larr; prev</button>
  <button onclick="goNext()">next &rarr;</button>
  <button class="ghost" onclick="goFirstUnrated()">jump to unrated</button>
  <span class="saved" id="savedFlash"></span>
</div>
<div class="hint" id="doneList"></div>

<script>
const NAME = {{ name|tojson }};
let state = null;       // current case
let progressInfo = null;
let notesTimer = null;

async function api(path, method, body) {
  const r = await fetch('/api/sheet/' + NAME + path, {
    method: method || 'GET',
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json();
}

async function refreshProgress() {
  progressInfo = await api('/progress');
  const p = progressInfo;
  document.getElementById('doneN').textContent = p.done;
  document.getElementById('totalN').textContent = p.total;
  document.getElementById('pctN').textContent = p.pct;
  document.getElementById('pbar').style.width = p.pct + '%';
  const unrated = p.done_ids.length;
  const list = p.done_ids.slice(-12).map(i =>
    '<a href="#" onclick="goCase(' + i + ');return false">' + i + '</a>').join(' ');
  document.getElementById('doneList').innerHTML =
    'done ids (last 12): ' + (list || 'none yet');
}

function flash(msg) {
  const el = document.getElementById('savedFlash');
  el.textContent = msg;
  clearTimeout(flash._t);
  flash._t = setTimeout(() => el.textContent = '', 1500);
}

async function renderCase(c) {
  state = c;
  document.getElementById('caseMeta').textContent =
    'id ' + c.id + '  ·  relation: ' + c.relation;
  document.getElementById('caseStmt').textContent = '“' + c.statement + '”';
  const img = document.getElementById('caseImg');
  img.src = c.img; img.style.display = '';
  const opts = {{ options|tojson }};
  const box = document.getElementById('options');
  box.innerHTML = '';
  opts.forEach((o, i) => {
    const lab = document.createElement('label');
    lab.className = 'opt' + (o === c.rating ? ' sel' : '');
    lab.innerHTML = '<input type="radio" name="rating" value="' + o + '"' +
      (o === c.rating ? ' checked' : '') + ' onchange="rate(' + i + ')"> ' +
      (i + 1) + '. ' + o;
    box.appendChild(lab);
  });
  document.getElementById('notes').value = c.notes || '';
  document.getElementById('hint').textContent =
    'keys: 1-' + opts.length + ' select · n next · p prev · r unrated';
}

async function loadCase(id) {
  const c = await api('/case/' + id);
  if (!c) { document.getElementById('caseStmt').textContent = 'case not found'; return; }
  await renderCase(c);
  await refreshProgress();
}

async function loadNext(current) {
  const c = await api('/next?after=' + (current || ''));
  if (!c) { document.getElementById('caseStmt').textContent =
    'All rated — you are done! 🎉'; await refreshProgress(); return; }
  await renderCase(c);
  await refreshProgress();
}

async function rate(i) {
  const opts = {{ options|tojson }};
  const val = opts[i];
  const notes = document.getElementById('notes').value;
  await api('/rate', 'POST', {id: state.id, rating: val, notes: notes});
  document.querySelectorAll('.opt').forEach((el, k) =>
    el.classList.toggle('sel', k === i));
  flash('saved ✓');
  await refreshProgress();
  setTimeout(() => loadNext(state.id), 120);   // auto-advance
}

function goNext() { loadNext(state ? state.id : ''); }
function goPrev() {
  const p = progressInfo;
  if (!state || !p) return;
  const ids = p.done_ids.concat(state.id).sort((a, b) => a - b);
  const i = ids.indexOf(state.id);
  loadCase(ids[Math.max(0, i - 1)]);
}
async function goFirstUnrated() { await loadNext(''); }
function goCase(id) { loadCase(String(id)); }

async function saveNotes() {
  if (!state) return;
  await api('/notes', 'POST', {id: state.id, notes: document.getElementById('notes').value});
  flash('notes saved ✓');
}
document.getElementById('notes').addEventListener('input', () => {
  clearTimeout(notesTimer);
  notesTimer = setTimeout(saveNotes, 800);
});

document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'TEXTAREA') return;
  const opts = {{ options|tojson }};
  const k = e.key.toLowerCase();
  if (k === 'n') goNext();
  else if (k === 'p') goPrev();
  else if (k === 'r') goFirstUnrated();
  else if (/^[1-9]$/.test(k) && parseInt(k) <= opts.length) rate(parseInt(k) - 1);
});

loadNext('');
</script>
</body></html>
"""


@app.route("/")
def index():
    prog = {name: progress(name) for name in SHEETS}
    return render_template_string(INDEX_HTML, sheets=SHEETS, prog=prog)


@app.route("/sheet/<name>")
def sheet(name):
    if name not in SHEETS:
        return "unknown sheet", 404
    cfg = SHEETS[name]
    return render_template_string(SHEET_HTML, cfg=cfg, name=name,
                                  options=cfg["options"])


@app.route("/api/sheet/<name>/progress")
def api_progress(name):
    if name not in SHEETS:
        return jsonify({"error": "unknown sheet"}), 404
    return jsonify(progress(name))


@app.route("/api/sheet/<name>/next")
def api_next(name):
    if name not in SHEETS:
        return jsonify({"error": "unknown sheet"}), 404
    rid = next_unrated(name, after=request.args.get("after", ""))
    if rid is None:
        return jsonify(None)
    return jsonify(case_payload(name, rid))


@app.route("/api/sheet/<name>/case/<rid>")
def api_case(name, rid):
    if name not in SHEETS:
        return jsonify({"error": "unknown sheet"}), 404
    return jsonify(case_payload(name, rid))


@app.route("/api/sheet/<name>/rate", methods=["POST"])
def api_rate(name):
    if name not in SHEETS:
        return jsonify({"error": "unknown sheet"}), 404
    cfg = SHEETS[name]
    data = request.get_json(force=True)
    rid = str(data["id"])
    rating = data["rating"]
    if rating not in cfg["options"]:
        return jsonify({"error": "invalid rating"}), 400
    rows = load_sheet_rows(name)
    if rid not in rows:
        return jsonify({"error": "unknown case"}), 404
    r = rows[rid]
    upsert(name, {"id": rid, "relation": r["relation"],
                  "statement": r["statement"],
                  "image_path": r.get("image_path", ""),
                  "image_url": r.get("image_url", ""),
                  cfg["rating_col"]: rating,
                  "notes": data.get("notes", "")})
    return jsonify({"ok": True, "saved_at": time.time()})


@app.route("/api/sheet/<name>/notes", methods=["POST"])
def api_notes(name):
    if name not in SHEETS:
        return jsonify({"error": "unknown sheet"}), 404
    cfg = SHEETS[name]
    data = request.get_json(force=True)
    rid = str(data["id"])
    rows = load_sheet_rows(name)
    if rid not in rows:
        return jsonify({"error": "unknown case"}), 404
    done = load_done(name)
    prev = done.get(rid, {})
    r = rows[rid]
    upsert(name, {"id": rid, "relation": r["relation"],
                  "statement": r["statement"],
                  "image_path": r.get("image_path", ""),
                  "image_url": r.get("image_url", ""),
                  cfg["rating_col"]: prev.get(cfg["rating_col"], ""),
                  "notes": data.get("notes", "")})
    return jsonify({"ok": True, "saved_at": time.time()})


@app.route("/img/<rid>")
def img(rid):
    p = IMGDIR / f"id{rid}.jpg"
    if not p.exists():
        return "not found", 404
    return send_file(str(p), mimetype="image/jpeg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blind IAA annotation server")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    for cfg in SHEETS.values():
        if not cfg["sheet"].exists():
            raise SystemExit(
                f"Missing blind sheet {cfg['sheet']}. Run "
                "scripts/export_iaa_sheets.py first.")

    print("\n  Blind IAA annotation server (auto-save ON)")
    print(f"  Open http://{args.host}:{args.port}")
    print(f"  Ratings -> {SHEETS['clean']['out'].name} / "
          f"{SHEETS['taxonomy']['out'].name} (saved on every click)\n")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
