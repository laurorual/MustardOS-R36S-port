#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 entry/lineage and real ext4 coordination; physical adapters are stubbed."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from types import SimpleNamespace
import importlib,json,os,shutil,stat,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as core
import phase4_root_migration as policy
import phase4_root_recovery as recovery
import phase4_recovery_image as image
import phase4_initial_migration as migration
import phase4_p2_initial as adapter
h=importlib.import_module('phase4-p2-initial')
capture=importlib.import_module('phase4-physical-capture')
shared=importlib.import_module('phase4-p2-recover')
os.umask(0o077);stage=Path(sys.argv[1]);prior=Path(sys.argv[2]);cases=[];size=32*1024*1024
def passed(name):cases.append(name);print('C94_ENTRY_PASS_'+name,flush=True)
def reject(name,call):
    try:call()
    except (ValueError,OSError,KeyError,TypeError):passed(name)
    else:raise AssertionError(name)
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def put(path,value):path.write_bytes(recovery.encoded(value))
def make(tree,name):
    target=stage/name
    with target.open('xb') as f:f.truncate(size)
    result=subprocess.run(['mke2fs','-q','-t','ext4','-F','-m','0','-E','no_copy_xattrs','-d',str(tree),str(target)],capture_output=True,timeout=45)
    assert result.returncode==0,result.stderr;return target
ft=stage/'factory-tree';ot=stage/'observed-tree'
shutil.copytree(prior/'factory-tree',ft,symlinks=True);shutil.copytree(prior/'observed-tree',ot,symlinks=True)
factory=make(ft,'factory.ext4');observed=make(ot,'observed.ext4');fsha,osha=core.sha(factory),core.sha(observed)
with image.source_image(observed,osha,size) as fd:scanned=image.scan(fd,folder('observed-scan'))
backup=deepcopy(scanned['private_files']);backup[recovery.COUNTER].update(sha256=recovery.hashed(b'72\n'),bytes=3)
backup[recovery.CREDIT].update(sha256=recovery.hashed(b'B'*256),bytes=256)
attempt=recovery.attempt_record(backup,72,'a'*64,'b'*64,74,'c'*32)
physical={'schema':86,'operation':'postboot','attempt_sha256':recovery.hashed(recovery.encoded(attempt)),
    'mbr_sha256':'1'*64,'boot_prefix_16MiB_sha256':'2'*64,'automount_guard_sha256':'3'*64,
    'backup_private_files':backup,'backup_counter':72,'backup_prefix_sha256':'a'*64,'reference_root_sha256':'4'*64}
ctx={'schema':94,'operation':'migrate-initial-p2-only','physical_capture':physical,
    'backup_directory':'/var/tmp/muos-r35s-c81-backup.12345678','backup_receipt_sha256':'5'*64,
    'backup_artifacts':{n:{'sha256':'a'*64,'bytes':640*1024*1024 if n=='prefix.backup' else policy.ROOT_BYTES if n=='root.ext4' else 1}
        for n in ['prefix.backup','boot.fat','root.ext4','private-files.json','userdata.tar','userdata-manifest.json']},
    'host_backup_ack_sha256':'6'*64,'factory_file':'/home/deck/muos-r35s-c94-factory.12345678/factory.ext4',
    'factory_sha256':h.C79_FACTORY_SHA256,'candidate_file':'/home/deck/muos-r35s-c94-candidate.12345678/candidate.ext4',
    'candidate_sha256':'7'*64,'expected_observed_sha256':osha,'expected_migration_counter':76,'next_attempt_id':'d'*32,
    'qualified_kernel':'fixture-kernel','recovery_ack_sha256':'8'*64,'recovery_boot_sha256':'9'*64,'known_boot_floor':75}
