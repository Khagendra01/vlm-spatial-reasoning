"""Summary analysis of orientation persistent failure annotations."""
import csv, json
from collections import Counter

with open("results/orientation_persistent_annotations.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open("results/orientation_persistent_failures_v2.json", encoding="utf-8") as f:
    cases = json.load(f)

print(f"Total annotated: {len(rows)}")
print()

# By annotation category
cats = Counter(r["annotation"] for r in rows)
print("=== FAILURE MODE DISTRIBUTION ===")
for cat, n in cats.most_common():
    pct = n / len(rows) * 100
    print(f"  {cat:45s} {n:3d} ({pct:.1f}%)")

print()
by_wc = Counter(r["wrong_count"] for r in rows)
print("=== BY WRONG COUNT ===")
for wc in sorted(by_wc.keys(), reverse=True):
    print(f"  wrong={wc}: {by_wc[wc]} cases")

print()
print("=== ANNOTATION x WRONG COUNT ===")
for cat, _ in cats.most_common():
    for wc in ["4", "3", "2"]:
        subset = [r for r in rows if r["annotation"] == cat and r["wrong_count"] == wc]
        if subset:
            ids = [r["id"] for r in subset]
            print(f"  {cat:40s} w={wc}: {len(subset):2d}  ids={ids}")

print()
rels = Counter(r["relation"] for r in rows)
print("=== BY RELATION ===")
for rel, n in rels.most_common():
    print(f"  {rel:20s} {n:3d}")

print()
labels = Counter(r["label"] for r in rows)
print("=== BY LABEL ===")
for l, n in labels.most_common():
    print(f"  {l:5s} {n:3d}")

print()
regressed = [c for c in cases if c["2B_zero_correct"] and not c["7B_zero_correct"]]
print(f"=== 7B REGRESSION CASES (2B right, 7B wrong) ===")
print(f"Count: {len(regressed)}")
for c in regressed:
    ann_row = next((r for r in rows if r["id"] == c["id"]), None)
    ann = ann_row["annotation"] if ann_row else "unknown"
    stmt = c["statement"][:65]
    print(f"  id={c['id']:>5s} {c['relation']:18s} {stmt:65s} [{ann}]")
