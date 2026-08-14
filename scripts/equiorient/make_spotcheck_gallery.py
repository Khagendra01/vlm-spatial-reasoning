"""Generate the EquiOrient human spot-check gallery (self-contained HTML).

Opens via double-click (file://) — no server required. Shows all 51
original|transformed pairs with per-image FLAG buttons and a JSON
verdict-download. Also offers a served mode via `python -m http.server`.
"""
import json
import sys
from pathlib import Path

WT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WT))

INSP = WT / "results" / "equiorient" / "human_inspection"
OUT = INSP / "gallery.html"

manifest = json.load(open(INSP / "manifest.json", encoding="utf-8"))
pngs = sorted(p.name for p in INSP.glob("*.png"))

# one card per PNG: pick the first (scene, transform) row for the caption
rows_by_png = {}
for r in manifest["rows"]:
    rows_by_png.setdefault(r["png"], r)

# per-transform human-readable expectation summary
EXPECT = {
    "hflip": "horizontal reflection: left<->right flip; above/below, "
             "in_front_of/behind, parallel/perpendicular unchanged",
    "vflip": "vertical reflection: above<->below flip; left/right, "
             "in_front_of/behind, parallel/perpendicular unchanged",
    "v_after_h": "V after H (composition): left<->right AND above<->below "
                 "flip; depth + orientation unchanged",
}

cards = []
for png in pngs:
    r = rows_by_png[png]
    cards.append(f'''
    <div class="card" id="card-{r['scene_id']}-{r['transform']}">
      <div class="head">
        <span class="scene">{r['scene_id']}</span>
        <span class="tr">{r['transform']}</span>
      </div>
      <img src="{png}" alt="{png}" loading="lazy"/>
      <div class="expect">Expect: {EXPECT.get(r['transform'], '')}</div>
      <div class="buttons">
        <button class="ok" onclick="mark('{r['scene_id']}|{r['transform']}', true)">&#10003; looks right</button>
        <button class="flag" onclick="mark('{r['scene_id']}|{r['transform']}', false)">&#9888; flag</button>
        <span class="state" id="st-{r['scene_id']}|{r['transform']}"></span>
      </div>
    </div>''')

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>EquiOrient — Gate 2 human spot check (51 pairs)</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 24px; background: #f4f4f6; }}
  h1 {{ font-size: 20px; }} p {{ max-width: 900px; color: #444; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(460px, 1fr)); gap: 14px; }}
  .card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }}
  .head {{ display: flex; justify-content: space-between; margin-bottom: 6px; }}
  .scene {{ font-weight: 700; }} .tr {{ color: #1f6feb; font-family: Consolas, monospace; }}
  img {{ width: 100%; border: 1px solid #ccc; border-radius: 4px; }}
  .expect {{ font-size: 12px; color: #666; margin: 6px 0; }}
  .buttons {{ display: flex; gap: 8px; align-items: center; }}
  button {{ padding: 4px 12px; border-radius: 4px; border: 1px solid #999; cursor: pointer; }}
  .ok {{ background: #e6f4ea; }} .ok.done {{ background: #34a853; color: #fff; }}
  .flag {{ background: #fdecea; }} .flag.done {{ background: #ea4335; color: #fff; }}
  .state {{ font-size: 12px; margin-left: 6px; }}
  .toolbar {{ margin: 14px 0; }}
  .progress {{ font-weight: 600; }}
</style>
</head>
<body>
<h1>EquiOrient — Gate 2 human spot check</h1>
<p>Look at each pair: LEFT = original scene, RIGHT = transformed scene
(object ids labeled). Verify the transform did what the algebra claims
(see the &quot;Expect&quot; line under each image) and that nothing looks
broken (collisions, wrong flips, artifacts). Click a verdict per image.
Then press <b>Download verdicts</b> and send me the JSON.</p>
<div class="toolbar">
  <button onclick="download()">&#8681; Download verdicts (JSON)</button>
  <span class="progress" id="prog">0/51 checked</span>
</div>
<div class="grid">
{''.join(cards)}
</div>
<script>
const verdicts = {{}};
const TOTAL = {len(cards)};
function mark(key, ok) {{
  verdicts[key] = ok;
  const [scene, tr] = key.split('|');
  const okBtn = document.querySelector(`#card-${{scene}}-${{tr}} .ok`);
  const flBtn = document.querySelector(`#card-${{scene}}-${{tr}} .flag`);
  const st = document.getElementById('st-' + key);
  okBtn.classList.toggle('done', ok);
  flBtn.classList.toggle('done', !ok);
  st.textContent = ok ? 'verified' : 'FLAGGED';
  document.getElementById('prog').textContent =
    Object.keys(verdicts).length + '/' + TOTAL + ' checked';
}}
function download() {{
  const blob = new Blob([JSON.stringify(verdicts, null, 2)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'equiorient_spotcheck_verdicts.json';
  a.click();
}}
</script>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT}  ({len(cards)} cards, {len(pngs)} images)")
