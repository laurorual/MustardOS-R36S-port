#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C17 abort-before-PID1 order/restore fixtures, no live services or power calls."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'network-warm'
stage=Path(tempfile.mkdtemp(prefix='pre-shutdown-checks.',dir=area))
code=r'''
set -eu
. /port/device/rk-r35s-p0/network-warm-diagnostic/pre-shutdown-functions.sh
c17_state=/tmp/state
reset() { rm -rf /tmp/state;: >/tmp/events;FAIL=; }
c17_exec() { echo "$1" >>/tmp/events;[ "$FAIL" != "$1" ]; }
refuse() { if "$@";then echo unexpected-success >&2;exit 1;fi; }
pass() { echo "PASS $1"; }
reset;c17_run
[ "$(tr '\n' ' ' </tmp/events)" = 'preflight baseline network-stop controller-unbind controller-absent archive final-seal request ' ]
pass durable-archive-before-final-seal-and-PID1
reset;FAIL=preflight;refuse c17_run
[ ! -d /tmp/state ] && [ "$(cat /tmp/events)" = preflight ];pass preflight-before-any-action
for step in baseline network-stop controller-unbind controller-absent archive final-seal;do
 reset;FAIL=$step;refuse c17_run
 ! grep -qx request /tmp/events
 [ "$(tail -n1 /tmp/events)" = abort-restore ]
 pass abort-restore-no-PID1-after-$step
done
reset;c17_run;refuse c17_run
[ "$(grep -cx request /tmp/events)" = 1 ];pass duplicate-transaction-refused
'''
cmd=['podman','run','--rm','--network=none','--cap-drop=all','--security-opt=no-new-privileges',
     '--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',
     (work/'rootfs-container.iid').read_text().strip(),'sh','-c',code]
(stage/'fixture.sh').write_text(code)
r=subprocess.run(cmd,text=True,capture_output=True,timeout=25)
(stage/'stdout').write_text(r.stdout);(stage/'stderr').write_text(r.stderr)
assert r.returncode==0,(r.stdout,r.stderr)
cases=[v[5:] for v in r.stdout.splitlines() if v.startswith('PASS ')];assert len(cases)==9,cases
sources=[Path(__file__),repo/'port/device/rk-r35s-p0/network-warm-diagnostic/pre-shutdown.sh',repo/'port/device/rk-r35s-p0/network-warm-diagnostic/pre-shutdown-functions.sh']
m={'passed':True,'case_count':9,'cases':cases,'hardware_and_PID1_calls_mocked':True,
   'sources':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');(area/'latest-pre-shutdown-checks').write_text(str(stage)+'\n')
print('C17 abortable order/archive:',len(cases),'checks passed;',stage)
