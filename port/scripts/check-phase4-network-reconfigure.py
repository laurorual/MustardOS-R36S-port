#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C14 selection, single attempt and configuration-restoration fault fixtures."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
stage=Path(tempfile.mkdtemp(prefix='reconfigure-checks.',dir=area))
script=r'''
set -eu
. /port/device/rk-r35s-p0/network-warm-diagnostic/reconfigure-functions.sh
c14_sys=/tmp/sys;c14_state=/tmp/state
reset() {
 rm -rf /tmp/sys /tmp/state /tmp/events;mkdir -p /tmp/sys/bus/usb/devices/1-1
 p=/tmp/sys/bus/usb/devices/1-1
 echo 0bda > "$p/idVendor";echo c820 > "$p/idProduct"
 echo 1 > "$p/bNumConfigurations";echo 1 > "$p/bConfigurationValue";echo ' 3' > "$p/bNumInterfaces"
 for n in 0 1 2;do
  mkdir "$p:1.$n"
  if [ "$n" = 2 ];then echo ff > "$p:1.$n/bInterfaceClass";echo ff > "$p:1.$n/bInterfaceSubClass";echo ff > "$p:1.$n/bInterfaceProtocol"
  else echo e0 > "$p:1.$n/bInterfaceClass";echo 01 > "$p:1.$n/bInterfaceSubClass";echo 01 > "$p:1.$n/bInterfaceProtocol";fi
 done
 FAIL=;: >/tmp/events
}
c14_exec() { echo "$1" >>/tmp/events;[ "$FAIL" != "$1" ]; }
refuse() { if "$@";then echo unexpected-success >&2;exit 1;fi; }
pass() { echo "PASS $1"; }
reset;c14_reconfigure
[ "$(tr '\n' ' ' </tmp/events)" = 'guard config-zero pause config-one ready ' ]
grep -qx C14_DRIVER_NETDEV_READY=1 /tmp/state/report.txt;pass exact-composite-single-reconfiguration
refuse c14_reconfigure
[ "$(grep -cx config-zero /tmp/events)" = 1 ];pass no-second-attempt
reset;FAIL=guard;refuse c14_reconfigure
[ ! -d /tmp/state ];pass guard-before-state-and-write
for kind in vendor product configuration config-count intf-count wrong-class bound foreign-BT ambiguous;do
 reset
 case "$kind" in
 vendor) echo ffff > "$p/idVendor";;
 product) echo 1a2b > "$p/idProduct";;
 configuration) echo 2 > "$p/bConfigurationValue";;
 config-count) echo 2 > "$p/bNumConfigurations";;
 intf-count) echo 4 > "$p/bNumInterfaces";;
 wrong-class) echo 08 > "$p:1.2/bInterfaceClass";;
 bound) mkdir /tmp/sys/rtl8821cu;ln -s /tmp/sys/rtl8821cu "$p:1.2/driver";;
 foreign-BT) mkdir /tmp/sys/foreign;ln -s /tmp/sys/foreign "$p:1.0/driver";;
 ambiguous) cp -r "$p" /tmp/sys/bus/usb/devices/1-2;;
 esac
 refuse c14_reconfigure
 ! grep -qx config-zero /tmp/events;pass refuse-$kind-before-USB-write
done
for failed in config-zero config-one ready;do
 reset;FAIL=$failed;refuse c14_reconfigure
 [ "$(tail -n1 /tmp/events)" = config-one ]
 grep -q '^C14_RESTORE_CONFIG_ONE_RC=' /tmp/state/report.txt
 ! grep -qx C14_DRIVER_NETDEV_READY=1 /tmp/state/report.txt
 pass restore-after-$failed
done

# Execute the actual one-shot wrapper with only guard, paths and helpers mocked.
mkdir -p /tmp/trial /tmp/boot /tmp/persistent /tmp/mock
cp /port/device/rk-r35s-p0/network-warm-diagnostic/usb-trial.sh /tmp/trial/wrapper
sed -i 's|/usr/libexec/muos-c14|/tmp/trial|g;s|/usr/libexec/muos-boot|/tmp/boot|g;s|/var/lib/muos-diagnostic|/tmp/persistent|g;s|/run/muos/selection/mode|/tmp/mode|g;s|export PATH=|export PATH=/tmp/mock:|' /tmp/trial/wrapper
printf 'c12_guard() { return 0; }\nc12_root_ro() { [ "$ROOT_RO" = 1 ]; }\n' >/tmp/boot/native-functions.sh
printf '#!/bin/sh\necho original >>/tmp/trial-events\n' >/tmp/trial/usb-mode.original
printf '#!/bin/sh\necho reconfigure >>/tmp/trial-events\n' >/tmp/trial/reconfigure.sh
printf '#!/bin/sh\necho sync >>/tmp/trial-events\n' >/tmp/mock/sync
chmod 755 /tmp/trial/* /tmp/mock/sync
export ROOT_RO=0
echo c07 >/tmp/mode
reset_trial() { rm -f /tmp/persistent/*;: >/tmp/trial-events;ROOT_RO=0; }
token() { printf 'MUOS-C14-ONCE\n' >/tmp/persistent/c14.once;chmod 600 /tmp/persistent/c14.once; }
reset_trial;sh /tmp/trial/wrapper
[ "$(cat /tmp/trial-events)" = original ];pass absent-token-original-only
reset_trial;token;sh /tmp/trial/wrapper
[ ! -e /tmp/persistent/c14.once ] && [ -f /tmp/persistent/c14.used ]
[ "$(tr '\n' ' ' </tmp/trial-events)" = 'sync original reconfigure ' ];pass consume-sync-before-USB-action
reset_trial;token;chmod 666 /tmp/persistent/c14.once;refuse sh /tmp/trial/wrapper
[ ! -s /tmp/trial-events ];pass writable-token-refused
reset_trial;ln -s /tmp/foreign-token /tmp/persistent/c14.once;refuse sh /tmp/trial/wrapper
[ ! -s /tmp/trial-events ];pass symlink-token-refused
reset_trial;token;ROOT_RO=1;refuse sh /tmp/trial/wrapper
[ -f /tmp/persistent/c14.once ] && [ ! -s /tmp/trial-events ];pass no-root-remount-to-consume-late-token
'''
command=['podman','run','--rm','--network=none','--cap-drop=all','--security-opt=no-new-privileges',
         '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',
         (work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
(stage/'fixture.sh').write_text(script)
r=subprocess.run(command,text=True,capture_output=True,timeout=30)
(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(r.stdout,r.stderr)
cases=[s[5:] for s in r.stdout.splitlines() if s.startswith('PASS ')];assert len(cases)==20,cases
sources=sorted((repo/'port/device/rk-r35s-p0/network-warm-diagnostic').glob('*'))+[Path(__file__)]
report={'passed':True,'case_count':len(cases),'cases':cases,'real_USB_or_device_changed':False,
        'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-reconfigure-checks').write_text(str(stage)+'\n')
print('C14 logical reconfiguration:',len(cases),'cases passed;',stage)
