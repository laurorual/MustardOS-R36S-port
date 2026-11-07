#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C96 real ext4 sector coordination on sparse regular files; fake controls."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from copy import deepcopy
import hashlib,importlib,json,os,shutil,struct,subprocess,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as core
import phase4_root_metadata as metadata
import phase4_root_recovery as recovery
h=importlib.import_module('phase4-root-repair-current');prep=importlib.import_module('prepare-phase4-root-repair-current')
os.umask(0o077);stage=Path(sys.argv[1]);cases=[];size=32*1024*1024;starts={2:128*1024*1024,3:640*1024*1024}
def passed(name):cases.append(name);print('C96_PASS_'+name,flush=True)
def reject(name,fn):
    try:fn()
    except (ValueError,OSError,KeyError,TypeError):passed(name)
    else:raise AssertionError(name)
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
def run(args):
    p=subprocess.run(args,capture_output=True,timeout=60);assert p.returncode==0,p.stderr[-1000:];return p
def put(path,value):path.write_bytes(recovery.encoded(value))
template=stage/'sparse-template.raw';fd=os.open(template,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);os.ftruncate(fd,starts[3]+size)
base=['has_journal','ext_attr','resize_inode','dir_index','filetype','extent','sparse_super','large_file','dir_nlink','extra_isize']
try:
    for n,features in [(2,base+['flex_bg','huge_file','metadata_csum']),(3,base+['uninit_bg'])]:
        p=stage/f'fixture-{n}.ext4'
        with p.open('xb') as f:f.truncate(size)
        run(['mke2fs','-q','-t','ext4','-b','4096','-I','256','-O','none,'+','.join(features),str(p)])
        run(['debugfs','-w','-R','set_inode_field <2> mode 040777',str(p)]);run(['e2fsck','-fn',str(p)])
        with p.open('rb') as f:
            for offset in range(0,size,1024*1024):
                raw=f.read(1024*1024)
                if raw!=bytes(len(raw)):assert os.pwrite(fd,raw,starts[n]+offset)==len(raw)
        p.unlink()
    os.fsync(fd)
finally:os.close(fd)
def capsule(fd,n,mode=0o40777):
    start=starts[n];sb=os.pread(fd,1024,start+1024);gd=os.pread(fd,4096,start+4096)
    layout=metadata.geometry(sb,gd,start,size);sector=os.pread(fd,512,layout['sector_offset'])
    return {'sb':sb,'gd':gd,'sector':sector,'patch':metadata.sector_patch(sb,gd,sector,start,size,mode)}
fd=os.open(template,os.O_RDONLY)
try:
    caps={n:capsule(fd,n) for n in (2,3)};before=core.region_sha(fd,0,640*1024*1024)
    digest=hashlib.sha256();p=caps[2]['patch'];offset=p['sector_offset']
    for i in range(0,640*1024*1024,1024*1024):
        raw=os.pread(fd,1024*1024,i)
        if i<=offset<i+len(raw):j=offset-i;raw=raw[:j]+bytes.fromhex(p['after'])+raw[j+512:]
        digest.update(raw)
    after=digest.hexdigest()
finally:os.close(fd)
plan={'schema':95,'current_prefix_before_sha256':before,'current_prefix_after_sha256':after,'patches':{str(n):c['patch'] for n,c in caps.items()},
    'native_receipt_sha256':'a'*64,'context_sha256':'b'*64,'independent_current_preimage_verified':True,'payload_write_authorized':False}
cap={'expected_boot_sequence':76,'runtime_guard_sha256':'c'*64}
root=folder('root')
for n in h.SOURCES:(root/n).write_text('synthetic source '+n+'\n')
ctx={'synthetic':True};put(root/'context.json',ctx)
guard=SimpleNamespace(identity=lambda:None);current=stage/'current.raw';events=[];failure=None
class Controller:
    def __init__(self):self.controls=[];self.claim=None;self.ro=[1,1,1,1];self.open_count=0
    def open_controls(self):
        self.controls=[os.open(current,os.O_RDONLY) for _ in range(4)];events.append('controls')
    def readonly(self):self.ro=[1,1,1,1];events.append('restore-RO')
    def flush(self):events.append('flush')
    def acquire(self,writable=False):
        assert self.claim is None;assert self.ro==([0,1,0,0] if writable else [1,1,1,1])
        self.claim=os.open(current,os.O_RDWR if writable else os.O_RDONLY);events.append('RW' if writable else 'R');return self.claim
    def close_claim(self):
        if self.claim is not None:os.close(self.claim);self.claim=None
    def idle(self):events.append('idle')
    def state(self,expected):assert self.ro==expected
def legacy_run(args):
    events.append(args[0]);return SimpleNamespace(stdout='77\n' if failure=='counter' else '76\n')
def backup():events.append('backup');return ['synthetic userdata']
def userdata(mode,rows):
    assert rows==['synthetic userdata'];events.append('userdata-'+oct(mode))
    if mode==0o755 and failure=='userdata':raise ValueError('post-repair userdata mismatch')
