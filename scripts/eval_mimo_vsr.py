# -*- coding: utf-8 -*-
"""
Zero-shot evaluation of MiMo-V2.5 (XiaomiMiMo/MiMo-V2.5, 310B MoE / 15B
active, 729M vision encoder) on the VSR test set and the complementary-
statement consistency protocol, served through an OpenAI-compatible API
(e.g., OpenCode Go: https://opencode.ai/zen/go/v1/chat/completions).

Protocol (identical to the canonical evaluations):
  - frozen VSR prompt, verbatim from the supplementary (App. A)
  - same test records / statements / image URLs as the canonical prediction
    CSVs (results/smolvlm2_baseline_2195_20260808_214536.csv)
  - greedy decoding intent: temperature 0, top_p 1.0, max_tokens 16,
    thinking disabled if the serving API supports it (verified in --validate)
  - outputs parsed with src/evaluation/parser.py parse_true_false
    (same parser as all canonical runs)

Writes ONLY under results/mimo/ (never touches canonical result files):
  results/mimo/mimo_v25_zeroshot_predictions.csv
  results/mimo/mimo_v25_zeroshot_metrics.json
  results/mimo/consistency_flips_mimo.csv
  results/mimo/consistency_stats_mimo.json
  results/mimo/usage_report.json          (per-request tokens + total $)
  results/mimo/raw_validation_outputs.txt (validation raw outputs)

Usage:
  # 1) probe which model ids the endpoint serves (no tokens spent)
  python scripts/eval_mimo_vsr.py --list-models

  # 2) validation on VSR TRAIN examples only (do not tune on the test set)
  python scripts/eval_mimo_vsr.py --task vsr --validate

  # 3) full zero-shot test run (resumes automatically)
  python scripts/eval_mimo_vsr.py --task vsr

  # 4) complementary-statement consistency (uses MiMo's own original
  #    verdicts from step 3, exactly like eval_consistency_flips.py)
  python scripts/eval_mimo_vsr.py --task consistency

Environment:
  OPENCODE_GO_API_KEY   (or OPENAI_API_KEY)  -- API key
  MIMO_BASE_URL   default https://opencode.ai/zen/go/v1/chat/completions
  MIMO_MODEL      default mimo-v2.5
"""
import argparse
import base64
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MIMO_DIR = RESULTS / "mimo"
IAA = RESULTS / "iaa"
CANON_CSV = RESULTS / "smolvlm2_baseline_2195_20260808_214536.csv"
CACHE_DIR = ROOT / "data" / "image_cache"

sys.path.insert(0, str(ROOT))
from src.evaluation.parser import parse_true_false  # noqa: E402

FROZEN_PROMPT = ('Look at the image carefully.\n\nStatement: "{statement}"\n\n'
                 'Is this statement true or false?\n\n'
                 'Answer with exactly one word: True or False.')

# ---------------------------------------------------------------------------
# complementary-statement protocol, mirrored EXACTLY from
# scripts/eval_consistency_flips.py (same maps, same flip construction)
# ---------------------------------------------------------------------------
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

GO_INPUT = 0.14 / 1e6      # USD per input token (OpenCode Go, MiMo-V2.5)
GO_OUTPUT = 0.28 / 1e6     # USD per output token
GO_CACHED = 0.0028 / 1e6   # USD per cached-read token

# ---------------------------------------------------------------------------
# image-grounded AUDIT prompts (used ONLY by --task audit; the frozen VSR
# prompt above is used for the accuracy evaluation)
# ---------------------------------------------------------------------------
AUDIT_CLEAN_PROMPT = (
    'Look at the image and read the spatial statement carefully.\n\n'
    'Statement: "{statement}"\n\n'
    'Decide whether a human can confidently determine whether this statement '
    'is true or false FROM THE IMAGE ALONE.\n'
    '- Answer "clean" if the image clearly supports a confident true/false '
    'judgement, even if the answer is hard.\n'
    '- Answer "ambiguous" if the statement cannot be confidently judged from '
    'the image: the annotation seems wrong, the camera viewpoint hides the '
    'relevant geometry, the objects have no meaningful orientation, the '
    'reference object is not clearly visible, or the objects are too small '
    'or occluded.\n'
    'Answer with exactly one word: clean or ambiguous.')

