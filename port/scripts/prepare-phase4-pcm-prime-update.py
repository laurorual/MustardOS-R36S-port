#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C36: two public files, one bounded direct-zero cycle before PipeWire."""
from pathlib import Path
import argparse
import ipaddress
import json
import shutil
import subprocess
import tempfile
from phase4_candidate import sha, sums, validate

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', required=True, type=ipaddress.IPv4Address)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'; area = work / 'rootfs-candidate'
previous = Path((area / 'latest-update').read_text().strip())
old = json.loads((previous / 'plan.json').read_text())
assert old['experiment'] == 'C33_ALSA_RW' and json.loads((previous / 'install-analysis.json').read_text())['passed']
checks = Path((work / 'audio-clock-audit/latest-prime-checks').read_text().strip())
report = json.loads((checks / 'analysis.json').read_text()); assert report['passed']
for name, digest in report['source_sha256'].items(): assert sha(repo / name) == digest
rehearsal = work / 'audio-clock-audit/zero-trial.d9xf4on4'
assert (rehearsal / 'aplay-rehearsal.exit').read_text().strip() == '0'
assert 'DIRECT_ZERO_PCM_COMPLETED' in (rehearsal / 'aplay-rehearsal.stdout').read_text()
base = Path(old['candidate_stage']) / 'target'
candidate = Path(tempfile.mkdtemp(prefix='c36-source.', dir=area)); root = candidate / 'target'
shutil.copytree(base, root, symlinks=True)
hook = repo / 'port/device/rk-r35s-p0/S95muos-core'
shutil.copyfile(hook, root / 'etc/init.d/S95muos-core')
foundation = root / 'usr/libexec/muos-session/prerequisites.sha256'; records = sums(foundation)
assert len(records) == 97
foundation.write_text(''.join(sha(root / n.lstrip('/')) + '  ' + n + '\n' for n in records))
analysis = validate(root)
assert analysis['foundation_files'] == 97
names = ['etc/init.d/S95muos-core', 'usr/libexec/muos-session/prerequisites.sha256']
stage = Path(tempfile.mkdtemp(prefix='c36-update.', dir=area))
code = '''set -eu
c25_store=/var/lib/muos-diagnostic; c25_state=/run/muos/c25
. /usr/libexec/muos-c25/policy.sh; . /usr/libexec/muos-c25/card-guard.sh; . /usr/libexec/muos-c25/native.sh
c25_ready
[ ! -e "$c25_store/c25.once" ]; [ ! -L "$c25_store/c25.once" ]
printf 'BOOT %s\\n' "$(cat "$c25_store/boot-seq")"
'''
for name in names:
    code += f'''[ -f /{name} ]; [ ! -L /{name} ]; [ "$(stat -c '%u:%g:%h' /{name})" = 0:0:1 ]
printf 'F %s %s {name}\\n' "$(stat -c %a /{name})" "$(sha256sum /{name} | cut -d' ' -f1)"
'''
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'), '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes',
       '-oHostKeyAlias=[192.168.15.17]:2222', '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'),
       '-oBatchMode=yes', '-oConnectTimeout=6', 'root@' + str(args.host), 'sh -s']
result = subprocess.run(ssh, input=code, text=True, capture_output=True, timeout=35)
for ext, value in [('sh', code), ('stdout', result.stdout), ('stderr', result.stderr)]: (stage / ('survey.' + ext)).write_text(value)
assert result.returncode == 0, result.stderr
lines = result.stdout.splitlines(); boot = int(lines.pop(0).split()[1]); rows = []
for line in lines:
    kind, mode, digest, name = line.split(); assert kind == 'F' and digest == sha(base / name)
    rows.append({'path': name, 'before': {'type': kind, 'mode': int(mode, 8), 'sha256': digest},
                 'after': {'type': 'file', 'mode': (root / name).stat().st_mode & 0o777, 'sha256': sha(root / name)}})
sources = [Path(__file__), hook, repo / 'port/scripts/phase4_candidate.py', repo / 'port/device/rk-r35s-p0/core-wireplumber.conf']
pins = {str(p.relative_to(repo)): sha(p) for p in sources}
analysis.update({'revision': 'C36', 'new_ELF': False, 'image_built': False, 'sources': pins,
                 'prime_checks_sha256': sha(checks / 'analysis.json'), 'prime_rehearsal_sha256': sha(rehearsal / 'aplay-rehearsal.stdout')})
(candidate / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
plan = {'schema': 1, 'experiment': 'C36_PCM_PRIME', 'candidate_stage': str(candidate),
        'candidate_analysis_sha256': sha(candidate / 'analysis.json'), 'boot_sequence': boot,
        'files': rows, 'new_directories': [], 'already_current_skipped': [],
        'factory_counter_excluded': True, 'private_state_or_p3_in_payload': False,
        'reboot_requested': False, 'previous_update_stage': str(previous), 'source_sha256': pins}
(stage / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(stage / 'foundation-before-source.sha256').write_bytes((base / 'usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(area / 'latest-update').write_text(str(stage) + '\n')
print('C36 prime plan, no device write:', stage)