def fresh_capsule(fd,n,mode=0o40777):
    c=capsule(fd,n,mode)
    if failure=='capsule' and mode==0o40777:c['patch']=dict(c['patch'],before_sha256='0'*64)
    return c
legacy=SimpleNamespace(ROOT=root,backup_check=backup,run=legacy_run,userdata_check=userdata,capsule=fresh_capsule)
original_pwrite=os.pwrite;original_fsync=os.fsync;original_write_new=core.write_new;original_region=core.region_sha
def transaction(name):
    global active
    run(['cp','--reflink=auto','--sparse=always',str(template),str(current)]);where=folder(name);active=Controller()
    def ioctl(fd,request,arg):
        assert request==0x125d and struct.unpack('i',arg)[0]==0
        index=active.controls.index(fd);events.append('unlock-'+str(index))
        assert (where/'unlock-intent.json').is_file()
        if failure=='unlock' and index==2:raise OSError('partial unlock failure')
        active.ro[index]=0;return 0
    def pwrite(fd,data,offset):
        events.append('pwrite-'+str(offset));assert (where/'write-intent.json').is_file() and active.ro==[0,1,0,0]
        if failure=='short':return original_pwrite(fd,data[:128],offset)
        if failure=='second-write' and offset==caps[3]['patch']['sector_offset']:raise OSError('second sector failed')
        return original_pwrite(fd,data,offset)
    def fsync(fd):
        if failure=='sync' and fd==active.claim and any(v.startswith('pwrite-') for v in events):raise OSError('card fsync failed')
        return original_fsync(fd)
    def write_new(path,data):
        if failure=='journal' and path.name=='unlock-intent.json':raise OSError('journal fsync failed')
        return original_write_new(path,data)
    def region(fd,offset,length):
        value=original_region(fd,offset,length)
        return '0'*64 if failure=='prefix' else value
    try:
        with patch.object(h.fcntl,'ioctl',ioctl),patch.object(h.os,'pwrite',pwrite),patch.object(h.os,'fsync',fsync),\
             patch.object(core,'write_new',write_new),patch.object(core,'region_sha',region):
            result=h.repair(where,ctx,cap,plan,legacy,guard,core,metadata,active)
        return where,result
    finally:assert active.controls==[] and active.claim is None and active.ro==[1,1,1,1]
where,result=transaction('success')
assert result['written_bytes']==1024 and len([v for v in events if v.startswith('pwrite-')])==2
assert events.index('unlock-0')<events.index('unlock-2')<events.index('unlock-3')<events.index('RW')
assert events.index('userdata-0o777')<events.index('RW')<events.index('userdata-0o755')
assert (where/'unlock-intent.json').is_file() and (where/'write-intent.json').is_file()
assert result['seed_loaded_or_generated'] is False and result['boot_handoff_authorized'] is False
passed('real-checksummed-and-uninit-ext4-two-sector-repair-after-durable-journals')
fd=os.open(current,os.O_RDONLY)
try:
    for n in (2,3):
        changed=capsule(fd,n,0o40755);assert changed['sector'].hex()==caps[n]['patch']['after']
        assert changed['sb']==caps[n]['sb'] and changed['gd']==caps[n]['gd']
        extracted=stage/f'after-{n}.ext4'
        out=os.open(extracted,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);os.ftruncate(out,size)
        try:
            for offset in range(0,size,1024*1024):
                raw=os.pread(fd,1024*1024,starts[n]+offset)
                if raw!=bytes(len(raw)):assert original_pwrite(out,raw,offset)==len(raw)
            original_fsync(out)
        finally:os.close(out)
        run(['e2fsck','-fn',str(extracted)]);extracted.unlink()
finally:os.close(fd)
passed('both-real-filesystems-fsck0-root0755-and-SB-GDT-preserved')
manifest={'files':{n:core.sha(root/n) for n in h.SOURCES}}
prep.validate_report(result,ctx,plan,manifest);passed('native-repair-receipt-tied-to-current-plan-and-package')
current.unlink()
for why in ['counter','capsule','prefix','journal','unlock','short','second-write','sync','userdata']:
    failure=why;events.clear()
    reject(why+'-failure-restores-all-RO-and-publishes-no-completion',lambda why=why:transaction('failure-'+why))
    where=stage/('failure-'+why);assert not (where/'analysis.json').exists()
    writes=[v for v in events if v.startswith('pwrite-')]
    if why in ['counter','capsule','prefix','journal','unlock']:assert not writes
    if why in ['short','sync']:assert len(writes)==1
    if why=='second-write':assert len(writes)==2
    current.unlink()
