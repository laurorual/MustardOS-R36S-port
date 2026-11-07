#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C24r1: restore mode600 after the first direct C07 boot; no counter rewrite."""
from pathlib import Path
import argparse,ipaddress,json,subprocess
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
s=Path((area/'latest-update').read_text().strip());plan=json.loads((s/'plan.json').read_text());expected=plan['boot_sequence']+1
assert json.loads((s/'install-analysis.json').read_text())['passed']
assert not (s/'counter-mode-repair.json').exists()
code=f'''set -eu
[ "$(id -u)" = 0 ];[ "$(readlink /proc/1/exe)" = /bin/busybox ]
[ "$(uname -r)" = 4.4.189-muos-r35s-p4 ];[ "$(cat /proc/sys/kernel/tainted)" = 0 ]
[ "$(stat -c '%u:%g:%a' /)" = 0:0:755 ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
. /usr/libexec/muos-diag-card-guard
[ "$(diag_card /sys)" = /dev/mmcblk0p1 ]
[ "$(findmnt -rn -o MAJ:MIN,FSTYPE,PARTUUID /)" = "$(cat /sys/class/block/mmcblk0p2/dev) ext4 4d554432-02" ]
! findmnt -rn -M /boot >/dev/null;! findmnt -rn -S /dev/mmcblk0p3 >/dev/null
for name in muxfrontend muhotkey muinput pipewire wireplumber dbus-daemon mulog;do ! pidof "$name" >/dev/null;done
[ -f /run/muos/entropy/stopped ];[ ! -e /run/muos/entropy/ready ]
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
/usr/libexec/muos-c07-network status
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
counter=/var/lib/muos-diagnostic/boot-seq
[ ! -L "$counter" ];[ "$(stat -c '%u:%g:%a:%h' "$counter")" = 0:0:644:1 ]
[ "$(cat "$counter")" = {expected} ]
before=$(sha256sum "$counter" | cut -d' ' -f1)
changed=0
finish() {{
 rc=$?;trap - EXIT HUP INT TERM
 if [ "$rc" != 0 ] && [ "$changed" = 1 ];then
  mount -o remount,rw / && chmod 644 "$counter" && sync || rc=1
 fi
 mount -o remount,ro / || rc=1
 findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro || rc=1
 exit "$rc"
}}
trap finish EXIT
trap 'exit 143' HUP INT TERM
mount -o remount,rw /
changed=1
chmod 600 "$counter"
[ "$(sha256sum "$counter" | cut -d' ' -f1)" = "$before" ]
[ "$(cat "$counter")" = {expected} ]
sync;mount -o remount,ro /
. /usr/libexec/muos-candidate-boot-checks
candidate_boot_check
printf 'C24_COUNTER_MODE_REPAIRED_644_TO_600_BYTES_UNCHANGED_BOOT=%s\\n' {expected}
'''
(s/'counter-mode-repair.sh').write_text(code)
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','root@'+str(a.host),'sh -s']
r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=30)
(s/'counter-mode-repair.stdout').write_text(r.stdout);(s/'counter-mode-repair.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
(s/'counter-mode-repair.json').write_text(json.dumps({'passed':True,'boot_sequence':expected,'before_mode':'644','after_mode':'600','counter_bytes_unchanged':True,'root_ro':True,'seed_reloaded':False},indent=2)+'\n');print(r.stdout)
