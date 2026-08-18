"""Verify deterministic dataset across two separate processes."""
import sys
sys.path.insert(0, '.')
from pathlib import Path
import shutil, hashlib

hashes = {}
for run in ['a', 'b']:
    d = Path(f'results/det_check_{run}')
    shutil.rmtree(d, ignore_errors=True)
    from equiorient.data.manifests import build
    r = build(d, n_dev=8, n_train=16, n_val=8, n_test=8)
    h = hashlib.sha256()
    for f in sorted(d.glob('*.png')):
        h.update(f.read_bytes())
    hashes[run] = h.hexdigest()
    print(f'{run}: png_sha={h.hexdigest()[:16]}... '
          f'manifest_sha={r["train_scene_manifest_sha256"][:16]}...')

print(f"\nDETERMINISTIC: {hashes['a'] == hashes['b']}")
