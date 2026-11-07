#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Root-in-container fixtures. Mount/card APIs are explicit fakes, never devices."""
from pathlib import Path
import os,shutil,struct,subprocess,zlib
q=['qemu-aarch64','-cpu','cortex-a35','-L','/','/sysroot/lib/ld-linux-aarch64.so.1','--inhibit-cache','--library-path','/sysroot/lib:/sysroot/usr/lib']
identity='ab'*32;count=0;seq=0
def passed(name):
 global count
 count+=1;print('C53_FIXTURE_PASS '+name,flush=True)
def run(args,rc=0):
 r=subprocess.run(args,capture_output=True,text=True,timeout=8)
 assert r.returncode==rc,(args,r.returncode,rc,r.stdout,r.stderr)
 return r
def put(p,data,mode=0o600):
 p.write_bytes(bytes(data) if isinstance(data,(bytes,bytearray)) else data.encode());p.chmod(mode)
def cap():
 global seq
 seq+=1;p=Path('/run/muos-prefs-data.'+f'{seq:06d}');p.mkdir(mode=0o700)
 (p/'data').mkdir(mode=0o755);(p/'data/MUOS').mkdir(mode=0o700)
 return p
def init(p,rc=0,product=False,id=identity):
 return run(q+['/payload/save-directory' if product else '/payload/save-directory-test',str(p),id],rc)
for label,change in [
 ('valid',lambda p:None),
 ('capsule-mode',lambda p:p.chmod(0o755)),
 ('data-mode',lambda p:(p/'data').chmod(0o700)),
 ('MUOS-mode',lambda p:(p/'data/MUOS').chmod(0o775)),
 ('data-symlink',lambda p:((p/'data').rename(p/'real'),(p/'data').symlink_to('real'))),
 ('MUOS-symlink',lambda p:((p/'data/MUOS').rename(p/'data/real'),(p/'data/MUOS').symlink_to('real'))),
 ('existing-root',lambda p:(p/'data/MUOS/port-saves-v1').mkdir()),
 ('existing-root-symlink',lambda p:(p/'data/MUOS/port-saves-v1').symlink_to('/tmp')),
 ('stale-stage',lambda p:(p/'data/MUOS/.port-saves-v1.c53-new').mkdir()),
 ('stale-stage-file',lambda p:put(p/'data/MUOS/.port-saves-v1.c53-new','keep'))]:
 p=cap();change(p);init(p,0 if label=='valid' else 64)
 if label=='valid':
  top=p/'data/MUOS/port-saves-v1';leaf=top/'gb'/identity
  assert (top/'.muos-save-root-v1').read_text()=='MUOS-R35S-SAVE-ROOT-V1\n'
  assert (leaf/'.muos-saves-v1').read_text()=='MUOS-R35S-SAVES-V1\n'
  assert not (p/'data/MUOS/.port-saves-v1.c53-new').exists()
  init(p,64);assert not (leaf/'HEAD').exists()
 passed('directory-'+label)
p=cap();(p/'data/MUOS').chmod(0o755);init(p);assert (p/'data/MUOS').stat().st_mode&0o777==0o755;passed('existing-parent-0755-preserved')
for label,id in [('identity-uppercase','AB'*32),('identity-short','ab'),('identity-traversal','../'+('a'*61))]:
 init(cap(),64,id=id);passed(label)
p=cap();init(p,64,product=True);passed('production-refuses-tmpfs')
run(q+['/payload/save-directory-test','/run/muos-prefs-data.000000/../000000',identity],64);passed('capsule-traversal')

# Execute the actual bridge with real C52/C51 binaries. Only mount/card APIs and
# production ext4 restriction of the initializer are replaced in this fixture.
p=cap();(p/'state').mkdir(mode=0o700);(p/'data/MUOS/preferences').mkdir(mode=0o700)
put(p/'data/MUOS/preferences/preferences','MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n')
put(p/'identity',identity+'\n');put(p/'role','prepare\n')
for name,target in [('save-directory','save-directory-test'),('save-store','save-store'),('state-metadata','state-metadata')]:
 put(p/name,'#!/bin/sh\nexec '+' '.join(q)+' /payload/'+target+' "$@"\n',0o700)
