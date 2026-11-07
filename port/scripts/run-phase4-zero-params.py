#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C35: bounded, RAM-only direct ALSA reproduction with digital zeros."""
from pathlib import Path
import argparse
import ipaddress
import json
import re
import subprocess
import tempfile
from phase4_candidate import sha
from phase4_pcm_rate import measure

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', required=True, type=ipaddress.IPv4Address)
parser.add_argument('--boot', required=True, type=int)
parser.add_argument('--binary-stage', required=True, type=Path)
args = parser.parse_args()
assert 1 <= args.boot <= 9999
repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
area = work / 'audio-clock-audit'
build = args.binary_stage.resolve()
assert build.is_relative_to(area) and (build / 'build.exit').read_text().strip() == '0'
binary = build / 'alsa-zero-params'
assert binary.is_file() and not binary.is_symlink()
stage = Path(tempfile.mkdtemp(prefix='zero-trial.', dir=area))
(area / 'latest-zero-trial').write_text(str(stage) + '\n')
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes',
       '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'),
       '-oBatchMode=yes', '-oConnectTimeout=6', 'root@' + str(args.host)]


def remote(label, code, timeout=35, required=True):
    (stage / (label + '.sh')).write_text(code)
    result = subprocess.run(ssh + ['sh -s'], input=code, text=True, capture_output=True, timeout=timeout)
    for ext, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (stage / (label + '.' + ext)).write_text(value)
    if required:
        assert result.returncode == 0, (stage, label, result.stdout, result.stderr)
    return result.stdout


common = f'''set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh
. /usr/libexec/muos-c25/card-guard.sh
. /usr/libexec/muos-c25/native.sh
c25_ready
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {args.boot} ]
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
'''
directory = remote('allocate', common + 'mktemp -d /run/muos-zero.XXXXXX\n').strip()
assert re.fullmatch(r'/run/muos-zero\.[A-Za-z0-9]{6}', directory)
wrapper = repo / 'port/device/rk-r35s-p0/audio-buffers/zero-params-trial.sh'
sources = [Path(__file__), wrapper, repo / 'port/tools/alsa-zero-params.c', repo / 'port/scripts/phase4_pcm_rate.py']
(stage / 'intent.json').write_text(json.dumps({'experiment': 'C35_ZERO_PARAMS', 'boot_sequence': args.boot,
    'directory': directory, 'binary_sha256': sha(binary), 'binary_build_stage': str(build),
    'zero_PCM_only': True, 'microphone_opened': False, 'rootfs_written': False,
    'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}, indent=2) + '\n')
result = subprocess.run(ssh + ['cat > ' + directory + '/alsa-zero-params'], input=binary.read_bytes(), capture_output=True, timeout=20)
assert result.returncode == 0, result.stderr
remote('prepare', common + f'''printf '%s  %s\\n' {sha(binary)} {directory}/alsa-zero-params | sha256sum -c -
chmod 700 {directory}/alsa-zero-params
cat > {directory}/probe.sh <<'C35_ZERO_PROBE'
''' + wrapper.read_text() + f'''C35_ZERO_PROBE
printf '%s  %s\\n' {sha(wrapper)} {directory}/probe.sh | sha256sum -c -
/bin/sh -n {directory}/probe.sh
''')
text = remote('probe', common + f'''mkdir -p /run/muos/session
[ ! -L /run/muos/session ]; [ "$(stat -c '%u:%g:%a' /run/muos/session)" = 0:0:700 ]
exec 8>/run/muos/session/lifetime.lock; flock -n 8
c25_ready
/usr/libexec/muos-session/mount-namespace /bin/sh {directory}/probe.sh {directory}
c25_ready
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
cmp {directory}/mixer-before.txt {directory}/mixer-after.txt
echo ZERO_PARAMS_CLEAN_ROOT_RO_MIXER_RESTORED_NETWORK_OK
''', timeout=50, required=False)
probe_ok = (stage / 'probe.exit').read_text().strip() == '0'
report = measure(text.split('END_PCM\n', 1)[0]) if probe_ok else {'PCM_measurement_valid': False}
remote('cleanup', common + f'''cmp {directory}/mixer-before.txt {directory}/mixer-after.txt
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
cat {directory}/player.log
cd {directory}
rm alsa-zero-params probe.sh mixer-before.txt mixer-after.txt mixer.state player.log
cd /
rmdir {directory}
c25_ready
echo ZERO_PARAMS_RAM_REMOVED
''')
report.update({'experiment': 'C35_ZERO_PARAMS', 'boot_sequence': args.boot, 'probe_passed': probe_ok,
               'cleanup_passed': True, 'physical_audio_qualified': False,
               'mixer_restored_byte_exact': True, 'rootfs_written': False})
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print(stage, json.dumps(report))
raise SystemExit(0 if probe_ok else 2)
