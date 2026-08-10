"""
SITE external-validation: 7B zero-shot evaluation on the frozen
preregistered subsets (primary / secondary / exploratory).

- Model: Qwen2-VL-7B-Instruct, frozen, greedy generation.
- Format: SITE native multiple-choice; prompt replicated from the official
  lmms-eval task (eval_scripts/sitebench/utils.py).
- Parsing: official parse_multi_choice_response (letter extraction);
  unparseable -> None (scored incorrect, no random fallback).
- Metrics: raw accuracy, chance-adjusted accuracy (official aggregate),
  95% Wilson CI, modality breakdown, source-dataset breakdown (n>=30).
- No training/fine-tuning on SITE.
"""
import os, sys, json, csv, time, hashlib, argparse
from pathlib import Path
from collections import Counter, defaultdict

os.chdir("/home/ubuntu/vlm-spatial-reasoning")
sys.path.insert(0, ".")

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

MODEL = "Qwen/Qwen2-VL-7B-Instruct"
MEDIA_ROOT = Path("data/site_media")
POST_PROMPT = "Give me the answer letter directly. The best answer is:"
PRE_PROMPT = ("Select the best answer to the following multiple-choice question "
              "based on the video. Respond with only the letter of the correct option.")
UPPER = list("ABCDEFGH")
OUT_DIR = Path("results/site")
VIDEO_FRAMES = 16


