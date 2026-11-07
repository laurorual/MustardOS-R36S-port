#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded direct-ALSA zero playback to separate PCM timing from PipeWire."""
from pathlib import Path
import argparse, io, ipaddress, json, re, subprocess, tarfile, tempfile
from phase4_candidate import sha

repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', type=ipaddress.IPv4Address, required=True)
parser.add_argument('--profile-route', action='store_true', help='Compare one MMAP S32 run with native SPK_HP/215; zero PCM only')
args = parser.parse_args()
area = work / 'audio-clock-audit'; area.mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix='silent.', dir=area))
(area / 'latest').write_text(str(stage) + '\n')
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes',
       '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'),
       '-oBatchMode=yes', '-oConnectTimeout=8', 'root@' + str(args.host)]
def remote(label, code, timeout=30):
    (stage / (label + '.sh')).write_text(code)
    result = subprocess.run(ssh + ['sh -s'], input=code, text=True, capture_output=True, timeout=timeout)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode)+'\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert result.returncode == 0, (label, stage, result.stdout, result.stderr)
    return result.stdout
common = '''set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
(cd /usr/libexec/muos-session && sha256sum -c payload.sha256 >/dev/null)
'''
boot = int(remote('preflight', common + 'cat /var/lib/muos-diagnostic/boot-seq\n').strip())
directory = remote('allocate', common + 'mktemp -d /run/muos-clock.XXXXXX\n').strip()
assert re.fullmatch('/run/muos-clock[.][A-Za-z0-9]{6}', directory)
source = repo / 'port/device/rk-r35s-p0/audio-buffers/silent-clock-probe.sh'
(stage / 'native-probe.sh').write_bytes(source.read_bytes())
remote('prepare', common + f"cat > {directory}/probe.sh <<'SILENT_CLOCK_PROBE'\n" + source.read_text() + 'SILENT_CLOCK_PROBE\n' +
       f"printf '%s  %s\\n' {sha(source)} {directory}/probe.sh | sha256sum -c -\n/bin/sh -n {directory}/probe.sh\n")
(stage / 'intent.json').write_text(json.dumps({'boot_sequence': boot, 'directory': directory,
    'source_sha256': sha(source), 'input': '/dev/zero', 'microphone_opened': False,
    'profile_changed': False, 'temporary_route': 'SPK_HP/215' if args.profile_route else 'original',
    'new_UI_or_reboot': False}, indent=2)+'\n')
remote('probe', common + f'''[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {boot} ]
mkdir -p /run/muos/session
[ ! -L /run/muos/session ]; [ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ]
exec 8>/run/muos/session/lifetime.lock; flock -n 8
c25_ready
/usr/libexec/muos-session/mount-namespace /bin/sh {directory}/probe.sh {directory} {'profile215' if args.profile_route else 'original'}
c25_ready
if findmnt -rn -M /sys/kernel/debug >/dev/null; then exit 64; fi
echo SILENT_PROBE_CLEAN_ROOT_RO_NETWORK_OK
''', timeout=45)
names = ['probe.sh', 'mixer.state', 'mixer-before.txt', 'mixer-after.txt']
variants = ['MMAP_S32_LE', 'MMAP_S16_LE', 'RW_SMALL_S32_LE']
if args.profile_route:
    variants = ['MMAP_S32_LE']
    names += ['route-set.log', 'gain-set.log', 'mixer-active.txt']
for fmt in variants:
    names += [fmt + '-' + n for n in ['player.log', 'params.txt', 'first.txt', 'second.txt', 'clocks.txt']]
code = common + f'cd {directory}\ntar -cf - ' + ' '.join(names) + '\n'
(stage / 'collect.sh').write_text(code)
result = subprocess.run(ssh + ['sh -s'], input=code.encode(), capture_output=True, timeout=20)
assert result.returncode == 0, result.stderr
out = stage / 'collected'; out.mkdir()
with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
    seen = set()
    for member in archive.getmembers():
        assert member.isfile() and member.name in names and member.name not in seen and member.size < 65536
        (out / member.name).write_bytes(archive.extractfile(member).read()); seen.add(member.name)
    assert seen == set(names)
assert (out / 'mixer-before.txt').read_bytes() == (out / 'mixer-after.txt').read_bytes()
remote('cleanup', common + f'cd {directory}\nrm ' + ' '.join(names) + f'\ncd /\nrmdir {directory}\nc25_ready\n')
measurements = {}
for fmt in variants:
    points = []
    for point in ['first', 'second']:
        text = (out / (fmt + '-' + point + '.txt')).read_text()
        assert 'state: RUNNING' in text
        points.append((float(re.search(r'^UPTIME\n([0-9.]+)', text)[1]), int(re.search(r'hw_ptr\s+: (\d+)', text)[1])))
    assert points[1][0] > points[0][0] and points[1][1] > points[0][1]
    measurements[fmt] = (points[1][1] - points[0][1]) / (points[1][0] - points[0][0])
(stage / 'analysis.json').write_text(json.dumps({'passed': True, 'boot_sequence': boot,
    'direct_ALSA_frames_per_second': measurements, 'declared_rate': 44100,
    'requested_period_frames': 512, 'requested_buffer_frames': 2048,
    'temporary_route': 'SPK_HP/215' if args.profile_route else 'original',
    'time_source': 'proc uptime; 10ms resolution, not ALSA tstamp which is disabled by aplay',
    'digital_zero_only': True, 'mixer_restored_byte_exact': True,
    'RAM_and_private_debugfs_cleaned': True, 'root_ro': True,
    'does_not_qualify_UI_audio': True}, indent=2)+'\n')
print('Silent PCM clock audit collected:', stage, measurements)
