#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C72 adapter control-flow fixtures with fixed hardware paths redirected offline."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, shutil, subprocess
from phase4_candidate import inventory, sha

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade-native'
stage = Path((area / 'latest-plan').read_text().strip())
binding = json.loads((stage / 'binding.json').read_text())
for n, h in binding['source_sha256'].items(): assert sha(repo / n) == h
assert sha(stage / 'deployment.tar') == binding['deployment_sha256']
plan = json.loads((stage / 'plan.json').read_text())
checks = stage / 'checks'
checks.mkdir()
native_source = repo / 'port/device/rk-r35s-p0/provider-upgrade-native/native.sh'
text = native_source.read_text()
replacements = {
    'install_root=;': 'install_root=/fixture/root;',
    'c25_store=/var/lib/muos-diagnostic;': 'c25_store=/fixture/diagnostic;',
    'cat /proc/asound/card0/pcm0p/sub0/status': 'cat /fixture/pcm.status',
    'cat /proc/sys/kernel/random/boot_id': 'cat /fixture/boot-id',
    'exec 8>/run/muos/session/lifetime.lock': 'exec 8>/fixture/lifetime.lock',
    'for path in /var/lib/muos-network /var/lib/muos-seedrng /root/.ssh /var/lib/muos-diagnostic/boot-seq; do':
        'for path in /fixture/private-network /fixture/private-seed /fixture/private-ssh /fixture/diagnostic/boot-seq; do',
}
for before, after in replacements.items():
    assert text.count(before) == 1, before
    text = text.replace(before, after)
(checks / 'native-fixture.sh').write_text(text)
cases = ['apply verify rollback', 'wrong boot', 'wrong UUID', 'active token', 'PCM open',
    'active muxretro', 'low free space', 'readiness failure', 'lock occupied',
    'RW remount failure', 'RO remount failure', 'atomic publish failure',
    'TERM during publication', 'private drift', 'unexpected published bytes',
    'corrupt source before RW', 'invalid operation', 'invalid capsule path']
mock = r'''# C72 hardware substitutions; no mount syscall or device path.
c25_ready() { [ "$CASE" != 'readiness failure' ]; }
c25_media() { return 0; }
c25_quiet() { return 0; }
c25_foundation() { return 0; }
c25_root_mode() { [ "$(cat /fixture/root-mode)" = "$1" ]; }
mount() {
    printf '%s\n' "$*" >> /fixture/remount-events
    case "$2:$CASE" in
      remount,rw:RW\ remount\ failure) return 1 ;;
      remount,ro:RO\ remount\ failure)
        if [ ! -e /fixture/RO-failed ]; then touch /fixture/RO-failed;return 1;fi ;;
    esac
    case "$2" in remount,rw) echo rw > /fixture/root-mode;;remount,ro) echo ro > /fixture/root-mode;;*) return 64;;esac
}
sync() { return 0; }
df() {
    echo 'Filesystem 1024-blocks Used Available Capacity Mounted on'
    if [ "$CASE" = 'low free space' ]; then echo 'fixture 100 99 1 99% /'; else echo 'fixture 100000 1 99999 1% /';fi
}
pidof() { [ "$CASE" = 'active muxretro' ]; }
mv() {
    case "$*" in *opt/muos/frontend/muxretro.c71-new*)
      if [ ! -e /fixture/publish-hook ]; then
        touch /fixture/publish-hook
        case "$CASE" in
          'atomic publish failure') return 1 ;;
          'TERM during publication') kill -TERM $$;return 1 ;;
        esac
        command mv "$@" || return $?
        case "$CASE" in
          'private drift') echo changed-private > /fixture/private-network/value ;;
          'unexpected published bytes') echo unknown-published > /fixture/root/opt/muos/frontend/muxretro;return 1 ;;
        esac
        return 0
      fi ;;
    esac
    command mv "$@"
}
'''
for index, name in enumerate(cases):
    case = checks / f'case-{index:02d}'
    root = case / 'root'; deployment = case / 'deployment'; mocks = case / 'mocks'
    root.mkdir(parents=True); deployment.mkdir(); mocks.mkdir()
    shutil.copytree(stage / 'payload', deployment / 'payload')
    for file in ['policy.sh', 'transaction.sh']:
        shutil.copyfile(stage / file, deployment / file)
    shutil.copyfile(checks / 'native-fixture.sh', deployment / 'native.sh')
    for directory in plan['old_directories']: (root / directory).mkdir(parents=True, exist_ok=True)
    for path, row in plan['before'].items():
        dest = root / path;dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(deployment / 'payload/old' / path, dest);dest.chmod(row['mode'])
    (root / 'preserved.txt').write_text('fixture public foundation\n')
    (deployment / 'payload/preserved.sha256').write_text(sha(root / 'preserved.txt') + '  preserved.txt\n')
    (case / 'diagnostic').mkdir();(case / 'diagnostic/boot-seq').write_text('71\n')
    (deployment / 'binding-boot').write_text('72\n' if name == 'wrong boot' else '71\n')
    uuid = '00000000-0000-0000-0000-000000000071\n'
    (case / 'boot-id').write_text(uuid)
    (deployment / 'binding-uuid').write_text('00000000-0000-0000-0000-000000000000\n' if name == 'wrong UUID' else uuid)
    (case / 'pcm.status').write_text('RUNNING\n' if name == 'PCM open' else 'closed\n')
    (case / 'root-mode').write_text('ro\n')
    for directory in ['private-network', 'private-seed', 'private-ssh']:
        (case / directory).mkdir();(case / directory / 'value').write_text('synthetic private sentinel\n')
    if name == 'active token': (case / 'diagnostic/c25.once').write_text('fixture token\n')
    if name == 'corrupt source before RW': (deployment / 'payload/new/opt/muos/frontend/muxretro').write_text('corrupt\n')
    (case / 'before.json').write_text(json.dumps(inventory(root), sort_keys=True))
    for file in ['policy.sh', 'card-guard.sh']: (mocks / file).write_text('# fixture import\n')
    (mocks / 'native.sh').write_text(mock)
    files = [p for p in deployment.rglob('*') if p.is_file()]
    (deployment / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(deployment)) + '\n' for p in files))
    argument = '/run/muos-c72.ABC123' if name != 'invalid capsule path' else '/tmp/not-authorized'
    action = 'apply' if name != 'invalid operation' else 'launch'
    script = f'''set -eu
if [ "$CASE" = 'lock occupied' ]; then exec 9>/fixture/lifetime.lock;flock -n 9;fi
set +e
sh {argument}/native.sh {argument} {action} > /fixture/native.stdout 2> /fixture/native.stderr
rc=$?
set -e
echo "$rc" > /fixture/native.exit
[ "$(cat /fixture/root-mode)" = ro ]
'''
    if name == 'invalid capsule path':
        # Execute the real redirected source with a bad argument, rather than
        # fail only because the invalid path has no native.sh file.
        script = script.replace('sh /tmp/not-authorized/native.sh', 'sh /run/muos-c72.ABC123/native.sh')
    if name == 'apply verify rollback':
        script += '''[ "$rc" = 0 ]
sh /run/muos-c72.ABC123/native.sh /run/muos-c72.ABC123 verify > /fixture/verify.stdout
sh /run/muos-c72.ABC123/native.sh /run/muos-c72.ABC123 rollback > /fixture/rollback.stdout
[ "$(cat /fixture/root-mode)" = ro ]
'''
    else: script += '[ "$rc" != 0 ]\n'
    (case / 'test.sh').write_text(script)

