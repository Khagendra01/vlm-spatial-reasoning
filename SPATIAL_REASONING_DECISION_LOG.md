# SPATIAL_REASONING_DECISION_LOG

Chronological, append-only record of decisions made for the spatial-reasoning
research line. Entries are stamped exactly when the described decision is
made. "FROZEN BEFORE TRAINING" entries bind the artifact versions they cite.

---

## 2026-08-11 - Seed Campaign pre-registration (FROZEN BEFORE TRAINING)

**Decision.** Re-train the two general-VSR LoRA backbones
(Qwen2-VL-7B-Instruct, SmolVLM2-2.2B-Instruct) under three fresh random
seeds (A=101, B=202, C=303) with every training-run input identical to the
respective seed-0 runs EXCEPT the seed. Three user-approved choices:

1. **Battery**: implement + pre-register the full HEAVY battery (normal,
   with_sample 2px, with_shuffle, relcomp <0.3, facing, hflip, hflip_inv)
   under the uniform 392px evaluation contract, evaluated on all six
   checkpoints.
2. **Split frozen at 42**: keep the 95/5 train/val split mapping at
   seed=42 for all runs; only train-time RNG (LoRA init, DataLoader
   shuffle order, dropout) varies with the campaign seed.
3. **Scope**: full 3x2 campaign runs in background; results reported per
   stage.

**Frozen bound artifacts.**
- Full spec: `configs/seed_campaign/SEED_CAMPAIGN.json`
- Battery rationale + contract: `configs/seed_campaign/BATTERY_JUSTIFICATION.md`
- Training recipe sources (verbatim): `scripts/run_7b_pipeline.py` PHASE 2
  (master), `src/training/lora.py` + `src/training/collator.py` (master)
- Seed-0 reference artifacts: `checkpoints/general_lora/final` incl.
  `training_log.json` (2B; epoch losses 0.513/0.414; 6253s),
  `checkpoints/qwen2vl_7b_general_lora/final` (7B; master)
- Manifest (NOT rebuilt): `data/manifests/general_train.jsonl`

**Findings recorded at freeze time.**
- Seed-0 training runs were unseeded; the campaign adds explicit seeds.
- The battery existed only as a spec (aftertrain.md); no implementation
  existed in the repo (all branches searched).
- 2B micro-batch ambiguity (train() signature defaults 4/4 vs CLI defaults
  1/16) resolved to the CLI defaults the seed-0 run used (effective batch
  16 identical either way); verified against seed-0 training_log.json.
- Seed-0 2B reference loss: epoch1 0.513, epoch2 0.414 (adaptation-sanity
  target for new seeds).

**State at freeze: no campaign files existed before this entry**
(configs/seed_campaign/, scripts/run_seed_campaign.py, battery drivers,
results/seed_campaign/ all absent; git tree clean).

---

## 2026-08-11 - Machine closure / handoff (campaign interrupted mid-run)

The cloud device was closed while the seed campaign training queue was
running (7B seedA in training loop; no adapter saved yet). All campaign
artifacts were pushed to origin/research/spatial-grounding-audit along with
configs/seed_campaign/RUN_STATUS.md (full resumption checklist, machine
config notes, pending-work list). Battery drivers were implemented but not
runtime-validated; battery evals + analysis remain pending. Campaign spec,
recipes, seed semantics and progress state are unchanged (frozen entry above).
