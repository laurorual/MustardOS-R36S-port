#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C24 guarded normal reboot/return, independent of legacy C12 selection state."""
from pathlib import Path
import argparse,ipaddress,json,subprocess,time
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['request','return']);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
s=Path((area/'latest-update').read_text().strip());plan=json.loads((s/'plan.json').read_text());assert json.loads((s/'install-analysis.json').read_text())['passed']
b=json.loads((s/'backup-descriptor.json').read_text());assert sha(Path(b['path']))==b['sha256']
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=5','root@'+str(a.host)]
code='''set -eu
[ "$(id -u)" = 0 ];[ "$(readlink /proc/1/exe)" = /bin/busybox ]
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ];[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
. /usr/libexec/muos-diag-card-guard
[ "$(diag_card /sys)" = /dev/mmcblk0p1 ]
[ "$(findmnt -rn -o MAJ:MIN,FSTYPE,PARTUUID /)" = "$(cat /sys/class/block/mmcblk0p2/dev) ext4 4d554432-02" ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
[ -f /run/muos/entropy/stopped ];[ ! -e /run/muos/entropy/ready ]
! findmnt -rn -M /boot >/dev/null;! findmnt -rn -S /dev/mmcblk0p3 >/dev/null
for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do ! pidof "$name" >/dev/null;done
. /usr/libexec/muos-candidate-boot-checks
candidate_boot_check
(cd /usr/libexec/muos-session && sha256sum -c payload.sha256) >/dev/null
(cd /usr/share/muos-r35s-profile && sha256sum -c /usr/libexec/muos-session/profile-source.sha256) >/dev/null
/usr/libexec/muos-c07-network status
'''
expected=plan['boot_sequence']+(a.operation=='return')
code+=f'[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {expected} ]\n'
def remote(label,body):
 (s/(label+'.sh')).write_text(body)
 r=subprocess.run(ssh+['sh -s'],input=body,capture_output=True,text=True,timeout=20)
 for suffix,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (s/(label+'.'+suffix)).write_text(value)
 return r
if a.operation=='request':
 assert not (s/'reboot-request.json').exists(),'Never repeat a dispatched reboot'
 r=remote('reboot-preflight',code+'sync\necho C24_REBOOT_PREFLIGHT_OK\n');assert r.returncode==0,(r.stdout,r.stderr)
 r=remote('reboot-request',code+'echo C24_NORMAL_PID1_REBOOT\n/sbin/reboot\n');assert r.returncode in (0,255),(r.stdout,r.stderr)
 (s/'reboot-request.json').write_text(json.dumps({'requested':True,'before':expected,'expected_after':expected+1,'normal_PID1':True,'C12_rearmed':False},indent=2)+'\n');print('C24 normal reboot requested; expected boot',expected+1)
else:
 assert json.loads((s/'reboot-request.json').read_text())['expected_after']==expected
 for attempt in range(1,13):
  r=remote('reboot-return',code+'''[ ! -e /run/muos/selection/mode ]
printf 'BOOT=';cat /var/lib/muos-diagnostic/boot-seq
printf 'BRIGHTNESS=';cat /sys/class/backlight/backlight/brightness
dmesg | awk '/Kernel panic|BUG:|Oops:|EXT4-fs error|I\\/O error|mmc.*timeout/ {n++} END{printf "KERNEL_STORAGE_SIGNATURES=%d\\n",n}'
echo C24_DIRECT_C07_BOOT_ROOT_RO_89_HASHES_NO_C12_MARKER
''')
  if r.returncode==0:break
  time.sleep(3)
 else:raise AssertionError(('Boot not verified; do not repeat reboot; inspect screen/IP',r.stdout,r.stderr))
 (s/'reboot-return.json').write_text(json.dumps({'passed':True,'boot_sequence':expected,'direct_C07_no_C12_marker':True,'root_ro_0755':True,'foundation89_and_payload15_and_profile_valid':True,'same_pinned_SSH_host_key':True,'WiFi_and_ssh_ready':True,'no_seed_reloaded_in_live_kernel':True,'attempts':attempt},indent=2)+'\n');print(r.stdout)
