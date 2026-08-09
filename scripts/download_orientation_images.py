"""Download images for the 48 persistent orientation failures for manual annotation."""
import json, os, urllib.request, sys

with open("results/orientation_persistent_failures_v2.json", encoding="utf-8") as f:
    cases = json.load(f)

out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.environ.get("TEMP", "/tmp"), "opencode", "orientation_ann")
os.makedirs(out_dir, exist_ok=True)

print(f"Downloading {len(cases)} images to {out_dir}")
ok = fail = 0
for c in cases:
    url = c["image_url"]
    fname = os.path.join(out_dir, f"id{c['id']}.jpg")
    if os.path.exists(fname) and os.path.getsize(fname) > 0:
        ok += 1
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r, open(fname, "wb") as f:
            f.write(r.read())
        ok += 1
    except Exception as e:
        fail += 1
        print(f"FAIL id={c['id']} {url}: {e}")
print(f"Done: {ok} ok, {fail} failed")
