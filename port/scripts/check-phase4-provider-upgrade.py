#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C71 migration/rollback fault fixtures on regular fixture directories only."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, os, shutil, subprocess, tempfile
from phase4_candidate import inventory, sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade'
plan_stage = Path((area / 'latest-plan').read_text().strip())
plan = json.loads((plan_stage / 'plan.json').read_text())
manifest = json.loads((plan_stage / 'manifest.json').read_text())
assert plan['passed'] and sha(plan_stage / 'plan.json') == manifest['plan_sha256']
assert sha(plan_stage / 'backup.json') == manifest['backup_sha256']
for n, h in sums(plan_stage / 'SHA256SUMS').items():
    assert sha(plan_stage / n) == h
for n, h in plan['source_sha256'].items():
    assert sha(repo / n) == h
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=area))
container = (work / 'rootfs-container.iid').read_text().strip()
rel = lambda p: '/work/' + str(p.relative_to(work))
events = ([('directory-created', n) for n in plan['new_directories']] +
          [(label, n) for n in sorted(plan['after']) for label in ['file-staged', 'file-installed']] +
          [('file-removed', n) for n in sorted(set(plan['before']) - set(plan['after']))] +
          [('directory-removed', n) for n in reversed(plan['old_directories'])] +
          [(n, '') for n in ['guard', 'rw', 'verify', 'sync', 'ro']])
cases = [{'name': 'complete apply and explicit rollback', 'kind': 'success'}]
cases += [{'name': 'fail ' + event + ' ' + name, 'kind': 'fault', 'event': event, 'path': name}
          for event, name in events]
cases += [{'name': name, 'kind': name} for name in ['wrong old hash', 'wrong old mode', 'old hardlink',
    'old symlink', 'shared parent symlink', 'unsafe shared parent', 'new destination collision',
    'temp collision', 'extra old metadata leaf', 'extra old empty directory', 'payload corruption',
    'backup corruption', 'extra BEFORE path', 'extra AFTER path', 'preserved drift',
    'preserve unexpected replacement', 'preserve corrupt temporary', 'preserve new neighbor']]
