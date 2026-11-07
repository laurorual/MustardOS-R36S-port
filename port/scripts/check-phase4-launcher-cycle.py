#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Test the real diagnostic hook and coordinator; fixtures never access devices."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'launcher-cycle'
build=Path((area/'latest-build').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
for n,h in br['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work))
root='/work/rootfs-candidate/composition.w59vz7vo/target'
retro=Path((work/'retro-session/latest').read_text().strip())
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -O2 -Wall -Wextra -Werror -mcpu=cortex-a35 -I/port/diagnostics /port/diagnostics/phase4-launcher-cycle-check.c -o {rel(stage)}/hook
qemu-aarch64 -cpu cortex-a35 -L {root} {rel(stage)}/hook
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={rel(build/'frontend-bin/lib')}:{root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(retro/'source/bin/muxretro')} --version
'''
(stage/'audit.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('audit.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr)
assert 'C45_LAUNCHER_HOOK_OK' in r.stdout
cycle=repo/'port/device/rk-r35s-p0/launcher-cycle/cycle.sh';worker=repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh'
for p in [cycle,worker]:subprocess.run(['sh','-n',str(p)],check=True)
runner=Path((work/'retro-session/latest-runner').read_text().strip())/'runner-host'
cases=[]
for name,mode,want in [('normal','cycle',0),('failure_return','core-failure',42),('observation','observe',0),('bad_action','cycle',1),('missing_present','cycle',1),('frontend_failed','cycle',7),('duplicate','cycle',1),('wrong_mode','shutdown',64)]:
 d=stage/name;d.mkdir(mode=0o700);(d/'state').mkdir();(d/'runtime').mkdir();(d/'lib').mkdir()
 (d/'runner').symlink_to(runner)
 frontend=d/'frontend';frontend.write_text('''#!/usr/bin/env python3
from pathlib import Path
import os,sys
p=Path(__file__).parent
phase=os.environ['MUOS_PORT_DIAGNOSTIC_CYCLE']
with (p/'calls').open('a') as f:f.write('menu:'+phase+'\\n')
if p.name=='frontend_failed':sys.exit(7)
action='port-retro-diagnostic' if phase=='dispatch' else 'port-cycle-done'
if p.name=='bad_action':action='shutdown'
(p/'runtime/action').write_text(action+'\\n')
if p.name!='missing_present':print('C45_LAUNCHER_PRESENT phase='+phase+' serial=4')
print('C45_LAUNCHER_EXIT action='+('port-retro-diagnostic' if phase=='dispatch' else 'port-cycle-done'))
''');frontend.chmod(0o700)
 core=d/'muxretro';core.write_text('''#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).parent
with (p/'calls').open('a') as f:f.write('core\\n')
print('C44_FIRST_PRESENT seconds=15 serial=3')
print('C44_NORMAL_EXIT expired=1 frames=900')
''');core.chmod(0o700)
 text=cycle.read_text().replace('/run/muos',str(d/'runtime')).replace('/opt/muos/frontend/muxfrontend',str(frontend)).replace('0:0:700',f'{os.getuid()}:{os.getgid()}:700')
 (d/'cycle.sh').write_text(text)
 if name=='duplicate':(d/'cycle.once').touch()
 result=subprocess.run(['sh',str(d/'cycle.sh'),str(d),mode],capture_output=True,text=True,timeout=15)
 (d/'stdout').write_text(result.stdout);(d/'stderr').write_text(result.stderr)
 assert result.returncode==want,(name,result.returncode,result.stdout,result.stderr)
 calls=(d/'calls').read_text().splitlines() if (d/'calls').exists() else []
 expected=['menu:dispatch','core','menu:return'] if want==0 else ['menu:dispatch','menu:return'] if name=='failure_return' else [] if name in ['duplicate','wrong_mode'] else ['menu:dispatch']
 assert calls==expected,(name,calls)
 cases.append(name)
# Real worker cleanup function, with all hardware paths/functions replaced by fixtures.
text=worker.read_text();cleanup=text[text.index('finish() {'):text.index('trap finish EXIT')]
for name,owned,prefs,operation,failed,want in [('cleanup_normal',1,1,0,False,0),('cleanup_partial',1,0,42,False,42),('cleanup_signal',1,1,143,False,143),('cleanup_failed',1,1,0,True,125),('cleanup_before_prepare',0,0,1,False,1)]:
 d=stage/name;d.mkdir();(d/'data/MUOS/preferences').mkdir(parents=True);(d/'preferences-before.sha256').touch();calls=d/'calls'
 code=f'''state={d};prefs_mount=$state/data;runtime_owned={owned};preferences_owned={prefs};reason=fixture;runner_pid=
runner_identity() {{ return 1; }}
session_stop_chain() {{ echo stop >> {calls};return {int(failed)}; }}
retro_logger_stop() {{ echo logger >> {calls}; }}
session_restore() {{ echo restore >> {calls}; }}
pidof() {{ return 1; }}
findmnt() {{ echo ro; }}
cat() {{ [ "$*" = /proc/sys/kernel/tainted ] && echo 0; }}
'''+cleanup.replace('/run/dbus/system_bus_socket',str(d/'dbus.sock'))+f'\ntrap finish EXIT\nexit {operation}\n'
 result=subprocess.run(['sh','-c',code],capture_output=True,text=True)
 assert result.returncode==want,(name,result.stderr)
 assert f'OPERATION={operation}\n' in (d/'result.txt').read_text()
 assert ('CLEANUP=1' in (d/'result.txt').read_text())==failed
 cases.append(name)
# Cross-source contract: the worker path must satisfy the installed data guard.
guard=repo/'port/device/rk-r35s-p0/preferences/data-functions.sh'
g=guard.read_text();contract=g[g.index('    case "$prefs_mount" in'):g.index('    prefs_data_source || return 64')]
assert '/run/muos-prefs-data.??????' in worker.read_text()
for mount,expected in [('/run/muos-prefs-data.Abc123/data',0),('/run/muos-cycle.Abc123/data',64)]:
 result=subprocess.run(['sh','-c','check() {\n'+contract+'\n};prefs_mount='+mount+';check'])
 assert result.returncode==expected
cases.append('installed_mount_path_contract')
report={'passed':True,'build_stage':str(build),'binary_sha256':br['binary_sha256'],'hook_on_real_AArch64_QEMU':True,'immediate_library_binding_passed':True,'coordinator_and_rollback_cases':cases,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-launcher-cycle.h',repo/'port/diagnostics/phase4-launcher-cycle-check.c',cycle,worker,guard]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C45 hook/binding/coordinator/rollback checks passed:',stage)
