#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Guarded first C12 install on the live test card; never requests reboot."""
from pathlib import Path
import argparse,hashlib,ipaddress,json,re,subprocess
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
stage=a.stage.resolve();assert stage.is_relative_to(repo/'build/phase4/boot-order')
meta=json.loads((stage/'manifest.json').read_text());assert meta['host_passed'] and meta['C07_fallback_next_boot'] and not meta['allow_power']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'deployment.tar')==meta['deployment_sha256']
for name,digest in meta['source_sha256'].items():assert sha(repo/name)==digest,name
coordinator=Path(meta['coordinator_stage']);assert sha(coordinator/'manifest.json')==meta['coordinator_manifest_sha256']
for name,digest in json.loads((coordinator/'manifest.json').read_text())['source_sha256'].items():assert sha(repo/name)==digest,name
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host)]
def remote(label,code,timeout=30):
 r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+suffix)).write_text(value)
 assert r.returncode==0,(label,r.stdout,r.stderr);return r.stdout
guard='''set -eu
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ]
[ "$(readlink /proc/1/exe)" = /bin/busybox ]
[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
. /usr/libexec/muos-diag-card-guard
boot=$(diag_card /sys);root=${boot%p1}p2
[ "$(findmnt -rn -o MAJ:MIN /)" = "$(cat /sys/class/block/${root##*/}/dev)" ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
! findmnt -rn -M /boot >/dev/null
/usr/libexec/muos-c07-network status
'''
infra='''for name in udevd wpa_supplicant udhcpc dropbear; do
 main=
 for pid in $(pidof "$name"); do
  [ "$(awk '/^PPid:/ {print $2}' /proc/$pid/status)" = 1 ] || continue
  [ -z "$main" ];main=$pid
 done
 [ -n "$main" ];printf '%s %s %s\\n' "$name" "$main" "$(awk '{print $22}' /proc/$main/stat)"
done
'''
assert not (stage/'remote-directory').exists(),'Resume the existing installation; do not overwrite its evidence'
remote('preflight',guard+f'[ "$(sha256sum /etc/inittab | cut -d" " -f1)" = {meta["inittab_before_sha256"]} ]\n[ ! -e /run/muos/session ]; [ ! -e /run/muos/boot ]\n')
remote('infrastructure-before',guard+infra)
directory=remote('allocate',guard+'mktemp -d /run/muos-c12boot.XXXXXX\n').strip();assert re.fullmatch(r'/run/muos-c12boot\.[A-Za-z0-9]{6}',directory)
(stage/'remote-directory').write_text(directory+'\n')
r=subprocess.run(ssh+['cat > '+directory+'/deployment.tar'],input=(stage/'deployment.tar').read_bytes(),capture_output=True,timeout=25);(stage/'upload.stderr').write_bytes(r.stderr);assert r.returncode==0,r.stderr
remote('unpack',f'set -eu\n[ "$(sha256sum {directory}/deployment.tar | cut -d" " -f1)" = {meta["deployment_sha256"]} ]\ntar -xf {directory}/deployment.tar -C {directory}\n')
remote('install',f'exec sh {directory}/install.sh {directory}\n',timeout=90)
remote('verify',guard+f'cd /; sha256sum -c {directory}/payload/SHA256SUMS\n[ "$(sha256sum /etc/inittab | cut -d" " -f1)" = {meta["inittab_selected_sha256"]} ]\n[ "$(stat -c "%u:%g:%a:%h:%s" /var/lib/muos-diagnostic/c12.once)" = 0:0:600:1:14 ]\n[ "$(cat /var/lib/muos-diagnostic/c12.once)" = MUOS-C12-ONCE ]\n')
assert remote('infrastructure-after',guard+infra)==(stage/'infrastructure-before.stdout').read_text()
record={'passed':True,'source_and_install_verified':True,'same_C07_infrastructure_PID_starttime':True,'root_readonly_fat_unmounted_taint0':True,'one_shot_armed':True,'reboot_requested':False,'private_seed_credentials_keys_collected':False,'installed_native_directory':directory,'installer_script_sha256':sha(Path(__file__))}
(stage/'install-analysis.json').write_text(json.dumps(record,indent=2)+'\n')
print('C12 targeted install verified, one-shot armed, original C07 network unchanged; NO reboot requested.')