for index, case in enumerate(cases):
    directory = stage / f'case-{index:03d}'
    root = directory / 'root'; payload = directory / 'payload'; state = directory / 'state'
    root.mkdir(parents=True); state.mkdir()
    shutil.copytree(plan_stage / 'payload', payload)
    for name in plan['old_directories']:
        (root / name).mkdir(parents=True, exist_ok=True)
    for name, row in plan['before'].items():
        dest = root / name; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(payload / 'old' / name, dest); dest.chmod(row['mode'])
    # A fixture sentinel represents the fixed public foundation guard; actual
    # native foundation/media checks remain the adapter's separate contract.
    (root / 'preserved.txt').write_text('unchanged public foundation fixture\n')
    (payload / 'preserved.sha256').write_text(sha(root / 'preserved.txt') + '  preserved.txt\n')
    baseline = inventory(root)
    (directory / 'before.json').write_text(json.dumps(baseline, sort_keys=True))
    leaf = root / 'opt/muos/frontend/muxretro'
    add = root / 'usr/share/muos-frontend-libs'
    kind = case['kind']
    if kind == 'wrong old hash': leaf.write_text('wrong old host\n')
    if kind == 'wrong old mode': leaf.chmod(0o700)
    if kind == 'old hardlink': os.link(leaf, directory / 'old.link')
    if kind == 'old symlink': leaf.unlink(); leaf.symlink_to('/outside-never-opened')
    if kind == 'shared parent symlink':
        parent = root / 'opt/muos/frontend'; parent.rename(directory / 'frontend'); parent.symlink_to(directory / 'frontend')
    if kind == 'unsafe shared parent': leaf.parent.chmod(0o777)
    if kind == 'new destination collision': add.mkdir(parents=True)
    if kind == 'temp collision': leaf.with_name(leaf.name + '.c71-new').write_text('foreign temporary\n')
    if kind == 'extra old metadata leaf': (root / 'usr/share/muos-muxretro/unknown.txt').write_text('keep me\n')
    if kind == 'extra old empty directory': (root / 'usr/share/muos-muxretro/unknown').mkdir()
    if kind == 'payload corruption': (payload / 'new/opt/muos/frontend/muxretro').write_text('corrupt new\n')
    if kind == 'backup corruption': (payload / 'old/opt/muos/frontend/muxretro').write_text('corrupt backup\n')
    if kind in ['extra BEFORE path', 'extra AFTER path']:
        with (payload / kind.split()[1]).open('a') as stream: stream.write('0' * 64 + ' 644 outside\n')
    if kind == 'preserved drift': (root / 'preserved.txt').write_text('drift\n')
    before_case = inventory(root)
    (directory / 'before-case.json').write_text(json.dumps(before_case, sort_keys=True))
    failure_event = case.get('event', '')
    failure_path = case.get('path', '')
    # Preserve tests mutate after the atomic host publication, then force
    # rollback: unexpected bytes/neighbors must remain for manual inspection.
    extra_hook = ''
    if kind.startswith('preserve '):
        failure_event = 'file-installed'; failure_path = 'opt/muos/frontend/muxretro'
        if kind == 'preserve unexpected replacement':
            extra_hook = 'printf "unknown replacement\\n" > "$install_root/opt/muos/frontend/muxretro"\n'
        elif kind == 'preserve corrupt temporary':
            extra_hook = 'printf "partial unknown\\n" > "$install_root/opt/muos/frontend/muxretro.c71-new"\n'
        else:
            extra_hook = 'printf "unknown neighbor\\n" > "$install_root/usr/share/muos-frontend-libs/unknown"\n'
    script = f'''set -eu
install_root={rel(root)}
install_payload={rel(payload)}
install_state={rel(state)}
install_rw=0
. {rel(plan_stage / 'policy.sh')}
. {rel(plan_stage / 'transaction.sh')}
install_exec() {{
    printf '%s %s\\n' "$1" "${{2:-}}" >> "$install_state/events"
    if [ "$1" = rw ]; then install_rw=1; fi
    if [ "$1" = '{failure_event}' ] && [ "${{2:-}}" = '{failure_path}' ] && [ ! -e "$install_state/injected" ]; then
        touch "$install_state/injected"
        {extra_hook}
        return 1
    fi
    return 0
}}
set +e
c71_apply > "$install_state/apply.log" 2>&1
rc=$?
set -e
printf '%s\\n' "$rc" > "$install_state/apply.rc"
'''
    if kind == 'success':
        script += '''[ "$rc" = 0 ]
c71_tree AFTER
install_rw=1
c71_rollback > "$install_state/rollback.log" 2>&1
c71_tree BEFORE
printf 'C71_EXACT_ROLLBACK_OK\n'
'''
    elif kind.startswith('preserve '):
        script += '''[ "$rc" != 0 ]
if c71_rollback > "$install_state/rollback.log" 2>&1; then exit 90; fi
printf 'C71_UNKNOWN_CONTENT_PRESERVED\n'
'''
    elif kind == 'fault':
        script += '''[ "$rc" != 0 ]
if [ "$install_rw" = 1 ]; then c71_rollback > "$install_state/rollback.log" 2>&1; fi
c71_tree BEFORE
printf 'C71_INJECTED_FAILURE_RECOVERED\n'
'''
    else:
        script += '''[ "$rc" != 0 ]
[ "$install_rw" = 0 ]
printf 'C71_PREFLIGHT_REFUSAL_NO_RW\n'
'''
    (directory / 'test.sh').write_text(script)
    case['directory'] = str(directory)

def execute(case):
    directory = Path(case['directory'])
    cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
        '--security-opt=no-new-privileges', '--userns=keep-id', '--tmpfs', '/tmp:rw,nosuid,nodev',
        '-v', f'{work}:/work:rw,z', container, '/work/graphics-config/output/host/bin/fakeroot',
        'sh', rel(directory / 'test.sh')]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (directory / suffix).write_text(value)
    assert result.returncode == 0, (directory, case['name'], result.stdout[-1000:], result.stderr[-1000:])
    kind = case['kind']
    if not kind.startswith('preserve '):
        expected = json.loads((directory / ('before.json' if kind in ['success', 'fault'] else 'before-case.json')).read_text())
        assert inventory(directory / 'root') == expected, (directory, 'fixture root differs')
    else:
        path = directory / 'root/opt/muos/frontend/muxretro'
        if kind == 'preserve unexpected replacement': assert path.read_text() == 'unknown replacement\n'
        if kind == 'preserve corrupt temporary': assert path.with_name(path.name + '.c71-new').read_text() == 'partial unknown\n'
        if kind == 'preserve new neighbor': assert (directory / 'root/usr/share/muos-frontend-libs/unknown').read_text() == 'unknown neighbor\n'
    return {'name': case['name'], 'passed': True, 'kind': kind}

# Independent fixture roots, three containers at most; no native device work.
results = []
with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(execute, cases):
        results.append(result)
        print('C71 fixture', len(results), '/', len(cases), result['name'], flush=True)
sources = [Path(__file__), repo / 'port/device/rk-r35s-p0/provider-upgrade/transaction.sh']
report = {'passed': True, 'experiment': 'C71_PROVIDER_UPGRADE_FAULT_FIXTURES',
    'plan_sha256': sha(plan_stage / 'plan.json'), 'cases': results,
    'public_payloads_only': True, 'native_adapter_tested': False,
    'device_contacted': False, 'device_written': False,
    'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-checks').write_text(str(stage) + '\n')
print('C71 migration/failure fixtures passed:', len(results), stage)
