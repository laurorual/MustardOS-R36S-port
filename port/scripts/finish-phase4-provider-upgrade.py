#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C72 final native read-only check and bounded cleanup after verified apply."""
from pathlib import Path
import argparse, json, re, subprocess
from phase4_candidate import sha, sums

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
a = p.parse_args()
stage = a.stage.resolve()
assert stage.is_relative_to(work / 'provider-upgrade-native')
r = json.loads((stage / 'install-analysis.json').read_text())
b = json.loads((stage / 'binding.json').read_text())
assert r['passed'] and r['binding_sha256'] == sha(stage / 'binding.json')
assert r['plan_sha256'] == b['plan_sha256'] == sha(stage / 'plan.json')
assert sha(stage / 'backup.json') == b['backup_sha256']
assert sha(stage / 'deployment.tar') == b['deployment_sha256']
for n, h in b['source_sha256'].items(): assert sha(repo / n) == h
proof = repo / 'dist/phase4/provider-upgrade'
assert sha(proof / 'SHA256SUMS') == b['C71_proof_sha256']
for n, h in sums(proof / 'SHA256SUMS').items(): assert sha(proof / n) == h
directory = (stage / 'remote-directory').read_text().strip()
assert re.fullmatch('/run/muos-c72[.][A-Za-z0-9]{6}', directory)
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'), '-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=6', 'root@' + b['host']]
def remote(label, code):
    (stage / (label + '.sh')).write_text(code)
    result = subprocess.run(ssh + ['sh -s'], input=code, capture_output=True, text=True, timeout=90)
    for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
        (stage / (label + '.' + suffix)).write_text(value)
    assert result.returncode == 0, (stage, label, result.stderr[-1200:])
    return result.stdout
health = (stage / 'final-health.sh').read_text()
assert remote('pre-cleanup-health', health) == b['infrastructure']
remote('pre-cleanup-tree', health + f'sh {directory}/native.sh {directory} verify\n')
for name in ['apply.log', 'apply.result', 'apply.done']:
    code = health + f'''[ -f {directory}/{name} ];[ ! -L {directory}/{name} ]
[ "$(stat -c '%u:%g:%h' {directory}/{name})" = 0:0:1 ]
[ "$(wc -c < {directory}/{name})" -le 131072 ]
cat {directory}/{name}
'''
    output = remote('collect-' + name, code)
    assert output.startswith(b['infrastructure'])
    (stage / ('collected-' + name)).write_text(output.removeprefix(b['infrastructure']))
assert (stage / 'collected-apply.result').read_text() == '0\n'
assert (stage / 'collected-apply.done').read_bytes() == b''
assert 'C72_PROVIDER_AND_HOST_INSTALLED_ROOT_RO' in (stage / 'collected-apply.log').read_text()
cleanup = health + f'''[ -d {directory} ];[ ! -L {directory} ]
[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
! findmnt -rn -M {directory} >/dev/null
cmp /proc/1/mountinfo {directory}/mounts.before
rm -rf {directory}
[ ! -e {directory} ];[ ! -L {directory} ]
echo C72_RAM_CAPSULE_REMOVED_ROOT_RO
'''
assert remote('cleanup', cleanup) == b['infrastructure'] + 'C72_RAM_CAPSULE_REMOVED_ROOT_RO\n'
screen = health + '''printf '\033[37;40m\033[2J\033[H%s\n' 'muOS - R35S / Panel 0
C72 diagnostic finished
Provider and muxretro installed.
No game or menu is running.
Root read-only. SSH ready.' > /dev/tty0
echo C72_STOPPED_SCREEN_WRITTEN
'''
assert remote('stopped-screen', screen) == b['infrastructure'] + 'C72_STOPPED_SCREEN_WRITTEN\n'
assert remote('post-cleanup-health', health) == b['infrastructure']
assert (work / 'graphics-config/output/.config').read_bytes() == (work / 'network-tools/baseline.config').read_bytes()
report = {'passed': True, 'experiment': 'C72_FINAL_READONLY_AUDIT',
    'install_analysis_sha256': sha(stage / 'install-analysis.json'),
    'binding_sha256': sha(stage / 'binding.json'), 'root_read_only': True,
    'installed_31_file_model_verified': True, 'public_before_backup_retained_on_host': True,
    'RAM_removed': True, 'diagnostic_screen_written': True,
    'infrastructure_and_global_mounts_preserved': True, 'SDK_config_unchanged': True,
    'p3_mounted': False, 'GUI_started': False, 'reboot_requested': False,
    'source_sha256': {str(Path(__file__).relative_to(repo)): sha(Path(__file__))}}
(stage / 'final-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print('C72 finalized: installed model valid, root RO, RAM removed, diagnostic page; backup retained')
