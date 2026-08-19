"""Build all data configs via Modal API (CPU-only, no model load)."""
import modal
import sys
sys.path.insert(0, ".")

# The modal app and functions are defined in modal/equiorient_nobox.py
# We need to import them via importlib to avoid the package name collision
import importlib.util
spec = importlib.util.spec_from_file_location(
    "eq_modal", "modal/equiorient_nobox.py")
mod = importlib.util.module_from_spec(spec)
# Pre-import the modal SDK so the local module finds it
sys.modules["modal_app"] = mod
spec.loader.exec_module(mod)
prepare_data = mod.prepare_data

configs = [
    {"target_size_min": 4.0, "target_size_max": 7.0,
     "n_dist_min": 6, "n_dist_max": 10, "noise_amp": 8,
     "variant": "nobox_v1"},
    {"target_size_min": 4.0, "target_size_max": 7.0,
     "n_dist_min": 6, "n_dist_max": 10, "noise_amp": 8,
     "variant": "nobox_v2_colorflip"},
    {"target_size_min": 6.0, "target_size_max": 10.0,
     "n_dist_min": 4, "n_dist_max": 6, "noise_amp": 4,
     "variant": "nobox_v2_colorflip"},
    {"target_size_min": 5.0, "target_size_max": 8.0,
     "n_dist_min": 5, "n_dist_max": 8, "noise_amp": 6,
     "variant": "nobox_v2_colorflip"},
    {"target_size_min": 4.0, "target_size_max": 7.0,
     "n_dist_min": 4, "n_dist_max": 6, "noise_amp": 4,
     "variant": "nobox_v2_colorflip"},
]

for i, cfg in enumerate(configs):
    print(f"[{i+1}/{len(configs)}] Building: {cfg}", flush=True)
    r = prepare_data.remote(**cfg)
    print(f"  key={r['data_key']} rebuilt={r['rebuilt']} "
          f"examples={r['n_examples']}", flush=True)
print("ALL DATA BUILT")
