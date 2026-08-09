"""
Build the persistent orientation failure set for manual annotation.

Definition (user-specified priority):
  A = wrong in BOTH 7B zero-shot AND 7B LoRA   (gold: resistant to scale + adaptation)
  C = wrong in >=3 of 4 conditions             (broad persistence)
  E = wrong in BOTH 2B zero-shot AND 7B zero-shot (scaling-persistent)

Output: results/orientation_persistent_failures_v2.json (~50 cases) with
full prediction record for 4 conditions + image URL, sorted by persistence.
"""
import csv, json

def load(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

BASE = "results/smolvlm2_baseline_2195_20260808_214536.csv"
GEN2 = "results/general_lora_predictions_20260809_054915.csv"
Z7 = "results/qwen2vl_7b_predictions_20260809_064919.csv"
GEN7 = "results/7B_general_lora_predictions_20260809_094930.csv"

RELATION_FAMILIES = {
    "horizontal": ["left of", "right of", "at the left side of", "at the right side of",
                   "at the side of", "beside", "next to", "alongside", "across from"],
    "vertical": ["above", "below", "over", "under", "beneath", "on top of"],
    "depth": ["in front of", "behind", "at the back of", "ahead of"],
    "orientation": ["facing", "facing away from", "parallel to", "perpendicular to"],
    "containment": ["in", "inside", "contains", "within", "enclosed by"],
    "proximity": ["near", "far from", "far away from", "close to", "away from"],
    "topology_contact": ["touching", "on", "at", "at the edge of", "against",
                         "attached to", "connected to", "detached from"],
    "compositional": ["part of", "has as a part", "consists of", "surrounding",
                      "in the middle of", "among"],
}

def fam(rel):
    for k, v in RELATION_FAMILIES.items():
        if rel in v:
            return k
    return "unknown"

def corr(r):
    return r["correct"].strip().lower() == "true"

def main():
    base, gen2, z7, gen7 = load(BASE), load(GEN2), load(Z7), load(GEN7)
    idx = [i for i in range(len(base)) if fam(base[i]["relation"]) == "orientation"]
    print(f"Orientation examples: {len(idx)}")

    c_base = [corr(base[i]) for i in idx]
    c_gen2 = [corr(gen2[i]) for i in idx]
    c_z7 = [corr(z7[i]) for i in idx]
    c_gen7 = [corr(gen7[i]) for i in idx]

    def wcount(i):
        return sum([not c_base[i], not c_gen2[i], not c_z7[i], not c_gen7[i]])

    A = set(i for i in range(len(idx)) if (not c_z7[i]) and (not c_gen7[i]))
    C = set(i for i in range(len(idx)) if wcount(i) >= 3)
    E = set(i for i in range(len(idx)) if (not c_base[i]) and (not c_z7[i]))
    U = sorted(A | C | E, key=lambda i: (-wcount(i), i))
    print(f"Set A (7B-persistent)  : {len(A)}")
    print(f"Set C (>=3 of 4 wrong) : {len(C)}")
    print(f"Set E (scaling-persist): {len(E)}")
    print(f"Union (annotation set) : {len(U)}")

    out = []
    for i in U:
        r = base[idx[i]]
        out.append({
            "id": r["id"],
            "statement": r["statement"],
            "relation": r["relation"],
            "label": r["ground_truth"],
            "image_url": r["image_url"],
            "wrong_count": wcount(i),
            "in_set": {
                "A_7b_persistent": i in A,
                "C_ge3of4": i in C,
                "E_scaling_persistent": i in E,
            },
            "2B_zero_pred": gen2[idx[i]]["prediction"] if False else base[idx[i]]["prediction"],
            "2B_zero_correct": c_base[i],
            "2B_lora_pred": gen2[idx[i]]["prediction"],
            "2B_lora_correct": c_gen2[i],
            "7B_zero_pred": z7[idx[i]]["prediction"],
            "7B_zero_correct": c_z7[i],
            "7B_lora_pred": gen7[idx[i]]["prediction"],
            "7B_lora_correct": c_gen7[i],
        })

    with open("results/orientation_persistent_failures_v2.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote results/orientation_persistent_failures_v2.json ({len(out)} cases)")

    # Summary
    from collections import Counter
    print("\nBy relation:", dict(Counter(o["relation"] for o in out)))
    print("By label:", dict(Counter(o["label"] for o in out)))
    print("Wrong in all 4:", sum(1 for o in out if o["wrong_count"] == 4))

if __name__ == "__main__":
    main()
