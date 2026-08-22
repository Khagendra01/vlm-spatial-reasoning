"""Lightning AI VRAM smoke test — decides the E1/E2 backbone plan in ~20 min.

Run on a Lightning A10G (24 GB) studio:
    pip install torch transformers peft accelerate pillow
    python scripts/lightning_smoke_test.py

Verdicts printed at the end:
  INFERENCE-FIT : Qwen2-VL-7B bf16 no_grad forward  -> E2 can run here
  TRAIN-FIT     : +LoRA r8, batch-1 fwd/bwd w/ grad checkpointing -> E1 7B viable
If TRAIN-FIT fails -> preregistered fallback: E1 backbone = SmolVLM2-2B.
"""
from __future__ import annotations

import gc

import torch
from PIL import Image

MODEL = "Qwen/Qwen2-VL-7B-Instruct"
LIMIT_GB = 24.0


def gb(x):
    return x / 1024**3


def report(tag, ok, peak_gb, need_note):
    verdict = "PASS" if ok else "FAIL"
    print(f"[{verdict}] {tag}: peak {peak_gb:.2f} / {LIMIT_GB} GB ({need_note})")
    return ok


def cleanup():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()


def main():
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    assert torch.cuda.is_available(), "need a GPU runtime"
    name = torch.cuda.get_device_name(0)
    total = gb(torch.cuda.get_device_properties(0).total_memory)
    print(f"GPU: {name} ({total:.1f} GB)")

    img = Image.new("RGB", (192, 192))
    for i in range(0, 192, 8):
        for j in range(0, 192, 8):
            img.putpixel((i, j), ((i * 7) % 255, (j * 13) % 255, 128))

    proc = AutoProcessor.from_pretrained(
        MODEL, min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)
    msgs = [{"role": "user",
             "content": [{"type": "image"}, {"type": "text",
                         "text": "The block is left of the cone. True or false?"}]}]
    prompt = proc.apply_chat_template(msgs, add_generation_prompt=True)
    enc = proc(text=[prompt], images=[img], return_tensors="pt")

    # ---- Phase 1: E2-style inference footprint ----
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, attn_implementation="sdpa")
    model.to("cuda").eval()
    pix = enc["pixel_values"].to("cuda", dtype=torch.bfloat16)
    grid = enc["image_grid_thw"].to("cuda")
    ids = enc["input_ids"].to("cuda")
    attn = enc["attention_mask"].to("cuda")
    with torch.no_grad():
        out = model(input_ids=ids, attention_mask=attn,
                    pixel_values=pix, image_grid_thw=grid)
        _ = out.logits.sum()
    peak_inf = gb(torch.cuda.max_memory_allocated())
    inf_ok = report("INFERENCE-FIT (E2)", peak_inf < LIMIT_GB - 1, peak_inf,
                    "Qwen2-VL bf16 no_grad")

    # ---- Phase 2: E1-style training step ----
    del out
    cleanup()
    try:
        from peft import LoraConfig, get_peft_model
        lcfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
        m = get_peft_model(model, lcfg)
        m.gradient_checkpointing_enable()
        m.enable_input_require_grads()
        m.train()
        labels = ids.clone()
        res = m(input_ids=ids, attention_mask=attn, pixel_values=pix,
                image_grid_thw=grid, labels=ids)
        res.loss.backward()
        m.zero_grad(set_to_none=True)
        peak_tr = gb(torch.cuda.max_memory_allocated())
        tr_ok = report("TRAIN-FIT (E1, 7B)", peak_tr < LIMIT_GB - 1, peak_tr,
                       "LoRA r8 batch1 + grad ckpt")
    except torch.cuda.OutOfMemoryError:
        peak_tr = gb(torch.cuda.max_memory_allocated())
        tr_ok = report("TRAIN-FIT (E1, 7B)", False, peak_tr,
                       "OOM during training step")
    finally:
        cleanup()

    # ---- Phase 3: fallback backbone ----
    if not tr_ok:
        print("-> 7B training does not fit; verifying SmolVLM2 fallback path...")
        try:
            del m, model
            cleanup()
            from transformers import AutoModelForImageTextToText, AutoProcessor as AP
            sm = AutoModelForImageTextToText.from_pretrained(
                "HuggingFaceTB/SmolVLM2-2.2B-Instruct", torch_dtype=torch.bfloat16)
            sm.to("cuda").train()
            sp = AP.from_pretrained("HuggingFaceTB/SmolVLM2-2.2B-Instruct")
            se = sp(images=[img], text="The block is left of the cone.", return_tensors="pt")
            loss = sm(**{k: v.to("cuda") for k, v in se.items()}).loss
            loss.backward()
            report("FALLBACK SmolVLM2-2B trains", True,
                   gb(torch.cuda.max_memory_allocated()), "fallback confirmed usable")
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] fallback check error: {e}")

    print("\nDECISION:")
    if inf_ok and tr_ok:
        print("  All-E1+E2 on this A10G (Scenario A). Proceed with 15 seeds.")
    elif inf_ok:
        print("  E2 here; E1 switches to preregistered SmolVLM2 fallback "
              "(Scenario B). Log deviation before training.")
    else:
        print("  This GPU cannot host Qwen2-VL bf16 at all — escalate.")


if __name__ == "__main__":
    main()