failure=None
for name,change in [('reject-replayed-operation',lambda r:r.update(operation='apply')),
    ('reject-wrong-write-extent',lambda r:r.update(written_bytes=512)),('reject-wrong-prefix-result',lambda r:r.update(prefix_after_sha256='0'*64)),
    ('reject-incomplete-RO',lambda r:r.update(all_four_aliases_kernel_readonly=False)),('reject-bad-fsck',lambda r:r.update(p3_fsck_exit=1)),
    ('reject-seed-side-effect',lambda r:r.update(seed_loaded_or_generated=True)),('reject-automatic-retry',lambda r:r.update(automatic_retry_or_rollback=True)),
    ('reject-handoff-claim',lambda r:r.update(boot_handoff_authorized=True)),('reject-source-change',lambda r:r.update(source_sha256={}))]:
    bad=deepcopy(result);change(bad);reject(name,lambda bad=bad:prep.validate_report(bad,ctx,plan,manifest))

# Exercise lineage against a synthetic C95 receipt and real reviewed source
# files, not private keys/seeds or production snapshots.
lineage=folder('lineage')
for n in h.SOURCES:
    if n.endswith('.py'):shutil.copyfile(Path('/port/scripts')/n,lineage/n)
old={'schema':83,'scope':'inode2_mode0777_to0755_only','host_copy_verified':True,'metadata_repair_required_before_boot':True,
    'deck_backup':'/var/tmp/muos-r35s-c81-backup.12345678','backup_artifacts':{}}
for n in ['host_ack_sha256','backup_receipt_sha256','prefix_before_sha256','mbr_sha256','boot_prefix_16MiB_sha256','automount_rule_sha256']:old[n]='a'*64
captured={'schema':95,'operation':'protect-and-capture','legacy_context':old,'runtime_guard_sha256':'c'*64,'expected_boot_sequence':76,'attempt_sha256':'d'*64}
put(lineage/'capture-context.json',captured)
native={'passed':True,'schema':95,'operation':'protect-and-capture','context_sha256':core.sha(lineage/'capture-context.json'),
    'attempt_sha256':'d'*64,'boot_sequence':76,'runtime_guard_sha256':'c'*64,'current_prefix_sha256':before,
    'prefix_bytes':640*1024*1024,'root_modes':{'p2':0o777,'p3':0o777},'p2_fsck_exit':0,'p3_fsck_exit':0,'patches':plan['patches'],
    'source_sha256':{n:core.sha(lineage/('capture-context.json' if n=='context.json' else n)) for n in prep.capture.helper.SOURCES}}
for n in ['physical_payload_written','repair_applied','media_unlocked','seed_loaded_or_generated']:native[n]=False
for n in ['historical_independent_backup_reverified','userdata_matches_C82','all_four_aliases_kernel_readonly','runtime_guard_restored_or_reverified']:native[n]=True
def checked(n=native,change_ack=None,change_plan=None):
    put(lineage/'native-capture.json',n)
    p=deepcopy(plan);p.update(context_sha256=core.sha(lineage/'capture-context.json'),native_receipt_sha256=core.sha(lineage/'native-capture.json'))
    if change_plan:change_plan(p)
    put(lineage/'repair-inputs.json',p)
    ack={'passed':True,'schema':95,'current_preimage_and_capsules_independently_verified':True,'no_payload_repair_executed':True,
        'all_aliases_RO_and_guard_verified':True,'files':{'context.json':core.sha(lineage/'capture-context.json'),
            'analysis.json':core.sha(lineage/'native-capture.json'),'repair-inputs.json':core.sha(lineage/'repair-inputs.json'),'current-prefix.backup':before}}
    if change_ack:change_ack(ack)
    put(lineage/'host-current-ack.json',ack)
    c={'schema':96,'operation':'repair-current-root-modes','qualified_kernel':'fixture-kernel',
        **{k:core.sha(lineage/v) for k,v in [('capture_context_sha256','capture-context.json'),('native_capture_sha256','native-capture.json'),
            ('host_current_ack_sha256','host-current-ack.json'),('repair_inputs_sha256','repair-inputs.json')]}}
    return h.validate_lineage(lineage,c,core,recovery,prep.capture.helper)
assert checked()[1]['patches']==plan['patches'];passed('independent-current-capture-plan-ACK-and-reviewed-sources-bound')
for name,change in [('capture-counter-changed',lambda x:x.update(boot_sequence=77)),('capture-wrote-payload',lambda x:x.update(physical_payload_written=True)),
    ('capture-source-inventory-empty',lambda x:x.update(source_sha256={})),('capture-dirty-root',lambda x:x.update(p2_fsck_exit=1))]:
    bad=deepcopy(native);change(bad);reject(name,lambda bad=bad:checked(bad))
reject('missing-independent-current-copy',lambda:checked(change_ack=lambda a:a.update(current_preimage_and_capsules_independently_verified=False)))
reject('wrong-independent-prefix',lambda:checked(change_ack=lambda a:a['files'].update({'current-prefix.backup':'0'*64})))
reject('unknown-plan-options',lambda:checked(change_plan=lambda p:p.update(arbitrary_offset=True)))
template.unlink()
put(stage/'fixture-results.json',{'passed':True,'case_count':len(cases),'cases':cases,'real_32MiB_ext4_pair_on_sparse_regular_file':True,
    'physical_controls_guard_backup_userdata_and_namespace_stubbed':True,'native_preparer_collector_mains_executed':False})