def load_video_frames(path, n=VIDEO_FRAMES, max_side=128):
    """Uniformly sample n frames with pyav, resized to <=max_side (np [n,H,W,3])."""
    import av
    import numpy as np
    from PIL import Image
    frames = []
    with av.open(str(path)) as c:
        stream = c.streams.video[0]
        dur = float(stream.duration * stream.time_base) if stream.duration else 0.0
        for i in range(n):
            t = i * dur / max(n - 1, 1)
            c.seek(int(t / stream.time_base), stream=stream)
            got = False
            for fr in c.decode(stream):
                arr = fr.to_ndarray(format="rgb24")
                img = Image.fromarray(arr)
                w, h = img.size
                scale = max_side / max(w, h)
                if scale < 1.0:
                    img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
                frames.append(np.asarray(img))
                got = True
                break
            if not got:
                frames.append(np.zeros((max_side // 2, max_side // 2, 3), dtype=np.uint8))
    return np.stack(frames)


def parse_multi_choice_response(response, all_choices):
    """Official SITE parsing (lmms-eval utils), minus random fallback."""
    response = " " + (response or "") + " "
    candidates = []
    for c in all_choices:
        if f"({c})" in response:
            candidates.append(c)
    if not candidates:
        for c in all_choices:
            if f" {c} " in response:
                candidates.append(c)
    if not candidates:
        for c in all_choices:
            if f"{c}." in response:
                candidates.append(c)
    if not candidates:
        for c in all_choices:
            if f"{c}:" in response or f":{c}" in response or f": {c}" in response:
                candidates.append(c)
    if not candidates:
        return None
    if len(candidates) > 1:
        start_indexes = [response.rfind(f" {c} ") for c in candidates]
        return candidates[int(max(range(len(candidates)), key=lambda i: start_indexes[i]))]
    return candidates[0]


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
    return max(0, center - margin), min(1, center + margin)


def build_prompt_image(doc):
    question = doc["question"].strip()
    option_text = "\n".join(f"{UPPER[i]}: {doc['options'][i]}" for i in range(len(doc["options"])))
    prompt = ""
    if "<image>" not in question and "<image>" not in option_text:
        prompt += "<image>" * len(doc["visual"]) + "\n"
    prompt += "Question: " + question + "\n" + "Options:\n" + option_text + "\n" + POST_PROMPT
    return prompt


def build_prompt_video(doc):
    question = doc["question"].strip()
    option_text = "\n".join(f"{UPPER[i]}: {doc['options'][i]}" for i in range(len(doc["options"])))
    return (PRE_PROMPT + "\n" + "Question: " + question + "\n"
            + "Options:\n" + option_text + "\n" + POST_PROMPT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", default=None,
                    help="primary|secondary|exploratory (default: union of all frozen subsets)")
    ap.add_argument("--attn", default="eager", choices=["eager", "flash_attention_2"])
    ap.add_argument("--out", default=None, help="output predictions CSV (resumes if exists)")
    ap.add_argument("--max-new-tokens", type=int, default=16,
                    help="generation ceiling; task needs only an answer letter "
                         "(protocol note: 128 -> 16, protocol-neutral efficiency change)")
    ap.add_argument("--images-only", action="store_true",
                    help="evaluate image examples only (stop before videos)")
    args = ap.parse_args()

    proto = json.load(open(OUT_DIR / "site_protocol.json"))
    frozen = proto["frozen_ids"]
    if args.subset:
        wanted = set(frozen[args.subset])
    else:
        wanted = set(frozen["primary"]) | set(frozen["secondary"]) | set(frozen["exploratory"])
    subset_of = {sid: [s for s, ids in frozen.items() if sid in ids] for sid in wanted}
    print(f"Examples to evaluate: {len(wanted)} (union of frozen subsets)")

    # ── frozen run metadata + config hash (reproducibility) ──
    import hashlib
    config = {
        "model": MODEL,
        "prompt_image": "official sitebench/spatial_doc_to_text_image (+post_prompt)",
        "prompt_video": "official sitebench/spatial_doc_to_text_video (+post_prompt)",
        "post_prompt": POST_PROMPT,
        "parser": "official parse_multi_choice_response (no random fallback)",
        "max_new_tokens": args.max_new_tokens,
        "max_new_tokens_previous": 128,
        "efficiency_note": "task requires only a single answer letter; truncation ceiling only, prompt/decoding/parser unchanged",
        "attn": args.attn,
        "subsets": {k: sorted(v) for k, v in frozen.items()},
        "images_only": args.images_only,
    }
    cfg_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
    config["config_hash"] = cfg_hash
    meta_path = OUT_DIR / "run_metadata.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta[cfg_hash] = config
    meta_path.write_text(json.dumps(meta, indent=1))
    print(f"Run metadata saved: config_hash={cfg_hash} (max_new_tokens={args.max_new_tokens})")

    from src.datasets.site import load_site
    records = [r for r in load_site() if r["id"] in wanted]
    print(f"Records loaded: {len(records)}")

    # resume: skip ids already saved AND load their rows so incremental
    # saves preserve them
    out_csv = Path(args.out) if args.out else None
    done_ids = set()
    prev_rows = []
    if out_csv and out_csv.exists():
        with open(out_csv) as f:
            for row in csv.DictReader(f):
                done_ids.add(row["id"])
                prev_rows.append(row)
        print(f"Resuming: {len(done_ids)} already evaluated")

    processor = AutoProcessor.from_pretrained(MODEL)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, dtype=torch.bfloat16, _attn_implementation=args.attn,
        low_cpu_mem_usage=True).to("cuda")
    model.eval()

    # split by modality
    image_recs = [r for r in records if r["modality"] in ("single-image", "multi-image")
                  and r["id"] not in done_ids]
    video_recs = [r for r in records if r["modality"] == "video"
                  and r["id"] not in done_ids]
    if args.images_only:
        video_recs = []
    print(f"Image examples: {len(image_recs)} | Video examples: {len(video_recs)} "
          f"(to evaluate)")

    results = list(prev_rows)
    t0 = time.time()

    def save_partial():
        if not out_csv:
            return
        with open(out_csv, "w", newline="") as f:
            if results:
                w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                w.writeheader()
                w.writerows(results)

    def gen_batch(batch, is_video):
        msgs, media_ok = [], []
        for r in batch:
            paths = [MEDIA_ROOT / v for v in r["visual"]]
            if is_video:
                p = paths[0]
                if not p.exists():
                    media_ok.append(False)
                    continue
                try:
                    video = load_video_frames(p)
                    content = [{"type": "video", "video": video},
                               {"type": "text", "text": build_prompt_video(r)}]
                except Exception:
                    media_ok.append(False)
                    continue
            else:
                imgs = []
                for p in paths:
                    if p.exists():
                        try:
                            im = Image.open(p).convert("RGB")
                            w, h = im.size
                            s = 2048 / max(w, h)
                            if s < 1.0:
                                im = im.resize((max(1, int(w * s)), max(1, int(h * s))))
                            imgs.append(im)
                        except Exception:
                            imgs = None
                            break
                if not imgs:
                    media_ok.append(False)
                    continue
                content = []
                q = r["question"] or ""
                opt_text = "\n".join(f"{UPPER[i]}: {r['options'][i]}" for i in range(len(r["options"])))
                # interleaved: placeholders inside question/options need images inserted
                prompt = build_prompt_image(r)
                # build content: images at <image> positions
                parts = prompt.split("<image>")
                for j, part in enumerate(parts):
                    if j > 0:
                        content.append({"type": "image", "image": imgs[min(j - 1, len(imgs) - 1)]})
                    if part:
                        content.append({"type": "text", "text": part})
                media_ok.append(True)
            msgs.append([{"role": "user", "content": content}])
        if not msgs:
            return []
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt")
        inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}
        out = None
        for scale in (None, 336, 224, 160, 96):
            msgs_cur = msgs
            if scale is not None:
                msgs_cur = []
                for m in msgs:
                    content = []
                    for c in m[0]["content"]:
                        if c["type"] == "image":
                            im = c["image"]
                            w, h = im.size
                            s = scale / max(w, h)
                            if s < 1.0:
                                im = im.resize((max(1, int(w * s)), max(1, int(h * s))))
                            content.append({"type": "image", "image": im})
                        else:
                            content.append(c)
                    msgs_cur.append([{"role": "user", "content": content}])
            try:
                inputs = processor.apply_chat_template(
                    msgs_cur, add_generation_prompt=True, tokenize=True,
                    return_dict=True, return_tensors="pt")
                inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}
                with torch.inference_mode():
                    out = model.generate(**inputs, do_sample=False,
                                         max_new_tokens=args.max_new_tokens)
                break
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                print(f"    OOM at scale {scale}, retrying smaller", flush=True)
        if out is None:
            print("    OOM at all scales — skipping batch", flush=True)
            return []
        in_len = inputs["input_ids"].shape[1]
        texts = processor.batch_decode(out[:, in_len:], skip_special_tokens=True)
        del inputs, out
        torch.cuda.empty_cache()
        return texts

    def run(batch_recs, is_video, tag, batch_size):
        nonlocal results
        for start in range(0, len(batch_recs), batch_size):
            batch = batch_recs[start:start + batch_size]
            print(f"[{tag}] {start}/{len(batch_recs)} ex={[r['id'] for r in batch]} "
                  f"({time.time()-t0:.0f}s)", flush=True)
            try:
                texts = gen_batch(batch, is_video)
            except Exception as ex:
                torch.cuda.empty_cache()
                print(f"    BATCH EXCEPTION {type(ex).__name__}: {str(ex)[:120]}", flush=True)
                texts = []
            mi = 0
            for r in batch:
                all_choices = UPPER[:len(r["options"])]
                if mi < len(texts):
                    pred = parse_multi_choice_response(texts[mi], all_choices)
                    raw = texts[mi]
                    mi += 1
                else:
                    pred, raw = None, None
                gt = r["answer"].strip().upper()
                results.append({
                    "id": r["id"], "subset": ",".join(subset_of[r["id"]]),
                    "category": r["category"], "source_dataset": r["source_dataset"],
                    "modality": r["modality"], "n_options": len(r["options"]),
                    "question": r["question"], "options": r["options"],
                    "answer": gt, "prediction": pred, "correct": 1 if pred == gt else 0,
                    "raw_output": (raw or "")[:200],
                })
            if len(results) % 25 == 0:
                save_partial()
                print(f"[{tag}] {len(results)} done ({time.time()-t0:.0f}s)", flush=True)

    # single-image examples batch at 8 (fast, memory-safe with max_new_tokens=16);
    # multi-image examples batch at 1 (long sequences, OOM-prone)
    single_recs = [r for r in image_recs if r["modality"] == "single-image"]
    multi_recs = [r for r in image_recs if r["modality"] == "multi-image"]
    print(f"  single-image: {len(single_recs)} (batch 8) | "
          f"multi-image: {len(multi_recs)} (batch 1)")
    run(single_recs, False, "img-single", 8)
    run(multi_recs, False, "img-multi", 1)
    run(video_recs, True, "video", 1)

    ts = time.strftime("%Y%m%d_%H%M%S")
    pred_file = out_csv if out_csv else OUT_DIR / f"zeroshot_7b_predictions_{ts}.csv"
    with open(pred_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"Saved {len(results)} predictions -> {pred_file}")

    # ── Metrics per subset ──
    metrics = {}
    for sub_name in ["primary", "secondary", "exploratory"]:
        sub = [r for r in results if sub_name in r["subset"].split(",")]
        n = len(sub)
        if n == 0:
            continue
        k = sum(r["correct"] for r in sub)
        raw = k / n
        lo, hi = wilson_ci(k, n)
        caa_num = sum(r["correct"] - 1 / r["n_options"] for r in sub)
        caa_den = sum(1 - 1 / r["n_options"] for r in sub)
        caa = caa_num / caa_den if caa_den else 0.0
        sub_metrics = {"n": n, "raw_acc": raw, "ci": [lo, hi],
                       "caa": caa, "chance": 1 / sum(1 / r["n_options"] for r in sub) / n if n else 0,
                       "unparseable": sum(1 for r in sub if r["prediction"] is None)}
        sub_metrics["by_modality"] = {}
        for m in ["single-image", "multi-image", "video"]:
            ms = [r for r in sub if r["modality"] == m]
            if len(ms) >= 30:
                kk = sum(r["correct"] for r in ms)
                nn = len(ms)
                sub_metrics["by_modality"][m] = {
                    "n": nn, "raw_acc": kk / nn,
                    "caa": (sum(r["correct"] - 1 / r["n_options"] for r in ms)
                            / sum(1 - 1 / r["n_options"] for r in ms)) if nn else 0.0,
                    "ci": wilson_ci(kk, nn),
                }
        sub_metrics["by_source"] = {}
        for ds, rows in Counter(r["source_dataset"] for r in sub).items():
            if rows < 30:
                continue
            rs = [r for r in sub if r["source_dataset"] == ds]
            kk = sum(r["correct"] for r in rs)
            nn = len(rs)
            sub_metrics["by_source"][ds] = {
                "n": nn, "raw_acc": kk / nn,
                "caa": (sum(r["correct"] - 1 / r["n_options"] for r in rs)
                        / sum(1 - 1 / r["n_options"] for r in rs)) if nn else 0.0,
                "ci": wilson_ci(kk, nn),
            }
        metrics[sub_name] = sub_metrics
        print(f"\n== {sub_name}: n={n} raw={raw:.4f} CI=[{lo:.4f},{hi:.4f}] CAA={caa:.4f}")

    mfile = OUT_DIR / f"zeroshot_7b_metrics_{ts}.json"
    mfile.write_text(json.dumps(metrics, indent=1))
    print(f"Saved metrics -> {mfile}")


if __name__ == "__main__":
    main()
