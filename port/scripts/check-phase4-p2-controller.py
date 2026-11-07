#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C87 descriptor/transaction/journal faults, with no physical device access."""
from pathlib import Path
from unittest.mock import patch
import ast,errno,importlib,importlib.util,json,os,stat,struct,tempfile,types
import phase4_p2_controller as c
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-writer'
os.umask(0o077);area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='controller-checks.',dir=area));cases=[]
def reject(name,call):
    try:call()
    except (ValueError,RuntimeError,OSError):cases.append(name)
    else:raise AssertionError(name)

parent=stage/'journal';parent.mkdir(mode=0o700);j=c.Journal(parent)
j.record('unlock-intent',{'kind':'test-only'});assert (parent/'unlock-intent.json').stat().st_mode&0o777==0o400
cases.append('journal-exclusive-mode400-canonical-json-file-and-directory-fsync')
reject('journal-reuse-refused-even-without-write',lambda:c.Journal(parent))
reject('journal-duplicate-event-refused',lambda:j.record('unlock-intent',{}))
reject('journal-unknown-event-refused',lambda:j.record('../x',{}))
parent=stage/'journal-bad-mode';parent.mkdir(mode=0o700);parent.chmod(0o755)
reject('journal-permissive-directory',lambda:c.Journal(parent))
parent=stage/'journal-sync-error';parent.mkdir(mode=0o700);j=c.Journal(parent)
with patch.object(c.os,'fsync',side_effect=OSError('fixture fsync')):
    reject('journal-fsync-error-keeps-partial',lambda:j.record('unlock-intent',{}))
assert (parent/'unlock-intent.json').exists()
reject('partial-journal-never-auto-resumes',lambda:c.Journal(parent))

events=[]
def opened(path,flags):events.append(('open',flags));return 100
info=types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=os.makedev(7,7))
with patch.object(c.os,'open',opened),patch.object(c.os,'close',side_effect=lambda fd:events.append(('close',fd))),patch.object(c.os,'fstat',return_value=info),patch.object(c.fcntl,'ioctl',return_value=struct.pack('Q',1234)):
    assert c.block_open('/dev/fixture-only',info.st_rdev,1234,os.O_RDONLY)==100
    assert events[-1][1]&os.O_NOFOLLOW and events[-1][1]&os.O_CLOEXEC
    cases.append('block-open-verifies-fstat-rdev-size-and-nofollow')
    reject('block-open-wrong-device',lambda:c.block_open('/dev/fixture-only',os.makedev(7,8),1234,os.O_RDONLY))
    reject('block-open-wrong-size',lambda:c.block_open('/dev/fixture-only',info.st_rdev,1235,os.O_RDONLY))
    info.st_mode=stat.S_IFREG
    reject('block-open-regular-device-alias',lambda:c.block_open('/dev/fixture-only',info.st_rdev,1234,os.O_RDONLY))

proc=stage/'proc';proc.mkdir();process=proc/str(os.getpid());(process/'fd').mkdir(parents=True)
leaf=process/'fd/100';leaf.write_text('not a block')
actual_stat=Path.stat
def fake_stat(path,*a,**kw):
    if path==leaf:return types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=123)
    return actual_stat(path,*a,**kw)
with patch.object(Path,'stat',fake_stat):
    reject('foreign-raw-open-refused',lambda:c.no_foreign_fds({123},set(),proc))
    c.no_foreign_fds({123},{100},proc);cases.append('owned-block-fd-exempt-only-for-same-pid-and-number')
    other=proc/'999999';(other/'fd').mkdir(parents=True);otherleaf=other/'fd/100';otherleaf.symlink_to(leaf)
    # Match both fd paths for a raw descriptor in another process.
    def fake_other(path,*a,**kw):
        if path in (leaf,otherleaf):return types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=123)
        return actual_stat(path,*a,**kw)
    with patch.object(Path,'stat',fake_other):reject('same-fd-number-other-process-not-exempt',lambda:c.no_foreign_fds({123},{100},proc))

otherleaf.unlink()
def denied_stat(path,*a,**kw):
    if path==leaf:raise PermissionError(errno.EACCES,'fixture FUSE access')
    return actual_stat(path,*a,**kw)
