# DEPRECATED / DRIFTED — audit history only

Protocol correction 2026-08-11 (see SPATIAL_REASONING_DECISION_LOG "battery
drift" entry). Code audit determined these row files were built by the
drifted heavy battery:

- `with_sample` is actually a *wrong-image* 2px substitution (mislabeled)
- `with_shuffle` uses a re-hashed shuffle mapping, not the frozen protocol
  permutation (`results/grounding/protocol/shuffle_mapping.json`)
- the uniform 392px eval cap is not part of the frozen protocol

These files are therefore NOT the seed-campaign battery and are retained
verbatim as audit history. The corrected battery is the legacy Tier-A/B/C
protocol (normal, shuffle, relcomp, facingcomp, hflip_flip, hflip_invariant),
driven by `scripts/grounding/run_seed_battery.py`. This directory is not
consumed by any reportable result.