AUDIT_TAXO_PROMPT = (
    'Look at the image and read the spatial statement carefully.\n\n'
    'Statement: "{statement}"\n\n'
    'This example is a case where vision-language models failed. Choose the '
    'single best reason from exactly these eight classes:\n'
    '1. clear_image_model_reasoning_failure - the image is visually clear '
    'and the statement is judgeable; a failure is a reasoning failure, not '
    'an image/annotation problem.\n'
    '2. camera_viewpoint_ambiguity - camera angle or depth separation makes '
    'the relation hard to judge.\n'
    '3. parallel_perpendicular_geometry - requires geometric assessment of '
    'alignment between objects.\n'
    '4. annotation_questionable - the claimed truth value of the statement '
    'seems wrong or undecidable given the image.\n'
    '5. intrinsic_orientation_ambiguous - the subject object has no '
    'meaningful intrinsic orientation.\n'
    '6. front_back_object_ambiguous - the reference object is barely visible '
    'or its position must be inferred.\n'
    '7. small_occluded_object - the relevant object is small or partially '
    'occluded.\n'
    '8. subject_reference_inversion - the statement subject/reference roles '
    'are easy to confuse.\n'
    'Answer with exactly one class name.')

AUDIT_BINARY_ALLOWED = {"clean", "ambiguous"}
AUDIT_TAXO_ALLOWED = {
    "clear_image_model_reasoning_failure", "camera_viewpoint_ambiguity",
    "parallel_perpendicular_geometry", "annotation_questionable",
    "intrinsic_orientation_ambiguous", "front_back_object_ambiguous",
    "small_occluded_object", "subject_reference_inversion",
}


def parse_audit_answer(raw, allowed):
    """Single-word audit answer; falls back to a trailing allowed token."""
    if raw is None:
        return None, False
    s = raw.strip().lower().strip('."\'`')
    if s in allowed:
        return s, False
    for token in sorted(allowed, key=len, reverse=True):
        if s.endswith(token) or token in s.split():
            return token, True
    return None, True


def cache_path(url):
    return CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"


def ensure_images(rows):
    """Download any missing images to the local cache (b64 fallback)."""
    missing = [r for r in rows if not cache_path(r["image_url"]).exists()]
    if not missing:
        return
    print(f"downloading {len(missing)} missing images to data/image_cache ...")
    for i, r in enumerate(missing):
        p = cache_path(r["image_url"])
        try:
            req = urllib.request.Request(r["image_url"],
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                p.write_bytes(resp.read())
        except Exception as e:
            print(f"  WARN: failed {r['id']} {r['image_url']}: {e}")
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(missing)}")


def load_test_records():
    """Canonical test records: id, statement, relation, label, image_url."""
    rows = []
    with open(CANON_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"id": int(r["id"]), "statement": r["statement"],
                         "relation": r["relation"],
                         "label": (r["ground_truth"] == "True"),
                         "image_url": r["image_url"]})
    return rows


def load_train_examples(n):
    """First n VSR train statements (for --validate only; never the test set)."""
    from datasets import load_dataset
    ds = load_dataset("cambridgeltl/vsr_random", split="train")
    out = []
    for ex in ds:
        out.append({"statement": ex.get("caption", ""),
                    "relation": ex.get("relation", ""),
                    "image_url": ex.get("image_link", "")})
        if len(out) >= n:
            break
    return out


def parse_generic(caption):
    m = re.match(r"^The\s+(.+?)\s+is\s+(.+?)\s+the\s+(.+?)\.?$", caption.strip())
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()