def execute(item):
    index, name = item
    case = checks / f'case-{index:02d}'
    cmd = ['podman', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=all',
        '--security-opt=no-new-privileges', '--userns=keep-id:uid=0,gid=0', '--user=0',
        '--tmpfs', '/tmp:rw,nosuid,nodev', '-v', f'{work}:/work:ro,z',
        '-v', f'{case}:/fixture:rw,z', '-v', f'{case}/deployment:/run/muos-c72.ABC123:rw,z',
        '-v', f'{case}/mocks:/usr/libexec/muos-c25:ro,z', '-e', 'CASE=' + name,
        (work / 'rootfs-container.iid').read_text().strip(), 'sh', '/fixture/test.sh']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    (case / 'container.stdout').write_text(result.stdout);(case / 'container.stderr').write_text(result.stderr)
    assert result.returncode == 0, (case, name, result.stderr[-1500:])
    before = json.loads((case / 'before.json').read_text())
    after = inventory(case / 'root')
    if name == 'unexpected published bytes':
        assert (case / 'root/opt/muos/frontend/muxretro').read_text() == 'unknown-published\n'
        assert (case / 'root-mode').read_text() == 'ro\n'
    else: assert before == after, (case, 'before-state not restored/preserved')
    if name == 'private drift':
        assert (case / 'private-network/value').read_text() == 'changed-private\n'
    else: assert (case / 'private-network/value').read_text() == 'synthetic private sentinel\n'
    return {'name': name, 'passed': True}

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(execute, enumerate(cases)))
sources = [Path(__file__), repo / 'port/scripts/run-phase4-provider-upgrade.py', native_source]
report = {'passed': True, 'experiment': 'C72_ADAPTER_CONTROL_FLOW_FIXTURES',
    'binding_sha256': sha(stage / 'binding.json'), 'cases': results,
    'fixed_path_substitutions': replacements, 'hardware_calls_mocked': True,
    'actual_device_remounts_tested': False, 'device_contacted': False, 'device_written': False,
    'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}
(stage / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
print('C72 bound adapter control-flow checks passed:', len(results), checks)
