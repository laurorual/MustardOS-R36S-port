#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in C21 RAM deployment; two bounded real-data sessions, no C12 rearm."""
from pathlib import Path
import argparse, hashlib, io, ipaddress, json, re, subprocess, tarfile, tempfile, time

repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
p.add_argument('--operation', choices=['stable', 'physical-edit', 'verify-after-reboot', 'package-isolation'], default='stable')
p.add_argument('--volume', type=int, default=60)
p.add_argument('--brightness', type=int, default=75)
p.add_argument('--after-boot', type=int)
a = p.parse_args()
if not (0 <= a.volume <= 100 and 40 <= a.brightness <= 160): p.error('pair outside qualified range')
if a.operation == 'physical-edit' and (a.volume < 5 or a.brightness < 45): p.error('cannot lower pair by5')
if a.operation == 'verify-after-reboot' and a.after_boot is None: p.error('--after-boot required')
initial_pair = (a.volume, a.brightness)
final_pair = (a.volume - 5, a.brightness - 5) if a.operation == 'physical-edit' else initial_pair
lease = 300 if a.operation == 'physical-edit' else 90
cycle_count = 1 if a.operation in ('verify-after-reboot', 'package-isolation') else 2
edit_observed = False
area = work / 'preferences'; stage = Path(tempfile.mkdtemp(prefix='session-native.', dir=area))
(area / 'latest-session-attempt').write_text(str(stage) + '\n')
prepared = Path((work / 'runtime-session/latest-service').read_text().strip())
meta = json.loads((prepared / 'manifest.json').read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert meta['host_passed']
for name, digest in meta['source_sha256'].items(): assert sha(repo / name) == digest, name
assert sha(prepared / 'deployment.tar') == meta['deployment_sha256']
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'), '-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=8', 'root@' + str(a.host)]
def remote(label, code, timeout=30, required=True):
    (stage / (label + '.sh')).write_text(code)
    r = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=timeout)
    for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    if required: assert r.returncode == 0, (label, r.stdout, r.stderr, stage)
    return r

guard = '''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
/usr/libexec/muos-c07-network status
'''
boot_sequence = int(remote('preflight', guard + 'cat /var/lib/muos-diagnostic/boot-seq\n').stdout.strip())
if a.operation == 'verify-after-reboot': assert boot_sequence > a.after_boot, 'not a later boot'
directory = remote('allocate', guard + 'umask 077\nmktemp -d /run/muos-c21.XXXXXX\n').stdout.strip()
assert re.fullmatch(r'/run/muos-c21\.[A-Za-z0-9]{6}', directory)
(stage / 'native-directory').write_text(directory + '\n')
r = subprocess.run(ssh + ['cat > ' + directory + '/deployment.tar'], input=(prepared / 'deployment.tar').read_bytes(), capture_output=True, timeout=30)
assert r.returncode == 0
remote('prepare', guard + f'''
printf '%s  %s\\n' {meta['deployment_sha256']} {directory}/deployment.tar | sha256sum -c -
mkdir -m 700 {directory}/package
cd {directory}/package
tar -xf ../deployment.tar
sha256sum -c SHA256SUMS >/dev/null
printf 'enabled=1\npreferences_enabled=1\nlease_seconds={lease}\nprofile_dir=/usr/libexec/muos-session/profile\nprerequisites=/usr/libexec/muos-session/prerequisites.sha256\n' > {directory}/session.conf
chmod 600 {directory}/session.conf
cat /proc/1/mountinfo > {directory}/global-before
''')
if a.operation == 'package-isolation':
    isolate = repo / 'port/diagnostics/session-package-isolate.sh'
    content = isolate.read_bytes()
    result = subprocess.run(ssh + ['cat > ' + directory + '/isolate-start.sh'], input=content, capture_output=True, timeout=20)
    assert result.returncode == 0
    remote('prepare-isolation', f'set -eu\nprintf \'%s  %s\\n\' {sha(isolate)} {directory}/isolate-start.sh | sha256sum -c -\nmkdir -m 700 {directory}/boot-hidden\n')
