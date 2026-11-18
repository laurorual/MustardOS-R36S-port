#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Re-pin firmware inputs to their rebuilt origin files (M5).
  pin-input.py PATH...   for each image PATH in firmware-inputs.json, set
                         sha256 from its origin file (repo-relative) and
                         print old -> new; then run build-image.sh inputs."""
import hashlib, json, os, sys
repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
man = os.path.join(repo, 'port/packaging/firmware-inputs.json')
d = json.load(open(man))
by_path = {e['path']: e for e in d['entries'] if isinstance(e, dict)}
for p in sys.argv[1:]:
    e = by_path.get(p) or sys.exit(f'not an input: {p}')
    with open(os.path.join(repo, e['origin']), 'rb') as f:
        new = hashlib.sha256(f.read()).hexdigest()
    print(f"{p}: {e['sha256'][:12]} -> {new[:12]}")
    e['sha256'] = new
with open(man + '.tmp', 'w') as f:
    json.dump(d, f, indent=1)
    f.write('\n')
os.replace(man + '.tmp', man)
