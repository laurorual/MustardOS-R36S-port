#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C15 sole-controller topology, no-adoption and restoration fixtures."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
stage=Path(tempfile.mkdtemp(prefix='controller-checks.',dir=area))
script=r'''
set -eu
. /port/device/rk-r35s-p0/network-warm-diagnostic/reconfigure-functions.sh
. /port/device/rk-r35s-p0/network-warm-diagnostic/controller-functions.sh
c15_sys=/tmp/sys;c15_state=/tmp/state
reset() {
 rm -rf /tmp/sys /tmp/state /tmp/events
 mkdir -p /tmp/sys/bus/platform/devices /tmp/sys/bus/platform/drivers/dwc2 /tmp/sys/bus/usb/devices
 ctl=/tmp/sys/devices/platform/ff300000.usb
 hub=$ctl/usb1;p=$hub/1-1
 mkdir -p "$p"
 ln -s "$ctl" /tmp/sys/bus/platform/devices/ff300000.usb
 ln -s /tmp/sys/bus/platform/drivers/dwc2 "$ctl/driver"
 ln -s "$hub" /tmp/sys/bus/usb/devices/usb1
 ln -s "$p" /tmp/sys/bus/usb/devices/1-1
 echo 1d6b >"$hub/idVendor";echo 0002 >"$hub/idProduct"
 echo 0bda >"$p/idVendor";echo c820 >"$p/idProduct"
 echo 1 >"$p/bNumConfigurations";echo 1 >"$p/bConfigurationValue";echo 3 >"$p/bNumInterfaces"
 for n in 0 1 2;do
  mkdir "$p:1.$n";ln -s "$p:1.$n" "/tmp/sys/bus/usb/devices/1-1:1.$n"
  if [ "$n" = 2 ];then echo ff >"$p:1.$n/bInterfaceClass";echo ff >"$p:1.$n/bInterfaceSubClass";echo ff >"$p:1.$n/bInterfaceProtocol"
  else echo e0 >"$p:1.$n/bInterfaceClass";echo 01 >"$p:1.$n/bInterfaceSubClass";echo 01 >"$p:1.$n/bInterfaceProtocol";fi
 done
 FAIL=;: >/tmp/events
}
c15_exec() { echo "$1" >>/tmp/events;[ "$FAIL" != "$1" ]; }
refuse() { if "$@";then echo unexpected-success >&2;exit 1;fi; }
pass() { echo "PASS $1"; }
reset;c15_rebind
[ "$(tr '\n' ' ' </tmp/events)" = 'guard unbind pause bind ready ' ]
grep -qx C15_DRIVER_NETDEV_READY=1 /tmp/state/report.txt
pass sole-dwc2-rebind-order
refuse c15_rebind
[ "$(grep -cx unbind /tmp/events)" = 1 ];pass no-second-controller-operation
for kind in guard foreign-controller shared-hub extra-device bound-wifi wrong-PID foreign-driver;do
 reset
 case "$kind" in
 guard) FAIL=guard;;
 foreign-controller) rm /tmp/sys/bus/platform/devices/ff300000.usb;;
 shared-hub) mkdir -p /tmp/sys/devices/platform/foreign/usb2;ln -s /tmp/sys/devices/platform/foreign/usb2 /tmp/sys/bus/usb/devices/usb2;;
 extra-device) mkdir /tmp/sys/bus/usb/devices/1-2;echo 1234 >/tmp/sys/bus/usb/devices/1-2/idVendor;echo 5678 >/tmp/sys/bus/usb/devices/1-2/idProduct;;
 bound-wifi) mkdir /tmp/sys/rtl8821cu;ln -s /tmp/sys/rtl8821cu "$p:1.2/driver";;
 wrong-PID) echo 1a2b >"$p/idProduct";;
 foreign-driver) rm "$ctl/driver";ln -s /tmp/sys/foreign "$ctl/driver";;
 esac
 refuse c15_rebind
 ! grep -qx unbind /tmp/events
 pass no-unbind-$kind
done
for failed in unbind bind ready;do
 reset;FAIL=$failed;refuse c15_rebind
 [ "$(tail -n1 /tmp/events)" = bind ]
 grep -q '^C15_RESTORE_CONTROLLER_BIND_RC=' /tmp/state/report.txt
 ! grep -qx C15_DRIVER_NETDEV_READY=1 /tmp/state/report.txt
 pass restore-controller-after-$failed
done
'''
command=['podman','run','--rm','--network=none','--cap-drop=all','--security-opt=no-new-privileges',
         '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',
         (work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
(stage/'fixture.sh').write_text(script)
r=subprocess.run(command,text=True,capture_output=True,timeout=30)
(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(r.stdout,r.stderr)
cases=[s[5:] for s in r.stdout.splitlines() if s.startswith('PASS ')];assert len(cases)==12,cases
sources=sorted((repo/'port/device/rk-r35s-p0/network-warm-diagnostic').glob('*'))+[Path(__file__)]
report={'passed':True,'case_count':len(cases),'cases':cases,'real_USB_or_device_changed':False,
        'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-controller-checks').write_text(str(stage)+'\n')
print('C15 controller topology/rebind:',len(cases),'cases passed;',stage)