# Only stopped-generation public files are collected. No /root, general logs,
# seed, credentials, or persistent data tree is exported.
names = ['report.txt', 'result', 'prepare.log', 'start.log', 'stop.log', 'restore.log',
         'checkpoint.log', 'checkpoint-stop.log', 'preferences-loaded.txt', 'preferences-active.txt',
         'preferences-candidate.txt', 'preferences-saved.txt', 'profile-source.txt',
         'profile-effective.txt', 'original-restored.txt', 'writer-restored.txt',
         'volume-before.sha256', 'volume-after.sha256', 'wireplumber-before.sha256',
         'wireplumber-after.sha256', 'brightness-before.txt', 'brightness-active.txt',
         'brightness-after.txt', 'mixer-before.txt', 'mixer-active.txt', 'mixer-after.txt',
         'drm-before.txt', 'drm-after.txt', 'software-volume.txt', 'ui-identity.txt',
         'first-paint.txt', 'launcher.log', 'root-writers.txt', 'rng.txt']
cycles = []
for number in range(1, cycle_count + 1):
    active_volume, active_brightness = initial_pair if number == 1 else final_pair
    label = 'cycle' + str(number)
    start_command = f'export MUOS_SESSION_CONFIG={directory}/session.conf\nsh {directory}/package/service.sh start\n'
    if a.operation == 'package-isolation':
        start_command = f'{directory}/package/mount-namespace /bin/sh {directory}/isolate-start.sh {directory}\n'
    r = remote(label + '-start', guard + start_command, timeout=135, required=False)
    generation = remote(label + '-generation', 'cat /run/muos/session/current\n').stdout.strip()
    assert re.fullmatch(r'run-[0-9]{4}', generation)
    current = '/run/muos/session/' + generation
    if r.returncode == 0:
        if a.operation == 'package-isolation':
            remote('isolation-proved', f'''set -eu
read manager ignored < {current}/manager
[ -f {current}/ready ]
[ ! -e /proc/$manager/root/usr/libexec/muos-boot/card-guard.sh ]
[ -f /usr/libexec/muos-boot/card-guard.sh ]
(cd {directory}/package && sha256sum -c payload.sha256)
echo C22_WORKER_WITHOUT_BOOT_PACKAGE_GLOBAL_PRESERVED
''')
        remote(label + '-active', f'''set -eu
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
read manager ignored < {current}/manager
[ -f {current}/ready ]
[ "$(readlink /proc/$manager/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
awk '$5=="/" {{if ($6 !~ /^ro(,|$)/) exit 1; found=1}} END {{if (!found) exit 1}}' /proc/$manager/mountinfo
findmnt -rn -o OPTIONS / | tr ',' '\n' | grep -qx ro
[ "$(cat /proc/$manager/root/opt/muos/config/settings/general/volume)" = {active_volume} ]
[ "$(cat /proc/$manager/root/opt/muos/config/settings/general/brightness)" = {active_brightness} ]
[ "$(cat /proc/$manager/root/opt/muos/config/settings/advanced/volume)" = 0 ]
[ "$(cat /sys/class/backlight/backlight/brightness)" = {active_brightness} ]
wpctl get-volume @DEFAULT_AUDIO_SINK@
cat {current}/preferences-active.txt
cmp /proc/1/mountinfo {directory}/global-before
[ ! -e /var/lib/muos-diagnostic/c12.once ]
printf 'DATA_RECORD_INODE=';stat -c %i /proc/$manager/root{current}/data/MUOS/preferences/preferences
echo C21_ACTIVE_{active_volume}_{active_brightness}_PRIVATE_ROOT_RO
''')
        print(f'{label}: C21 active {active_volume}/{active_brightness}, both roots RO', flush=True)
        if a.operation == 'physical-edit' and number == 1:
            print(f'PHYSICAL_EDIT_READY target={final_pair[0]}/{final_pair[1]} stage={stage}', flush=True)
            sample = f'''set -eu
read manager ignored < {current}/manager
[ -f {current}/ready ]
printf '%s %s\\n' "$(cat /proc/$manager/root/opt/muos/config/settings/general/volume)" "$(cat /proc/$manager/root/opt/muos/config/settings/general/brightness)"
'''
            (stage / 'physical-sample.sh').write_text(sample)
            deadline = time.monotonic() + 180
            previous = None
            while time.monotonic() < deadline:
                observation = subprocess.run(ssh + ['sh -s'], input=sample, capture_output=True, text=True, timeout=15)
                if observation.returncode: break
                values = observation.stdout.strip()
                with (stage / 'physical-observations.jsonl').open('a') as stream:
                    stream.write(json.dumps({'pair': values, 'seconds_remaining': int(deadline-time.monotonic())}) + '\n')
                if values == f'{final_pair[0]} {final_pair[1]}' and previous == values:
                    edit_observed = True; break
                previous = values
                time.sleep(2)
            print('PHYSICAL_EDIT_OBSERVED=' + str(edit_observed), flush=True)
        remote(label + '-stop', f'set -eu\nsh {directory}/package/service.sh stop\n', timeout=110)
    # Collect even failed startup so that rollback can be diagnosed without retry.
    target = stage / label; target.mkdir()
    code = f'cd {current} || exit 1; set --; for name in ' + ' '.join(names) + '; do [ ! -f "$name" ] || set -- "$@" "$name"; done; tar -cf - "$@"'
    collected = subprocess.run(ssh + [code], capture_output=True, timeout=30)
    assert collected.returncode == 0
    with tarfile.open(fileobj=io.BytesIO(collected.stdout)) as archive:
        for member in archive.getmembers():
            assert member.isfile() and member.name in names and member.size < 524288
            (target / member.name).write_bytes(archive.extractfile(member).read())
    remote(label + '-health', guard + f'''
cmp /proc/1/mountinfo {directory}/global-before
[ "$(cat /sys/class/backlight/backlight/brightness)" = 80 ]
! findmnt -rn -S /dev/mmcblk0p3 >/dev/null
[ -f {current}/done ]
echo C21_STOPPED_NO_GLOBAL_MOUNT_ROOT_RO_ORIGINALS_INTACT
''')
    assert r.returncode == 0 and (target / 'result').read_text().strip() == '0', (label, stage)
    loaded = f'MUOS-PREFS-1\nVOLUME={active_volume}\nBRIGHTNESS={active_brightness}\n'
    saved = f'MUOS-PREFS-1\nVOLUME={final_pair[0]}\nBRIGHTNESS={final_pair[1]}\n'
    assert (target / 'preferences-loaded.txt').read_text() == loaded
    if a.operation != 'physical-edit' or edit_observed:
        assert (target / 'preferences-saved.txt').read_text() == saved
    for before, after in [('volume-before.sha256', 'volume-after.sha256'),
                          ('wireplumber-before.sha256', 'wireplumber-after.sha256'),
                          ('mixer-before.txt', 'mixer-after.txt'), ('drm-before.txt', 'drm-after.txt')]:
        assert (target / before).read_bytes() == (target / after).read_bytes()
    cycles.append(generation)
    if a.operation == 'physical-edit' and not edit_observed: break
