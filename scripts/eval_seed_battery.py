"""Battery evaluation driver for the seed campaign (frozen spec:
configs/seed_campaign/SEED_CAMPAIGN.json battery section).

Evaluates one adapter checkpoint on the frozen battery rows
(results/seed_campaign/rows) under the 392px contract with the canonical
prompt, greedy decoding (max_new_tokens=5), one-word True|False answers.

Usage:
  python scripts/eval_seed_battery.py --backbone qwen2vl_7b \
      --adapter checkpoints/qwen2vl_7b_general_lora/final --tag seed0 \
      [--conditions normal,with_sample]   (default: all 7)
Outputs (mirroring legacy naming):
  results/seed_campaign/{backbone}/seed{tag}/{condition}_metrics_{ts}.json
  results/seed_campaign/{backbone}/seed{tag}/{condition}_predictions_{ts}.csv
"""

import argparse
import csv
import json
import hashlib
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from src.evaluation import battery

PROMPT_TEMPLATE = (
    'Look at the image carefully.\n\n'
    'Statement: "{statement}"\n\n'
    'Is this statement true or false?\n\n'
    'Answer with exactly one word: True or False.'
)
MAX_NEW_TOKENS = 5
CONDITIONS = ["normal", "with_sample", "with_shuffle", "relcomp", "facing", "hflip", "hflip_inv"]


def parse_answer(text: str):
    t = text.strip().lower().split()[0] if text.strip() else ""
    for k, w in (("true", True), ("false", False)):
        if t.startswith(k):
            return w
    return None


def load_model_7b(adapter_path):
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    from peft import PeftModel
    model_id = "Qwen/Qwen2-VL-7B-Instruct"
    processor = AutoProcessor.from_pretrained(model_id)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    return processor, model


def load_model_2b(adapter_path):
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from peft import PeftModel
    model_id = "HuggingFaceTB/SmolVLM2-2.2B-Instruct"
    processor = AutoProcessor.from_pretrained(model_id)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    model = AutoModelForImageTextToText.from_pretrained(
        model_id, dtype=torch.bfloat16, _attn_implementation="eager",
        low_cpu_mem_usage=True).to("cuda")
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    return processor, model


def messages_for(processor, statement, img):
    prompt = PROMPT_TEMPLATE.format(statement=statement)
    return [{"role": "user", "content": [{"type": "image", "image": img},
                                          {"type": "text", "text": prompt}]}]


def eval_condition(processor, model, rows, batch_size):
    t0 = time.time()
    n_pred, n_parse_err = 0, 0
    rows_w_pred = []
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        imgs = [battery.sample_image(r) for r in chunk]
        for r, img in zip(chunk, imgs):
            if img is None:
                r = dict(r)
                r["prediction"], r["parse_error"] = None, True
                rows_w_pred.append(r)
                n_parse_err += 1
                continue
            msgs = [messages_for(processor, r["statement"], img)]
            inputs = processor.apply_chat_template(msgs, add_generation_prompt=True,
                                                   tokenize=True, return_dict=True,
                                                   return_tensors="pt")
            inputs = {k: v.to("cuda") for k, v in inputs.items() if hasattr(v, "to")}
            with torch.no_grad():
                with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                    out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS,
                                         do_sample=False)
            text = processor.decode(out[0][inputs["input_ids"].shape[1]:],
                                    skip_special_tokens=True)
            pred = parse_answer(text)
            if pred is None:
                n_parse_err += 1
            r = dict(r)
            r["prediction"] = pred
            r["parse_error"] = pred is None
            rows_w_pred.append(r)
    elapsed = time.time() - t0
    correct = sum(1 for r in rows_w_pred if r["prediction"] == r["label"])
    by_family = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in rows_w_pred:
        by_family[r["family"]]["total"] += 1
        by_family[r["family"]]["correct"] += r["prediction"] == r["label"]
    fam = {k: {"accuracy": v["correct"] / max(1, v["total"]), "correct": v["correct"],
               "total": v["total"]} for k, v in by_family.items()}
    metrics = {
        "condition": rows[0]["condition"] if rows else None,
        "accuracy": correct / max(1, len(rows_w_pred)),
        "correct": correct,
        "total": len(rows_w_pred),
        "parse_errors": n_parse_err,
        "by_family": fam,
        "elapsed_s": round(elapsed, 1),
        "examples_per_s": round(len(rows_w_pred) / max(0.01, elapsed), 2),
        "config": {"batch_size": batch_size, "do_sample": False,
                   "max_new_tokens": MAX_NEW_TOKENS, "image_contract": "392px long-side cap",
                   "prompt_sha256": hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest(),
                   "rows_manifest": str(battery._rows_path(rows[0]["condition"]))},
    }
    return metrics, rows_w_pred


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", choices=["qwen2vl_7b", "smolvlm2_2b"], required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--allow-drifted", action="store_true",
                    help="run the drifted heavy battery anyway (results must NOT"
                         " be reported as the campaign battery)")
    args = ap.parse_args()

    if not args.allow_drifted:
        raise SystemExit(
            "DRIFTED BATTERY DRIVER DEPRECATED (protocol correction 2026-08-11; "
            "see SPATIAL_REASONING_DECISION_LOG 'battery drift' entry). This "
            "script builds rows from the drifted heavy battery (wrong-image 2px "
            "with_sample, re-hashed shuffle, uniform-392 rescale) and must not "
            "be used for the seed campaign. Use "
            "scripts/grounding/run_seed_battery.py (corrected battery = frozen "
            "Paper-2 Tier-A/B/C protocol). Pass --allow-drifted only for "
            "historical reproduction.")

    adapter_path = None if args.adapter.lower() in ("none", "zeroshot", "") else args.adapter
    conditions = [c for c in args.conditions.split(",") if c]
    out_root = Path("results/seed_campaign") / args.backbone / f"seed{args.tag}"
    out_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Loading {args.backbone} model + adapter {adapter_path} ...")
    if args.backbone == "qwen2vl_7b":
        processor, model = load_model_7b(adapter_path)
    else:
        processor, model = load_model_2b(adapter_path)
    print("Model ready.")

    for cond in conditions:
        rows = battery.build_rows(cond)
        print(f"[{cond}] {len(rows)} rows", flush=True)
        metrics, preds = eval_condition(processor, model, rows, args.batch_size)
        metrics["global"] = {"model": args.backbone, "adapter": adapter_path,
                             "tag": args.tag, "campaign_id": battery.CAMPAIGN_ID,
                             "timestamp": datetime.now().isoformat(),
                             "condition": cond}
        with open(out_root / f"{cond}_metrics_{ts}.json", "w") as f:
            json.dump(metrics, f, indent=2)
        with open(out_root / f"{cond}_predictions_{ts}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "statement", "label", "prediction",
                                              "parse_error", "condition", "image"])
            w.writeheader()
            for r in preds:
                w.writerow({k: r.get(k) for k in
                            ["id", "statement", "label", "prediction", "parse_error",
                             "condition", "image"]})
        print(f"[{cond}] acc={metrics['accuracy']:.4f} ({metrics['correct']}/{metrics['total']}) "
              f"{metrics['elapsed_s']:.0f}s -> {out_root}/{cond}_metrics_{ts}.json", flush=True)

    print(f"DONE {args.backbone} tag={args.tag}")
    with open(out_root / "done.log", "w") as f:
        f.write(datetime.now().isoformat() + "\n")


if __name__ == "__main__":
    main()