#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Synthetic storage fixtures only. No ROM, device or native frontend involved."""
from pathlib import Path
import fcntl,os,shutil,struct,subprocess,tempfile,zlib

base=Path(tempfile.mkdtemp(prefix='c52.',dir='/tmp'));identity='ab'*32
root=os.environ['C52_ROOT'];binary=os.environ['C52_BINARY'];test_binary=os.environ['C52_TEST_BINARY']
prefix=['qemu-aarch64','-cpu','cortex-a35','-L','/']
count=0
def expect(name,fn):
 global count
 fn();count+=1;print('C52_FIXTURE_PASS '+name,flush=True)
def run(op,store,ram=None,rc=0,id=identity,fault=None):
 cmd=prefix[:]
 if fault:cmd+=['-E','SAVE_STORE_FAILURE='+fault]
 cmd+=[root+'/lib/ld-linux-aarch64.so.1','--inhibit-cache','--library-path',root+'/lib:'+root+'/usr/lib',test_binary if fault else binary,op,str(store),id]
 if ram is not None:cmd+=[str(ram)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
 assert r.returncode==rc,(op,rc,r.returncode,r.stdout,r.stderr)
 assert (r.stdout.startswith('MUOS_SAVE_STORE_OK ') if rc==0 else r.stdout=='')
 return r
def mkdir(name):
 p=base/name;p.mkdir(mode=0o700);return p
def data(label):
 payload=label.encode()*1024
 state=b'PKST'+struct.pack('<HHIIII',1,0,len(payload),0,zlib.crc32(payload),0)+bytes(8)+payload
 return {'quicksave.state':state,'states.ini':b'[quicksave]\nname=fixture\ncreated=1\ncrc=fixture\ncore=fixture\ncore_version=fixture\n','quicksave.png':b'\x89PNG\r\n\x1a\nsynthetic'}
def source(name,label):
 p=mkdir(name)
 for n,b in data(label).items():(p/n).write_bytes(b);(p/n).chmod(0o600)
 return p
def store(name):
 p=mkdir(name);(p/'.muos-saves-v1').write_text('MUOS-R35S-SAVES-V1\n');(p/'.muos-saves-v1').chmod(0o600)
 run('init',p);return p
def equal_export(s,label,name):
 dst=mkdir(name);run('export',s,dst)
 assert {f.name:f.read_bytes() for f in dst.iterdir()}==data(label)
def unchanged(s,op):
 before=(s/'HEAD').read_bytes();op();assert (s/'HEAD').read_bytes()==before
try:
 a=source('a','A');b=source('b','B');s=store('store')
 expect('init-idempotent',lambda:unchanged(s,lambda:run('init',s)))
 expect('empty-export-refused',lambda:run('export',s,mkdir('empty'),rc=3))
 expect('commit-first',lambda:run('commit',s,a))
 expect('export-exact-three-files',lambda:equal_export(s,'A','export-a'))
 expect('commit-second',lambda:run('commit',s,b))
 expect('export-current',lambda:equal_export(s,'B','export-b'))
 p=s/'00000002.bundle';raw=p.read_bytes();bad=bytearray(raw);bad[140]^=1;p.write_bytes(bad)
 expect('corrupt-current-refused-unchanged',lambda:unchanged(s,lambda:run('export',s,mkdir('bad-export'),rc=64)))
 expect('explicit-recovery',lambda:run('recover',s))
 expect('recovered-previous-exact',lambda:equal_export(s,'A','export-recovered'))
 expect('recovery-preserves-corrupt-generation',lambda:(_ for _ in ()).throw(AssertionError()) if p.read_bytes()!=bad else None)
 expect('next-counter-survives-recovery',lambda:run('commit',s,b))
 assert (s/'00000003.bundle').is_file()
 expect('identity-mismatch-refused',lambda:unchanged(s,lambda:run('status',s,id='cd'*32,rc=64)))
 for label,change in [
  ('invalid-PKST',lambda d:(d/'quicksave.state').write_bytes(b'invalid')),
  ('invalid-manifest',lambda d:(d/'states.ini').write_bytes(b'[other]\n')),
  ('invalid-PNG',lambda d:(d/'quicksave.png').write_bytes(b'invalid')),
  ('mode',lambda d:(d/'quicksave.state').chmod(0o644)),
  ('hardlink',lambda d:os.link(d/'quicksave.state',d/'alias')),
  ('symlink',lambda d:((d/'quicksave.state').rename(d/'original'),(d/'quicksave.state').symlink_to('original'))),
  ('FIFO',lambda d:((d/'quicksave.state').unlink(),os.mkfifo(d/'quicksave.state',0o600))),
  ('oversized',lambda d:(d/'states.ini').write_bytes(b'x'*16385))]:
  d=source('source-'+label,'A');change(d)
  expect('source-'+label,lambda d=d:unchanged(s,lambda:run('commit',s,d,rc=64)))
 link=base/'link';link.symlink_to(s)
 expect('ancestor-symlink-refused',lambda:run('status',link,rc=64))
 dirty=mkdir('dirty');(dirty/'keep').write_text('untouched')
 expect('nonempty-export-refused',lambda:run('export',s,dirty,rc=64))
 assert (dirty/'keep').read_text()=='untouched'
 lock=os.open(s/'.lock',os.O_RDONLY);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 expect('concurrent-writer-refused',lambda:run('commit',s,a,rc=75));os.close(lock)
 head=(s/'HEAD').read_bytes();(s/'HEAD').write_bytes(b'invalid')
 expect('corrupt-HEAD-preserved',lambda:unchanged(s,lambda:run('init',s,rc=64)))
 (s/'HEAD').write_bytes(head)
 os.link(s/'00000003.bundle',s/'alias')
 expect('bundle-hardlink-refused',lambda:run('status',s,rc=64));(s/'alias').unlink()
 for step in ['bundle-file','bundle-directory','head-file','head-directory']:
  d=store('fault-'+step);run('commit',d,a);before=(d/'HEAD').read_bytes()
  expect('fault-'+step,lambda d=d,step=step:run('commit',d,b,rc=74,fault=step))
  if step=='head-directory':
   assert (d/'HEAD').read_bytes()!=before;equal_export(d,'B','after-'+step)
  else:
   assert (d/'HEAD').read_bytes()==before;equal_export(d,'A','after-'+step)
   if step!='bundle-file':
    expect('orphan-not-adopted-'+step,lambda d=d:run('commit',d,b,rc=74))
 d=store('stale');run('commit',d,a);(d/'.head.new').write_text('unknown');(d/'.head.new').chmod(0o600)
 expect('stale-staging-preserved',lambda:unchanged(d,lambda:run('commit',d,b,rc=74)))
 assert (d/'.head.new').read_text()=='unknown'
 fresh=mkdir('unknown');(fresh/'.muos-saves-v1').write_text('MUOS-R35S-SAVES-V1\n');(fresh/'.muos-saves-v1').chmod(0o600)
 (fresh/'00000001.bundle').write_text('orphan')
 expect('init-will-not-adopt-orphans',lambda:run('init',fresh,rc=64))
 limit=store('limit')
 for unused in range(32):run('commit',limit,a)
 expect('generation-limit-preserves-current',lambda:unchanged(limit,lambda:run('commit',limit,a,rc=73)))
 print('C52_FIXTURES_PASSED count='+str(count),flush=True)
finally:shutil.rmtree(base)
