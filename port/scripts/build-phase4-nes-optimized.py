#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C48 same pinned FCEUmm, O3/LTO, no fast-math or clock changes."""
from pathlib import Path
import json, shutil, subprocess, tarfile, tempfile
from phase4_candidate import sha
repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
area = work/'nes-profile'
parent = Path((work/'nes-core/latest').read_text().strip())
prior = json.loads((parent/'analysis.json').read_text())
assert prior['passed'] and sha(parent/'r35s-flight.nes') == prior['ROM_sha256']
for name,h in prior['source_sha256'].items(): assert sha(repo/name) == h
commit = prior['commit']
archive = work/'nes-core/cache'/('fceumm-'+commit+'.tar.gz')
assert sha(archive) == prior['archive_sha256']
stage = Path(tempfile.mkdtemp(prefix='core.',dir=area))
(area/'latest-core-attempt').write_text(str(stage)+'\n')
with tarfile.open(archive) as stream:
    license = next(m for m in stream.getmembers() if m.name.endswith('/Copying'))
    assert 'Version 2, June 1991' in stream.extractfile(license).read().decode()
    stream.extractall(stage,filter='data')
source = stage/('libretro-fceumm-'+commit)
shutil.copyfile(parent/'r35s-flight.nes',stage/'r35s-flight.nes')
(stage/'system').mkdir()
# Included after the upstream makefile: retain all its feature/PIC defines and
# append the effective optimisation level, instead of accidentally overriding it.
(stage/'optimization.mk').write_text('override CFLAGS += -O3 -flto=4 -fno-semantic-interposition\noverride LDFLAGS += -O3 -flto=4\n')
rel = lambda p: '/work/'+str(p.relative_to(work))
root = '/work/rootfs-candidate/composition.w59vz7vo/target'
code = f'''sdk=/work/graphics-config/output/host
export CC="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" LD="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" AR="$sdk/bin/aarch64-buildroot-linux-gnu-gcc-ar"
export CFLAGS="-O2 -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/work=."
export LDFLAGS="-Wl,-z,relro,-z,now"
cd {rel(source)}
make -f Makefile.libretro -f {rel(stage)}/optimization.mk -j4 platform=unix HAVE_HDPACK=0 HAVE_NTSC=0 WANT_32BPP=0
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d fceumm_libretro.so
"$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -mcpu=cortex-a35 -I/work/foundation/frontend-source/retro/core /port/diagnostics/phase4-nes-core-check.c -ldl -o {rel(stage)}/check
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 {rel(stage)}/check {rel(source)}/fceumm_libretro.so {rel(stage)}/r35s-flight.nes {rel(stage)}/system
'''
(stage/'build.sh').write_text(code)
cmd = ['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
       '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
       '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
       (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r = subprocess.run(cmd,capture_output=True,text=True,timeout=240)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
    (stage/('build.'+ext)).write_text(value)
assert r.returncode == 0, (stage,r.stderr[-3000:])
assert 'C47_NES_API_OK' in r.stdout and 'C47_ROM_PIXELS colors=3 ship38=1 stars160=1' in r.stdout
assert (work/'graphics-config/output/.config').read_bytes() == (work/'network-tools/baseline.config').read_bytes()
assert sha(Path(prior['source_stage'])/'fceumm_libretro.so') == prior['core_sha256']
report = {'passed':True,'experiment':'C48_OPTIMIZED_FCEUMM','parent_core_stage':str(parent),
          'parent_core_sha256':prior['core_sha256'],'commit':commit,'archive_sha256':prior['archive_sha256'],
          'source_stage':str(source),'core_sha256':sha(source/'fceumm_libretro.so'),
          'ROM_sha256':sha(stage/'r35s-flight.nes'),'API_passed':True,'native_qualified':False,
          'source_unchanged':True,'SDK_baseline_preserved':True,'device_written':False,
          'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-nes-core-check.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-core').write_text(str(stage)+'\n')
print('C48 optimised core, API/pixels passed:',stage)
