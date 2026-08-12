"""
Model-consensus audit: run 7B General LoRA over all 451 orientation train
examples and flag label disagreements for manual review.
"""
import os, sys, csv, time, hashlib
from pathlib import Path
from PIL import Image

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

def parse_tf(text):
    t = text.strip().lower()
    if "assistant:" in t:
        t = t.split("assistant:")[-1].strip()
    if t.startswith("true"):
        return True
    if t.startswith("false"):
        return False
    return None

def main():
    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    from peft import PeftModel

    MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"
    LORA_PATH = "checkpoints/qwen2vl_7b_general_lora/final"

    with open("results/orientation_train_audit_base.csv") as f:
        rows = list(csv.DictReader(f))
    print(f"Examples to audit: {len(rows)}")

    missing_imgs = 0
    for r in rows:
        h = hashlib.md5(r["image"].encode()).hexdigest()
        p = Path("data/image_cache") / f"{h}.jpg"
        r["_img_path"] = str(p) if p.exists() else None
        if not p.exists():
            missing_imgs += 1
    print(f"Missing images: {missing_imgs}")
    if missing_imgs:
        print("Waiting for download... check /tmp/hn_download.log")
        return

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16,
        _attn_implementation="eager", low_cpu_mem_usage=True,
    ).to("cuda")
    model = PeftModel.from_pretrained(model, LORA_PATH)
    model.eval()
    print(f"Model loaded: {torch.cuda.memory_allocated()/1e9:.1f}GB")

    prompt_template = 'Look at the image carefully.\n\nStatement: "{statement}"\n\nIs this statement true or false?\n\nAnswer with exactly one word: True or False.'

    t0 = time.time()
    for i, r in enumerate(rows):
        img = Image.open(r["_img_path"]).convert("RGB")
        p = prompt_template.format(statement=r["statement"])
        msgs = [[{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": p}
        ]}]]
        inputs = processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt", padding=True,
        ).to("cuda", dtype=torch.bfloat16)
        with torch.inference_mode():
            out = model.generate(**inputs, do_sample=False, max_new_tokens=5)
        text = processor.batch_decode(
            out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
        pred = parse_tf(text)
        disagree = (pred is not None) and (pred != (r["label"] == "True"))
        r["model_pred"] = "True" if pred is True else ("False" if pred is False else "NA")
        r["model_disagree"] = "yes" if disagree else "no"
        del inputs, out
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(rows)}] {time.time()-t0:.0f}s")
    print(f"Done in {time.time()-t0:.0f}s")

    with open("results/orientation_train_audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "statement", "relation", "label",
                                          "subject", "object", "image",
                                          "heuristic_reasons", "model_pred",
                                          "model_disagree", "final_status"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ["id", "statement", "relation", "label",
                                          "subject", "object", "image",
                                          "heuristic_reasons", "model_pred",
                                          "model_disagree", "final_status"]})
    print("Saved: results/orientation_train_audit.csv")

if __name__ == "__main__":
    main()
