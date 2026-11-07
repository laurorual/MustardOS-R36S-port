#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/retro-session'
source=repo/'port/device/rk-r35s-p0/retro-session/worker.sh';text=source.read_text()
assert subprocess.run(['sh','-n',str(source)]).returncode==0
stage=Path(tempfile.mkdtemp(prefix='worker-checks.',dir=area));cases=[]
cleanup=text[text.index('finish() {'):text.index('trap finish EXIT')]
for name,owned,preferences,operation,failed,want in [
    ('normal',1,1,0,False,0),('partial_prepare',1,0,42,False,42),
    ('signal',1,1,143,False,143),('stop_failure',1,1,0,True,125),('before_prepare',0,0,1,False,1),
]:
    d=stage/name;d.mkdir();(d/'data/MUOS/preferences').mkdir(parents=True);(d/'preferences-before.sha256').write_text('')
    calls=d/'calls'
    code=f'''state={d};prefs_mount=$state/data;runtime_owned={owned};preferences_owned={preferences};reason=fixture;runner_pid=
runner_identity() {{ return 1; }}
session_stop_chain() {{ echo stop >> {calls}; return {1 if failed else 0}; }}
retro_logger_stop() {{ echo logger >> {calls}; }}
session_restore() {{ echo restore >> {calls}; }}
pidof() {{ return 1; }}
findmnt() {{ echo ro; }}
cat() {{ [ "$*" = /proc/sys/kernel/tainted ] && echo 0; }}
'''+cleanup.replace('/run/dbus/system_bus_socket',str(d/'dbus.sock'))+f'\ntrap finish EXIT\nexit {operation}\n'
    r=subprocess.run(['sh','-c',code],capture_output=True,text=True)
    assert r.returncode==want,(name,r.stdout,r.stderr)
    result=(d/'result.txt').read_text();assert f'OPERATION={operation}\n' in result
    assert ('CLEANUP=1' in result)==failed
    assert (calls.read_text().splitlines() if calls.exists() else [])==(['stop','logger','restore','logger'] if owned else [])
    assert (d/'done').exists();(d/'fixture.sh').write_text(code);cases.append(name)
prefix=text[:text.index('package=/usr/libexec/muos-session')]
for name in ['wrong_path','wrong_mode','symlink','same_namespace','wrong_mode_name']:
    d=stage/name;d.mkdir();target=d/'capsule';target.mkdir(mode=0o700)
    if name=='wrong_mode':target.chmod(0o755)
    if name=='symlink':target.rmdir();target.symlink_to(d,target_is_directory=True)
    stub='''stat() { printf '0:0:%s\\n' "$(command stat -c %a "$3")"; }
readlink() { echo SAME; }
'''
    arg='/wrong' if name=='wrong_path' else str(target);mode='wrong' if name=='wrong_mode_name' else 'graphics'
    code=stub+f'set -- "{arg}" {mode}\n'+prefix.replace('/run/muos-prefs-data.??????',str(target))+'\necho UNSAFE\n'
    r=subprocess.run(['sh','-c',code],capture_output=True,text=True)
    assert r.returncode!=0 and 'UNSAFE' not in r.stdout,(name,r.stdout,r.stderr);cases.append(name)
report={'passed':True,'cases':cases,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),source]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-worker-checks').write_text(str(stage)+'\n')
print('C44 worker rollback/guard tests:',len(cases),stage)
