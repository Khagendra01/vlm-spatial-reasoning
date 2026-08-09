"""
Logical-consistency analysis: evaluate models on FLIPPED complementary
statements (same image, same objects, complementary relation).

Families: left<->right, front<->behind, facing<->facing-away,
          parallel<->perpendicular (soft complement).

For each test statement S with label l, the flipped S' has truth !l
(objects verified present in image caption). We already have verdicts on S
from the saved prediction CSVs; here we evaluate S' for all 5 conditions,
then compute: self-consistency v' == !v, contradiction v' == v,
flip accuracy, both-correct / both-wrong.
"""
import os, sys, re, time, hashlib, json, csv, argparse
from pathlib import Path

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

import torch
from PIL import Image
from datasets import load_dataset
from transformers import AutoProcessor
from src.evaluation.parser import parse_true_false

PROMPT = ('Look at the image carefully.\n\nStatement: "{statement}"\n\n'
          'Is this statement true or false?\n\n'
          'Answer with exactly one word: True or False.')

COMPLEMENTS = {
    "left of": "right of", "right of": "left of",
    "at the left side of": "at the right side of",
    "at the right side of": "at the left side of",
    "in front of": "behind", "behind": "in front of",
    "at the back of": "in front of",
    "facing": "facing away from", "facing away from": "facing",
    "parallel to": "perpendicular to", "perpendicular to": "parallel to",
}
FAMILY = {
    "left of": "LR", "right of": "LR",
    "at the left side of": "LR", "at the right side of": "LR",
    "in front of": "FB", "behind": "FB", "at the back of": "FB",
    "facing": "FF", "facing away from": "FF",
    "parallel to": "PP", "perpendicular to": "PP",
}
STRICT = {"LR", "FB", "FF"}  # strict complements (exactly one holds)

def cache_path(url):
    return Path("data/image_cache") / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def parse_generic(caption):
    m = re.match(r"^The\s+(.+?)\s+is\s+(.+?)\s+the\s+(.+?)\.?$", caption.strip())
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()

def build_flips():
    ds = load_dataset("cambridgeltl/vsr_random", split="test")
    flips = []
    for i, r in enumerate(ds):
        rel = r["relation"]
        if rel not in COMPLEMENTS:
            continue
        p = parse_generic(r["caption"])
        if p is None:
            continue
        subj, _, ref = p
        flip_stmt = f"The {subj} is {COMPLEMENTS[rel]} the {ref}."
        flips.append({
            "orig_idx": i, "family": FAMILY[rel], "orig_rel": rel,
            "flip_rel": COMPLEMENTS[rel], "statement": flip_stmt,
            "orig_label": bool(r["label"]), "flip_label": not bool(r["label"]),
            "image": r["image_link"],
        })
    return flips

def load_original_verdicts(csv_path):
    out = {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            pred = row["prediction"]
            if pred in ("True", "False"):
                out[int(row["id"])] = (pred == "True")
    return out

def evaluate(flips, model_name, base_model, lora_path, out_csv, orig_csv):
    import torch
    from transformers import AutoModelForImageTextToText
    from peft import PeftModel

    processor = AutoProcessor.from_pretrained(base_model)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    model = AutoModelForImageTextToText.from_pretrained(
        base_model, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    if lora_path:
        model = PeftModel.from_pretrained(model, lora_path)
    model.eval()

    def extract(text):
        if "Assistant:" in text:
            text = text.split("Assistant:")[-1].strip()
        return text

    results = []
    t0 = time.time()
    for start in range(0, len(flips), 8):
        batch = flips[start:start + 8]
        imgs, stmts = [], []
        for fl in batch:
            p = cache_path(fl["image"])
            img = Image.open(p).convert("RGB") if p.exists() else None
            imgs.append(img)
            stmts.append(PROMPT.format(statement=fl["statement"]))
        msgs = [[{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": t},
        ]}] for img, t in zip(imgs, stmts) if img is not None]
        if not msgs:
            continue
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        )
        inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        in_len = inputs["input_ids"].shape[1]
        texts = processor.batch_decode(out[:, in_len:], skip_special_tokens=True)
        for fl, t in zip(batch, texts):
            pred = parse_true_false(extract(t))
            results.append({**fl, "flip_prediction": pred})
        del inputs, out
        torch.cuda.empty_cache()
        if (start // 8) % 25 == 0:
            print(f"  [{start+len(batch)}/{len(flips)}] {time.time()-t0:.0f}s", flush=True)

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"Saved {len(results)} -> {out_csv}")

    # ── Analysis ──
    orig = load_original_verdicts(orig_csv)
    return analyze(results, orig, model_name)

