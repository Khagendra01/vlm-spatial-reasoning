# Handoff note for the orchestrator (from the cloud/seed-variance session)

## What was completed (all pushed; HEAD = d6d9588 on paper-draft-v1)

1. **Seed-variance experiment: DONE** (reviewer P3 deliverable).
   - Required runs (per SEED_VARIANCE_JOB.md): general 101/202, hardneg 101/202
     — all COMPLETE with metrics.json + predictions.csv + consistency_flips.csv.
   - Bonus runs that also completed: general/303, targeted/101, targeted/202.
   - Interrupted at teardown (not reportable): targeted/303 (weights saved, no
     eval), hardneg/303 (empty). Excluded from all summaries.
   - Results committed at results/seed_variance/ (84 tracked files) and
     summarized in results/seed_variance/summary.json.

2. **Paper text updated** (main.tex + sec/A_appendix.tex):
   - App. D "Single-checkpoint note" rewritten with measured multi-seed stats:
     General 84.15 ± 0.36% overall / 67.15 ± 2.63% orientation (3 seeds);
     Targeted 83.39 ± 0.10 / 64.96 ± 3.10 (2 seeds); Hard-Neg 83.85 ± 0.23 /
     67.52 ± 0.52 (2 seeds). Every between-condition orientation delta falls
     INSIDE the pooled seed-to-seed SD (1.9-2.9 pp). FF consistency stable
     (hardneg 72.8% both seeds).
   - main.tex Limitations: "multi-seed extension is prepared" -> "completed ...
     deltas inside seed SD (App. D)".
   - Appendix Environments + artifacts-table rows updated.

3. **PDFs rebuilt with tectonic** (no LaTeX toolchain was available locally;
   tectonic 0.17.0 was used):
   - submission/wacv2027/main.pdf = 9 pages (8 content + refs) — matches
     the established target.
   - submission/wacv2027/supplementary.pdf = 12 pages — matches the last
     documented count.
   - Verified the new seed-variance text is present in the built PDFs.
   - Note: tectonic emits pre-existing overfull-hbox warnings (artifacts-table
     caption, line-129 paragraph); these existed before and do not change
     pagination vs. the prior build.

## Cloud state

- All instances deleted, 0 snapshots, billing stopped. Nothing running.
- Provisioner (cloud_setup/setup_machine.sh) + supervisor
  (cloud_setup/job_supervisor.sh) committed for any future re-run;
  re-provisioning is ~10 min if the two partial 303s are ever wanted.

## Issues found & fixed along the way (for the record)

- Repo clone was 1.2 GB (checkpoints/); provisioner now uses sparse +
  partial clone (--filter=blob:none) — cone: src/scripts/configs/data/
  cloud_setup/docs + top-level files.
- requirements.txt was unresolvable: huggingface_hub 0.29.2 -> 1.27.0
  (transformers 5.14.1 needs >=1.5); added torchvision==0.27.1+cu130 and
  num2words==0.5.14 (both required by the Qwen2-VL / SmolVLM2 processors).
- run_seed_variance.py: manifest ids normalized to str — hardneg_train.jsonl
  mixes int ids (430) with string ids ("171_hn"), which crashed
  Dataset.from_list with ArrowInvalid (caught by the supervisor on both
  hardneg seeds).

## Remaining (optional)

- Token rotation: HF hf_Uldjpf..., Go API key, GitHub PAT ghp_gtt8... were
  exposed in-session; rotate when convenient.
- The two partial 303 runs could be completed later (~$1.30, ~2 h) if
  symmetric 3-seed stats are ever wanted — not required.
