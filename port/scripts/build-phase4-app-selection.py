#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C46 private native application selection; preserve C45 artifacts."""
from pathlib import Path
import json,shutil,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'app-selection'
base=Path((work/'launcher-cycle/latest-build').read_text().strip());candidate=work/'rootfs-candidate/composition.w59vz7vo/target'
original=base/'frontend-bin/lib/libmuxmod.so'
prior=json.loads((base/'analysis.json').read_text());assert prior['passed']
assert sha(original)==prior['binary_sha256']
for n,h in prior['source_sha256'].items():assert sha(repo/n)==h
oldhash=sha(original);stage=Path(tempfile.mkdtemp(prefix='build.',dir=area))
(area/'latest-build-attempt').write_text(str(stage)+'\n')
for name in ['frontend-source','frontend-objects','frontend-bin']:
    shutil.copytree(base/name,stage/name)
# The makefile's sibling deps and generated dependency paths remain in this private tree.
shutil.copytree(base/'deps',stage/'deps')
patch=repo/'port/patches/0011-frontend-diagnostic-application.patch';header=repo/'port/diagnostics/phase4-app-selection.h'
subprocess.run(['git','-C',str(stage/'frontend-source'),'apply',str(patch)],check=True)
shutil.copyfile(header,stage/'frontend-source/module/port_app_selection.h')
(stage/'frontend-objects/module/muxapp.o').unlink()
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''sdk=/work/graphics-config/output/host
export PATH="$sdk/bin:$PATH"
export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
cd {rel(stage/'frontend-source')}
make -f phase4-frontend.mk -j4 ../frontend-bin/lib/libmuxmod.so CC="$sdk/bin/aarch64-buildroot-linux-gnu-gcc" PKG_CONFIG="$sdk/bin/pkg-config" CFLAGS="-O2 -mcpu=cortex-a35"
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -d ../frontend-bin/lib/libmuxmod.so
'''
(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('build.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stderr[-2500:])
assert sha(original)==oldhash
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
report={'passed':True,'original_library_sha256':oldhash,'binary_sha256':sha(stage/'frontend-bin/lib/libmuxmod.so'),'parent_stage':str(base),'parent_analysis_sha256':sha(base/'analysis.json'),'device_written':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),patch,header]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-build').write_text(str(stage)+'\n')
print('C46 private application library built:',stage)
