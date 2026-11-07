#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise real C07 hooks with fake USB sysfs and command stubs, no hardware."""
from pathlib import Path
import json, re, subprocess, tempfile

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
stage=Path(tempfile.mkdtemp(prefix='hooks.',dir=work/'network-tools'))
marker=stage/'marker';marker.write_text('MUOS-R35S-NETWORK-P4-C07\n')
run_text=(repo/'port/device/rk-r35s-p0/network-diagnostic/run.sh').read_text()
deadlines=re.findall(r'^\s*step ([a-z-]+) ([0-9]+) ',run_text,re.M)
assert [n for n,_ in deadlines]==['entropy-start','udev','usb-mode','network','entropy-stop']
assert all(1<=int(n)<=120 for _,n in deadlines)
script=r'''
set -eu
export PATH=/tmp/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /tmp/bin /run/muos/c07 /sys/bus/usb/devices /usr/libexec
cat > /usr/libexec/muos-run-bounded <<'EOF'
#!/bin/sh
shift
exec "$@"
EOF
cat > /tmp/bin/usb_modeswitch <<'EOF'
#!/bin/sh
case "$*" in
 '-R -v 0bda -p c820 -b 1 -g 2')
  echo reset >> /tmp/calls
  [ "${MOCK_RESET_FAIL:-0}" = 0 ] || exit 1
  if [ "${MOCK_RESET_TO_DISK:-0}" = 1 ]; then
   echo 1a2b > /sys/bus/usb/devices/1-1/idProduct
   echo 08 > /sys/bus/usb/devices/1-1:1.0/bInterfaceClass
  fi
  [ "${MOCK_RESET_NO_CONFIRM:-0}" = 1 ] || echo ' Device was reset'
  ;;
 '-K -v 0bda -p 1a2b -b 1 -g 2')
  echo eject >> /tmp/calls
  echo c820 > /sys/bus/usb/devices/1-1/idProduct
  echo ff > /sys/bus/usb/devices/1-1:1.0/bInterfaceClass ;;
 *) exit 1 ;;
esac
EOF
printf '#!/bin/sh\n[ "$*" = "settle --timeout=10" ]\n' > /tmp/bin/udevadm
printf '#!/bin/sh\n[ "$*" = "8821cu" ]\n' > /tmp/bin/modprobe
cat > /tmp/bin/ifconfig <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> /tmp/ifconfig-calls
EOF
printf '#!/bin/sh\nexit 0\n' > /tmp/bin/sleep
chmod 755 /tmp/bin/* /usr/libexec/muos-run-bounded
usb=/port/device/rk-r35s-p0/network-diagnostic/usb-mode.sh
dhcp=/port/device/rk-r35s-p0/network-diagnostic/dhcp.sh
network=/port/device/rk-r35s-p0/network-diagnostic/network.sh
new_usb() {
 rm -rf /sys/bus/usb/devices/*
 : > /tmp/calls
 : > /sys/bus/usb/drivers_probe
 mkdir -p /sys/bus/usb/devices/1-1 /sys/bus/usb/devices/1-1:1.0
 echo 0bda > /sys/bus/usb/devices/1-1/idVendor
 echo "$1" > /sys/bus/usb/devices/1-1/idProduct
 echo "$2" > /sys/bus/usb/devices/1-1:1.0/bInterfaceClass
 echo ff > /sys/bus/usb/devices/1-1:1.0/bInterfaceSubClass
 echo ff > /sys/bus/usb/devices/1-1:1.0/bInterfaceProtocol
 echo 1 > /sys/bus/usb/devices/1-1/busnum
 echo 2 > /sys/bus/usb/devices/1-1/devnum
}
new_usb c820 ff
sh "$usb"
[ "$(cat /tmp/calls)" = reset ]
[ "$(cat /sys/bus/usb/drivers_probe)" = '1-1:1.0' ]
new_usb c820 ff
MOCK_RESET_TO_DISK=1 sh "$usb"
[ "$(cat /tmp/calls)" = "$(printf 'reset\neject')" ]
[ "$(cat /sys/bus/usb/devices/1-1/idProduct)" = c820 ]
new_usb c820 ff
if MOCK_RESET_NO_CONFIRM=1 sh "$usb"; then exit 1; fi
[ ! -s /sys/bus/usb/drivers_probe ]
new_usb c820 ff
if MOCK_RESET_FAIL=1 sh "$usb"; then exit 1; fi
[ ! -s /sys/bus/usb/drivers_probe ]
new_usb c820 ff
touch /run/muos/c07/ready
if sh "$usb"; then exit 1; fi
[ ! -s /tmp/calls ]
rm /run/muos/c07/ready
new_usb c820 ff
mv /sys/bus/usb/devices/1-1:1.0 /sys/bus/usb/devices/1-1:1.2
mkdir /sys/bus/usb/devices/1-1:1.0
echo e0 > /sys/bus/usb/devices/1-1:1.0/bInterfaceClass
echo 01 > /sys/bus/usb/devices/1-1:1.0/bInterfaceSubClass
echo 01 > /sys/bus/usb/devices/1-1:1.0/bInterfaceProtocol
sh "$usb"
[ "$(cat /sys/bus/usb/drivers_probe)" = '1-1:1.2' ]
new_usb c820 ff
ln -s /sys/bus/usb/drivers/rtl8821cu /sys/bus/usb/devices/1-1:1.0/driver
sh "$usb"
[ ! -s /sys/bus/usb/drivers_probe ]
new_usb 1a2b 08
sh "$usb"
[ "$(cat /tmp/calls)" = eject ]
[ "$(cat /sys/bus/usb/devices/1-1/idProduct)" = c820 ]
new_usb 1a2b 03
if sh "$usb"; then exit 1; fi
[ ! -s /tmp/calls ]
new_usb 1a2b 08
cp -r /sys/bus/usb/devices/1-1 /sys/bus/usb/devices/1-2
if sh "$usb"; then exit 1; fi
[ ! -s /tmp/calls ]
new_usb 1234 08
if sh "$usb"; then exit 1; fi
[ ! -s /tmp/calls ]
echo wlan0 > /run/muos/c07/interface
: > /tmp/ifconfig-calls
if interface=eth0 ip=192.0.2.10 subnet=255.255.255.0 sh "$dhcp" bound; then exit 1; fi
if interface=wlan0 ip=300.0.2.10 subnet=255.255.255.0 sh "$dhcp" bound; then exit 1; fi
[ ! -s /tmp/ifconfig-calls ]
interface=wlan0 ip=192.0.2.10 subnet=255.255.255.0 sh "$dhcp" bound
[ "$(cat /run/muos/c07/address)" = 192.0.2.10 ]
[ "$(cat /tmp/ifconfig-calls)" = 'wlan0 192.0.2.10 netmask 255.255.255.0 up' ]
interface=wlan0 sh "$dhcp" deconfig
[ ! -e /run/muos/c07/address ]
if sh "$network" start; then exit 1; fi
[ ! -s /tmp/calls ]
sh "$network" stop
sh "$network" stop
if qemu-aarch64 -cpu cortex-a35 -L /runtime -E LD_LIBRARY_PATH=/runtime/lib /bounded 200 /bin/true; then
 exit 1
else
 [ "$?" = 125 ]
fi
qemu-aarch64 -cpu cortex-a35 -L /runtime -E LD_LIBRARY_PATH=/runtime/lib /bounded 120 /bin/true
echo 'PASS: USB ready/eject/wrong-class/ambiguous/unknown; DHCP interface/address/bound/deconfig; RNG guard; idempotent stop'
echo 'PASS: actual AArch64 bounded executor rejects 200 with125; accepts120; all C07 stage limits validated'
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
      '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev',
      '--tmpfs','/sys:rw,nosuid,nodev','--tmpfs','/usr/libexec:rw,nosuid,nodev',
      '-v',f'{repo}/port:/port:ro,z','-v',f'{work}/linux-diagnostic/network.n09y22sw/extracted/usr/libexec/muos-run-bounded:/bounded:ro,z',
      '-v',f'{work}/linux-diagnostic/network.n09y22sw/extracted/lib:/runtime/lib:ro,z',
      '-v',f'{marker}:/etc/muos-network-diagnostic:ro,z',
      (work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=40)
(stage/'stdout.txt').write_text(r.stdout);(stage/'stderr.txt').write_text(r.stderr)
assert r.returncode==0,(stage,r.stderr)
(stage/'report.json').write_text(json.dumps({'passed':True,'hardware_access':False,'real_driver_or_radio_tested':False,
 'cases':['USB warm reset exact bus/device and Wi-Fi reprobe','USB warm reset returns disk then eject','USB reset false success refused',
          'USB reset failed refused','USB active network reset refused','USB Bluetooth interface not reprobed','USB bound interface not reprobed',
          'USB standard eject exact bus/device','USB wrong class refused','USB ambiguous refused','USB unknown refused',
          'DHCP wrong interface refused','DHCP invalid address refused','DHCP bound','DHCP deconfig','RNG guard','stop idempotent',
          'actual bounded executor200 rejects125','actual bounded executor120 succeeds','all stage limits within120'],
 'stage_limits':dict(deadlines)},indent=2)+'\n')
(work/'network-tools/latest-hooks').write_text(str(stage)+'\n')
print('C07 hook fixtures passed:',stage)
