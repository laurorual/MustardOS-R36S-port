#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C93 header and guarded-descriptor tests on synthetic regular ext4 only."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import importlib,json,os,shutil,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_initial_migration as migration
import phase4_p2_initial as adapter
import phase4_recovery_image as image
import phase4_root_recovery as recovery
from phase4_backup_core import sha
prep=importlib.import_module('prepare-phase4-initial-migration')

os.umask(0o077);stage=Path(sys.argv[1]);prior=Path(sys.argv[2]);size=32*1024*1024;cases=[]
def passed(name):cases.append(name);print('C93_PASS_'+name,flush=True)
def reject(name,call):
    try:call()
    except (ValueError,OSError):passed(name)
    else:raise AssertionError(name)
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def make(tree,name):
    target=stage/name
    with target.open('xb') as f:f.truncate(size)
    p=subprocess.run(['mke2fs','-q','-t','ext4','-F','-m','0','-E','no_copy_xattrs','-d',str(tree),str(target)],capture_output=True,timeout=45)
    assert p.returncode==0,p.stderr;return target
# Reuse only C92's tiny synthetic trees, copying before any change. No old
# C92 test is rerun, and no private production key/seed/image is used.
ft=stage/'factory-tree';ot=stage/'observed-tree'
shutil.copytree(prior/'factory-tree',ft,symlinks=True);shutil.copytree(prior/'observed-tree',ot,symlinks=True)
factory=make(ft,'factory.ext4');observed=make(ot,'observed.ext4');fsha,osha=sha(factory),sha(observed)
with image.source_image(observed,osha,size) as fd:source=image.scan(fd,folder('source-scan'))
backup=deepcopy(source['private_files']);backup[recovery.COUNTER].update({'sha256':recovery.hashed(b'72\n'),'bytes':3})
backup[recovery.CREDIT].update({'sha256':recovery.hashed(b'B'*256),'bytes':256})
attempt=recovery.attempt_record(backup,72,'a'*64,'b'*64,74,'c'*32)
physical={'schema':86,'operation':'postboot','attempt_sha256':recovery.hashed(recovery.encoded(attempt)),
    'mbr_sha256':'1'*64,'boot_prefix_16MiB_sha256':'2'*64,'automount_guard_sha256':'3'*64,
    'backup_private_files':backup,'backup_counter':72,'backup_prefix_sha256':'a'*64,'reference_root_sha256':'4'*64}
held={'next_attempt_id':attempt['attempt_id'],'next_attempt_sha256':physical['attempt_sha256']}
native={'operation':'postboot','boot_sequence':75,'context_sha256':recovery.hashed(recovery.encoded(physical))}
prep.freshness(held,physical,attempt,native,75);passed('current-fence-and-qualified-boot75-bound')
next_boot=dict(native,boot_sequence=76);prep.freshness(held,physical,attempt,next_boot,75);passed('newer-capture-after-user-reboot-accepted')
for name,change in [('older-fence',lambda h,c,a,n,k:h.update({'next_attempt_sha256':'d'*64})),
    ('wrong-attempt-id',lambda h,c,a,n,k:a.update({'attempt_id':'d'*32})),
    ('reference-context',lambda h,c,a,n,k:c.update({'operation':'reference'})),
    ('reference-receipt',lambda h,c,a,n,k:n.update({'operation':'reference'})),
    ('stale-capture73',lambda h,c,a,n,k:n.update({'boot_sequence':73})),
    ('boolean-counter',lambda h,c,a,n,k:n.update({'boot_sequence':True})),
    ('exhausted-counter',lambda h,c,a,n,k:n.update({'boot_sequence':9999})),
    ('context-hash-tamper',lambda h,c,a,n,k:n.update({'context_sha256':'d'*64})),
    ('invalid-fence-digest',lambda h,c,a,n,k:c.update({'attempt_sha256':'bad'}))]:
    h,c,a,n=map(deepcopy,[held,physical,attempt,native]);change(h,c,a,n,75)
    reject(name,lambda h=h,c=c,a=a,n=n:prep.freshness(h,c,a,n,75))
