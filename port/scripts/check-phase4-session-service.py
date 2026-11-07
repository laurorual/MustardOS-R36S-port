#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C11 transaction rollback, idempotence and PID-reuse guards in isolation."""
from pathlib import Path
import json,os,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-session';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));services=stage/'services';services.mkdir()
names=['S30dbus-daemon','S90muos-storage','S95muos-core','S96muos-input-ready','S99muos-ui']
for n in names:
 p=services/n;p.write_text('#!/bin/sh\necho "${0##*/}:$1" >> "$EVENTS"\n[ "$FAIL" != "${0##*/}:$1" ]\n');p.chmod(0o755)
cases={}
for label,fail in [('success',''),('bus-fail','S30dbus-daemon:start'),('storage-fail','S90muos-storage:start'),('core-fail','S95muos-core:start'),('input-fail','S96muos-input-ready:start'),('ui-fail','S99muos-ui:start'),('ui-status-fail','S99muos-ui:status'),('stop-error-continues','S95muos-core:stop')]:
 state=stage/label;state.mkdir();env={**os.environ,'CHAIN':str(repo/'port/device/rk-r35s-p0/session/chain.sh'),'STATE':str(state),'SERVICES':str(services),'EVENTS':str(state/'events'),'FAIL':fail}
 code='''. "$CHAIN"
state=$STATE;service_dir=$SERVICES
session_exec() { "$@"; }
session_start_chain; start=$?
session_stop_chain; stop=$?
if [ "$stop" = 0 ]; then session_stop_chain || exit 99; fi
printf '%s %s\\n' "$start" "$stop"
'''
 r=subprocess.run(['sh','-c',code],env=env,capture_output=True,text=True);assert r.returncode==0,(label,r.stderr)
 expected=(0,0) if label=='success' else (0,1) if label=='stop-error-continues' else (1,0);assert tuple(map(int,r.stdout.split()))==expected
 events=(state/'events').read_text().splitlines();attempts=names if label in ['success','stop-error-continues','ui-status-fail'] else names[:names.index(fail.split(':')[0])+1]
 assert events[-len(attempts):]==[n+':stop' for n in reversed(attempts)],label
 assert not any(n in '\n'.join(events) for n in ['S05','S10','network','seedrng'])
 cases[label]={'passed':True,'events':events}
script=r'''
set -eu
mkdir -p /tmp/package
cp /port/device/rk-r35s-p0/session/service.sh /port/device/rk-r35s-p0/session/control-functions.sh /tmp/package/
cat > /tmp/package/mount-namespace <<'EOF'
#!/bin/sh
exec "$@"
EOF
cat > /tmp/package/worker.sh <<'EOF'
#!/bin/sh
set -eu
state=$1
printf '%s %s\n' "$$" "$(awk '{print $22}' /proc/$$/stat)" > "$state/manager"
trap 'rm -f "$state/ready"; echo 0 > "$state/result"; touch "$state/done"; exit 0' TERM HUP INT
touch "$state/ready"
while :; do sleep 0.1; done
EOF
chmod 755 /tmp/package/*
config=/tmp/session.conf
export MUOS_SESSION_CONFIG=$config
printf 'enabled=0\nlease_seconds=30\n' > "$config";chmod 600 "$config"
sh /tmp/package/service.sh start
[ ! -f /run/muos/session/current ]
if sh /tmp/package/service.sh status; then exit 1; else [ "$?" = 3 ]; fi
printf 'enabled=1\nlease_seconds=30\n' > "$config"
sh /tmp/package/service.sh start
sh /tmp/package/service.sh status
cp /run/muos/session/current /tmp/first-generation
read generation < /run/muos/session/current
cp /run/muos/session/$generation/manager /tmp/first-manager
sh /tmp/package/service.sh start
cmp /tmp/first-generation /run/muos/session/current
cmp /tmp/first-manager /run/muos/session/$generation/manager
sh /tmp/package/service.sh stop
sh /tmp/package/service.sh stop
if sh /tmp/package/service.sh status; then exit 1; else [ "$?" = 3 ]; fi
sh /tmp/package/service.sh start
read second < /run/muos/session/current
[ "$second" != "$generation" ]
! cmp -s /tmp/first-manager /run/muos/session/$second/manager
sh /tmp/package/service.sh stop
# A foreign live PID with a mismatched start time/cmdline must never be killed.
sleep 30 & foreign=$!
mkdir /run/muos/session/run-9999
printf '%s 1\n' "$foreign" > /run/muos/session/run-9999/manager
echo run-9999 > /run/muos/session/current
if sh /tmp/package/service.sh stop; then exit 1; fi
kill -0 "$foreign"
if sh /tmp/package/service.sh start; then exit 1; fi
kill -0 "$foreign"
kill "$foreign";wait "$foreign" 2>/dev/null || :
echo "$second" > /run/muos/session/current
printf 'enabled=1\nlease_seconds=0\n' > "$config"
if sh /tmp/package/service.sh start; then exit 1; fi
printf 'enabled=1\nlease_seconds=601\n' > "$config"
if sh /tmp/package/service.sh start; then exit 1; fi
printf 'enabled=1\nlease_seconds=30\n' > "$config"
printf '#!/bin/sh\nexit 125\n' > /tmp/package/mount-namespace
if sh /tmp/package/service.sh start; then exit 1; fi
read third < /run/muos/session/current
[ "$(cat /run/muos/session/$third/launch-failed)" = 125 ]
echo 'PASS disabled/idempotent/start/status/stop/restart/PID-reuse/dirty transaction/lease guard/launcher error'
'''
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/run:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-c',script]
r=subprocess.run(args,capture_output=True,text=True,timeout=30);(stage/'controller.stdout').write_text(r.stdout);(stage/'controller.stderr').write_text(r.stderr);assert r.returncode==0,(stage,r.stdout,r.stderr)
report={'passed':True,'chain_cases':cases,'controller_cases':['disabled no spawn','ready status','idempotent start same PID/generation','stop and repeated stop','new generation/PID after restart','foreign PID never signaled','dirty transaction refuses start','lease0 refused','lease601 refused','namespace launcher error125 surfaced'],'real_namespace_hardware_or_network_tested':False}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C11 service8 transaction and10 controller cases passed:',stage)
