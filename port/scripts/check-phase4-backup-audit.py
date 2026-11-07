#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Focused C82 diagnostic checks; synthetic files, existing container, no devices."""
from pathlib import Path
import ast,importlib.util,json,os,shutil,subprocess,tempfile
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'offline-backup'
stage=Path(tempfile.mkdtemp(prefix='audit-checks.',dir=area));cases=[]
spec=importlib.util.spec_from_file_location('audit',repo/'port/scripts/audit-phase4-backup-private.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def reject(name,call):
    try:call()
    except (ValueError,OSError):cases.append(name)
    else:raise AssertionError(name)
for value in ['/dev/mmcblk0','/var/tmp/muos-r35s-c81-backup.12345678/../foreign','/var/tmp/muos-r35s-c81-backup.bad;reboot']:
    reject('refuse-non-partial-path-'+str(len(cases)),lambda:a.partial_path(value))
assert a.partial_path('/var/tmp/muos-r35s-c81-backup.12345678').name.endswith('12345678');cases.append('exact-partial-path')
bundle=stage/'package';bundle.mkdir(mode=0o700)
prior=Path((area/'latest-package').read_text().strip())/'bundle'
for name in a.ALLOWED:
    src=repo/'port/scripts'/name if name=='audit-phase4-backup-private.py' else prior/name
    shutil.copyfile(src,bundle/name);(bundle/name).chmod(0o600)
manifest={'diagnostic_only':True,'files':{n:sha(bundle/n) for n in a.ALLOWED}}
(bundle/'package.json').write_text(json.dumps(manifest))
snapshot=stage/'snapshot';snapshot.mkdir(mode=0o700);a.snapshot_package(bundle,snapshot)
assert all(sha(snapshot/n)==h for n,h in manifest['files'].items());cases.append('snapshot-hashes-and-copy')
leaf=bundle/'phase4_backup_core.py';data=leaf.read_bytes();leaf.write_bytes(data+b'corrupt')
destination=stage/'bad-snapshot';destination.mkdir(mode=0o700)
reject('snapshot-rejects-corrupted-source',lambda:a.snapshot_package(bundle,destination));leaf.write_bytes(data)
leaf.unlink();leaf.symlink_to(prior/'phase4_backup_core.py')
destination=stage/'link-snapshot';destination.mkdir(mode=0o700)
reject('snapshot-rejects-source-symlink',lambda:a.snapshot_package(bundle,destination))
fixture=r'''
from pathlib import Path
import importlib.util,json,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as c
from phase4_root_migration import PRIVATE_FILES,OPTIONAL_PRIVATE
spec=importlib.util.spec_from_file_location('audit','/port/scripts/audit-phase4-backup-private.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
stage=Path(sys.argv[1]);old=Path(sys.argv[2]);partial=stage/'partial';partial.mkdir(mode=0o700)
shutil.copyfile(old/'fixture.ext4',partial/'root.ext4')
with (partial/'root.ext4').open('r+b') as f:f.truncate(512*1024*1024)
rows={}
for name in PRIVATE_FILES|OPTIONAL_PRIVATE:
 p=old/'tree'/name
 rows[name]={'mode':p.stat().st_mode&0o777,'uid':0,'gid':0,'links':1,'bytes':p.stat().st_size,'sha256':c.sha(p)}
plan={'survey_boot_sequence':72,'private_files_at_live_survey':rows}
def run(args):
 assert args[0]=='debugfs' and args[-1]==str(partial/'root.ext4')
 r=subprocess.run(args,capture_output=True,text=True,timeout=20);assert r.returncode==0;return r
before=c.sha(partial/'root.ext4')
for kind in ['same','new-boot','changed-key']:
 target=stage/kind;target.mkdir(mode=0o700)
 current=json.loads(json.dumps(plan))
 if kind=='new-boot':current['survey_boot_sequence']=73
 if kind=='changed-key':current['private_files_at_live_survey']['var/lib/muos-network/dropbear_ed25519_host_key']['sha256']='0'*64
 result=a.probe(partial,current,c,run,target)
 assert result['parents']['/var/lib']['mode']==0o755 and result['parents']['/var/lib/muos-network']['mode']==0o700
 assert result['offline_boot']==72 and not result['backup_qualified'] and not result['device_opened']
 if kind=='same':assert result['private_extraction_passed'] and result['refusal'] is None
 if kind=='new-boot':assert not result['same_boot'] and result['refusal']=='Boot changed; new survey required'
 if kind=='changed-key':assert result['refusal']=='Private network/key identity changed'
 assert 'S'*64 not in json.dumps(result) and all(v['sha256'] not in json.dumps(result) for v in rows.values())
 print('C82_AUDIT_PASS_'+kind)
assert c.sha(partial/'root.ext4')==before
print('C82_AUDIT_PASS_source-unchanged-and-no-private-output')
'''
(stage/'fixture.py').write_text(fixture)
container=(work/'rootfs-container.iid').read_text().strip()
old=area/'checks.y1i3sznc';assert (old/'fixture.ext4').is_file()
rel=lambda p:'/work/'+str(p.relative_to(work))
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0',
 '--tmpfs','/tmp:rw,nosuid,nodev,size=64m','-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',rel(stage/'fixture.py'),rel(stage),rel(old)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:(stage/('fixture.'+ext)).write_text(data)
assert r.returncode==0,(stage,r.stderr[-1500:])
passed=[line for line in r.stdout.splitlines() if line.startswith('C82_AUDIT_PASS_')];assert len(passed)==4;cases.extend(passed)
ast.parse(Path(a.__file__).read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),Path(a.__file__)]},'physical_device_opened':False},indent=2)+'\n')
(area/'latest-audit-checks').write_text(str(stage)+'\n')
print('C82 partial audit:',len(cases),'checks passed:',stage)

if __name__=='__main__':pass
