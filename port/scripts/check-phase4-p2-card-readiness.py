#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C90 transition faults / no-payload source contract. No real block IO."""
from pathlib import Path
from unittest.mock import patch
import ast,importlib,json,os,struct,tempfile,types
from phase4_backup_core import sha

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/card-readiness';area.mkdir(exist_ok=True)
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases=[]
helper=importlib.import_module('phase4-p2-card-readiness')
for fault in [None,'open-controls','before-read','unlock-journal','unlock-ioctl','wrong-state','exclusive-open',
    'wrong-access','during-read','RO-restore','cold-read','complete-journal']:
    events=[];state=[1,1,1,1];read_count=[0];records=[]
    class J:
        def record(self,name,value):
            events.append(name)
            if fault=='unlock-journal' and name=='unlock-intent' or fault=='complete-journal' and name=='complete':raise OSError('fixture journal')
            records.append((name,value))
    class C:
        controls=[];claim=None;journal=J()
        def open_controls(self):
            if fault=='open-controls':raise ValueError('fixture identity')
            self.controls=[100,101,102,103];events.append('owned-fds')
        def readonly(self):
            events.append('RO1')
            if fault=='RO-restore' and read_count[0]>=2:raise OSError('fixture RO')
            state[:]=[1,1,1,1]
        def flush(self):events.append('flush')
        def acquire(self,writable=False):
            if fault=='exclusive-open' and writable:raise OSError('fixture EXCL')
            self.claim=200 if writable else 201;events.append('RW' if writable else 'RO');return self.claim
        def state(self,expected):
            if fault=='wrong-state' and expected[0]==0:raise ValueError('fixture state')
            assert state==expected
        def close_claim(self):self.claim=None;events.append('closed')
        def idle(self):events.append('identity-idle')
    def ioctl(fd,request,arg):
        assert request==0x125d and struct.unpack('i',arg)[0]==0 and fd in (100,102)
        assert 'unlock-intent' in events
        if fault=='unlock-ioctl':raise OSError('fixture ioctl')
        state[0 if fd==100 else 2]=0;events.append('SETRO0')
    def verify(fd):
        read_count[0]+=1;events.append('verified')
        if fault=='before-read' and read_count[0]==1 or fault=='during-read' and read_count[0]==2 or fault=='cold-read' and read_count[0]==3:raise ValueError('fixture p2 change')
    c=C()
    with patch.object(helper.fcntl,'fcntl',return_value=os.O_RDONLY if fault=='wrong-access' else os.O_RDWR):
        try:helper.transition(c,verify,ioctl)
        except (ValueError,OSError):
            assert fault is not None and not any(n=='complete' for n,v in records) and 'RO1' in events and c.claim is None
            cases.append('readiness-'+fault+'-restores-owned-protection-and-no-complete')
        else:
            assert fault is None and read_count[0]==3 and state==[1,1,1,1]
            assert [n for n,v in records]==['unlock-intent','complete'] and 'write-intent' not in events
            assert events.index('unlock-intent')<events.index('SETRO0')<events.index('RW')<events.index('complete')
            cases.append('readiness-exact-RO-RW-RO-sequence-and-triple-byte-verification-no-write-intent')
tree=ast.parse((repo/'port/scripts/phase4-p2-card-readiness.py').read_text())
transition=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='transition')
for node in ast.walk(transition):
    if isinstance(node,ast.Call):
        name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
        assert name not in {'apply','write_p2','write','pwrite','writev','pwritev','sparse_clone','copy_region','mount','reboot','getrandom'}
cases.append('transition-AST-has-no-payload-write-or-image-or-boot-or-RNG-operation')
try:helper.operation()
except ValueError:cases.append('internal-entry-refuses-unsealed-non-root-source')
else:raise AssertionError('unsealed entry allowed')

bundle=stage/'bundle';bundle.mkdir(mode=0o700)
for n in helper.SOURCES:(bundle/n).write_bytes(b'fixture-only')
manifest={'operation':'card-readiness-no-payload','files':{n:sha(bundle/n) for n in helper.SOURCES}}
(bundle/'package.json').write_text(json.dumps(manifest));executed=[];roots=[];old_read=Path.read_text;mkdtemp=tempfile.mkdtemp
def read(path,*a,**kw):return 'Jupiter' if str(path)=='/sys/class/dmi/id/product_name' else old_read(path,*a,**kw)
def make(**kw):p=Path(mkdtemp(prefix='sealed.',dir=stage));roots.append(p);return str(p)
class ExecStopped(Exception):pass
def execute(*args):executed.append(args);raise ExecStopped()
with patch.object(helper,'__file__',str(bundle/'phase4-p2-card-readiness.py')),patch.object(helper.os,'geteuid',return_value=0),patch.object(helper.platform,'machine',return_value='x86_64'),patch.object(Path,'read_text',read),patch.object(helper.tempfile,'mkdtemp',make),patch.object(helper.os,'execve',execute):
    try:helper.bootstrap()
    except ExecStopped:pass
    assert executed[0][1][-1]=='_check' and executed[0][2]['PYTHONDONTWRITEBYTECODE']=='1'
    assert {p.name for p in roots[-1].iterdir()}==helper.SOURCES and all(p.stat().st_mode&0o777==0o400 for p in roots[-1].iterdir())
    cases.append('bootstrap-seals-exact-code-context-and-clean-env')
    for name in ['recover-p2-only','apply-initial']:
        manifest['operation']=name;(bundle/'package.json').write_text(json.dumps(manifest))
        try:helper.bootstrap()
        except ValueError:cases.append('bootstrap-refuses-'+name)
        else:raise AssertionError('payload mode accepted')
sources=[Path(__file__),repo/'port/scripts/phase4-p2-card-readiness.py',*[repo/'port/scripts'/n for n in helper.SOURCES-{'context.json'}]]
hashes={str(p.relative_to(repo)):sha(p) for p in set(sources)}
(stage/'analysis.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_device_or_network_contacted':False,'kernel_transition_only_virtual_tested_here':True,'source_sha256':hashes},indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n');print('C90 readiness:',len(cases),'checks passed:',stage)