with patch.object(Path,'stat',denied_stat):
    with patch.object(c,'owner_fd_stat',return_value=(stat.S_IFREG,0)) as fallback:
        c.no_foreign_fds({123},set(),proc);assert fallback.call_count==1
        cases.append('FUSE-root-denial-requires-positive-owner-metadata')
    with patch.object(c,'owner_fd_stat',return_value=(stat.S_IFBLK,123)):
        reject('FUSE-fallback-block-device-refused',lambda:c.no_foreign_fds({123},set(),proc))
    with patch.object(c,'owner_fd_stat',side_effect=PermissionError(errno.EACCES,'still denied')):
        reject('FUSE-unreadable-owner-fd-fails-closed',lambda:c.no_foreign_fds({123},set(),proc))
    later=process/'fd/101';later.write_text('fixture')
    def two_fds(path,*a,**kw):
        if path==leaf:raise PermissionError(errno.EACCES,'fixture')
        if path==later:return types.SimpleNamespace(st_mode=stat.S_IFBLK,st_rdev=123)
        return actual_stat(path,*a,**kw)
    with patch.object(Path,'stat',two_fds),patch.object(c,'owner_fd_stat',side_effect=FileNotFoundError(errno.ENOENT,'fd closed')):
        reject('closed-FUSE-fd-does-not-skip-later-raw-fd',lambda:c.no_foreign_fds({123},set(),proc))
    later.unlink()
target=Path('/proc/1234/fd/9')
for fault in [None,'owner-changed','worker-denied','worker-malformed','worker-overflow']:
    creds=[(1000,1000,'42'),(1001,1000,'42')] if fault=='owner-changed' else [(1000,1000,'42')]*2
    output=b'{"mode":32768,"rdev":0}'
    if fault=='worker-denied':output=b'{"errno":13}'
    if fault=='worker-malformed':output=b'{"mode":true,"rdev":0}'
    if fault=='worker-overflow':output=b' '*257
    result=types.SimpleNamespace(returncode=1 if fault=='worker-denied' else 0,stdout=output)
    with patch.object(c.os,'geteuid',return_value=0),patch.object(c,'process_credentials',side_effect=creds),patch.object(c.subprocess,'run',return_value=result) as worker:
        if fault:reject('fd-owner-'+fault,lambda:c.owner_fd_stat(target))
        else:
            assert c.owner_fd_stat(target)==(32768,0)
            assert worker.call_args.kwargs['user']==1000 and worker.call_args.kwargs['group']==1000 and worker.call_args.kwargs['extra_groups']==[]
            cases.append('owner-stat-worker-drops-uid-gid-groups-and-rechecks-starttime')
reject('owner-fd-fallback-rejects-arbitrary-path',lambda:c.owner_fd_stat(Path('/tmp/arbitrary')))

aliases=[(Path('/dev/fixture-'+str(n)),100+n,size) for n,size in enumerate([656*1024*1024,100*1024*1024,c.ROOT_BYTES,16*1024*1024])]
cl=c.Controller(aliases,lambda:None,aliases[0][2],None);cl.controls=[100,101,102,103]
seen=[]
def failing_ro(fd,request,arg):
    seen.append(fd)
    if fd==102:raise OSError('fixture one RO failure')
with patch.object(c.fcntl,'ioctl',failing_ro):
    reject('RO-failure-still-attempts-all-owned-aliases',cl.readonly)
assert seen==[101,102,103,100]
reject('duplicate-aliases-refused',lambda:c.Controller([aliases[0]]*4,lambda:None,aliases[0][2],None))

