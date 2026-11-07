#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 finite package/context/copy faults; no device, sudo, network or mount."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,importlib,json,os,tempfile,types
import phase4_root_recovery as recovery
import phase4_root_migration as policy
import phase4_recovery_image as image
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-recovery';os.umask(0o077)
area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='entry-checks.',dir=area));cases=[]
helper=importlib.import_module('phase4-p2-recover');capture=importlib.import_module('phase4-physical-capture')
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)
rows={n:{'sha256':recovery.hashed(b'72\n' if n==recovery.COUNTER else b'x'*64),
    'bytes':3 if n==recovery.COUNTER else 64,'mode':0o400 if n==recovery.CREDIT else 0o644 if n.startswith('etc/') else 0o600,
    'uid':0,'gid':0,'links':1} for n in recovery.PRIVATE_FILES}
physical={'schema':86,'operation':'postboot','mbr_sha256':'1'*64,'boot_prefix_16MiB_sha256':'2'*64,
    'automount_guard_sha256':'3'*64,'backup_private_files':rows,'backup_counter':72,'backup_prefix_sha256':'4'*64,
    'reference_root_sha256':'5'*64,'attempt_sha256':'6'*64}
artifacts={n:{'sha256':'7'*64,'bytes':size} for n,size in [('prefix.backup',640*1024*1024),('boot.fat',100*1024*1024),
    ('root.ext4',policy.ROOT_BYTES),('private-files.json',1000),('userdata.tar',61440),('userdata-manifest.json',1000)]}
artifacts['prefix.backup']['sha256']=physical['backup_prefix_sha256']
ctx={'schema':89,'operation':'recover-p2-only','physical_capture':physical,
    'backup_directory':'/var/tmp/muos-r35s-c81-backup.abcdefgh','backup_receipt_sha256':'8'*64,'backup_artifacts':artifacts,
    'host_backup_ack_sha256':'9'*64,'recovery_file':'/home/deck/muos-r35s-c89-recovery.abcdefgh/recovery.ext4',
    'recovery_sha256':'a'*64,'expected_observed_sha256':'b'*64,'expected_recovery_counter':74,'next_attempt_id':'c'*32,'qualified_kernel':'fixture-kernel'}
helper.validate_context(ctx,capture,policy,recovery);cases.append('finite-recovery-context-binds-C86-and-C82')
for name,key,value in [('factory-mode','operation','apply-factory'),('wrong-schema','schema',88),
    ('other-backup','backup_directory','/tmp/backup'),('other-source','recovery_file','/dev/mmcblk0'),
    ('C88-initial-candidate','recovery_file','/home/deck/muos-r35s-c88-candidate.abcdefgh/candidate.ext4'),
    ('bad-image-hash','recovery_sha256','bad'),('bad-counter','expected_recovery_counter',True),
    ('counter-overflow','expected_recovery_counter',9999),('bad-fence-id','next_attempt_id','x'*32),('missing-kernel-binding','qualified_kernel','')]:
    bad=deepcopy(ctx);bad[key]=value;reject(name,lambda bad=bad:helper.validate_context(bad,capture,policy,recovery))
for name,change in [('reference-instead-of-postboot',lambda x:x['physical_capture'].update({'operation':'reference'})),
    ('bad-prefix-binding',lambda x:x['backup_artifacts']['prefix.backup'].update({'sha256':'0'*64})),
    ('wrong-p2-size',lambda x:x['backup_artifacts']['root.ext4'].update({'bytes':True})),
    ('unknown-backup-leaf',lambda x:x['backup_artifacts'].update({'../other':{'sha256':'0'*64,'bytes':10}}))]:
    bad=deepcopy(ctx);change(bad);reject(name,lambda bad=bad:helper.validate_context(bad,capture,policy,recovery))
reject('internal-entrypoint-not-from-protected-run-snapshot',helper.operation)

