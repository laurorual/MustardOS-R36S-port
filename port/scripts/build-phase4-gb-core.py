#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pinned Game Boy core preparation, without loading/copying private ROMs."""
from pathlib import Path
import json, subprocess, tarfile, tempfile
from phase4_candidate import sha
repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
area = work/'gb-core'
commit = '77f2567d718b8973d02caa2daa8dce4953faf811'
archive = area/'cache'/('gambatte-'+commit+'.tar.gz')
archive_sha = '45e63bc79390093b78de025172ea289ded139f4ecf1e8072242f34d7dd540338'
assert sha(archive) == archive_sha
assert (work/'graphics-config/output/.config').read_bytes() == (work/'network-tools/baseline.config').read_bytes()
stage = Path(tempfile.mkdtemp(prefix='build.',dir=area))
(area/'latest-attempt').write_text(str(stage)+'\n')
with tarfile.open(archive) as stream:
    license = next(m for m in stream.getmembers() if m.name.endswith('/COPYING'))
    assert 'Version 2, June 1991' in stream.extractfile(license).read().decode()
    stream.extractall(stage, filter='data')
source = stage/('gambatte-libretro-'+commit)
rel = lambda p: '/work/'+str(p.relative_to(work))
root = '/work/rootfs-candidate/composition.w59vz7vo/target'
code = f'''sdk=/work/graphics-config/output/host
export CC="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" CXX="$sdk/bin/aarch64-buildroot-linux-gnu-g++"
export CFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/work=."
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-Wl,-z,relro,-z,now"
cd {rel(source)}
make -f Makefile.libretro -j4 platform=unix HAVE_NETWORK=0 VIDEO_RGB565=1
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d gambatte_libretro.so
"$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -O2 -mcpu=cortex-a35 -I{rel(source)}/libgambatte/libretro-common/include /port/diagnostics/phase4-gb-identity-check.c -ldl -o {rel(stage)}/identity-check
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/usr/lib:{root}/lib {rel(stage)}/identity-check {rel(source)}/gambatte_libretro.so
'''
(stage/'build.sh').write_text(code)
cmd = ['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
       '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
       '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
       (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r = subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
    (stage/('build.'+ext)).write_text(value)
assert r.returncode == 0, (stage,r.stderr[-3000:])
assert 'C48_GB_IDENTITY_OK' in r.stdout
assert 'Machine:                           AArch64' in r.stdout
assert (work/'graphics-config/output/.config').read_bytes() == (work/'network-tools/baseline.config').read_bytes()
report = {'passed':True,'core':'Gambatte','upstream':'https://github.com/libretro/gambatte-libretro',
          'commit':commit,'archive_sha256':archive_sha,'license':'GPL-2.0; source archive and COPYING retained',
          'source_stage':str(source),'core_sha256':sha(source/'gambatte_libretro.so'),
          'QEMU_loader_API_metadata_checked':True,'ROM_loaded':False,'ROM_copied':False,
          'native_runtime_qualified':False,'SDK_baseline_preserved':True,'device_written':False,
          'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-gb-identity-check.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest').write_text(str(stage)+'\n')
print('C48 Gambatte built; metadata/loader only, no ROM:',stage)