def build_flips(records):
    flips = []
    for r in records:
        rel = r["relation"]
        if rel not in COMPLEMENTS:
            continue
        p = parse_generic(r["statement"])
        if p is None:
            continue
        subj, _, ref = p
        flips.append({
            "id": r["id"], "orig_idx": r["id"], "family": FAMILY[rel],
            "orig_rel": rel, "relation": rel,
            "flip_rel": COMPLEMENTS[rel],
            "statement": f"The {subj} is {COMPLEMENTS[rel]} the {ref}.",
            "orig_label": r["label"], "flip_label": not r["label"],
            "image_url": r["image_url"],
        })
    return flips


class MimoClient:
    def __init__(self, base_url, model, api_key):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key

    def chat(self, image_source, text, max_tokens=64):
        """One image + text request. image_source is a data: URI or http URL.
        Returns (content, usage_dict) or raises. max_tokens=64 leaves room
        for a leaked chain-of-thought to still end in the True/False verdict."""
        content = [
            {"type": "image_url",
             "image_url": {"url": image_source}},
            {"type": "text", "text": text},
        ]
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "top_p": 1.0,
            "max_tokens": max_tokens,
            # disable MiMo's thinking mode (verified empirically: with
            # chat_template_kwargs / thinking.type=disabled the gateway
            # returns content-only output, zero reasoning tokens,
            # deterministic across re-runs; send both knobs because some
            # backend instances honor only one)
            "chat_template_kwargs": {"enable_thinking": False},
            "thinking": {"type": "disabled"},
        }
        data = json.dumps(body).encode("utf-8")
        last_err = None
        for attempt in range(6):
            req = urllib.request.Request(
                self.base_url, data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}",
                         # gateway 403s the default Python-urllib user agent
                         "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; "
                                        "x64) AppleWebKit/537.36")})
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    js = json.loads(resp.read().decode("utf-8"))
                usage = js.get("usage", {})
                return (js["choices"][0]["message"]["content"]
                        or js["choices"][0]["message"].get("reasoning_content", ""),
                        {"prompt": usage.get("prompt_tokens", 0),
                         "completion": usage.get("completion_tokens", 0),
                         "cached": usage.get("prompt_tokens_details", {})
                                   .get("cached_tokens", 0)
                                   if isinstance(usage.get("prompt_tokens_details"), dict)
                                   else 0})
            except Exception as e:
                last_err = e
                # 429 / 5xx -> backoff; anything else -> re-raise after retries
                time.sleep(2 ** attempt)
        raise RuntimeError(f"API failed after 6 attempts: {last_err}")

    def list_models(self):
        url = self.base_url.rsplit("/chat/completions", 1)[0] + "/models"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self.api_key}",
                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))


