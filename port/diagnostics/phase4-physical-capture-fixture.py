#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 copy/scan protocol with a synthetic regular descriptor, not a block."""
from pathlib import Path
from unittest.mock import patch
import importlib.util,json,os,shutil,struct,subprocess,sys,types
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as core
import phase4_root_migration as policy
import phase4_root_recovery as recovery
import phase4_recovery_image as image
os.umask(0o077);stage=Path(sys.argv[1]);fixtures=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location('helper','/port/scripts/phase4-physical-capture.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def passed(n):print('C86_PASS_'+n,flush=True)
def reject(n,fn):
    try:fn()
    except (ValueError,RuntimeError,OSError):passed(n)
    else:raise AssertionError(n)
def folder(n):p=stage/n;p.mkdir(mode=0o700);return p
reference=stage/'reference.ext4';shutil.copyfile(fixtures/'backup.ext4',reference)
p=subprocess.run(['debugfs','-w','-R','set_inode_field <2> mode 040755',str(reference)],capture_output=True);assert p.returncode==0
with image.source_image(reference,core.sha(reference),32*1024*1024) as fd:base=image.scan(fd,folder('baseline'))
original_hash=core.sha(reference);observed=fixtures/'observed.ext4'
toy=types.SimpleNamespace(**{n:getattr(policy,n) for n in ['digest','geometry','ROOT_OFFSET','DECK_CID','CAPACITY']},ROOT_BYTES=32*1024*1024)
card=stage/'fake-card.regular';mbr=bytearray(512);struct.pack_into('<I',mbr,440,0x4d554432);mbr[510:]=b'\x55\xaa'
for i,row in enumerate([(0x80,0x0c,32768,204800),(0,0x83,262144,1048576),(0,0x83,1310720,248561664)]):struct.pack_into('<B3xB3xII',mbr,446+i*16,*row)
with card.open('xb') as f:f.write(mbr);f.truncate(toy.ROOT_OFFSET+toy.ROOT_BYTES)
def populate(source):
    fd=os.open(card,os.O_RDWR)
    try:
        with source.open('rb') as f:
            offset=toy.ROOT_OFFSET
            while data:=f.read(1024*1024):assert os.pwrite(fd,data,offset)==len(data);offset+=len(data)
        os.fsync(fd)
    finally:os.close(fd)
populate(reference)
fd=os.open(card,os.O_RDONLY)
try:prefix=core.region_sha(fd,0,16*1024*1024)
finally:os.close(fd)
ctx={'schema':86,'operation':'reference','mbr_sha256':recovery.hashed(mbr),'boot_prefix_16MiB_sha256':prefix,
    'automount_guard_sha256':'3'*64,'backup_private_files':base['private_files'],'backup_counter':72,
    'backup_prefix_sha256':'4'*64,'reference_root_sha256':original_hash}
events=[];guard=types.SimpleNamespace(identity=lambda:events.append('identity'),open_card=lambda:events.append('open-readonly') or os.open(card,os.O_RDONLY))
def protect(*a):events.append('RO-before-copy')
def verify(*a):events.append('RO-verified');guard.identity()
def capture(action,dest,context=ctx,attempt=None):
    with patch.object(helper,'protect_aliases',protect),patch.object(helper,'verify_ro',verify),patch.object(helper,'read_protection',side_effect=lambda *a:guard.identity()):
        return helper.capture(guard,core,toy,recovery,image,context,action,dest,attempt)
snapshot=folder('reference-capture')
with patch.object(os,'getrandom',side_effect=AssertionError('must not generate/load entropy')):result=capture('reference',snapshot)
assert result['root_sha256']==original_hash and result['boot_sequence']==72 and result['physical_postboot_capture'] is False
assert not (snapshot/'capture-context.json').exists() and not (snapshot/'observation.json').exists()
assert events.index('RO-before-copy')<events.index('open-readonly') and core.sha(snapshot/'root.ext4')==original_hash
passed('reference-fixed-p2-copy-and-real-ext4-scan')
passed('reference-never-claims-postboot-or-generates-seed')
passed('RO-gate-before-opening-source-and-readonly-source-descriptor')
fence=recovery.attempt_record(base['private_files'],72,'4'*64,'5'*64,72,'b'*32)
post={**ctx,'operation':'postboot','attempt_sha256':recovery.hashed(recovery.encoded(fence))}
populate(observed);snapshot=folder('postboot-capture');result=capture('postboot',snapshot,post,fence)
physical=json.loads((snapshot/'capture-context.json').read_text());obs=json.loads((snapshot/'observation.json').read_text())
assert result['physical_postboot_capture'] is True and result['boot_sequence']==75 and obs['boot_sequence']==75
assert physical['root_sha256']==core.sha(observed) and physical['root_bytes']==toy.ROOT_BYTES
assert physical['attempt_sha256']==post['attempt_sha256']
passed('postboot-context-derived-from-copied-image-and-sealed-intent')
passed('postboot-observed-counter-derived-from-source75')
plan=recovery.recovery_plan(base['private_files'],72,'4'*64,fence,obs);assert plan['recovery_counter']==76
passed('physical-protocol-output-consumed-by-C84-policy')
populate(reference)
dest=folder('copy-failed')
with patch.object(core,'copy_region',side_effect=OSError('fixture short write')):reject('copy-failure-no-context-publication',lambda:capture('reference',dest))
assert not list(dest.iterdir())
dest=folder('scan-failed')
with patch.object(image,'scan',side_effect=ValueError('fixture fsck nonzero')):reject('fsck-failure-no-context-publication',lambda:capture('reference',dest))
assert not (dest/'tree.json').exists()
original_scan=image.scan
def changed_source(fd,path):
    result=original_scan(fd,path)
    changed=os.open(card,os.O_RDWR)
    try:os.pwrite(changed,b'!',toy.ROOT_OFFSET+1000);os.fsync(changed)
    finally:os.close(changed)
    return result
dest=folder('source-changed')
with patch.object(image,'scan',changed_source):reject('source-p2-change-after-scan-no-context',lambda:capture('reference',dest))
assert not (dest/'tree.json').exists();populate(reference)
bad=dict(ctx);bad['reference_root_sha256']='0'*64;dest=folder('wrong-reference')
reject('reference-changed-since-C83-refused',lambda:capture('reference',dest,bad));assert not (dest/'tree.json').exists()
assert core.sha(reference)==original_hash and core.sha(observed)==core.sha(fixtures/'observed.ext4')
passed('all-regular-source-images-preserved')
