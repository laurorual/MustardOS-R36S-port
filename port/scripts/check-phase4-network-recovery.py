#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C07 recovery guards and physical-replug state machine, isolated fake sysfs."""
from pathlib import Path
import json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path(tempfile.mkdtemp(prefix='recovery-hooks.',dir=work/'network-tools'))
script=r'''
set -eu
export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /tmp/bin /sys/bus/usb/devices /sys/class/block/mmcblk0p2 /run/muos/entropy /run/muos/c07 /var/lib/muos-network
printf 'MUOS-R35S-NETWORK-P4-C07\n' > /tmp/marker
printf '179:2\n' > /sys/class/block/mmcblk0p2/dev
cat > /tmp/bin/readlink <<'EOF'
#!/bin/sh
if [ "$*" = /proc/1/exe ]; then echo /bin/busybox; else /usr/bin/readlink "$@"; fi
EOF
printf '#!/bin/sh\necho 4.4.189-muos-r35s-p4\n' > /tmp/bin/uname
cat > /tmp/bin/findmnt <<'EOF'
#!/bin/sh
case "$*" in
 '-rn -o OPTIONS /') echo "${MOCK_ROOT:-ro}" ;;
 '-rn -o MAJ:MIN /') echo 179:2 ;;
 *) exit 1 ;;
esac
EOF
cat > /tmp/bin/sleep <<'EOF'
#!/bin/sh
n=$(cat /tmp/tick); n=$((n+1)); echo "$n" > /tmp/tick
case "${MOCK_SEQUENCE:-replug}:$n" in
 replug:1|unknown:1|noinsert:1) rm -rf /sys/bus/usb/devices/1-1 ;;
 replug:12|unknown:12)
  mkdir -p /sys/bus/usb/devices/1-1
  echo 0bda > /sys/bus/usb/devices/1-1/idVendor
  if [ "${MOCK_SEQUENCE:-replug}" = replug ]; then echo 1a2b; else echo 1234; fi > /sys/bus/usb/devices/1-1/idProduct ;;
esac
EOF
cat > /usr/libexec/muos-run-bounded <<'EOF'
#!/bin/sh
[ "$1" -le 120 ] || exit 125
shift
exec "$@"
EOF
printf '#!/bin/sh\n[ "${MOCK_RNG:-ready}" = ready ]\n' > /usr/libexec/muos-rng-ready
printf 'diag_card() { echo /dev/mmcblk0p1; }\n' > /usr/libexec/muos-diag-card-guard
cat > /usr/libexec/muos-c07-network <<'EOF'
#!/bin/sh
echo "network-$1" >> /tmp/calls
case "$1" in
 stop) rm -f /run/muos/c07/ready ;;
 recover) [ "$(cat /sys/bus/usb/devices/1-1/idProduct)" = c820 ]; touch /run/muos/c07/ready ;;
 *) exit 1 ;;
esac
EOF
cat > /usr/libexec/muos-c07-usb-mode <<'EOF'
#!/bin/sh
echo usb >> /tmp/calls
[ "$(cat /sys/bus/usb/devices/1-1/idProduct)" = 1a2b ] || exit 1
[ "${MOCK_USB:-pass}" = pass ] || exit 1
echo c820 > /sys/bus/usb/devices/1-1/idProduct
EOF
chmod 755 /tmp/bin/* /usr/libexec/*
# Rewrite only the marker path and display sink; all guards/state logic are real.
sed -e 's@/etc/muos-network-diagnostic@/tmp/marker@g' -e 's@> /dev/tty0@> /tmp/screen@g' /port/device/rk-r35s-p0/network-diagnostic/recover.sh > /tmp/recover.sh
sed 's@export PATH=.*@export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin@' /tmp/recover.sh > /tmp/recover-path.sh
sed 's@export PATH=.*@export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin@' /port/device/rk-r35s-p0/network-diagnostic/network.sh > /tmp/network.sh
new_case() {
 rm -rf /run/muos/c07/recovery /run/muos/c07/ready /sys/bus/usb/devices/*
 : > /tmp/calls; echo 0 > /tmp/tick
 touch /run/muos/entropy/stopped
 mkdir -p /sys/bus/usb/devices/1-1
 echo 0bda > /sys/bus/usb/devices/1-1/idVendor
 echo c820 > /sys/bus/usb/devices/1-1/idProduct
 echo fixture-not-a-real-key > /var/lib/muos-network/dropbear_ed25519_host_key
 chmod 600 /var/lib/muos-network/dropbear_ed25519_host_key
}
new_case
sh /tmp/recover-path.sh > /tmp/success
[ "$(cat /tmp/calls)" = "$(printf 'network-stop\nusb\nnetwork-recover')" ]
grep -q 'physical-removal-observed' /tmp/success
grep -q 'ssh-process-ready ROOT_RO=1' /tmp/success
if sh /tmp/recover-path.sh; then exit 1; fi # active ready/reentry
new_case
mkdir /run/muos/c07/recovery
if sh /tmp/recover-path.sh; then exit 1; fi
[ ! -s /tmp/calls ]
new_case
if MOCK_ROOT=rw sh /tmp/recover-path.sh; then exit 1; fi
[ ! -s /tmp/calls ]
new_case
if MOCK_RNG=unready sh /tmp/recover-path.sh; then exit 1; fi
[ ! -s /tmp/calls ]
new_case
rm /var/lib/muos-network/dropbear_ed25519_host_key
if sh /tmp/recover-path.sh; then exit 1; fi
[ ! -s /tmp/calls ]
new_case
if MOCK_SEQUENCE=retained sh /tmp/recover-path.sh > /tmp/no-remove; then exit 1; fi
grep -q removal-timeout /tmp/no-remove
[ "$(cat /tmp/calls)" = network-stop ]
new_case
if MOCK_SEQUENCE=unknown sh /tmp/recover-path.sh > /tmp/unknown; then exit 1; fi
grep -q insertion-timeout /tmp/unknown
[ "$(cat /tmp/calls)" = network-stop ]
new_case
if MOCK_USB=fail sh /tmp/recover-path.sh; then exit 1; fi
[ "$(cat /tmp/calls)" = "$(printf 'network-stop\nusb')" ]
new_case
rm /run/muos/entropy/stopped
if sh /tmp/network.sh recover; then exit 1; fi
new_case
rm /var/lib/muos-network/dropbear_ed25519_host_key
if sh /tmp/network.sh recover; then exit 1; fi
new_case
if MOCK_RNG=unready sh /tmp/network.sh recover; then exit 1; fi
# Public driver output has labels/counts only, even with private-looking input.
printf 'RTW: rtw_usb_primary_adapter_init Failed! secret-ssid\nRTW: rtw_usb_if1_init, failed MAC=aa:bb:cc:dd:ee:ff\n' > /tmp/raw
sed -n "/    dmesg | awk '/,/    exit 1/p" /tmp/network.sh | sed '1s/dmesg/cat \/tmp\/raw/;$d' > /tmp/filter.sh
sh /tmp/filter.sh > /tmp/filtered
grep -q 'primary=1.*ifinit=1' /tmp/filtered
! grep -Eq 'secret|aa:bb|RTW:' /tmp/filtered
printf 'PASS recovery state machine, guards, failure paths and sanitized driver counters\n'
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0',
 '--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/sys:rw,nosuid,nodev','--tmpfs','/usr/libexec:rw,nosuid,nodev','--tmpfs','/var/lib:rw,nosuid,nodev',
 '-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=45)
(stage/'stdout.txt').write_text(r.stdout);(stage/'stderr.txt').write_text(r.stderr)
cases=['physical removal then insertion required','active ready refused','reentry refused','RW root refused','unready RNG refused','missing key refused','no removal timeout','unknown insertion timeout','USB failure prevents network start','network recovery stopped-RNG marker guard','network recovery requires existing key','network recovery checks live RNG','public diagnostic filter excludes private-looking text']
(stage/'report.json').write_text(json.dumps({'passed':r.returncode==0,'exit':r.returncode,'cases':cases,'real_usb_or_network_tested':False},indent=2)+'\n')
assert r.returncode==0,(stage,r.stderr[-2000:])
(work/'network-tools/latest-recovery-hooks').write_text(str(stage)+'\n')
print('C07 physical recovery fixtures passed:',stage)
