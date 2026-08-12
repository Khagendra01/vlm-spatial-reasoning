"""
Vision-side LoRA conditions for the orientation causal study.
Conditions (--target):
  projector     : LoRA on the vision patch-merger (projector) only
  vision_proj   : LoRA on upper vision blocks (last 8) + merger

Recipe is IDENTICAL to the LM-only General LoRA control
(scripts/run_7b_pipeline.py): same manifest, prompt, collation,
2 epochs, batch_size=1, AdamW lr=1e-4 wd=0.01, linear warmup 10%,
LoRA r=8 alpha=16 dropout=0.05, gradient clipping 1.0.
"""
import os, sys, json, time, hashlib, argparse
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

import torch
from PIL import Image
from datasets import Dataset, load_dataset
from torch.utils.data import DataLoader
from transformers import (AutoProcessor, Qwen2VLForConditionalGeneration,
                          get_linear_schedule_with_warmup)
from peft import LoraConfig, get_peft_model, TaskType

MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"
TRAIN_PROMPT = ('Look at the image carefully.\n\nStatement: "{statement}"\n\n'
                'Is this statement true or false?\n\n'
                'Answer with exactly one word: True or False.')

def cache_path(url):
    return Path("data/image_cache") / f"{hashlib.md5(url.encode()).hexdigest()}.jpg"

def collate_batch(processor, examples, max_length=2048):
    true_tokens = processor.tokenizer.encode(" True", add_special_tokens=False)
    false_tokens = processor.tokenizer.encode(" False", add_special_tokens=False)
    processor.tokenizer.padding_side = "right"
    if processor.tokenizer.pad_token is None:
        processor.tokenizer.pad_token = processor.tokenizer.eos_token

    processed = []
    for ex in examples:
        img_p = cache_path(ex["image"])
        if not img_p.exists():
            continue
        img = Image.open(img_p).convert("RGB")
        prompt = TRAIN_PROMPT.format(statement=ex["statement"])
        answer = "True" if ex["label"] else "False"
        messages = [{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": prompt}
        ]}]
        prompt_inputs = processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt",
        )
        prompt_ids = prompt_inputs["input_ids"].squeeze(0)
        answer_ids = torch.tensor(true_tokens if ex["label"] else false_tokens,
                                  dtype=prompt_ids.dtype)
        full_ids = torch.cat([prompt_ids, answer_ids])[:max_length]
        attention_mask = torch.ones_like(full_ids)
        labels = torch.full_like(full_ids, -100)
        labels[prompt_ids.shape[0]:full_ids.shape[0]] = full_ids[prompt_ids.shape[0]:full_ids.shape[0]]
        pixel_values = prompt_inputs.get("pixel_values", None)
        if pixel_values is not None and pixel_values.dim() >= 2:
            pixel_values = pixel_values.squeeze(0) if pixel_values.dim() == 3 else pixel_values
        else:
            pixel_values = None
        image_grid_thw = prompt_inputs.get("image_grid_thw", None)
        if image_grid_thw is not None:
            image_grid_thw = image_grid_thw.squeeze(0) if image_grid_thw.dim() == 2 else image_grid_thw
        mm_tt = prompt_inputs.get("mm_token_type_ids", None)
        if mm_tt is not None:
            mm_tt = mm_tt.squeeze(0)
            extra_len = full_ids.shape[0] - mm_tt.shape[0]
            if extra_len > 0:
                mm_tt = torch.cat([mm_tt, torch.zeros(extra_len, dtype=mm_tt.dtype)])
            mm_tt = mm_tt[:max_length]
        else:
            mm_tt = None
        processed.append({"input_ids": full_ids, "attention_mask": attention_mask,
                          "labels": labels, "pixel_values": pixel_values,
                          "image_grid_thw": image_grid_thw, "mm_token_type_ids": mm_tt})
    if not processed:
        return None
    max_len = max(p["input_ids"].shape[0] for p in processed)
    batch_ids, batch_mask, batch_labels, batch_pv, batch_grid, batch_mm = [], [], [], [], [], []
    for p in processed:
        ids = p["input_ids"][:max_len]
        mask = p["attention_mask"][:max_len]
        labels = p["labels"][:max_len]
        pad = max_len - ids.shape[0]
        if pad > 0:
            ids = torch.cat([ids, torch.zeros(pad, dtype=ids.dtype)])
            mask = torch.cat([mask, torch.zeros(pad, dtype=mask.dtype)])
            labels = torch.cat([labels, torch.full((pad,), -100, dtype=labels.dtype)])
        batch_ids.append(ids)
        batch_mask.append(mask)
        batch_labels.append(labels)
        if p["pixel_values"] is not None:
            batch_pv.append(p["pixel_values"])
        if p["image_grid_thw"] is not None:
            batch_grid.append(p["image_grid_thw"])
        if p.get("mm_token_type_ids") is not None:
            batch_mm.append(p["mm_token_type_ids"].squeeze(0) if p["mm_token_type_ids"].dim() > 1 else p["mm_token_type_ids"])
    result = {"input_ids": torch.stack(batch_ids), "attention_mask": torch.stack(batch_mask),
              "labels": torch.stack(batch_labels)}
    if batch_pv:
        result["pixel_values"] = torch.stack(batch_pv)
    if batch_grid:
        result["image_grid_thw"] = torch.stack(batch_grid)
    if batch_mm:
        mm_max = max(m.shape[0] for m in batch_mm)
        padded = [torch.cat([m, torch.zeros(mm_max - m.shape[0], dtype=m.dtype)]) if m.shape[0] < mm_max else m for m in batch_mm]
        result["mm_token_type_ids"] = torch.stack(padded)
    return result