h.validate_context(ctx,capture,policy,recovery);passed('finite-current-initial-context')
for name,change in [
    ('no-arbitrary-options',lambda c:c.update(extra=True)),('no-recovery-mode',lambda c:c.update(operation='recover-p2-only')),
    ('no-unpinned-factory',lambda c:c.update(factory_sha256='0'*64)),('no-bare-factory-as-candidate',lambda c:c.update(candidate_sha256=h.C79_FACTORY_SHA256)),
    ('no-counter-rewind',lambda c:c.update(expected_migration_counter=75)),('no-boolean-counter',lambda c:c.update(expected_migration_counter=True)),
    ('no-exhausted-counter',lambda c:c.update(expected_migration_counter=9999)),('no-empty-kernel',lambda c:c.update(qualified_kernel='')),
    ('no-foreign-factory-role',lambda c:c.update(factory_file='/dev/mmcblk0p2')),
    ('no-stale-C88-candidate-role',lambda c:c.update(candidate_file='/home/deck/muos-r35s-c88-candidate.12345678/candidate.ext4')),
    ('no-foreign-backup',lambda c:c.update(backup_directory='/tmp/backup')),
    ('no-unknown-backup-leaf',lambda c:c['backup_artifacts'].update({'../evil':{'sha256':'a'*64,'bytes':1}})),
    ('no-prefix-binding-mismatch',lambda c:c['backup_artifacts']['prefix.backup'].update(sha256='b'*64)),
    ('no-truncated-backup',lambda c:c['backup_artifacts']['root.ext4'].update(bytes=1)),
    ('no-invalid-next-fence',lambda c:c.update(next_attempt_id='bad')),
    ('no-reference-capture',lambda c:c['physical_capture'].update(operation='reference'))]:
    bad=deepcopy(ctx);change(bad);reject(name,lambda bad=bad:h.validate_context(bad,capture,policy,recovery))
lineage=folder('lineage')
ack={n:True for n in ['passed','physical_p2_recovery_verified','new_fence_independent_host_copy_verified','all_receipts_and_directory_fsynced']}
ack.update(next_attempt_id=attempt['attempt_id'],next_attempt_sha256=physical['attempt_sha256'])
boot={n:True for n in ['passed','physical_boot_after_recovery_qualified','seedless_start_without_crediting_2048bits_verified',
    'rng_ready_before_new_creditable_seed_and_stop_verified','old_seed_hashes_absent']}
boot.update(boot_sequence=75,recovery_host_copy_sha256=recovery.hashed(recovery.encoded(ack)))
def check_lineage(a=ack,b=boot,c=ctx):
    c=deepcopy(c);put(lineage/'host-recovery-ack.json',a);put(lineage/'host-recovery-boot.json',b)
    c.update(recovery_ack_sha256=core.sha(lineage/'host-recovery-ack.json'),recovery_boot_sha256=core.sha(lineage/'host-recovery-boot.json'))
    h.validate_lineage(c,lineage,attempt,core,recovery)
check_lineage();passed('independent-C89-fence-and-actual-first-boot-required')
for name,change in [('missing-host-copy',lambda a,b:a.update(new_fence_independent_host_copy_verified=False)),
    ('wrong-current-fence',lambda a,b:a.update(next_attempt_sha256='0'*64)),
    ('wrong-boot-ack',lambda a,b:b.update(recovery_host_copy_sha256='0'*64)),
    ('unqualified-boot',lambda a,b:b.update(physical_boot_after_recovery_qualified=False)),
    ('not-first-boot-after-recovery',lambda a,b:b.update(boot_sequence=76)),
    ('old-seed-still-present',lambda a,b:b.update(old_seed_hashes_absent=False)),
    ('credit-before-ready',lambda a,b:b.update(rng_ready_before_new_creditable_seed_and_stop_verified=False))]:
    a,b=deepcopy(ack),deepcopy(boot);change(a,b)
    reject(name,lambda a=a,b=b:check_lineage(a,b))
check_lineage();reject('tampered-lineage-bytes',lambda:h.validate_lineage(ctx,lineage,attempt,core,recovery))