def analyze(results, orig, model_name):
    from collections import defaultdict
    fam_stats = defaultdict(lambda: {"n": 0, "orig_acc": 0, "flip_acc": 0,
                                     "consistent": 0, "contradiction": 0,
                                     "both_correct": 0, "both_wrong": 0,
                                     "flip_na": 0, "orig_na": 0})
    for fl in results:
        st = fam_stats[fl["family"]]
        st["n"] += 1
        o = orig.get(fl["orig_idx"])
        fp = fl["flip_prediction"]
        if o is None:
            st["orig_na"] += 1
        if fp is None:
            st["flip_na"] += 1
        if o is not None and fp is not None:
            if o == fl["orig_label"]:
                st["orig_acc"] += 1
            if fp == fl["flip_label"]:
                st["flip_acc"] += 1
            if fp == (not o):
                st["consistent"] += 1
            if fp == o:
                st["contradiction"] += 1
            if o == fl["orig_label"] and fp == fl["flip_label"]:
                st["both_correct"] += 1
            if o != fl["orig_label"] and fp != fl["flip_label"]:
                st["both_wrong"] += 1
    return fam_stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True,
                    choices=["7B_zero_shot", "LM_only_LoRA", "hardneg_LoRA",
                             "projector_LoRA", "vision_proj_LoRA"])
    args = ap.parse_args()

    CONDS = {
        "7B_zero_shot": ("Qwen/Qwen2-VL-7B-Instruct", None, "qwen2vl_7b_predictions_20260809_064919"),
        "LM_only_LoRA": ("Qwen/Qwen2-VL-7B-Instruct", "checkpoints/qwen2vl_7b_general_lora/final", "7B_general_lora_predictions_20260809_094930"),
        "hardneg_LoRA": ("Qwen/Qwen2-VL-7B-Instruct", "checkpoints/qwen2vl_7b_hardneg_lora/final", "7B_hardneg_lora_predictions_20260809_164619"),
        "projector_LoRA": ("Qwen/Qwen2-VL-7B-Instruct", "checkpoints/qwen2vl_7b_projector_lora/final", "qwen2vl_7b_projector_lora_predictions_20260809_221720"),
        "vision_proj_LoRA": ("Qwen/Qwen2-VL-7B-Instruct", "checkpoints/qwen2vl_7b_vision_proj_lora/final", "qwen2vl_7b_vision_proj_lora_predictions_20260809_222845"),
    }
    base, lora, orig_name = CONDS[args.condition]
    flips = build_flips()
    print(f"{args.condition}: {len(flips)} flip statements")
    fam_stats = evaluate(flips, args.condition, base, lora,
                         f"results/consistency_flips_{args.condition}.csv",
                         f"results/{orig_name}.csv")
    for fam in ["LR", "FB", "FF", "PP"]:
        s = fam_stats[fam]
        n = s["n"]
        if n == 0:
            continue
        print(f"  {fam} n={n} | orig_acc={s['orig_acc']/n:.3f} flip_acc={s['flip_acc']/n:.3f} "
              f"consistent={s['consistent']/n:.3f} contradiction={s['contradiction']/n:.3f} "
              f"both_correct={s['both_correct']/n:.3f} both_wrong={s['both_wrong']/n:.3f}")
    (Path("results") / f"consistency_stats_{args.condition}.json").write_text(
        json.dumps({k: dict(v) for k, v in fam_stats.items()}, indent=1))

if __name__ == "__main__":
    main()