def build_lora_targets(target):
    if target == "projector":
        return ["visual.merger.mlp.0", "visual.merger.mlp.2"]
    if target == "vision_proj":
        mods = ["visual.merger.mlp.0", "visual.merger.mlp.2"]
        for i in range(24, 32):
            mods += [f"visual.blocks.{i}.attn.qkv", f"visual.blocks.{i}.attn.proj",
                     f"visual.blocks.{i}.mlp.fc1", f"visual.blocks.{i}.mlp.fc2"]
        return mods
    raise ValueError(target)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["projector", "vision_proj"])
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    args = ap.parse_args()

    with open("data/manifests/general_train.jsonl") as f:
        examples = [json.loads(l) for l in f]
    print(f"Manifest: {len(examples)} examples", flush=True)

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, dtype=torch.bfloat16,
        _attn_implementation="eager", low_cpu_mem_usage=True,
    ).to("cuda")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    targets = build_lora_targets(args.target)
    print(f"LoRA targets ({len(targets)}): {targets}", flush=True)
    lora_config = LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
                             lora_dropout=0.05, target_modules=targets)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    dataset = Dataset.from_list(examples)
    split = dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split["train"]
    print(f"Train: {len(train_ds)}", flush=True)

    loader = DataLoader(train_ds, batch_size=1, shuffle=True,
                        collate_fn=lambda b: collate_batch(processor, b),
                        num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, total_steps // 10, total_steps)
    print(f"Total steps: {total_steps}", flush=True)

    out_dir = Path(f"checkpoints/qwen2vl_7b_{args.target}_lora")
    out_dir.mkdir(parents=True, exist_ok=True)
    model.train()
    global_step = 0
    t0 = time.time()
    for epoch in range(args.epochs):
        for batch in loader:
            if batch is None:
                continue
            input_ids = batch["input_ids"].to("cuda")
            attention_mask = batch["attention_mask"].to("cuda")
            labels = batch["labels"].to("cuda")
            fwd = dict(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            if "pixel_values" in batch:
                fwd["pixel_values"] = batch["pixel_values"].to("cuda")
            if "image_grid_thw" in batch:
                fwd["image_grid_thw"] = batch["image_grid_thw"].to("cuda")
            if "mm_token_type_ids" in batch:
                fwd["mm_token_type_ids"] = batch["mm_token_type_ids"].to("cuda")
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                out = model(**fwd)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            global_step += 1
            if global_step % 50 == 0:
                print(f"  Step {global_step}/{total_steps} | Loss: {out.loss.item():.4f} "
                      f"| {time.time()-t0:.0f}s", flush=True)
        print(f"Epoch {epoch+1}/{args.epochs} done | Loss: {out.loss.item():.4f}", flush=True)

    model.save_pretrained(out_dir / "final")
    processor.save_pretrained(out_dir / "final")
    print(f"Saved: {out_dir}/final in {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
