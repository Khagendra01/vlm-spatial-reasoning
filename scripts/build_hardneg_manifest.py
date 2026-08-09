"""
Build the hard-negative orientation training manifest.

Design (fair comparison vs 7B General LoRA = general_train.jsonl, 2000 rows):
  - Total rows: 2000 (same as control).
  - Non-orientation rows: taken from general_train.jsonl, every family trimmed
    proportionally to make room for an enlarged orientation block.
  - Orientation block: audited-clean originals + paired hard negatives
    (facing <-> facing away from, parallel to <-> perpendicular to).
    The negative of a True statement is the same image with the paired
    relation swapped and label flipped, and vice versa.
  - Questionable examples (final_status != clean) are excluded from originals
    AND are never used to generate synthetic negatives.

Usage: python3 scripts/build_hardneg_manifest.py [--orient-block O]
"""
import os, sys, json, csv, argparse
from collections import defaultdict, Counter

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

RELATION_PAIRS = [
    ("facing", "facing away from"),
    ("parallel to", "perpendicular to"),
]

def swap_relation(statement: str, from_rel: str, to_rel: str) -> str:
    return statement.replace(f" {from_rel} ", f" {to_rel} ")

def flip_relation(statement: str, relation: str) -> tuple[str, str]:
    for a, b in RELATION_PAIRS:
        if relation == a:
            return swap_relation(statement, a, b), b
        if relation == b:
            return swap_relation(statement, b, a), a
    return None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orient-block", type=int, default=234,
                        help="Target size of the orientation block (originals + negatives)")
    parser.add_argument("--out", default="data/manifests/hardneg_train.jsonl")
    args = parser.parse_args()

    audit_path = "results/orientation_train_audit.csv"
    with open(audit_path) as f:
        audit_rows = list(csv.DictReader(f))
    excluded = {r["id"] for r in audit_rows if r["final_status"].strip() == "exclude"}
    no_neg = {r["id"] for r in audit_rows if r["final_status"].strip() == "original_only"}
    print(f"Excluded from everything: {len(excluded)}")
    print(f"Original-only (no negatives): {len(no_neg)}")
    clean_audit = [r for r in audit_rows if r["id"] not in excluded]
    print(f"Usable pool: {len(clean_audit)}")
    by_rel = Counter(r["relation"] for r in clean_audit)
    print("  by relation:", dict(by_rel))

    # Load general manifest
    with open("data/manifests/general_train.jsonl") as f:
        general = [json.loads(l) for l in f]
    non_orient = [e for e in general if e["family"] != "orientation"]
    orient_gen = [e for e in general if e["family"] == "orientation"]
    print(f"General manifest: {len(general)} (non-orient {len(non_orient)}, orient {len(orient_gen)})")

    audit_by_id = {r["id"]: r for r in audit_rows}

    # ── Orientation block ──
    # Originals: prefer general manifest's orientation examples, then fill from
    # the audited pool (all 4 relations) to reach the target. Excluded examples
    # are never used; original_only examples are kept but not inverted.
    originals = []
    seen_ids = set()
    for e in orient_gen:
        if str(e["id"]) in excluded:
            continue
        originals.append(e)
        seen_ids.add(str(e["id"]))

    # Fill with audited pool examples (stratified across 4 relations)
    n_originals = args.orient_block // 2
    fill_needed = n_originals - len(originals)
    if fill_needed > 0:
        pool_by_rel = defaultdict(list)
        for r in clean_audit:
            if r["id"] in seen_ids:
                continue
            pool_by_rel[r["relation"]].append(r)
        keys = sorted(pool_by_rel.keys())
        i = 0
        while len(originals) < n_originals and fill_needed > 0 and keys:
            rel = keys[i % len(keys)]
            pool = pool_by_rel[rel]
            if pool:
                r = pool.pop(0)
                originals.append({
                    "id": int(r["id"]), "statement": r["statement"],
                    "label": r["label"] == "True", "relation": r["relation"],
                    "family": "orientation", "image": r["image"],
                })
                seen_ids.add(r["id"])
            else:
                keys.remove(rel)
                continue
            fill_needed -= 1
            i += 1
    print(f"Orientation originals: {len(originals)}")

    # Paired negatives from clean originals (never from excluded/original_only)
    negatives = []
    for e in originals:
        if str(e["id"]) in no_neg or str(e["id"]) in excluded:
            continue
        new_stmt, new_rel = flip_relation(e["statement"], e["relation"])
        if new_stmt is None or new_stmt == e["statement"]:
            continue
        negatives.append({
            "id": f"{e['id']}_hn", "statement": new_stmt,
            "label": not e["label"], "relation": new_rel,
            "family": "orientation", "image": e["image"],
            "source_id": e["id"], "is_hard_negative": True,
        })
    print(f"Generated negatives: {len(negatives)}")

    orient_block = originals + negatives
    print(f"Orientation block total: {len(orient_block)}")
    print("  block relations:", dict(Counter(e["relation"] for e in orient_block)))
    print("  block labels:", dict(Counter(e["label"] for e in orient_block)))

    # ── Non-orientation: proportional trim of general manifest ──
    n_non = 2000 - len(orient_block)
    fam_counts = Counter(e["family"] for e in non_orient)
    non_by_fam = defaultdict(list)
    for e in non_orient:
        non_by_fam[e["family"]].append(e)

    alloc = {}
    remaining = n_non
    fams = sorted(fam_counts.keys(), key=lambda f: -fam_counts[f])
    for f in fams:
        if f == fams[-1]:
            alloc[f] = remaining
        else:
            alloc[f] = int(n_non * fam_counts[f] / len(non_orient))
            remaining -= alloc[f]

    non_orient_out = []
    for f, n in alloc.items():
        pool = non_by_fam[f]
        non_orient_out.extend(pool[:n])
    print(f"Non-orientation: {len(non_orient_out)}")

    manifest = non_orient_out + orient_block
    with open(args.out, "w") as f:
        for e in manifest:
            row = {
                "id": e["id"], "statement": e["statement"], "label": e["label"],
                "relation": e["relation"], "family": e["family"], "image": e["image"],
            }
            if e.get("is_hard_negative"):
                row["is_hard_negative"] = True
                row["source_id"] = e["source_id"]
            f.write(json.dumps(row) + "\n")

    print(f"\nSaved: {args.out} ({len(manifest)} rows)")
    dist = Counter(e["family"] for e in manifest)
    print("Family distribution:")
    for f, n in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"  {f:20s} {n:5d} {n/len(manifest)*100:5.1f}%")
    orient_rel = Counter(e["relation"] for e in orient_block)
    print("Orientation block by relation:", dict(orient_rel))
    hn = sum(1 for e in manifest if e.get("is_hard_negative"))
    print(f"Hard negatives in manifest: {hn}")

if __name__ == "__main__":
    main()
