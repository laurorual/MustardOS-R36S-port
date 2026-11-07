#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C72 bound, selective public-payload migration; never flash the C70 image."""
from pathlib import Path
import argparse, ipaddress, json, os, re, shutil, subprocess, tarfile, tempfile, time
from phase4_candidate import sha, sums
from phase4_muxretro_provider_session import historical, current_common

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
area = work / 'provider-upgrade-native'
area.mkdir(exist_ok=True)
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('operation', choices=['prepare', 'apply', 'verify', 'rollback'])
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
p.add_argument('--stage', type=Path)
a = p.parse_args()
proof = repo / 'dist/phase4/provider-upgrade'
for n, h in sums(proof / 'SHA256SUMS').items():
    assert sha(proof / n) == h
offline = Path((work / 'provider-upgrade/latest-plan').read_text().strip())
plan = json.loads((offline / 'plan.json').read_text())
assert (offline / 'plan.json').read_bytes() == (proof / 'plan.json').read_bytes()
for n, h in plan['source_sha256'].items():
    assert sha(repo / n) == h, n
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'), '-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=6', 'root@' + str(a.host)]
stage = Path(tempfile.mkdtemp(prefix='install.', dir=area)) if a.operation == 'prepare' else (
    a.stage.resolve() if a.stage else Path((area / 'latest-plan').read_text().strip()))
assert stage.is_relative_to(area)
stage.chmod(0o700)
def remote(label, code, timeout=40):
    (stage / (label + '.sh')).write_text(code)
    r = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=timeout)
    for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert r.returncode == 0, (stage, label, r.stderr[-1200:])
    return r.stdout

def leaves(records):
    code = ''
    for name, row in sorted(records.items()):
        code += f'''[ -f /{name} ];[ ! -L /{name} ]
[ "$(stat -c '%u:%g:%a:%h' /{name})" = 0:0:{row['mode']:o}:1 ]
[ "$(sha256sum /{name} | cut -d' ' -f1)" = {row['sha256']} ]
'''
    return code