mock=f'''model=ro
prefs_device=/dev/synthetic-never-opened
prefs_data_mounted() {{ [ "$model" = "$1" ]; }}
findmnt() {{
 case "$*" in
 *'-T '*) echo tmpfs;;
 *'-o OPTIONS'*) [ "$model" != none ] && echo "$model";;
 *) [ "$model" != none ];;
 esac
}}
umount() {{ echo unmount >> {p}/mount-calls;model=none; }}
mount() {{ case "$*" in *'rw,'*) model=rw;;*) model=ro;;esac;echo "$model" >> {p}/mount-calls; }}
'''
put(p/'mock',mock)
code=Path('/payload/store.sh').read_text().replace('. /usr/libexec/muos-session/card-guard.sh','. '+str(p/'mock')).replace('. /usr/libexec/muos-session/data-functions.sh',':')
put(p/'bridge',code)
def bridge(op,rc=0):return run(['sh',str(p/'bridge'),str(p),op],rc)
bridge('prepare');assert (p/'mount-calls').read_text()=='unmount\nrw\nunmount\nro\n';passed('bridge-initialize-and-restore-ro')
native=Path('/run/muos/storage/pickles/state/core.so/GB/private');native.mkdir(parents=True,mode=0o700)
payload=b'synthetic'*128
state=b'PKST'+struct.pack('<HHIIII',1,0,len(payload),0,zlib.crc32(payload),0)+bytes(8)+payload
files={'quicksave.state':state,'states.ini':b'[quicksave]\nname=fixture\ncreated=1\ncrc=fixture\ncore=fixture\ncore_version=fixture\n','quicksave.png':b'\x89PNG\r\n\x1a\nfixture'}
put(p/'role','save\n');bridge('seed');passed('bridge-empty-store-seed')
for n,b in files.items():put(native/n,b)
put(p/'state/game.log','C50_EXIT reason=deadline frames=100\nQuick Save (hotkey)\nSaved state to synthetic\n')
bridge('commit',1);passed('bridge-refuses-deadline-before-rw')
put(p/'state/game.log','C50_EXIT reason=hotkey frames=100\nQuick Save (hotkey)\nSaved state to synthetic\n')
put(native/'quicksave.png',b'invalid');bridge('commit',64);passed('bridge-refuses-invalid-metadata')
put(native/'quicksave.png',files['quicksave.png']);bridge('commit');passed('bridge-commit-validated-native-state')
leaf=p/'data/MUOS/port-saves-v1/gb'/identity
assert 'CURRENT=00000001\n' in (leaf/'HEAD').read_text()
assert (p/'data/MUOS/preferences/preferences').read_text()=='MUOS-PREFS-1\nVOLUME=55\nBRIGHTNESS=70\n'
for f in native.iterdir():f.unlink()
put(p/'role','load\n');bridge('seed')
assert {f.name:f.read_bytes() for f in native.iterdir()}==files;passed('bridge-export-identity-and-metadata-valid')
bridge('verify');passed('bridge-load-preserves-entire-store')
put(p/'role','save\n');bridge('commit',1);passed('bridge-refuses-second-first-save')
put(p/'role','load\n');raw=(leaf/'00000001.bundle').read_bytes();bad=bytearray(raw);bad[140]^=1;put(leaf/'00000001.bundle',bad)
for f in native.iterdir():f.unlink()
bridge('seed',64);assert not list(native.iterdir());passed('bridge-corruption-never-seeds-or-resets')

# Exercise the selector tail independently: failure must still present launcher.
for label,role in [('save','save'),('load','load'),('app-failure','save'),('deadline','save'),('inspector-failure','save'),('transaction-failure','save'),('missing-load','load')]:
 d=Path('/tmp')/('dispatch-'+label);d.mkdir(mode=0o700);(d/'state').mkdir();(d/'runtime').mkdir();put(d/'role',role)
 reason='deadline' if label=='deadline' else 'hotkey'
 game=f'C50_EXIT reason={reason} frames=100\nQuick Save (hotkey)\nSaved state to synthetic\n'
 if label!='missing-load':game+='Quick Load (hotkey)\nLoaded state from synthetic\n'
 put(d/'game.template',game)
 put(d/'runner',f'''#!/bin/sh
set -eu
echo "$1" >> {d}/calls
case "$1" in
65) cat {d}/game.template;[ '{label}' != app-failure ];;
35) printf 'port-cycle-done\\n' > {d}/runtime/action;printf 'C45_LAUNCHER_PRESENT phase=return serial=20\\nC45_LAUNCHER_EXIT action=port-cycle-done\\n';;
*) exit 99;;esac
''',0o700)
 put(d/'state-metadata',f'#!/bin/sh\n[ "{label}" != inspector-failure ]\n',0o700)
 put(d/'store.sh',f'echo "$2" >> {d}/bridge-calls\n[ "{label}" != transaction-failure ]\n')
 text=Path('/payload/select.sh').read_text().split('c46_consume\n',1)[1].replace('/run/muos/',str(d/'runtime')+'/')
 put(d/'fixture','set -eu\ncapsule='+str(d)+'\nappdir='+str(d)+'\n'+text)
 good=label in {'save','load'}
 r=run(['sh',str(d/'fixture')],0 if good else 64)
 assert (d/'calls').read_text()=='65\n35\n'
 assert ('C53_STATE_CYCLE_COMPLETE' in r.stdout)==good
 if good:assert (d/'bridge-calls').read_text()==('commit\n' if role=='save' else 'verify\n')
 passed('dispatch-'+label)
print('C53_FIXTURES_PASSED count='+str(count),flush=True)
