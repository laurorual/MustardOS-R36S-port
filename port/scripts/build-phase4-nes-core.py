#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pinned FCEUmm private SDK build and original cartridge; no device write."""
from pathlib import Path
import json,subprocess,tarfile,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'nes-core'
commit='ac0d00a7fc01166f84c7bac01d1084ebfd2b865e';archive=area/'cache'/('fceumm-'+commit+'.tar.gz')
archive_sha='364affeeea3d91ab8de4ef2a333cb0ca4d7d8e8992e94366a270b32e309485ca'
assert sha(archive)==archive_sha
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
with tarfile.open(archive) as stream:
 text=next(m for m in stream.getmembers() if m.name.endswith('/Copying'));assert 'Version 2, June 1991' in stream.extractfile(text).read().decode()
 stream.extractall(stage,filter='data')
source=stage/('libretro-fceumm-'+commit)
subprocess.run(['python3',str(repo/'port/diagnostics/phase4-nes-demo.py'),str(stage/'r35s-flight.nes')],check=True)
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''sdk=/work/graphics-config/output/host
export CC="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" LD="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" AR="$sdk/bin/aarch64-buildroot-linux-gnu-ar"
export CFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/work=."
export LDFLAGS="-Wl,-z,relro,-z,now"
cd {rel(source)}
make -f Makefile.libretro -j4 platform=unix HAVE_HDPACK=0 HAVE_NTSC=0 WANT_32BPP=0
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d fceumm_libretro.so
'''
(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('build.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stderr[-2500:])
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
report={'passed':True,'core':'FCEUmm','upstream':'https://github.com/libretro/libretro-fceumm','commit':commit,'archive_sha256':archive_sha,'license':'GPL-2.0; retain Copying/source archive','source_stage':str(source),'core_sha256':sha(source/'fceumm_libretro.so'),'ROM_sha256':sha(stage/'r35s-flight.nes'),'ROM_license':'MIT; entirely original code/artwork','SDK_baseline_preserved':True,'device_written':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-nes-demo.py']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest').write_text(str(stage)+'\n');print('C47 FCEUmm private build:',stage)
