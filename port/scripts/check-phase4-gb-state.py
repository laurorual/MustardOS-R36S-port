#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the A35 metadata inspector and reject synthetic invalid state files."""
from pathlib import Path
import json, subprocess, tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-state'
area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
source=repo/'port/diagnostics/phase4-state-metadata.c'
(stage/source.name).write_bytes(source.read_bytes())
rel='/work/'+str(stage.relative_to(work))
code=f'''
sdk=/work/graphics-config/output/host
root=/work/rootfs-candidate/composition.w59vz7vo/target
"$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -O2 -mcpu=cortex-a35 -Wall -Wextra -Werror -fstack-protector-strong -Wl,-z,relro,-z,now {rel}/{source.name} -lz -o {rel}/state-metadata
export C51_BINARY={rel}/state-metadata C51_ROOT="$root"
python3 {rel}/fixtures.py
'''
fixtures='''import os,pathlib,shutil,struct,subprocess,tempfile,zlib
binary=os.environ['C51_BINARY'];root=os.environ['C51_ROOT']
cmd=['qemu-aarch64','-cpu','cortex-a35','-L',root,'-E','LD_BIND_NOW=1','-E','LD_LIBRARY_PATH='+root+'/lib:'+root+'/usr/lib',binary]
payload=bytes(range(256))*8
state=b'PKST'+struct.pack('<HHIIII',1,0,len(payload),0,zlib.crc32(payload),0)+bytes(8)+payload
manifest=b'[quicksave]\\nname=fixture\\ncreated=1\\ncrc=fixture\\ncore=fixture\\ncore_version=fixture\\n'
base=pathlib.Path(tempfile.mkdtemp(prefix='c51.',dir='/tmp'))
count=0
def run(name,change=None,ok=False,where=None):
 global count
 d=base/name;d.mkdir(mode=0o700)
 for file,data in [('quicksave.state',state),('states.ini',manifest),('quicksave.png',b'\\x89PNG\\r\\n\\x1a\\nfixture')]:
  p=d/file;p.write_bytes(data);p.chmod(0o600)
 if change:change(d)
 r=subprocess.run(cmd+[str(where or d)],capture_output=True,text=True)
 assert (r.returncode==0)==ok,(name,r.returncode,r.stdout,r.stderr)
 assert not r.stdout if not ok else r.stdout.startswith('C51_STATE_VALID ')
 assert 'fixture' not in r.stdout+r.stderr
 count+=1;print('C51_FIXTURE_PASS '+name)
def mutate(d,offset,value):
 p=d/'quicksave.state';b=bytearray(p.read_bytes());b[offset]=value;p.write_bytes(b)
try:
 run('valid',ok=True)
 run('magic',lambda d:mutate(d,0,0))
 run('version',lambda d:mutate(d,4,2))
 run('flags',lambda d:mutate(d,6,1))
 run('padding',lambda d:mutate(d,31,1))
 run('crc',lambda d:mutate(d,40,99))
 run('length',lambda d:mutate(d,8,1))
 run('truncated',lambda d:(d/'quicksave.state').write_bytes(state[:25]))
 run('manifest-missing-key',lambda d:(d/'states.ini').write_bytes(b'[quicksave]\\nname=fixture\\n'))
 run('manifest-duplicate',lambda d:(d/'states.ini').write_bytes(manifest+b'name=duplicate\\n'))
 run('png',lambda d:(d/'quicksave.png').write_bytes(b'bad'))
 run('mode',lambda d:(d/'quicksave.state').chmod(0o644))
 run('hardlink',lambda d:os.link(d/'quicksave.state',d/'alias'))
 run('symlink',lambda d:((d/'quicksave.state').rename(d/'original'),(d/'quicksave.state').symlink_to('original')))
 run('dir-symlink',lambda d:(base/'alias').symlink_to(d),where=base/'alias')
 run('fifo',lambda d:((d/'quicksave.state').unlink(),os.mkfifo(d/'quicksave.state',0o600)))
 run('dir-mode',lambda d:d.chmod(0o755))
 # /work is the persistent build bind, not tmpfs. Refuse even valid bytes there.
 persist=pathlib.Path(binary).parent/'not-tmpfs';persist.mkdir(mode=0o700)
 for n in ['quicksave.state','states.ini','quicksave.png']:
  shutil.copyfile(base/'valid'/n,persist/n);(persist/n).chmod(0o600)
 run('persistent',where=persist)
 shutil.rmtree(persist)
 print('C51_FIXTURES_PASSED count='+str(count))
finally:shutil.rmtree(base)
'''
(stage/'fixtures.py').write_text(fixtures);(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
     '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
     '-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
 (stage/('check.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stderr[-2000:])
report={'passed':True,'experiment':'C51_RAM_STATE_METADATA','synthetic_cases':18,
        'binary_sha256':sha(stage/'state-metadata'),'device_written':False,
        'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),source]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-checks').write_text(str(stage)+'\n')
print('C51 inspector built and synthetic cases passed:',stage)