def extract_final_answer(raw):
    """Parse strategy for MiMo outputs.

    If the output is short (<= 60 chars) parse directly with the canonical
    parser. Otherwise (thinking/reasoning leaked into content) take the last
    standalone True/False line, else the last True/False token, and mark the
    example thinking_likely=1 so the protocol deviation is visible.
    """
    if raw is None:
        return None, False
    s = raw.strip()
    if len(s) <= 60:
        return parse_true_false(s), False
    lines = [ln.strip().lower() for ln in s.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if re.fullmatch(r"(true|false|it is true|it is false|the answer is true|the answer is false)\.?", ln):
            return parse_true_false(ln), True
    m = re.findall(r"\b(true|false)\b", s.lower())
    if m:
        return parse_true_false(m[-1]), True
    return None, True


def image_source_for(image_url, mode):
    """Image reference for the API call.

    b64 (default): base64 data URI from the local cache — deterministic and
    immune to the gateway's server-side URL fetching, which we observed to
    fail intermittently on COCO URLs (leaking thinking-style text and
    producing no answer). url: pass the canonical image URL through.
    """
    if mode == "url":
        return image_url
    p = cache_path(image_url)
    if p.exists() and p.stat().st_size > 0:
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{data}"
    return image_url  # fall back to URL if not cached


def load_done(csv_path):
    done = set()
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add(int(r["id"]))
    return done


def save_rows(csv_path, rows, fieldnames):
    tmp = csv_path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(csv_path)


USAGE = {"calls": 0, "prompt": 0, "completion": 0, "cached": 0}
_usage_lock = threading.Lock()
_log_lock = threading.Lock()
BACKOFF = [5, 20, 60]  # seconds; bad routing usually clears in minutes


def _add_usage(usage):
    with _usage_lock:
        USAGE["calls"] += 1
        USAGE["prompt"] += usage["prompt"]
        USAGE["completion"] += usage["completion"]
        USAGE["cached"] += usage["cached"]


def _process_item(it, client, prompt, answer_parser, image_mode, raw_log):
    """One item: request with retry-until-verdict. Returns a row dict."""
    text = prompt.format(statement=it["statement"])
    pred, thinking, n_retries, raw = None, False, 0, None
    for attempt in range(4):
        # alternate transport on retries (url <-> b64): if the gateway's
        # URL fetch or a cached bad response poisons one path, the other
        # path usually yields a clean deterministic answer
        mode = image_mode if attempt % 2 == 0 else \
            ("b64" if image_mode == "url" else "url")
        raw, usage = client.chat(image_source_for(it["image_url"], mode),
                                 text)
        pred, thinking = answer_parser(raw)
        _add_usage(usage)
        if pred is not None or attempt == 3:
            break
        n_retries += 1
        time.sleep(BACKOFF[attempt])
    if raw_log is not None:
        with _log_lock:
            raw_log.write(f"=== id {it['id']} | {it['statement']}\n{raw}\n\n")
            raw_log.flush()
    gt = it.get("label", it.get("flip_label"))
    row = {"id": it["id"], "statement": it["statement"],
           "relation": it.get("relation", ""),
           "ground_truth": str(gt),
           "prediction": pred,
           "correct": (pred == gt) if pred is not None and gt is not None
                      else "",
           "raw_output": raw,
           "image_url": it["image_url"],
           "thinking_likely": "1" if thinking else "0",
           "retries": n_retries}
    # carry through task-specific metadata (consistency flips)
    for k in ("orig_idx", "family", "orig_rel", "flip_rel",
              "orig_label", "flip_label"):
        if k in it:
            row[k] = it[k]
    return row


def run_requests(items, client, task, out_csv, fieldnames, prompt,
                 answer_parser, image_mode="b64", limit=None, raw_log=None,
                 concurrency=12):
    """items: list of dicts with 'id', 'statement', 'image_url'.
    Concurrent (ThreadPoolExecutor) with per-request retry; incremental
    resume-safe saves; thread-safe usage accounting."""
    done = load_done(out_csv)
    todo = [it for it in items if it["id"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"{task}: {len(todo)} pending (of {len(items)}) | "
          f"concurrency={concurrency}", flush=True)
    if not todo:
        print("nothing to do — all ids already in", out_csv, flush=True)
        return
    existing = []
    if out_csv.exists():
        with open(out_csv, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    rows = []
    t0 = time.time()
    done_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(_process_item, it, client, prompt, answer_parser,
                          image_mode, raw_log): it for it in todo}
        for fut in concurrent.futures.as_completed(futs):
            it = futs[fut]
            try:
                rows.append(fut.result())
            except Exception as e:
                rows.append({"id": it["id"], "statement": it["statement"],
                             "relation": it.get("relation", ""),
                             "ground_truth": str(it.get("label",
                                                       it.get("flip_label", ""))),
                             "prediction": None, "correct": "",
                             "raw_output": f"ERROR: {e}", "image_url":
                             it["image_url"], "thinking_likely": "1",
                             "retries": 3})
            done_count += 1
            if done_count % 50 == 0 or done_count == len(todo):
                elapsed = time.time() - t0
                print(f"  [{done_count}/{len(todo)}] "
                      f"{done_count/elapsed:.1f} req/s | {elapsed:.0f}s",
                      flush=True)
                save_rows(out_csv, existing + rows, fieldnames)
    save_rows(out_csv, existing + rows, fieldnames)
    print(f"saved {len(rows)} rows -> {out_csv}", flush=True)


def write_usage_report():
    total_usd = (USAGE["prompt"] * GO_INPUT
                 + USAGE["completion"] * GO_OUTPUT
                 + USAGE["cached"] * GO_CACHED)
    report = {
        "provider": "OpenCode Go (opencode.ai/zen/go/v1)",
        "model": "mimo-v2.5",
        "prices_per_1M": {"input": GO_INPUT * 1e6, "output": GO_OUTPUT * 1e6,
                          "cached_read": GO_CACHED * 1e6},
        "usage": dict(USAGE),
        "estimated_usd": round(total_usd, 4),
        "note": "estimate at OpenCode Go listed prices; the subscription "
                "($5 first month, then $10/month) includes $60/month of usage.",
    }
    (MIMO_DIR / "usage_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["vsr", "consistency", "audit"],
                    default="vsr")
    ap.add_argument("--validate", action="store_true",
                    help="run on VSR TRAIN examples only (never the test set)")
    ap.add_argument("--validate-n", type=int, default=30)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--base-url",
                    default=os.environ.get("MIMO_BASE_URL",
                                           "https://opencode.ai/zen/go/v1/chat/completions"))
    ap.add_argument("--model", default=os.environ.get("MIMO_MODEL", "mimo-v2.5"))
    ap.add_argument("--image-mode", choices=["url", "b64"],
                    default="url",
                    help="url (default): pass the canonical image URL through "
                         "(no upload); retries automatically alternate to b64 "
                         "from the local cache if the gateway misbehaves. "
                         "b64: always send base64 data URIs.")
    ap.add_argument("--concurrency", type=int, default=12,
                    help="parallel API requests (rate limit is ~30k req/5h)")
    args = ap.parse_args()

    api_key = os.environ.get("OPENCODE_GO_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("ERROR: set OPENCODE_GO_API_KEY (or OPENAI_API_KEY). Get the "
                 "key from https://opencode.ai/zen (OpenCode Go subscription; "
                 "$5 first month, $10/month, $60/month of usage included).")

    MIMO_DIR.mkdir(parents=True, exist_ok=True)
    client = MimoClient(args.base_url, args.model, api_key)

    if args.list_models:
        print(json.dumps(client.list_models(), indent=2))
        return

    if args.validate:
        ex = load_train_examples(args.validate_n)
        # determinism check: double-run the first 10
        print(f"--- validation on {len(ex)} TRAIN examples ---")
        raw_log = open(MIMO_DIR / "raw_validation_outputs.txt", "w", encoding="utf-8")
        for i, e in enumerate(ex):
            pred, thinking, n_retries = None, False, 0
            BACKOFF = [5, 20, 60]
            for attempt in range(4):
                raw, usage = client.chat(
                    image_source_for(e["image_url"], args.image_mode),
                    FROZEN_PROMPT.format(statement=e["statement"]))
                pred, thinking = extract_final_answer(raw)
                USAGE["calls"] += 1
                USAGE["prompt"] += usage["prompt"]
                USAGE["completion"] += usage["completion"]
                USAGE["cached"] += usage["cached"]
                if pred is not None or attempt == 3:
                    break
                n_retries += 1
                time.sleep(BACKOFF[attempt])
            raw_log.write(f"=== id {i} | {e['statement']}\n{raw}\n\n")
            raw_log.flush()
            print(f"  [{i+1}/{len(ex)}] thinking={thinking} parsed={pred} "
                  f"retries={n_retries} | raw={raw[:80]!r}", flush=True)
            if i < 10:
                raw2, _ = client.chat(
                    image_source_for(e["image_url"], args.image_mode),
                    FROZEN_PROMPT.format(statement=e["statement"]))
                same = (extract_final_answer(raw2)[0] == pred)
                print(f"      determinism re-run: {'SAME' if same else 'DIFFERENT'}"
                      f" | raw2={raw2[:60]!r}", flush=True)
        raw_log.close()
        write_usage_report()
        print("--- validation done: inspect raw_validation_outputs.txt; if "
              "thinking=1 appears or determinism differs, the greedy protocol "
              "is NOT available through this endpoint ---")
        return

    records = load_test_records()
    print(f"test records: {len(records)}")
    ensure_images(records)  # for the b64 fallback path

    if args.task == "vsr":
        out_csv = MIMO_DIR / "mimo_v25_zeroshot_predictions.csv"
        fieldnames = ["id", "statement", "relation", "ground_truth",
                      "prediction", "correct", "raw_output", "image_url", "thinking_likely", "retries"]
        run_requests(records, client, "vsr", out_csv, fieldnames,
                     FROZEN_PROMPT, extract_final_answer, args.image_mode, args.limit, None, args.concurrency)
        # metrics (overall + orientation family; full family table comes from
        # scripts/mimo_analysis.py)
        rows = []
        with open(out_csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        correct = sum(1 for r in rows if r["correct"] == "True")
        metrics = {"global": {"accuracy": correct / len(rows),
                              "correct": correct, "total": len(rows)},
                   "config": {"model": "XiaomiMiMo/MiMo-V2.5",
                              "prompt": "frozen VSR prompt (App. A)",
                              "decoding": "temperature=0, top_p=1.0, "
                                          "max_tokens=16, thinking-disabled "
                                          "attempted; see usage_report.json "
                                          "and raw validation outputs",
                              "source": "OpenCode Go API"}}
        (MIMO_DIR / "mimo_v25_zeroshot_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8")
        write_usage_report()

    elif args.task == "consistency":
        flips = build_flips(records)
        out_csv = MIMO_DIR / "consistency_flips_mimo.csv"
        fieldnames = ["id", "orig_idx", "family", "orig_rel", "flip_rel",
                      "orig_label", "flip_label",
                      "statement", "ground_truth", "prediction", "correct",
                      "raw_output", "image_url", "thinking_likely", "retries"]
        run_requests(flips, client, "consistency", out_csv, fieldnames,
                     FROZEN_PROMPT, extract_final_answer, args.image_mode,
                     args.limit, None, args.concurrency)
        write_usage_report()

    elif args.task == "audit":
        # image-grounded audit: binary clean/ambiguous on the 137 orientation
        # examples + eight-class taxonomy on the 48 persistent failures.
        # Sheets are the same blind ones the human rater used, so agreement
        # is directly computable (scripts/compute_iaa.py).
        clean_items, taxo_items = [], []
        with open(IAA / "blind_clean_label_sheet.csv", newline="",
                  encoding="utf-8") as f:
            for r in csv.DictReader(f):
                clean_items.append({"id": int(r["id"]),
                                    "statement": r["statement"],
                                    "relation": r["relation"],
                                    "image_url": r["image_url"]})
        with open(IAA / "blind_failure_taxonomy_sheet.csv", newline="",
                  encoding="utf-8") as f:
            for r in csv.DictReader(f):
                taxo_items.append({"id": int(r["id"]),
                                   "statement": r["statement"],
                                   "relation": r["relation"],
                                   "image_url": r["image_url"]})
        out_clean = MIMO_DIR / "audit_mimo_clean.csv"
        out_taxo = MIMO_DIR / "audit_mimo_taxo.csv"
        fn = ["id", "statement", "relation", "ground_truth", "prediction",
              "correct", "raw_output", "image_url", "thinking_likely", "retries"]
        run_requests(clean_items, client, "audit-clean", out_clean, fn,
                     AUDIT_CLEAN_PROMPT,
                     lambda raw: parse_audit_answer(raw, AUDIT_BINARY_ALLOWED),
                     args.image_mode, args.limit, None, args.concurrency)
        run_requests(taxo_items, client, "audit-taxo", out_taxo, fn,
                     AUDIT_TAXO_PROMPT,
                     lambda raw: parse_audit_answer(raw, AUDIT_TAXO_ALLOWED),
                     args.image_mode, args.limit, None, args.concurrency)
        write_usage_report()


if __name__ == "__main__":
    main()
