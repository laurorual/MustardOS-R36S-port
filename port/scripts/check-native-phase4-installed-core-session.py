#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C77 native fixed dispatcher check in RAM, without core initialization or GUI."""
from pathlib import Path
import argparse, ipaddress, json, re, subprocess, tempfile
from phase4_installed_core_session import *

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
p.add_argument('--observation', required=True, type=Path)
args = p.parse_args()
observation_path = args.observation.resolve()
assert observation_path.is_relative_to(AREA)
obs = json.loads((observation_path / 'observation.json').read_text())
assert obs['host'] == str(args.host)
for n, h in obs['source_sha256'].items(): assert sha(REPO / n) == h, n
ctx, prior_stage, prior, provider_stage, provider, _ = historical()
bind(prior, provider, obs, obs['boot_sequence'], obs['kernel_boot_id'])
checks = Path((AREA / 'latest-checks').read_text().strip())
check = json.loads((checks / 'analysis.json').read_text())
assert check['passed']
for n, h in check['source_sha256'].items(): assert sha(REPO / n) == h, n
common = current_common(ctx['common'], prior['boot_sequence'], obs['boot_sequence'])
common += '[ "$(cat /proc/sys/kernel/random/boot_id)" = ' + obs['kernel_boot_id'] + ' ]\n'
stage = Path(tempfile.mkdtemp(prefix='native-guard.', dir=AREA))
ssh = ['ssh','-p','2222','-i',str(WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile='+str(WORK/'private/c07-known_hosts'),'-oBatchMode=yes',
       '-oConnectTimeout=6','root@'+str(args.host)]
def remote(label, code):
    (stage / (label + '.sh')).write_text(code)
    r = subprocess.run(ssh+['sh -s'], input=code, capture_output=True, text=True, timeout=40)
    for ext, v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
        (stage / (label + '.' + ext)).write_text(v)
    assert r.returncode == 0, (label, stage)
    return r.stdout

assert remote('preflight', common+ctx['infra']) == obs['infrastructure']
directory = remote('allocate', common+'mktemp -d /run/muos-prefs-data.XXXXXX\n').strip()
assert re.fullmatch('/run/muos-prefs-data[.][a-zA-Z0-9]{6}', directory)
files = {n: NATIVE / n for n in ['installed-host.sh','frontend-libs.sh']}
for n in NAMES:
    f = provider_stage / 'target/opt/muos/frontend/lib' / n
    files['provider-lib/' + n] = f
    if n != 'libmuxmod.so': files['lib/' + n] = f
try:
    remote('subdirs', common+f'mkdir -m 700 {directory}/lib {directory}/provider-lib\n')
    for n, f in files.items():
        r = subprocess.run(ssh+['cat > '+directory+'/'+n],input=f.read_bytes(),capture_output=True,timeout=30)
        assert r.returncode == 0, (n, stage)
    code = common
    for n, f in files.items():
        code += f"chmod 700 {directory}/{n}\nprintf '%s  %s\\n' {sha(f)} {directory}/{n} | sha256sum -c - >/dev/null\n"
    code += f"printf 'load\\n' > {directory}/role\nchmod 600 {directory}/role\n"
    code += f'/bin/sh {directory}/installed-host.sh {directory} check\n'
    output = remote('dispatcher-check', code)
    assert output == 'C77_PROVIDER_VALID files=7 operation=check\nC77_INSTALLED_HOST_CORE_VALID files=40 operation=check\n'
finally:
    cleanup = common+f'''for info in /proc/[0-9]*/mountinfo;do
 [ -r "$info" ] || continue
 if awk -v prefix={directory}/ '$5 ~ "^"prefix {{f=1}} END{{exit !f}}' "$info" 2>/dev/null;then exit 64;fi
done
[ ! -L {directory} ];[ "$(stat -c '%u:%g:%a' {directory})" = 0:0:700 ]
rm -rf {directory}
'''
    remote('cleanup', cleanup)
assert remote('final-health', common+ctx['infra']) == obs['infrastructure']
report = {'passed':True, 'experiment':'C77_NATIVE_DISPATCHER_CHECK', 'boot_sequence':obs['boot_sequence'],
          'observation_sha256':sha(observation_path/'observation.json'), 'checks_analysis_sha256':sha(checks/'analysis.json'),
          'installed_leaves_verified':40, 'preserved_prerequisites_verified':132, 'RAM_removed':True,
          'infrastructure_preserved':True, 'root_read_only':True, 'ROM_transferred':False,
          'host_or_core_ELF_transferred':False, 'core_initialized':False, 'GUI_or_audio_started':False,
          'source_sha256':{str(Path(__file__).resolve().relative_to(REPO)):sha(Path(__file__))}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(AREA/'latest-native-guard').write_text(str(stage)+'\n')
print('C77 native dispatcher40 passed without ROM/GUI/core initialization; RAM removed:', stage)
