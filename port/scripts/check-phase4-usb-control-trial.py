#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C16 wrapper ordering and original-result preservation in an isolated fixture."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
stage=Path(tempfile.mkdtemp(prefix='control-checks.',dir=area))
script=r'''
set -eu
mkdir -p /tmp/c16 /tmp/persist /tmp/boot /tmp/bin /tmp/muos
cp /port/device/rk-r35s-p0/network-warm-diagnostic/usb-control-trial.sh /tmp/c16/wrapper
sed -i 's|/usr/libexec/muos-c16|/tmp/c16|g;s|/var/lib/muos-diagnostic|/tmp/persist|g;s|/usr/libexec/muos-boot|/tmp/boot|g;s|/run/muos/selection/mode|/tmp/mode|g;s|/run/muos/c07/control-probe|/tmp/muos/state|g;s|/usr/libexec/muos-run-bounded|/tmp/bin/bounded|g;s|export PATH=|export PATH=/tmp/bin:|' /tmp/c16/wrapper
printf 'c12_guard() { return 0; }\nc12_root_ro() { [ "$ROOT_RO" = 1 ]; }\n' >/tmp/boot/native-functions.sh
printf '#!/bin/sh\necho "$1" >>/tmp/events\nexit "$PROBE_RC"\n' >/tmp/c16/usb-control-probe
printf '#!/bin/sh\necho original >>/tmp/events\nexit "$ORIGINAL_RC"\n' >/tmp/c16/usb-mode.original
printf '#!/bin/sh\nshift\nexec "$@"\n' >/tmp/bin/bounded
printf '#!/bin/sh\necho sync >>/tmp/events\n' >/tmp/bin/sync
chmod 755 /tmp/bin/* /tmp/c16/*
export ROOT_RO=0 PROBE_RC=0 ORIGINAL_RC=0
echo c07 >/tmp/mode
reset() { rm -f /tmp/persist/*;rm -rf /tmp/muos/state;: >/tmp/events;ROOT_RO=0;PROBE_RC=0;ORIGINAL_RC=0; }
token() { printf 'MUOS-C16-ONCE\n' >/tmp/persist/c16.once;chmod 600 /tmp/persist/c16.once; }
refuse() { if "$@";then echo unexpected-success >&2;exit 1;fi; }
pass() { echo "PASS $1"; }
reset;sh /tmp/c16/wrapper >/tmp/output
[ "$(cat /tmp/events)" = original ];pass default-original-only
reset;token;sh /tmp/c16/wrapper >/tmp/output
[ "$(tr '\n' ' ' </tmp/events)" = 'sync retained-pre original retained-post ' ]
[ ! -e /tmp/persist/c16.once ] && [ -f /tmp/persist/c16.used ];pass consume-before-fixed-observations
reset;token;PROBE_RC=64;sh /tmp/c16/wrapper >/tmp/output
grep -qx C16_PRE_PROBE_RC=64 /tmp/output;grep -qx C16_POST_PROBE_RC=64 /tmp/output
pass observation-failure-does-not-mask-original-success
reset;token;ORIGINAL_RC=1;refuse sh /tmp/c16/wrapper >/tmp/output
[ "$(tail -n1 /tmp/events)" = retained-post ];pass original-failure-propagates-after-post-observation
for mode in writable symlink malformed rootRO;do
 reset;token
 case "$mode" in
 writable) chmod 666 /tmp/persist/c16.once;;
 symlink) rm /tmp/persist/c16.once;ln -s /tmp/foreign /tmp/persist/c16.once;;
 malformed) printf BAD >/tmp/persist/c16.once;;
 rootRO) ROOT_RO=1;;
 esac
 refuse sh /tmp/c16/wrapper
 [ ! -s /tmp/events ];pass refuse-$mode-before-probe
done
'''
cmd=['podman','run','--rm','--network=none','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',
     (work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
(stage/'fixture.sh').write_text(script)
r=subprocess.run(cmd,text=True,capture_output=True,timeout=25)
(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(r.stdout,r.stderr)
cases=[s[5:] for s in r.stdout.splitlines() if s.startswith('PASS ')];assert len(cases)==8,cases
files=[repo/'port/device/rk-r35s-p0/network-warm-diagnostic/usb-control-trial.sh',repo/'port/scripts/usb_control_actions.py',Path(__file__)]
m={'passed':True,'case_count':8,'cases':cases,'real_USB_or_device_used':False,
   'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');(area/'latest-control-checks').write_text(str(stage)+'\n')
print('C16 observer/token/original-result:',len(cases),'cases passed;',stage)