source_dir=stage/'source';source_dir.mkdir(mode=0o700);source=source_dir/'input.ext4'
with source.open('xb') as out:out.truncate(32*1024*1024);out.seek(1024);out.write(b'regular-copy-fixture')
source.chmod(0o600);expected=sha(source);account=types.SimpleNamespace(pw_uid=os.getuid())
core=importlib.import_module('phase4_backup_core');output=stage/'copied.ext4'
helper.copy_image(source,expected,output,account,core,image,32*1024*1024)
assert sha(output)==expected==sha(source);cases.append('real-private-32MiB-sparse-copy-fsync-readback-source-preserved')
reject('existing-root-snapshot-never-overwritten',lambda:helper.copy_image(source,expected,output,account,core,image,32*1024*1024))
reject('source-wrong-size',lambda:helper.copy_image(source,expected,stage/'wrong-size.ext4',account,core,image,512*1024*1024))
reject('source-wrong-hash',lambda:helper.copy_image(source,'0'*64,stage/'wrong-sha.ext4',account,core,image,32*1024*1024))
source.chmod(0o644);reject('source-public-mode-refused',lambda:helper.copy_image(source,expected,stage/'bad-mode.ext4',account,core,image,32*1024*1024));source.chmod(0o600)
link=source_dir/'alias.ext4';link.symlink_to(source)
reject('source-symlink-refused',lambda:helper.copy_image(link,expected,stage/'link.ext4',account,core,image,32*1024*1024))
os.link(source,source_dir/'hard.ext4')
reject('source-hardlink-refused',lambda:helper.copy_image(source,expected,stage/'hard.ext4',account,core,image,32*1024*1024));(source_dir/'hard.ext4').unlink()
original=image.sparse_clone
def mutate(source_fd,out,size):original(source_fd,out,size);os.utime(source,ns=(1,2))
with patch.object(image,'sparse_clone',mutate):
    reject('source-metadata-changed-during-seal',lambda:helper.copy_image(source,expected,stage/'changed.ext4',account,core,image,32*1024*1024))

bundle=stage/'bundle';bundle.mkdir(mode=0o700)
for n in helper.SOURCES:(bundle/n).write_bytes(b'fixture-not-code')
manifest={'operation':'recover-p2-only','files':{n:sha(bundle/n) for n in helper.SOURCES}}
(bundle/'package.json').write_text(json.dumps(manifest));roots=[];executed=[];original_read=Path.read_text;mkdtemp=tempfile.mkdtemp
def read(p,*a,**kw):return 'Jupiter' if str(p)=='/sys/class/dmi/id/product_name' else original_read(p,*a,**kw)
def make_root(**kw):p=Path(mkdtemp(prefix='sealed.',dir=stage));roots.append(p);return str(p)
class ExecStopped(Exception):pass
def execute(*args):executed.append(args);raise ExecStopped()
with patch.object(helper,'__file__',str(bundle/'phase4-p2-recover.py')),patch.object(helper.os,'geteuid',return_value=0),patch.object(helper.platform,'machine',return_value='x86_64'),patch.object(Path,'read_text',read),patch.object(helper.tempfile,'mkdtemp',make_root),patch.object(helper.os,'execve',execute):
    try:helper.bootstrap()
    except ExecStopped:pass
    assert executed[0][1][-1]=='_recover' and executed[0][2]['PYTHONDONTWRITEBYTECODE']=='1'
    assert {p.name for p in roots[-1].iterdir()}==helper.SOURCES and all(p.stat().st_mode&0o777==0o400 for p in roots[-1].iterdir())
    cases.append('bootstrap-sealed-exact-payload-and-clean-env')
    manifest['operation']='apply-initial';(bundle/'package.json').write_text(json.dumps(manifest));reject('bootstrap-no-initial-migration-mode',helper.bootstrap)
    manifest['operation']='recover-p2-only';(bundle/'package.json').write_text(json.dumps(manifest));(bundle/'attempt.json').write_bytes(b'tampered')
    reject('bootstrap-prior-fence-hash-changed',helper.bootstrap)
for p in stage.glob('*.ext4'):p.unlink()
source.unlink()
sources=[Path(__file__),repo/'port/scripts/phase4-p2-recover.py',repo/'port/scripts/phase4_p2_recovery.py']
for p in sources:ast.parse(p.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'root_entrypoint_IO_guarded_and_not_executed':True,
    'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-entry-checks').write_text(str(stage)+'\n');print('C89 entry:',len(cases),'checks passed:',stage)
