"""
Orientation failure annotation tool.
Shows persistent hard cases with images and predictions for manual categorization.
"""
import json, os, hashlib
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

DATA_FILE = "results/orientation_persistent_failures.json"
ANNOTATIONS_FILE = "results/orientation_annotations.json"

with open(DATA_FILE) as f:
    cases = json.load(f)

# Load existing annotations
annotations = {}
if os.path.exists(ANNOTATIONS_FILE):
    with open(ANNOTATIONS_FILE) as f:
        annotations = json.load(f)

CATEGORIES = [
    "object_pose_not_clear",
    "intrinsic_orientation_ambiguous",
    "camera_viewpoint_ambiguity",
    "parallel_perpendicular_geometry",
    "front_back_object_ambiguous",
    "subject_reference_inversion",
    "small_occluded_object",
    "annotation_questionable",
    "clear_image_model_reasoning_failure",
]

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<title>Orientation Failure Annotation</title>
<style>
body { font-family: Arial; margin: 20px; background: #f5f5f5; }
.case { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; }
.case-header { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
.statement { font-size: 16px; color: #333; margin: 10px 0; }
.relation { color: #666; font-size: 14px; }
.image-container { display: flex; gap: 20px; margin: 15px 0; }
.prediction { padding: 5px 10px; border-radius: 4px; margin: 5px 0; }
.correct { background: #d4edda; color: #155724; }
.wrong { background: #f8d7da; color: #721c24; }
.categories { margin: 15px 0; }
.categories label { display: block; margin: 5px 0; cursor: pointer; }
.categories input[type=radio] { margin-right: 8px; }
textarea { width: 100%; height: 60px; margin-top: 10px; }
.save-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; }
.save-btn:hover { background: #0056b3; }
.saved { color: green; font-weight: bold; margin-left: 10px; }
.progress { font-size: 14px; color: #666; margin-bottom: 10px; }
</style>
</head>
<body>
<h1>Orientation Failure Annotation</h1>
<p>Manually categorize each persistent orientation failure.</p>
<p class="progress">Case <span id="case-num">1</span>/{{ cases|length }}</p>

{% for case in cases %}
<div class="case" id="case-{{ case.id }}">
    <div class="case-header">Case {{ case.id }}: {{ case.relation }}</div>
    <div class="statement">"{{ case.statement }}"</div>
    <div class="relation">Label: <b>{{ case.label }}</b></div>
    
    <div class="image-container">
        <div>
            <img src="{{ case.image_url }}" style="max-width:300px; max-height:300px;" 
                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22><text y=%22150%22 x=%2250%22>Image unavailable</text></svg>'">
        </div>
        <div style="min-width: 250px;">
            <div class="prediction {{ 'correct' if case.2B_zero_correct else 'wrong' }}">
                2B Zero-shot: {{ case.2B_zero_pred }} ({{ 'correct' if case.2B_zero_correct else 'wrong' }})
            </div>
            <div class="prediction {{ 'correct' if case.2B_lora_correct else 'wrong' }}">
                2B LoRA: {{ case.2B_lora_pred }} ({{ 'correct' if case.2B_lora_correct else 'wrong' }})
            </div>
            <div class="prediction wrong">
                7B Zero-shot: {{ case.7B_zero_pred }} (wrong)
            </div>
            <div class="prediction {{ 'correct' if case.7B_lora_correct else 'wrong' }}">
                7B LoRA: {{ case.7B_lora_pred }} ({{ 'correct' if case.7B_lora_correct else 'wrong' }})
            </div>
        </div>
    </div>
    
    <div class="categories">
        <b>Failure category:</b><br>
        {% for cat in categories %}
        <label>
            <input type="radio" name="cat_{{ case.id }}" value="{{ cat }}">
            {{ cat | replace('_', ' ') | title }}
        </label>
        {% endfor %}
    </div>
    
    <textarea id="notes_{{ case.id }}" placeholder="Notes (optional)..."></textarea>
    <br>
    <button class="save-btn" onclick="saveAnnotation({{ case.id }})">Save</button>
    <span class="saved" id="saved_{{ case.id }}"></span>
</div>
{% endfor %}

<script>
function saveAnnotation(caseId) {
    const cat = document.querySelector(`input[name="cat_${caseId}"]:checked`);
    const notes = document.getElementById(`notes_${caseId}`).value;
    
    fetch('/annotate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            id: caseId,
            category: cat ? cat.value : null,
            notes: notes
        })
    }).then(r => r.json()).then(d => {
        document.getElementById(`saved_${caseId}`).textContent = 'Saved!';
        setTimeout(() => document.getElementById(`saved_${caseId}`).textContent = '', 2000);
    });
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE, cases=cases, categories=CATEGORIES)

@app.route("/annotate", methods=["POST"])
def annotate():
    data = request.json
    annotations[str(data["id"])] = {
        "category": data["category"],
        "notes": data["notes"],
    }
    with open(ANNOTATIONS_FILE, "w") as f:
        json.dump(annotations, f, indent=2)
    return jsonify({"ok": True})

@app.route("/progress")
def progress():
    total = len(cases)
    done = len(annotations)
    return jsonify({"total": total, "done": done, "pct": done/total*100})

if __name__ == "__main__":
    print(f"Starting annotation tool with {len(cases)} cases")
    print(f"Annotations so far: {len(annotations)}")
    app.run(host="0.0.0.0", port=5000, debug=False)