# Real bounded snapshot/bootstrap, with only DMI, /run destination and exec
# replaced. The production entrypoint has no test flag or alternate root.
package=folder('package');product=stage/'product';product.write_text('Jupiter\n')
for name in h.SOURCES:(package/name).write_bytes(('fixture '+name+'\n').encode())
def manifest(op='migrate-initial-p2-only',extra=False):
    files={n:core.sha(package/n) for n in h.SOURCES}
    if extra:files['unknown.py']='0'*64
    put(package/'package.json',{'operation':op,'files':files})
manifest();roots=[]
def mkdtemp(**kw):
    assert kw=={'prefix':'muos-r35s-c94.','dir':'/run'}
    p=folder('snapshot-'+str(len(roots)));roots.append(p);return str(p)
def path(value):return product if str(value)=='/sys/class/dmi/id/product_name' else Path(value)
class ExecReached(Exception):pass
def execve(binary,argv,env):
    assert binary=='/usr/bin/python3' and argv[2]=='_migrate' and set(env)=={'PATH','LC_ALL','PYTHONDONTWRITEBYTECODE'}
    assert Path(argv[1]).parent==roots[-1] and stat.S_IMODE(roots[-1].stat().st_mode)==0o700
    for n in h.SOURCES:assert (roots[-1]/n).read_bytes()==(package/n).read_bytes() and stat.S_IMODE((roots[-1]/n).stat().st_mode)==0o400
    raise ExecReached
with patch.object(h,'__file__',str(package/'phase4-p2-initial.py')),patch.object(h,'Path',path),\
     patch.object(h.tempfile,'mkdtemp',mkdtemp),patch.object(h.os,'execve',execve):
    try:h.bootstrap()
    except ExecReached:passed('protected-snapshot-hashes-private-modes-and-clean-exec')
    else:raise AssertionError('exec not reached')
    with patch.object(h.os,'geteuid',return_value=1000):reject('sudo-required-before-snapshot',h.bootstrap)
    product.write_text('Other\n');reject('Deck-DMI-required',h.bootstrap);product.write_text('Jupiter\n')
    manifest('recover-p2-only');reject('bootstrap-refuses-recovery-mode',h.bootstrap)
    manifest(extra=True);reject('bootstrap-refuses-extra-code',h.bootstrap);manifest()
    leaf=package/'phase4_p2_initial.py';original=leaf.read_bytes()
    leaf.write_bytes(b'tampered');reject('bootstrap-hash-mismatch',h.bootstrap);leaf.write_bytes(original);manifest()
    leaf.chmod(0o666);reject('bootstrap-writable-code',h.bootstrap);leaf.chmod(0o600)
    alias=package/'hardlink';os.link(leaf,alias);reject('bootstrap-hardlink',h.bootstrap);alias.unlink()
    leaf.unlink();leaf.symlink_to(package/'context.json');reject('bootstrap-symlink',h.bootstrap);leaf.unlink();leaf.write_bytes(original)
    leaf.write_bytes(b'x'*(1024*1024+1));manifest();reject('bootstrap-oversize',h.bootstrap);leaf.write_bytes(original);manifest()

# Coordinate actual C92/C93 scans on real ext4 files. Stub ONLY physical card
# IO/identity/controller and remote-backup check. These seams cannot be selected
# by CLI; the production operation always binds the fixed test128 adapters.
scanctx={'schema':85,'attempt_id':attempt['attempt_id'],'attempt_sha256':physical['attempt_sha256'],
    'root_sha256':osha,'root_bytes':size,'cid_sha256':recovery.DECK_CID,'capacity_sectors':recovery.CAPACITY,
    'offline':True,'all_namespaces_unmounted':True,'alias_cache_synchronized':True,'captured_after_handoff':True}