source=stage/'source.sparse';source.touch(mode=0o600)
with source.open('r+b') as f:f.truncate(c.ROOT_BYTES)
fd=os.open(source,os.O_RDONLY)
try:
    for fault in [None,'initial-id','source-validator','source-metadata','old-root','protected-before','unlock-journal',
        'unlock-ioctl','unlock-state','exclusive-reopen','write-journal','short-write','flush-after',
        'protected-after','cold-readback','final-protected','RO-restore','complete-journal']:
        events=[];state=[1,1,1,1];completed=[];recorded=[];written=[];hash_calls=[0];protected_calls=[0];restores=[0]
        def ioctl(descriptor,request,arg):
            assert request==c.SETRO
            value=struct.unpack('i',arg)[0];events.append(('SETRO',descriptor,value))
            if fault=='unlock-ioctl' and value==0:raise OSError('fixture unlock')
            state[0 if descriptor==100 else 2]=value
            return 0
        class J:
            def record(self,name,value):
                events.append(name);recorded.append(name)
                if fault==name+'-journal' or fault=='unlock-journal' and name=='unlock-intent' or fault=='write-journal' and name=='write-intent':raise OSError('fixture journal')
                if name=='complete':completed.append(value)
        class Model(c.Controller):
            def idle(self):events.append('idle')
            def open_controls(self):
                if fault=='initial-id':raise ValueError('fixture identity')
                self.controls=[100,101,102,103];events.append('controls')
            def readonly(self):
                events.append('RO1');restores[0]+=1
                if fault=='RO-restore' and written:raise OSError('fixture restore')
                state[:]=[1,1,1,1]
            def state(self,expected):
                if fault=='unlock-state' and expected[0]==0:raise ValueError('fixture RO transition')
                assert state==expected
            def flush(self):
                events.append('flush')
                if fault=='flush-after' and written:raise OSError('fixture flush')
            def acquire(self,writable=False):
                if fault=='exclusive-reopen' and writable:raise OSError('fixture EXCL')
                self.claim=200 if writable else 201;events.append('RW-claim' if writable else 'RO-claim');return self.claim
            def close_claim(self):self.claim=None;events.append('close-claim')
            def protected(self,target):
                protected_calls[0]+=1
                if fault=='protected-before' or fault=='protected-after' and written or fault=='final-protected' and completed==[] and protected_calls[0]==4:return ['f'*64]*2
                return ['a'*64,'b'*64]
        def hash_region(descriptor,start,size,read):
            if descriptor==fd:return 'c'*64
            if fault=='old-root' and not written:return 'e'*64
            if fault=='cold-readback' and written and state[0]==1:return 'e'*64
            return 'c'*64 if written else 'd'*64
        def writer(source,target,new,old,**kw):
            assert 'unlock-intent' in recorded and events.index('unlock-intent')<events.index('RW-claim')
            try:
                kw['preflight']();kw['verify_protected']();kw['record_intent']({'fixture':True})
                written.append(True);events.append('payload')
                if fault=='short-write':raise ValueError('fixture short write')
                kw['verify_protected']()
            finally:kw['restore_readonly']()
            kw['record_complete']({'fixture':True})
            return {'passed':True}
        def validator(descriptor):
            events.append('validate-image')
            if fault=='source-validator':raise ValueError('fixture image invalid')
            if fault=='source-metadata':os.utime(source,ns=(1,2))
        m=Model(aliases,lambda:None,aliases[0][2],J())
        with patch.object(c.fcntl,'ioctl',ioctl),patch.object(c.os,'close'),patch.object(c.core,'region_hash',hash_region),patch.object(c.core,'write_p2',writer):
            if fault is None:
                assert m.apply(fd,'c'*64,'d'*64,['a'*64,'b'*64],validator)['passed']
                assert completed and events.index('validate-image')<events.index('unlock-intent')<events.index('payload')<events.index('complete')
                assert state==[1,1,1,1];cases.append('controller-positive-order-candidate-before-unlock-and-completion-after-final-cold-readback')
            else:
                reject('controller-'+fault,lambda:m.apply(fd,'c'*64,'d'*64,['a'*64,'b'*64],validator))
                assert not completed and restores[0]>=1
                if fault in ['initial-id','source-validator','source-metadata','old-root','protected-before','unlock-journal','unlock-ioctl','unlock-state','exclusive-reopen','write-journal']:assert not written
finally:os.close(fd);source.unlink()

helper=importlib.import_module('phase4-p2-qualify')
reject('qualification-has-no-user-directory-internal-entry',helper.operation)
assert helper.fixture_mbr(656*1024*1024)[510:]==b'\x55\xaa'
reject('qualification-fixed-small-loop-geometry',lambda:helper.fixture_mbr(127934660608))
sources=[Path(__file__),repo/'port/scripts/phase4_p2_controller.py',repo/'port/scripts/phase4-p2-qualify.py',
    repo/'port/scripts/phase4_p2_write_core.py']
for p in sources:ast.parse(p.read_text())
report={'passed':True,'case_count':len(cases),'cases':cases,'physical_device_or_network_contacted':False,
    'kernel_RO_transition_exercised':False,'virtual_descriptor_controller_faults':True,
    'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-controller-checks').write_text(str(stage)+'\n')
print('C87 controller:',len(cases),'cases passed:',stage)
