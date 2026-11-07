#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Request one normal C07 reboot only after frozen successful physical-edit proof."""
from pathlib import Path
import argparse, hashlib, ipaddress, json, subprocess, tempfile

repo = Path(__file__).resolve().parents[2]; area = repo / 'build/phase4/preferences'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
a = p.parse_args()
physical = Path((area / 'latest-session-physical-edit').read_text().strip())
assert physical.is_relative_to(area)
proof = repo / 'dist/phase4/preferences-session-physical-edit'
for line in (proof / 'SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ', 1)
    path = (proof / name).resolve(); assert path.is_relative_to(proof)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
report = json.loads((physical / 'analysis.json').read_text())
assert report == json.loads((proof / 'analysis.json').read_text())
assert report['passed'] and report['physical_edit_observed'] and len(report['cycles']) == 2
assert report['operation'] == 'physical-edit'
assert json.loads((proof / 'inode-commit.json').read_text())['record_inode_changed']
previous = report['boot_sequence']
stage = Path(tempfile.mkdtemp(prefix='session-reboot.', dir=area))
(area / 'latest-session-reboot-request').write_text(str(stage) + '\n')
ssh = ['ssh', '-p', '2222', '-i', str(repo / 'build/phase4/private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes',
       '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(repo / 'build/phase4/private/c07-known_hosts'),
       '-oBatchMode=yes', '-oConnectTimeout=8', 'root@' + str(a.host)]
guard = f'''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
c12_session_quiescent || exit 1
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {previous} ]
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
[ -f /run/muos/entropy/stopped ];[ ! -e /run/muos/entropy/ready ]
! findmnt -rn -S /dev/mmcblk0p3 >/dev/null
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
/usr/libexec/muos-c07-network status
'''
def run(label, code):
    (stage / (label + '.sh')).write_text(code)
    result = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=30)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    return result
preflight = run('preflight', guard + 'sync\necho C21_EDIT_REBOOT_PREFLIGHT_OK\n')
assert preflight.returncode == 0, (preflight.stdout, preflight.stderr)
# Separate guarded request through normal BusyBox PID1 shutdown; never -f,
# sysrq, seed reload, root reflash, C12 token, or Bluetooth/USB changes.
request = run('request', guard + 'echo C21_REQUEST_NORMAL_C07_REBOOT\n/sbin/reboot\n')
assert request.returncode in (0, 255), (request.stdout, request.stderr)
(stage / 'request.json').write_text(json.dumps({'requested': True, 'return_verified': False,
    'previous_boot_sequence': previous, 'pair': report['pair'],
    'physical_proof_sha256': hashlib.sha256((proof / 'analysis.json').read_bytes()).hexdigest(),
    'C12_rearmed': False}, indent=2) + '\n')
print('Normal C07 reboot requested; verify later boot/pinned SSH before UI reload:', stage)