reject('qualified-boot-not-first-after-current-fence',lambda:prep.freshness(held,physical,attempt,native,76))
leaf=stage/'backup-metadata.json';data=b'{"synthetic":true}\n';leaf.write_bytes(data);leaf.chmod(0o600)
assert prep.verified_file(leaf,recovery.hashed(data))==data
assert prep.verified_file(leaf,recovery.hashed(data),len(data)) is None
passed('existing-private-backup-bytes-and-metadata-readback-verified')
reject('backup-hash-mismatch',lambda:prep.verified_file(leaf,'0'*64))
reject('backup-size-mismatch',lambda:prep.verified_file(leaf,recovery.hashed(data),len(data)+1))
reject('backup-boolean-size',lambda:prep.verified_file(leaf,recovery.hashed(data),True))
leaf.chmod(0o644);reject('backup-public-mode',lambda:prep.verified_file(leaf,recovery.hashed(data)));leaf.chmod(0o600)
link=stage/'backup-symlink';link.symlink_to(leaf)
reject('backup-symlink',lambda:prep.verified_file(link,recovery.hashed(data)))
alias=stage/'backup-hardlink';os.link(leaf,alias)
reject('backup-hardlink',lambda:prep.verified_file(leaf,recovery.hashed(data)));alias.unlink()
context={'schema':85,'attempt_id':attempt['attempt_id'],'attempt_sha256':physical['attempt_sha256'],
    'root_sha256':osha,'root_bytes':size,'cid_sha256':recovery.DECK_CID,'capacity_sectors':recovery.CAPACITY,
    'offline':True,'all_namespaces_unmounted':True,'alias_cache_synchronized':True,'captured_after_handoff':True}
composition=folder('composition')
result=migration.compose(factory,fsha,observed,osha,size,composition,backup,72,'a'*64,attempt,context,rng=lambda n,f:bytes(range(256)))
candidate=composition/'candidate.ext4';csha=result['candidate_sha256'];fd=os.open(candidate,os.O_RDONLY)
def validate(name,**changes):
    args={'source':fd,'candidate_sha256':csha,'factory':factory,'factory_sha256':fsha,
        'current':observed,'current_sha256':osha,'image_bytes':size,'stage':folder(name),
        'backup_rows':backup,'backup_counter':72,'prefix_sha256':'a'*64,'attempt':attempt,'context':context}
    args.update(changes);return adapter.validate_fd(**args)
try:
    plan=validate('valid');assert plan['recovery_counter']==76 and plan['next_C07_counter']==77
    os.fstat(fd);passed('three-real-FD-scans-derive-counter76-and-preserve-caller-descriptor')
    for name,changes in [('candidate-hash',{'candidate_sha256':'0'*64}),('factory-hash',{'factory_sha256':'0'*64}),
        ('current-hash',{'current_sha256':'0'*64}),('candidate-size',{'image_bytes':size+1})]:
        reject(name,lambda name=name,changes=changes:validate('bad-'+name,**changes))
    candidate.chmod(0o644);reject('public-candidate-mode',lambda:validate('bad-mode'));candidate.chmod(0o600)
    alias=stage/'candidate-hardlink';os.link(candidate,alias)
    reject('candidate-hardlink',lambda:validate('bad-hardlink'));alias.unlink()
    link=stage/'current-symlink';link.symlink_to(observed)
    reject('current-symlink',lambda:validate('bad-symlink',current=link))
    reader,writer=os.pipe()
    try:reject('nonregular-candidate-descriptor',lambda:validate('bad-pipe',source=reader))
    finally:os.close(reader);os.close(writer)
    before=candidate.stat();scan=image.scan
    def change_metadata(source,*args,**kwargs):
        value=scan(source,*args,**kwargs)
        if source==fd:os.utime(candidate,ns=(1,2))
        return value
    with patch.object(image,'scan',change_metadata):reject('candidate-changed-during-descriptor-scan',lambda:validate('bad-race'))
    os.utime(candidate,ns=(before.st_atime_ns,before.st_mtime_ns))
finally:os.close(fd)
assert sha(factory)==fsha and sha(observed)==osha and sha(candidate)==csha;passed('all-regular-source-bytes-preserved')
for path in stage.rglob('*.ext4'):path.unlink()
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'synthetic_32MiB_ext4_only':True,'root_block_controller_or_entrypoint_executed':False})+'\n')