composition=folder('composition')
composed=migration.compose(factory,fsha,observed,osha,size,composition,backup,72,'a'*64,attempt,scanctx,rng=lambda n,f:bytes(range(256)))
testctx=deepcopy(ctx);testctx.update(factory_file=str(factory),factory_sha256=fsha,candidate_file=str(composition/'candidate.ext4'),candidate_sha256=composed['candidate_sha256'])
txroot=folder('transaction-root')
for n in h.SOURCES:(txroot/n).write_text('synthetic package leaf '+n+'\n')
events=[];failure=None
class FileController:
    def protected(self,fd):events.append('protected-complement');return ('1'*64,'2'*64)
    def apply(self,fd,wanted,current,protected,validate):
        events.append('callback');validate(fd);events.append('validated')
        if failure=='write':raise OSError('one simulated write failure')
        assert wanted==core.sha(composition/'candidate.ext4') and current==osha
        events.append('write');return {'passed':True}
def physical_capture(guard,core,policy,recovery,image,context,action,where,fence):
    events.append('capture');shutil.copyfile(observed,where/'root.ext4');(where/'root.ext4').chmod(0o600)
    put(where/'capture-context.json',scanctx)
    return {'root_sha256':osha if failure!='capture' else '0'*64,'boot_sequence':75}
fakecapture=SimpleNamespace(capture=physical_capture,verify_ro=lambda *a:events.append('verify-RO'),protect_aliases=lambda *a:events.append('final-RO'))
fakeguard=SimpleNamespace(open_card=lambda:os.open(observed,os.O_RDONLY))
fakepolicy=SimpleNamespace(ROOT_BYTES=size,ROOT_OFFSET=0)
def copy_image(path,wanted,dest,account,core,image,size):
    events.append('copy-'+dest.stem);return shared.copy_image(path,wanted,dest,account,core,image,size)
def check_backup(*args):
    events.append('backup')
    if failure=='backup':raise ValueError('changed remote backup')
fakeshared=SimpleNamespace(copy_image=copy_image,check_backup=check_backup)
target=SimpleNamespace(card_target=lambda *a:FileController())
account=SimpleNamespace(pw_uid=os.getuid(),pw_gid=os.getgid())
def transaction(where):return h.transaction(txroot,where,testctx,attempt,account,core,fakepolicy,recovery,image,target,adapter,fakecapture,fakeguard,fakeshared)
success=folder('transaction-success');result=transaction(success)
assert events.index('backup')<events.index('capture')<events.index('callback')<events.index('validated')<events.index('write')<events.index('final-RO')
assert result['schema']==94 and result['migration_counter']==76 and result['boot_handoff_authorized'] is False
fence=recovery.load_attempt(success/'handoff',testctx['next_attempt_id'],result['next_attempt_sha256'])
assert fence['candidate_root_sha256']==composed['candidate_sha256'] and fence['counter_floor']==76
assert result['source_sha256']=={n:core.sha(txroot/n) for n in h.SOURCES};passed('real-three-image-scans-before-simulated-write-and-new-fence-after')
for reason in ['backup','capture','counter','write']:
    failure=reason;events.clear();where=folder('transaction-failure-'+reason)
    if reason=='counter':testctx['expected_migration_counter']=77
    reject('transaction-'+reason+'-failure-no-completion-or-fence',lambda where=where:transaction(where))
    assert not (where/'analysis.json').exists() and not (where/'handoff').exists()
    assert 'write' not in events
    testctx['expected_migration_counter']=76
failure=None;events.clear();where=folder('transaction-fence-failure')
with patch.object(recovery,'seal_attempt',side_effect=OSError('fence sync failed')):
    reject('post-write-fence-failure-is-not-success',lambda:transaction(where))
assert 'write' in events and not (where/'analysis.json').exists()
assert core.sha(factory)==fsha and core.sha(observed)==osha;passed('original-regular-source-images-preserved')
for p in stage.rglob('*.ext4'):p.unlink()
put(stage/'fixture-results.json',{'passed':True,'case_count':len(cases),'cases':cases,'real_32MiB_ext4_fixtures':True,
    'privileged_operation_namespace_and_physical_adapters_executed':False,'transaction_body_executed_with_stubbed_card':True})
