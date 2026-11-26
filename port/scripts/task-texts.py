#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# M9: the Task Toolkit texts in every MustardOS language, from one source
# (port/packaging/task-texts.json):
#   - port/packaging/language/<Language>.json, section muxtask: task and
#     folder names and help texts (frontend patch 0013 shows names through
#     it); English and English (American) get only the port's overrides
#   - rootfs /usr/share/muos-r35s/task-text/<Language>.txt: "English<TAB>
#     translation" lines that the update task scripts look up (T in
#     muos-update-finish.sh and Install Firmware Update.sh)
#   task-texts.py write | check   (check: the generated files are current)
import json, os, sys
repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = json.load(open(os.path.join(repo, 'port/packaging/task-texts.json'), encoding='utf-8'))
langdir = os.path.join(repo, 'port/packaging/language')
txtdir = os.path.join(repo, 'port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/task-text')
keys = src['keys']
want = {}  # path -> text
for lang, values in sorted(src['tr'].items()):
    assert len(values) == len(keys), lang
    pairs = dict(zip(keys, values))
    path = os.path.join(langdir, lang + '.json')
    data = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    data.setdefault('muxtask', {}).update(pairs)
    want[path] = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    want[os.path.join(txtdir, lang + '.txt')] = ''.join(f'{k}\t{v}\n' for k, v in pairs.items() if '\t' not in k + v and '\n' not in k + v)
for lang in ('English', 'English (American)'):
    path = os.path.join(langdir, lang + '.json')
    data = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    data.setdefault('muxtask', {}).update(src['English'])
    want[path] = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
stale = [p for p, t in want.items() if not os.path.exists(p) or open(p, encoding='utf-8').read() != t]
if mode == 'write':
    os.makedirs(txtdir, exist_ok=True)
    for p in stale:
        open(p, 'w', encoding='utf-8').write(want[p])
    print(f'wrote {len(stale)} of {len(want)} files')
elif mode == 'check':
    if stale:
        sys.exit('stale (run task-texts.py write): ' + ', '.join(os.path.relpath(p, repo) for p in stale))
    print(f'ok: {len(want)} files current')
else:
    sys.exit(__doc__ or 'usage: task-texts.py write|check')
