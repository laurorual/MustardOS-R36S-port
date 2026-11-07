#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C10 recipe/post-overlay tests, path guards, atomic rollback and determinism."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'runtime-profile'
base=Path((area/'latest-profile').read_text().strip());stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Independent regeneration must produce the same public payload bytes.
r=subprocess.run([sys.executable,str(repo/'port/scripts/prepare-phase4-runtime-profile.py')],capture_output=True,text=True,check=True)
repeat=Path((area/'latest-profile').read_text().strip())
def tree(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
assert tree(base/'source')==tree(repeat/'source');cases={'deterministic-regeneration':True}
source=stage/'recipe-source';shutil.copytree(base/'source',source);target=stage/'recipe-target';target.mkdir()
(target/'opt/muos/device/config/board').mkdir(parents=True);(target/'opt/muos/device/config/board/name').write_text('rk-r35s-p0\n')
# Invoke the REAL install macro, without building unrelated dependency packages.
harness=stage/'recipe.mk';harness.write_text('TARGET_DIR := /work/'+str(target.relative_to(work))+'\nINSTALL := install\ngeneric-package =\ninclude /port/buildroot/package/muos-r35s-profile/muos-r35s-profile.mk\n/work/'+str((source/'.installed').relative_to(work))+':\n\t$(MUOS_R35S_PROFILE_INSTALL_TARGET_CMDS)\n\ttouch $@\n')
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'make','-f','/work/'+str(harness.relative_to(work))]
r=subprocess.run(args,capture_output=True,text=True,timeout=30);(stage/'recipe.stdout').write_text(r.stdout);(stage/'recipe.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
cases['actual-install-macro']=True
# Simulate the LATER generic overlay restoring the old defaults.
(target/'etc/default').mkdir(parents=True);(target/'etc/default/muos-core').write_text('audio=0\ninput=1\n');(target/'etc/default/muos-ui').write_text('enabled=0\nhotkeys=0\n')
apply=repo/'port/scripts/apply-phase4-runtime-profile.py';hook=repo/'port/scripts/phase4-runtime-post-build.sh'
r=subprocess.run([str(hook),str(target)],capture_output=True,text=True);(stage/'post-hook.stdout').write_text(r.stdout);(stage/'post-hook.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
assert (target/'etc/default/muos-core').read_text()=='audio=1\ninput=1\naudio_quantum=1024\n' and (target/'etc/default/muos-ui').read_text()=='enabled=0\nhotkeys=1\n'
profile_files=json.loads((target/'usr/share/muos-r35s-profile/manifest.json').read_text())['files'];assert all(sha(target/n)==v['sha256'] for n,v in profile_files.items());cases['post-overlay-applies-profile-ui-disabled']=True
before=tree(target);subprocess.run([str(hook),str(target)],capture_output=True,check=True);assert tree(target)==before;cases['idempotent-apply']=True

def fresh(label):
 p=stage/label;shutil.copytree(target,p)
 # Originals differ from the reviewed payload to make partial writes observable.
 for name in profile_files:(p/name).write_text('fixture-before\n')
 return p

def check_refusal(label,mutate):
 p=fresh(label);mutate(p);before={n:sha(p/n) for n in profile_files if (p/n).is_file() and not (p/n).is_symlink()}
 r=subprocess.run([sys.executable,str(apply),'--target',str(p)],capture_output=True,text=True)
 assert r.returncode!=0,label
 assert all(sha(p/n)==v for n,v in before.items()),label
 cases[label]=True
check_refusal('wrong-board',lambda p:(p/'opt/muos/device/config/board/name').write_text('other-board\n'))
check_refusal('corrupt-payload-before-any-write',lambda p:(p/'usr/share/muos-r35s-profile/overlay/etc/default/muos-core').write_text('corrupt\n'))
def ui_enabled(p):
 payload=p/'usr/share/muos-r35s-profile';f=payload/'overlay/etc/default/muos-ui';f.write_text('enabled=1\nhotkeys=1\n');m=json.loads((payload/'manifest.json').read_text());m['files']['etc/default/muos-ui']['sha256']=sha(f);(payload/'manifest.json').write_text(json.dumps(m))
check_refusal('autostart-refused-even-with-updated-digest',ui_enabled)
def bad_path(p):
 f=p/'usr/share/muos-r35s-profile/manifest.json';m=json.loads(f.read_text());m['files']['../escape']={'sha256':'0'*64,'mode':420};f.write_text(json.dumps(m))
check_refusal('unlisted-path-refused',bad_path)
p=fresh('symlink-parent');outside=stage/'outside';outside.mkdir();(outside/'sentinel').write_text('unchanged');folder=p/'opt/muos/config/settings/general';shutil.rmtree(folder);folder.symlink_to(outside,target_is_directory=True)
before=sha(p/'etc/default/muos-core');r=subprocess.run([sys.executable,str(apply),'--target',str(p)],capture_output=True);assert r.returncode!=0 and sha(p/'etc/default/muos-core')==before and (outside/'sentinel').read_text()=='unchanged';cases['symlink-parent-refused']=True
p=fresh('rollback');before={n:sha(p/n) for n in profile_files}
code='''import os,runpy,sys
real=os.replace
count=0
def replace(src,dst):
 global count
 count+=1
 if count==2:raise OSError('fixture replacement failure')
 return real(src,dst)
os.replace=replace
sys.argv=[sys.argv[1],'--target',sys.argv[2]]
runpy.run_path(sys.argv[0],run_name='__main__')
'''
r=subprocess.run([sys.executable,'-c',code,str(apply),str(p)],capture_output=True,text=True);assert r.returncode!=0 and all(sha(p/n)==v for n,v in before.items());cases['mid-write-failure-rolls-back']=True
report={'passed':True,'cases':cases,'binary_compilation_or_device_access':False,'full_buildroot_dependency_build_performed':False,'base_stage':str(base),'repeat_stage':str(repeat),'target':str(target)}
(stage/'report.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C10 profile recipe/post-overlay checks passed:',stage,len(cases),'cases')