infra = '''for name in udevd wpa_supplicant udhcpc dropbear; do
for pid in $(pidof "$name"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
base = '''set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic;c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e "$c25_store/c25.once" ];[ ! -L "$c25_store/c25.once" ]
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
if pidof muxretro smoke-check >/dev/null;then exit 64;fi
'''
if a.operation == 'prepare':
    # Do not loosen a historical session guard. The new deployment is bound to
    # the exact C68 boot before constructing its own before/after health gates.
    context, prior_stage, prior, provider_stage, provider, _ = historical()
    native_stage = work / 'muxretro-provider-session/load.8ef49rho'
    native = json.loads((native_stage / 'analysis.json').read_text())
    physical = json.loads((native_stage / 'physical-observation.json').read_text())
    assert native['passed'] and native['RAM_removed'] and native['cleanup_passed']
    assert physical['session_analysis_sha256'] == sha(native_stage / 'analysis.json')
    assert physical['image_and_navigation_confirmed'] and physical['sound_clean_and_audible_confirmed']
    assert physical['restore_to_saved_position_confirmed'] and physical['launcher_return_confirmed']
    boot, uuid = native['boot_sequence'], native['kernel_boot_id']
    assert type(boot) is int and re.fullmatch('[0-9a-f-]{36}', uuid)
    common = current_common(context['common'], prior['boot_sequence'], boot)
    common += f'[ "$(cat /proc/sys/kernel/random/boot_id)" = {uuid} ]\n'
    observed = remote('survey', common + leaves(plan['before']) + infra)
    assert observed == json.loads(Path(native['observation_stage'], 'observation.json').read_text())['infrastructure']
    for name in ['payload', 'policy.sh', 'transaction.sh', 'plan.json', 'backup.json']:
        source, target = offline / name, stage / name
        if source.is_dir(): shutil.copytree(source, target)
        else: shutil.copyfile(source, target)
    native_source = repo / 'port/device/rk-r35s-p0/provider-upgrade-native/native.sh'
    shutil.copyfile(native_source, stage / 'native.sh')
    (stage / 'binding-boot').write_text(str(boot) + '\n')
    (stage / 'binding-uuid').write_text(uuid + '\n')
    shutil.copyfile(provider_stage / 'load-probe', stage / 'provider-probe')
    (stage / 'provider-probe').chmod(0o700)
    files = [p for p in sorted((stage / 'payload').rglob('*')) if p.is_file()]
    files += [stage / name for name in ['policy.sh', 'transaction.sh', 'native.sh', 'binding-boot', 'binding-uuid', 'provider-probe']]
    (stage / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + str(p.relative_to(stage)) + '\n' for p in files))
    with tarfile.open(stage / 'deployment.tar', 'w') as archive:
        for path in files + [stage / 'SHA256SUMS']:
            info = archive.gettarinfo(str(path), arcname=str(path.relative_to(stage)))
            info.uid = info.gid = 0; info.uname = info.gname = 'root'
            with path.open('rb') as stream: archive.addfile(info, stream)
    (stage / 'deployment.tar').chmod(0o600)
    source_files = [Path(__file__), native_source]
    metadata = {'passed': True, 'experiment': 'C72_BOUND_PROVIDER_UPGRADE', 'host': str(a.host),
        'boot_sequence': boot, 'kernel_boot_id': uuid, 'infrastructure': observed,
        'C68_analysis_sha256': sha(native_stage / 'analysis.json'),
        'C71_proof_sha256': sha(proof / 'SHA256SUMS'), 'plan_sha256': sha(stage / 'plan.json'),
        'backup_sha256': sha(stage / 'backup.json'), 'deployment_sha256': sha(stage / 'deployment.tar'),
        'source_sha256': {str(p.relative_to(repo)): sha(p) for p in source_files}}
    (stage / 'binding.json').write_text(json.dumps(metadata, indent=2) + '\n')
    for path in [stage / name for name in ['plan.json', 'backup.json', 'deployment.tar', 'binding.json']]:
        with path.open('rb') as stream: os.fsync(stream.fileno())
    fd = os.open(stage, os.O_DIRECTORY); os.fsync(fd); os.close(fd)
    (area / 'latest-plan').write_text(str(stage) + '\n')
    print('C72 exact C68 boot surveyed; selective backup synced; no persistent write:', stage)
    raise SystemExit(0)

binding = json.loads((stage / 'binding.json').read_text())
assert binding['host'] == str(a.host) and binding['C71_proof_sha256'] == sha(proof / 'SHA256SUMS')
for name, key in [('plan.json', 'plan_sha256'), ('backup.json', 'backup_sha256'), ('deployment.tar', 'deployment_sha256')]:
    assert sha(stage / name) == binding[key]
for n, h in binding['source_sha256'].items():
    assert sha(repo / n) == h, n
base += f'''[ "$(cat "$c25_store/boot-seq")" = {binding['boot_sequence']} ]
[ "$(cat /proc/sys/kernel/random/boot_id)" = {binding['kernel_boot_id']} ]
'''
before, after = base + leaves(plan['before']), base + leaves(plan['after'])
for name in sorted(set(plan['before']) - set(plan['after'])):
    after += f'[ ! -e /{name} ];[ ! -L /{name} ]\n'
for name in plan['old_directories']:
    after += f'[ ! -e /{name} ];[ ! -L /{name} ]\n'
after += '''sha256sum -c /usr/share/muos-frontend-libs/payload.sha256 >/dev/null
sha256sum -c /usr/share/muos-muxretro-provider/payload.sha256 >/dev/null
sha256sum -c /usr/share/muos-muxretro-provider/provider-runtime.sha256 >/dev/null
sha256sum -c /usr/libexec/muos-save-store/payload.sha256 >/dev/null
'''
def capsule():
    directory = (stage / 'remote-directory').read_text().strip()
    assert re.fullmatch('/run/muos-c72[.][A-Za-z0-9]{6}', directory)
    return directory

if a.operation == 'apply':
    checks = json.loads((stage / 'checks.json').read_text())
    assert checks['passed'] and checks['binding_sha256'] == sha(stage / 'binding.json')
    for n, h in checks['source_sha256'].items(): assert sha(repo / n) == h
    assert not (stage / 'remote-directory').exists(), 'Never redispatch an allocated deployment'
    assert remote('before', before + infra) == binding['infrastructure']
    directory = remote('allocate', before + 'mktemp -d /run/muos-c72.XXXXXX\n').strip()
    assert re.fullmatch('/run/muos-c72[.][A-Za-z0-9]{6}', directory)
    (stage / 'remote-directory').write_text(directory + '\n')
    result = subprocess.run(ssh + ['cat > ' + directory + '/deployment.tar'],
                            input=(stage / 'deployment.tar').read_bytes(), capture_output=True, timeout=40)
    assert result.returncode == 0, 'RAM transfer failed; do not reapply'
    remote('unpack', f'''set -eu
