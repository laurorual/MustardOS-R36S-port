#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C46 real hook/loader plus filesystem request validation and process coordination."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'app-selection'
build=Path((area/'latest-build').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
for n,h in br['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work))
root='/work/rootfs-candidate/composition.w59vz7vo/target';retro=Path((work/'retro-session/latest').read_text().strip())
upstream=build/'frontend-source/common'
def function(path,start):
 text=path.read_text();a=text.index(start);b=text.index('\n}\n',a)+3;return text[a:b]
writer_source=upstream/'storage/fileio.c';action_source=upstream/'runtime/exec.c';reader_source=upstream/'storage/fileio_lite.c'
real_writer='#include <stdio.h>\n#include <stdlib.h>\n#include <stdarg.h>\n#include <string.h>\n#define MAX_BUFFER_SIZE 4096\n#include <sys/stat.h>\n#define CHAR 1\n#define INT 2\n#define LOG_ERROR(...) ((void)0)\nstatic const char *test_action;\n#define MUOS_ACT_LOAD test_action\nstatic void vs_invalidate_path(const char *p) {(void)p;}\n'+function(writer_source,'int write_text_to_file(')+'\n'+function(action_source,'void load_mux(')+'\n'+function(reader_source,'char *read_line_char_from(')+'\nint main(int argc,char **argv){if(argc!=3)return 2;umask(077);test_action=argv[1];load_mux("app");if(!write_text_to_file(argv[2],"w",CHAR,"/opt/muos/config/port-apps/R35S-Diagnostic"))return 1;char *missing=read_line_char_from(argv[2],2);if(!missing||*missing)return 3;free(missing);return 0;}\n'
(stage/'real-writer.c').write_text(real_writer)
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -O2 -mcpu=cortex-a35 {rel(stage/'real-writer.c')} -o {rel(stage/'real-writer')}
qemu-aarch64 -cpu cortex-a35 -L {root} {rel(stage/'real-writer')} {rel(stage/'real-action')} {rel(stage/'real-application')}
"$cc" -O2 -Wall -Wextra -Werror -mcpu=cortex-a35 -I/port/diagnostics /port/diagnostics/phase4-app-selection-check.c -o {rel(stage)}/hook
qemu-aarch64 -cpu cortex-a35 -L {root} {rel(stage)}/hook
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={rel(build/'frontend-bin/lib')}:{root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(retro/'source/bin/muxretro')} --version
'''
(stage/'audit.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('audit.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr)
assert 'C46_APP_HOOK_OK' in r.stdout
assert (stage/'real-action').read_bytes()==b'app\n'
assert (stage/'real-application').read_bytes()==b'/opt/muos/config/port-apps/R35S-Diagnostic'
base=repo/'port/device/rk-r35s-p0/app-selection';files=[base/n for n in ['select.sh','adapter.sh','app-launch.sh','stopped-screen.sh','worker.sh']]
for p in files:subprocess.run(['sh','-n',str(p)],check=True)
assert (base/'worker.sh').read_text()==(repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh').read_text().replace('"$dir/runner" 150','"$dir/runner" 210')
runner=Path((work/'retro-session/latest-runner').read_text().strip())/'runner-host'
cases=[]
for name,mode,want in [('guard','cycle',0),('normal','observe',0),('cancel','observe',0),('timeout','observe',0),('wrong_app','observe',64),('changed_launcher','observe',64),('frontend_failure','observe',7),('app_failure_return','observe',0),('duplicate','observe',2),('occupied_mount','observe',64),('extra_argument','observe',64),('newline_application','observe',64),('wrong_governor','observe',64)]:
 d=stage/name;d.mkdir(mode=0o700);(d/'state').mkdir();(d/'runtime').mkdir();(d/'lib').mkdir();(d/'runner').symlink_to(runner);(d/'device-default-governor').write_text('schedutil')
 # Only paths, uid/gid, and mount syscalls are replaced; validator, script body,
 # exact request consumption, and the real process owner run unchanged.
 def fixture(s):return s.replace('/run/muos-prefs-data.??????',str(d)).replace('/run/muos',str(d/'runtime')).replace('/opt/muos/config/port-apps',str(d/'app-tree')).replace('0:0:',f'{os.getuid()}:{os.getgid()}:').replace('/opt/muos/device/config/cpu/default',str(d/'device-default-governor'))
 for n in ['adapter.sh','app-launch.sh']:(d/n).write_text(fixture((base/n).read_text()))
 (d/'launcher.sha256').write_text(sha(d/'app-launch.sh')+'\n');(d/'launcher.sha256').chmod(0o600)
 frontend=d/'frontend';frontend.write_text('''#!/usr/bin/env python3
from pathlib import Path
import os,sys
p=Path(__file__).parent;phase='dispatch' if os.getenv('MUOS_PORT_APP_DIAGNOSTIC') else 'return'
with (p/'calls').open('a') as f:f.write(phase+'\\n')
if p.name=='frontend_failure':sys.exit(7)
if phase=='dispatch':
 print('C46_APP_PRESENT serial=7')
 kind=p.name if p.name in ['cancel','timeout'] else None
 if kind:
  action='port-app-'+kind;print('C46_APP_LEAVE action='+action)
 else:
  action='app';app=str(p/'app-tree/R35S-Diagnostic')
  (p/'runtime/application').write_text(('/tmp/other' if p.name=='wrong_app' else app)+('\\n' if p.name=='newline_application' else ''));(p/'runtime/application').chmod(0o600)
  (p/'runtime/governor').write_text('powersave' if p.name=='wrong_governor' else 'schedutil');(p/'runtime/governor').chmod(0o600)
  (p/'runtime/controller').write_text('system');(p/'runtime/controller').chmod(0o600)
  if p.name=='changed_launcher':(p/'app-tree/R35S-Diagnostic/mux_launch.sh').write_text('changed')
else:
 assert not (p/'runtime/governor').exists() and not (p/'runtime/controller').exists(),'stale launch options'
 print('C45_LAUNCHER_PRESENT phase=return serial=8');print('C45_LAUNCHER_EXIT action=port-cycle-done');action='port-cycle-done'
(p/'runtime/action').write_text(action+'\\n');(p/'runtime/action').chmod(0o600)
''');frontend.chmod(0o700)
 core=d/'muxretro';core.write_text('''#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(__file__).parent
with (p/'calls').open('a') as f:f.write('core\\n')
if p.name=='app_failure_return':sys.exit(9)
print('C44_FIRST_PRESENT seconds=30 serial=7');print('C44_NORMAL_EXIT expired=1 frames=1800')
''');core.chmod(0o700)
 text=fixture((base/'select.sh').read_text()).replace('/opt/muos/frontend/muxfrontend',str(frontend))
 text='mount() { return 0; };findmnt() { return '+('0' if name=='occupied_mount' else '1')+'; };\n'+text
 (d/'select.sh').write_text(text)
 if name=='duplicate':(d/'selection.once').touch()
 r=subprocess.run(['sh',str(d/'select.sh'),str(d),mode]+(['extra'] if name=='extra_argument' else []),capture_output=True,text=True,timeout=15)
 (d/'stdout').write_text(r.stdout);(d/'stderr').write_text(r.stderr)
 assert (r.returncode!=0 if name=='duplicate' else r.returncode==want),(name,r.returncode,r.stdout,r.stderr)
 calls=(d/'calls').read_text().splitlines() if (d/'calls').exists() else []
 expected=[] if name in ['guard','duplicate','occupied_mount','extra_argument'] else ['dispatch','core','return'] if name in ['normal','app_failure_return'] else ['dispatch']
 assert calls==expected,(name,calls)
 cases.append(name)
report={'passed':True,'build_stage':str(build),'binary_sha256':br['binary_sha256'],'hook_real_AArch64_QEMU':True,'library_binding_passed':True,'coordinator_cases':cases,'native_guard_cases_in_fixture':6,'real_upstream_writer_bytes_verified':True,'upstream_source_sha256':{str(p):sha(p) for p in [writer_source,action_source,reader_source]},'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),*files,repo/'port/diagnostics/phase4-app-selection.h',repo/'port/diagnostics/phase4-app-selection-check.c',repo/'port/device/rk-r35s-p0/launcher-cycle/worker.sh']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C46 hook/binding/coordinator/guards passed:',stage)
