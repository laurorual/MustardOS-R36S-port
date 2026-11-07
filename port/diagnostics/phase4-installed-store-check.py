#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C58 dispatch/gate fixtures: synthetic package and backend, no private assets."""
from pathlib import Path
import hashlib,os,re,shutil,subprocess
payload=Path('/payload');counter=0
names=['usr/libexec/muos-save-store/muos-save-store','usr/libexec/muos-save-store/payload.sha256','usr/share/muos-save-store/contract.json','usr/share/licenses/muos-save-store/LICENSE']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s,mode):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);p.chmod(mode)
def reset():
 global counter
 counter+=1;cap=Path('/run/muos-prefs-data.'+f'{counter:06d}');cap.mkdir(mode=0o700)
 root=Path('/tmp/pkg'+str(counter));root.mkdir(mode=0o755)
 for n in names:
  data=('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(cap/'called')+'\n') if n==names[0] else 'fixture '+n+'\n'
  put(root/n,data,0o755 if n==names[0] else 0o644)
 for p in root.rglob('*'):
  if p.is_dir():p.chmod(0o755)
 put(cap/'role','load\n',0o600);put(cap/'identity','ab'*32+'\n',0o600)
 text=(payload/'installed-store.sh').read_text().replace('root=/\n','root='+str(root)+'\n')
 text=text.replace('umask 077\n','umask 077\nstat() { qemu-aarch64 -cpu cortex-a35 -L /sysroot /sysroot/bin/busybox stat "$@"; }\ndirname() { qemu-aarch64 -cpu cortex-a35 -L /sysroot /sysroot/bin/busybox dirname "$@"; }\n',1)
 for n in names:
  text=re.sub(r'^[0-9a-f]{64}( (?:644|755) '+re.escape(n)+r')$',lambda m:sha(root/n)+m[1],text,flags=re.M)
 put(cap/'fixture.sh',text,0o700)
 return cap,root
labels=['status','export','init','commit','recover','unknown','extra-status-argument','export-wrong-destination','wrong-role','role-extra-LF','wrong-identity','identity-extra-LF','invalid-ID','capsule-shadow','capsule-shadow-symlink','binary-missing','binary-hash','manifest-hash','contract-hash','license-hash','binary-mode','binary-hardlink','binary-symlink','parent-symlink']
for label in labels:
 cap,root=reset();identity='ab'*32;op=label if label in ['status','export','init','commit','recover','unknown'] else 'status'
 if label=='wrong-role':put(cap/'role','save\n',0o600)
 if label=='role-extra-LF':put(cap/'role','load\n\n',0o600)
 if label=='wrong-identity':identity='cd'*32
 if label=='identity-extra-LF':put(cap/'identity','ab'*32+'\n\n',0o600)
 if label=='invalid-ID':identity='X'*64
 if label=='capsule-shadow':put(cap/'save-store','not executable',0o600)
 if label=='capsule-shadow-symlink':(cap/'save-store').symlink_to('/absent')
 if label=='binary-missing':(root/names[0]).unlink()
 for tag,index in [('binary-hash',0),('manifest-hash',1),('contract-hash',2),('license-hash',3)]:
  if label==tag:
   with (root/names[index]).open('a') as f:f.write('tamper\n')
 if label=='binary-mode':(root/names[0]).chmod(0o644)
 if label=='binary-hardlink':os.link(root/names[0],root/'alias')
 if label=='binary-symlink':(root/names[0]).rename(root/'real');(root/names[0]).symlink_to(root/'real')
 if label=='parent-symlink':
  parent=(root/names[0]).parent;parent.rename(root/'real-parent');parent.symlink_to(root/'real-parent',target_is_directory=True)
 store=str(cap/'data/MUOS/port-saves-v1/gb'/identity)
 cmd=['sh',str(cap/'fixture.sh'),str(cap),op,store,identity]
 if op=='export':cmd.append('/run/muos/storage/pickles/state/core.so/GB/private')
 if label=='extra-status-argument':cmd.append('extra')
 if label=='export-wrong-destination':cmd[3]='export';cmd.append(str(cap/'elsewhere'))
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
 good=label in ['status','export']
 assert (r.returncode==0)==good,(label,r.returncode,r.stderr)
 assert (cap/'called').exists()==good,label
 if good:
  assert (cap/'called').read_text().splitlines()==[op,store,identity]+(cmd[-1:] if op=='export' else [])
 print('C58_PASS dispatcher-'+label)
for label in ['seed','verify','prepare','commit','wrong-role','bad-backend-digest','backend-hardlink','bad-dispatch-digest','dispatch-symlink','extra-argument']:
 cap,root=reset()
 put(cap/'store-base.sh',f'printf "%s\\n" "$2" > {cap}/backend-called\n',0o700)
 put(cap/'installed-store.sh','exit 0\n',0o700)
 put(cap/'store-base.sha256',sha(cap/'store-base.sh')+'\n',0o600)
 put(cap/'installed-store.sha256',sha(cap/'installed-store.sh')+'\n',0o600)
 if label=='wrong-role':put(cap/'role','save\n',0o600)
 if label=='bad-backend-digest':put(cap/'store-base.sha256','00'*32+'\n',0o600)
 if label=='backend-hardlink':os.link(cap/'store-base.sh',cap/'alias')
 if label=='bad-dispatch-digest':put(cap/'installed-store.sha256','00'*32+'\n',0o600)
 if label=='dispatch-symlink':(cap/'installed-store.sh').rename(cap/'real');(cap/'installed-store.sh').symlink_to(cap/'real')
 op=label if label in ['seed','verify','prepare','commit'] else 'seed'
 cmd=['sh',str(payload/'store.sh'),str(cap),op]+(['extra'] if label=='extra-argument' else [])
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=5);good=label in ['seed','verify']
 assert (r.returncode==0)==good,(label,r.returncode,r.stderr)
 assert (cap/'backend-called').exists()==good,label
 print('C58_PASS gate-'+label)
