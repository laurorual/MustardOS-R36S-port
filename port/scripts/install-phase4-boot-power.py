#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Apply the tested five-file C12 update; no token, persistent power flag, or reboot."""
from pathlib import Path
import argparse, hashlib, ipaddress, json, re, subprocess

repo = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path); p.add_argument('--host', required=True, type=ipaddress.IPv4Address)
a = p.parse_args(); stage = a.stage.resolve()
assert stage.is_relative_to(repo/'build/phase4/boot-order')
meta = json.loads((stage/'manifest.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert meta['host_passed'] and not meta['token_armed_by_update'] and not meta['default_power_enabled']
assert sha(stage/'deployment.tar') == meta['deployment_sha256']
for name, digest in meta['source_sha256'].items(): assert sha(repo/name) == digest, name
coordinator = Path(meta['coordinator_stage'])
assert sha(coordinator/'manifest.json') == meta['coordinator_manifest_sha256']
for name, digest in json.loads((coordinator/'manifest.json').read_text())['source_sha256'].items():
    assert sha(repo/name) == digest, name
ssh = ['ssh', '-p', '2222', '-i', str(repo/'build/phase4/private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes', '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'), '-oBatchMode=yes',
       '-oConnectTimeout=8', 'root@'+str(a.host)]
def remote(label, code, timeout=30):
    r = subprocess.run(ssh+['sh -s'], input=code, capture_output=True, text=True, timeout=timeout)
    for suffix, value in [('stdout', r.stdout), ('stderr', r.stderr), ('exit', str(r.returncode)+'\n')]:
        (stage/(label+'.'+suffix)).write_text(value)
    assert r.returncode == 0, (label, r.stdout, r.stderr)
    return r.stdout
guard = '''set -eu
boot_package=/usr/libexec/muos-boot
. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro
[ "$allow_power" = 0 ]
[ "$(cat /run/muos/selection/mode)" = c07 ]
[ ! -e /run/muos/boot ] && [ ! -e /run/muos/session ]
[ ! -e /var/lib/muos-diagnostic/c12.once ]
/usr/libexec/muos-c07-network status
'''
infra = '''for name in udevd wpa_supplicant udhcpc dropbear; do
for pid in $(pidof "$name"); do
[ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
printf '%s %s %s\n' "$name" "$pid" "$(awk '{print $22}' /proc/$pid/stat)"
done;done
'''
assert not (stage/'remote-directory').exists(), 'Do not overwrite an existing native update record'
remote('infrastructure-before', guard+infra)
directory = remote('allocate', guard+'mktemp -d /run/muos-c12power.XXXXXX\n').strip()
assert re.fullmatch(r'/run/muos-c12power\.[A-Za-z0-9]{6}', directory)
(stage/'remote-directory').write_text(directory+'\n')
(stage/'native-address').write_text(str(a.host)+'\n')
r = subprocess.run(ssh+['cat > '+directory+'/deployment.tar'], input=(stage/'deployment.tar').read_bytes(), capture_output=True, timeout=25)
(stage/'upload.stderr').write_bytes(r.stderr); assert r.returncode == 0, r.stderr
remote('unpack', f'set -eu\n[ "$(sha256sum {directory}/deployment.tar | cut -d" " -f1)" = {meta["deployment_sha256"]} ]\ntar -xf {directory}/deployment.tar -C {directory}\n')
remote('install', f'exec sh {directory}/power-update.sh {directory}\n', timeout=90)
remote('verify', guard+f'cd /;sha256sum -c {directory}/payload/installed-after.sha256\nsha256sum -c /usr/libexec/muos-session/prerequisites.sha256\n')
assert remote('infrastructure-after', guard+infra) == (stage/'infrastructure-before.stdout').read_text()
# Exercise the real refusal with power enabled only in a RAM config. C07 must
# be rejected before creating coordinator state, stopping network or touching RNG.
remote('C07-power-refusal', guard+f'''
cp /etc/default/muos-boot {directory}/power.conf
sed -i 's/^allow_power=0$/allow_power=1/' {directory}/power.conf
chmod 600 {directory}/power.conf
set +e
MUOS_BOOT_CONFIG={directory}/power.conf /usr/libexec/muos-boot/service.sh reboot
rc=$?
set -e
[ "$rc" = 64 ]
[ ! -e /run/muos/boot ]
/usr/libexec/muos-c07-network status
echo C07_POWER_REFUSED_RC64_NO_STATE
''')
assert remote('infrastructure-after-refusal', guard+infra) == (stage/'infrastructure-before.stdout').read_text()
report = {'passed': True, 'root_readonly_FAT_unmounted_taint0': True,
          'all_installed_hashes_and_55_prerequisites_match': True,
          'C07_power_refusal_64_no_state_same_network_identities': True,
          'token_armed': False, 'reboot_requested': False, 'native_power_tested': False}
(stage/'install-analysis.json').write_text(json.dumps(report, indent=2)+'\n')
print('C12 public power update verified; C07 refused power; no token/reboot, persistent allow_power=0.')
