#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C87 fault/extent tests with virtual descriptors, no filesystem/media IO."""
from pathlib import Path
import ast,hashlib,json,os,tempfile
import phase4_p2_write_core as c
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-writer';area.mkdir(exist_ok=True)
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
zero=bytes(c.CHUNK);one=b'A'*c.CHUNK
def hashed(block):
    h=hashlib.sha256()
    for _ in range(c.ROOT_BYTES//c.CHUNK):h.update(block)
    return h.hexdigest()
old=hashed(zero);new=hashed(one)
def run(fault=None):
    events=[];written={};reads={};calls=[0];complete=[];restored=[]
    def pread(fd,count,offset):
        assert count==c.CHUNK
        if fd==1:
            assert 0<=offset<c.ROOT_BYTES;reads[offset]=reads.get(offset,0)+1
            if fault=='source-short' and offset==0:return b'x'
            if fault=='source-drift' and reads[offset]>1:return zero
            return one
        assert fd==2 and c.ROOT_OFFSET<=offset< c.ROOT_OFFSET+c.ROOT_BYTES
        if fault=='bad-readback' and offset in written:return zero
        return written.get(offset,zero)
    def pwrite(fd,data,offset):
        assert fd==2 and len(data)==c.CHUNK and c.ROOT_OFFSET<=offset and offset+len(data)<=c.ROOT_OFFSET+c.ROOT_BYTES
        assert 'intent' in events;calls[0]+=1
        if fault=='write-error':raise OSError('fixture write failure')
        if fault=='short-write':return 512
        written[offset]=data;return len(data)
    def preflight():
        events.append('preflight')
        if fault=='preflight':raise ValueError('fixture preflight')
    def intent(value):
        events.append('intent')
        assert value['offset']==c.ROOT_OFFSET and value['bytes']==c.ROOT_BYTES
        if fault=='intent-sync':raise OSError('fixture intent fsync')
    def sync(fd):
        events.append('fsync')
        if fault=='fsync':raise OSError('fixture target fsync')
    def protect():
        restored.append(True)
        if fault=='restore-ro':raise OSError('fixture protection failure')
    def protected():
        events.append('protected')
        if fault=='protected-before' or fault=='protected-after' and calls[0]:raise ValueError('fixture protected region')
    try:
        result=c.write_p2(1,2,new,old if fault!='old-hash' else new,pread=pread,pwrite=pwrite,fsync=sync,
            preflight=preflight,record_intent=intent,record_complete=complete.append,restore_readonly=protect,verify_protected=protected)
    except (ValueError,OSError):
        assert fault is not None and not complete and restored==[True]
        if fault in ['preflight','source-short','old-hash','intent-sync','protected-before']:assert calls[0]==0
        if fault in ['short-write','write-error']:assert calls[0]==1
        return
    assert fault is None and result['written_bytes']==c.ROOT_BYTES and result['boot_handoff_authorized'] is False
    assert len(written)==c.ROOT_BYTES//c.CHUNK and min(written)==c.ROOT_OFFSET and max(written)+c.CHUNK==c.ROOT_OFFSET+c.ROOT_BYTES
    assert len(complete)==1 and restored==[True]

run();cases.append('all512MiB-copied-with-exact-p2-offset-and-extent-only')
for fault in ['preflight','source-short','old-hash','intent-sync','short-write','write-error','fsync',
    'source-drift','bad-readback','protected-before','protected-after','restore-ro']:
    run(fault);cases.append(fault+'-no-completed-receipt-no-automatic-retry')
for args in [(1,1,new,old),(True,2,new,old),(1,2,'bad',old)]:
    try:c.write_p2(*args,preflight=lambda:None,record_intent=lambda x:None,record_complete=lambda x:None,restore_readonly=lambda:None,verify_protected=lambda:None)
    except ValueError:cases.append('invalid-descriptor-or-digest-'+str(len(cases)))
    else:raise AssertionError('invalid args accepted')
sources=[Path(__file__),repo/'port/scripts/phase4_p2_write_core.py',repo/'port/scripts/phase4_root_migration.py']
for path in sources:ast.parse(path.read_text())
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'virtual_descriptor_callbacks_only':True,
    'physical_entrypoint_or_RO_unlock_implemented':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n');print('C87 bounded core:',len(cases),'cases passed:',stage)
