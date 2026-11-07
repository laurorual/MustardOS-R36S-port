#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Host-only C12 ordering/failure tests; callbacks never touch real services."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/boot-order';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));source=repo/'port/device/rk-r35s-p0/boot/order.sh';contract=json.loads((source.parent/'contract.json').read_text());cases={}
def check(label,action,fail='',expected=0):
 state=stage/label;state.mkdir()
 code='''. "$ORDER"
boot_state=$STATE
boot_exec() { printf '%s\\n' "$1" >> "$boot_state/events"; case " $FAIL " in *" $1 "*) return 1 ;; *) return 0 ;; esac; }
case "$ACTION" in
 start) c12_start ;;
 twice) c12_start && c12_start ;;
 failed-retry) c12_start; first=$?; c12_start; second=$?; [ "$first:$second" = 1:64 ] ;;
 stop) c12_prepare_shutdown ;;
 stop-twice) c12_prepare_shutdown && c12_prepare_shutdown ;;
esac
'''
 env={**os.environ,'ORDER':str(source),'STATE':str(state),'ACTION':action,'FAIL':fail}
 r=subprocess.run(['sh','-c',code],env=env,capture_output=True,text=True);(state/'stdout').write_text(r.stdout);(state/'stderr').write_text(r.stderr);assert r.returncode==expected,(label,r.returncode,r.stderr)
 events=(state/'events').read_text().splitlines()
 for step,seconds in re.findall(r'STEP=([a-z.]+) LIMIT=([0-9]+)',(state/'steps.txt').read_text()):assert int(seconds)==contract['limits_seconds'][step] and 1<=int(seconds)<=120
 cases[label]={'passed':True,'rc':r.returncode,'events':events}
 return events
normal=['entropy.start','udev.start','usb.switch','network.start','entropy.stop','root.seal','session.start','session.status']
assert check('startup','start')==normal
assert check('start-idempotent-no-seed-reload','twice')==normal+['session.status']
e=check('failed-start-cannot-reload-seed','failed-retry','entropy.start');assert e.count('entropy.start')==1
for fail in ['entropy.start','udev.start','entropy.stop','root.seal']:
 e=check('required-'+fail,'start',fail,1);assert 'session.start' not in e and e.count('entropy.stop')<=1
for fail in ['usb.switch','network.start']:
 e=check('offline-'+fail,'start',fail);assert 'session.start' in e and e.index('entropy.stop')<e.index('session.start')
 if fail=='network.start':assert e.index('network.stop')<e.index('session.start')
e=check('partial-network-cleanup-fails-closed','start','network.start network.stop',1);assert 'session.start' not in e
for fail in ['session.start','session.status']:
 e=check('ui-failure-'+fail,'start',fail,1);assert 'session.stop' in e and 'network.stop' not in e and 'udev.stop' not in e
shutdown=contract['shutdown_before_pid1_request'];assert check('shutdown-order','stop')==shutdown
assert check('shutdown-idempotent','stop-twice')==shutdown
for fail in ['session.stop','session.quiescent','network.stop','udev.stop','root.sync','root.seal']:
 e=check('shutdown-block-'+fail,'stop',fail,1);assert e==shutdown[:shutdown.index(fail)+1]
assert contract['persistence']['implemented_mode']=='volatile' and not contract['persistence']['persistent_mode_enabled']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'passed':True,'cases':cases,'case_count':len(cases),'real_services_device_reboot_mounts_executed':False,'tests_cover_native_adapters':False,'persistence_implemented':False,'sources':{str(p.relative_to(repo)):sha(p) for p in [source,source.parent/'contract.json',Path(__file__)]}}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C12 host-only boot ordering checks passed:',len(cases),'cases;',stage)
