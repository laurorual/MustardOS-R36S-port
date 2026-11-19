#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Re-pin firmware inputs to their rebuilt origin files (M5).
  pin-input.py PATH...   for each image PATH in firmware-inputs.json, set
                         sha256 from its origin file (repo-relative) and
                         print old -> new; then run build-image.sh inputs.
  pin-input.py --origin PATH ORIGIN [MODE]   M6: point PATH at another
                         origin (repo-relative), adding the entry (MODE,
                         default 755) when it is new, and pin it."""
import hashlib, json, os, sys
repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
man = os.path.join(repo, 'port/packaging/firmware-inputs.json')
d = json.load(open(man))
by_path = {e['path']: e for e in d['entries'] if isinstance(e, dict)}
args = sys.argv[1:]
if args[:1] == ['--origin']:
    if len(args) not in (3, 4):
        sys.exit('usage: pin-input.py --origin PATH ORIGIN [MODE]')
    path, origin = args[1], args[2]
    if not os.path.isfile(os.path.join(repo, origin)):
        sys.exit(f'no origin file: {origin}')
    if path not in by_path:
        parent = os.path.dirname(path)
        if by_path.get(parent, {}).get('type') != 'dir':
            sys.exit(f'parent is not an input dir: {parent}')
        by_path[path] = {'path': path, 'type': 'file', 'mode': args[3] if len(args) == 4 else '755', 'sha256': '', 'origin': origin}
        d['entries'].append(by_path[path])
        print(f'{path}: new input')
    by_path[path]['origin'] = origin
    args = [path]
for p in args:
    e = by_path.get(p) or sys.exit(f'not an input: {p}')
    with open(os.path.join(repo, e['origin']), 'rb') as f:
        new = hashlib.sha256(f.read()).hexdigest()
    print(f"{p}: {e['sha256'][:12] or '-'} -> {new[:12]}")
    e['sha256'] = new
with open(man + '.tmp', 'w') as f:
    json.dump(d, f, indent=1)
    f.write('\n')
os.replace(man + '.tmp', man)