# Keep bounded public generation evidence in /run until the operator reviews it;
# remove only this deployed package, whose hashes and inactivity are rechecked.
remote('cleanup', guard + f'''
cd {directory}/package
sha256sum -c SHA256SUMS >/dev/null
cmp /proc/1/mountinfo {directory}/global-before
cd /
rm -r {directory}/package
rm {directory}/deployment.tar {directory}/session.conf {directory}/global-before
if [ -f {directory}/isolate-start.sh ];then
 rm {directory}/isolate-start.sh
 rmdir {directory}/boot-hidden
fi
rmdir {directory}
echo C21_RAM_PACKAGE_REMOVED
''')
report = {'passed': a.operation != 'physical-edit' or edit_observed, 'operation': a.operation, 'boot_sequence': boot_sequence, 'initial_pair': list(initial_pair), 'physical_edit_observed': edit_observed, 'cycles': cycles, 'pair': {'volume': final_pair[0], 'brightness': final_pair[1]},
          'real_p3_loaded_and_checkpointed': True, 'root_ro_private_and_global': True,
          'original_files_and_hardware_restored': True, 'C12_rearmed': False,
          'boot_package_hidden_from_worker': a.operation == 'package-isolation',
          'permanent_runtime_enabled': False, 'reboot_tested': a.operation == 'verify-after-reboot', 'previous_boot_sequence': a.after_boot,
          'prepared_manifest_sha256': sha(prepared / 'manifest.json'),
          'runner_sha256': sha(Path(__file__))}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
if report['passed']:
    (area / 'latest-session-native').write_text(str(stage) + '\n')
    (area / ('latest-session-' + a.operation)).write_text(str(stage) + '\n')
assert report['passed'], ('Physical target not observed; session stopped/collected and RAM package removed', stage)
print('C21 native sessions passed:', a.operation, stage)