printf '%s  %s\\n' {binding['deployment_sha256']} {directory}/deployment.tar | sha256sum -c - >/dev/null
tar -xf {directory}/deployment.tar -C {directory}
cd {directory}
sha256sum -c SHA256SUMS >/dev/null
''')
    remote('inspect', before + f'sh {directory}/native.sh {directory} inspect\n', timeout=90)
    remote('mounts-before', before + f'cat /proc/1/mountinfo > {directory}/mounts.before\n')
    remote('dispatch', before + f'nohup setsid sh {directory}/native.sh {directory} apply > {directory}/apply.log 2>&1 < /dev/null &\necho C72_DISPATCHED\n')
elif a.operation == 'rollback':
    directory = capsule()
    # An explicit recovery reuses the independent synced host backup. No
    # counter/key/seed/preferences/save bytes are restored by this action.
    remote('rollback', after + f'sh {directory}/native.sh {directory} rollback\n', timeout=120)
    assert remote('rollback-health', before + infra) == binding['infrastructure']
    print('C72 reviewed public before-state restored; root RO:', stage)
    raise SystemExit(0)
else:
    directory = capsule()

for attempt in range(60):
    result = subprocess.run(ssh + [f'test -f {directory}/apply.done'], capture_output=True, timeout=10)
    if result.returncode == 0: break
    time.sleep(1)
else:
    raise AssertionError('C72 pending: inspect existing capsule, never redispatch')
result = remote('result', f'cat {directory}/apply.result\ncat {directory}/apply.log\n')
assert result.splitlines()[0] == '0', ('Inspect root RO and rollback, never redispatch', stage)
remote('native-tree', after + f'sh {directory}/native.sh {directory} verify\n', timeout=90)
assert remote('after', after + infra) == binding['infrastructure']
remote('mounts-after', after + f'cmp /proc/1/mountinfo {directory}/mounts.before\n')
arguments = ' '.join('/opt/muos/frontend/lib/' + name for name in sorted(
    json.loads((repo / 'dist/phase4/muxretro-provider-session/analysis.json').read_text())['libraries']))
abi = after + f'''exec 8>/run/muos/session/lifetime.lock
flock -n 8
export LD_BIND_NOW=1 LD_LIBRARY_PATH=/opt/muos/frontend/lib
{directory}/provider-probe {arguments}
/opt/muos/frontend/muxretro --version
/opt/muos/frontend/muxretro --help
echo C72_INSTALLED_PROVIDER4_AND_HOST_EAGER_CLI_OK
'''
output = remote('native-ABI', abi)
assert output.count('C65 eager load: ') == 4 and 'muxretro interface 1' in output
assert output.endswith('C72_INSTALLED_PROVIDER4_AND_HOST_EAGER_CLI_OK\n')
assert remote('final-health', after + infra) == binding['infrastructure']
# Keep the rollback capsule until the proof has been archived on the host.
report = {'passed': True, 'experiment': 'C72_PROVIDER_AND_CONSUMER_INSTALLED',
    'boot_sequence': binding['boot_sequence'], 'replace_files': 5, 'add_files': 26,
    'obsolete_metadata_files_removed': 12, 'new_directories': 29, 'old_directories_removed': 13,
    'before_public_payloads_backed_up': 17, 'root_read_only': True,
    'native_installed_provider4_and_host_eager_CLI_passed': True,
    'private_state_fingerprint_unchanged': True, 'infrastructure_and_global_mounts_unchanged': True,
    'foundation_files': 97, 'preserved_prerequisites': 101,
    'reboot_requested': False, 'p3_mounted': False, 'GUI_replayed': False,
    'token_or_service_enabled': False, 'image_C70_flashed': False,
    'binding_sha256': sha(stage / 'binding.json'), 'plan_sha256': sha(stage / 'plan.json'),
    'C71_proof_sha256': sha(proof / 'SHA256SUMS'), 'source_sha256': binding['source_sha256'],
    'RAM_capsule_retained_for_finalization': True}
(stage / 'install-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print('C72 installed provider+host, eager CLI passed; root RO, no reboot/p3/GUI:', stage)
