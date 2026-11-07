#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C76 exact-scope additive install/failure/rollback fixtures, no block devices."""
from pathlib import Path
import ast, json, subprocess
from phase4_candidate import sha
from phase4_gambatte_install import context, AREA, REPO, WORK, NATIVE

context()
stage=Path((AREA/'latest-plan').read_text().strip())
plan=json.loads((stage/'plan.json').read_text())
for n,h in plan['source_sha256'].items():assert sha(REPO/n)==h,n
checks=stage/'checks';checks.mkdir()
parent=REPO/'port/scripts/check-phase4-muxretro-install.py'
assert parent.read_bytes()==(REPO/'dist/phase4/muxretro-installed/source'/parent.relative_to(REPO)).read_bytes()
node=next(n for n in ast.parse(parent.read_text()).body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='script' for t in n.targets))
script=ast.literal_eval(node.value).replace('c62','c76').replace('C62','C76')
script=script.replace('/muxretro-install/','/gambatte-install/')
script=script.replace('opt/muos/frontend/muxretro','opt/muos/share/core/gambatte_libretro.so')
script=script.replace('opt/muos/frontend','opt/muos/share')
script=script.replace('usr/share/muos-muxretro','usr/share/muos-gambatte')
script=script.replace('provenance.json','license-review.json')
script=script.replace('[ "$files" = 13 ]','[ "$files" = 9 ]')
assert script.count('for pos in $(seq 1 13); do')==2
script=script.replace('for pos in $(seq 1 13); do','for pos in $(seq 1 8); do',1)
script=script.replace('for pos in $(seq 1 13); do','for pos in $(seq 1 9); do',1)
old='reset;printf collision > "$install_root/opt/muos/share/core/gambatte_libretro.so.c76-new"'
assert script.count(old)==1
script=script.replace(old,'reset;printf collision > "$install_root/opt/muos/share/core.c76-new"')
script=script.replace('chmod 600 "$install_payload/new/opt/muos/share/core/gambatte_libretro.so"',
                      'chmod 755 "$install_payload/new/opt/muos/share/core/gambatte_libretro.so"')
script=script.replace('executable_mode_required','shared_library_mode_0644_required')
script+='''
# The core tree is a third owned root, and must protect its neighbors too.
reset;c76_apply;printf unexpected > "$install_root/opt/muos/share/core/neighbor"
snapshot >/tmp/c76-before;install_rw=1
if c76_rollback;then exit 1;fi
snapshot >/tmp/c76-after;cmp /tmp/c76-before /tmp/c76-after;pass rollback_preserves_core_neighbor
reset;c76_apply;mkdir "$install_root/opt/muos/share/core/empty-neighbor"
snapshot >/tmp/c76-before;install_rw=1
if c76_rollback;then exit 1;fi
snapshot >/tmp/c76-after;cmp /tmp/c76-before /tmp/c76-after;pass rollback_preserves_core_empty_directory
'''
(checks/'fixtures.sh').write_text(script)
for source in NATIVE.glob('*.sh'):subprocess.run(['sh','-n',str(source)],check=True)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=128m',
 '-v',f'{WORK}:/work:ro,z','-v',f'{REPO}/port:/port:ro,z',
 '-e','PREPARED=/work/'+str(stage.relative_to(WORK)),
 '-e','SYSROOT=/work/save-store-image/image.nlnmgzzb/target',
 (WORK/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',script]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for ext,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (checks/ext).write_text(v)
assert r.returncode==0,(checks,r.stdout[-1500:],r.stderr[-2000:])
cases=[line for line in r.stdout.splitlines() if line.startswith('C76_PASS_')]
assert len(cases)==50,len(cases)
sources=[Path(__file__),REPO/'port/scripts/phase4_gambatte_install.py',*NATIVE.glob('*.sh')]
report={'passed':True,'experiment':'C76_GAMBATTE_INSTALL_FIXTURES','plan_sha256':sha(stage/'plan.json'),
 'case_count':len(cases),'cases':cases,'device_written':False,'ROM_or_core_executed':False,
 'source_sha256':{str(n.relative_to(REPO)):sha(n) for n in sources}}
(checks/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print('C76 additive install/failure/rollback fixtures passed:',len(cases),checks)
