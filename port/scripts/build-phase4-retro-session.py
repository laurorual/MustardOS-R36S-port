#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C44 incremental private build; preserve the C41 host and approved libraries."""
from pathlib import Path
import json,shutil,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session';area.mkdir(exist_ok=True)
old=Path((work/'muxretro/latest').read_text().strip());prior=json.loads((old/'analysis.json').read_text());assert prior['passed']
assert sha(old/'source/bin/muxretro')==prior['binary_sha256']
for name,digest in prior['source_sha256'].items():assert sha(repo/name)==digest
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area));(area/'latest-attempt').write_text(str(stage)+'\n')
shutil.copytree(old,stage,dirs_exist_ok=True)
for n in ['analysis.json','build.stdout','build.stderr','build.exit']:(stage/n).unlink(missing_ok=True)
patch=repo/'port/patches/0009-muxretro-diagnostic-deadline.patch'
subprocess.run(['git','-C',str(stage/'source'),'apply',str(patch)],check=True)
for n in ['main','startup']:(stage/'source/retro/core'/(n+'.o')).unlink(missing_ok=True)
rel=lambda p:'/work/'+str(p.relative_to(work))
old_code=(old/'build.sh').read_text();body=old_code[old_code.index('pkgs='):].replace(rel(old),rel(stage))
code='''sdk=/work/graphics-config/output/host
export PATH="$sdk/bin:$PATH"
export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
'''+f'out={rel(stage)}\n'+body
(stage/'build.sh').write_text(code)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(container,capture_output=True,text=True,timeout=120)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('build.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stderr[-3000:])
assert sha(old/'source/bin/muxretro')==prior['binary_sha256']
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
report={'passed':True,'experiment':'C44_RETRO_SESSION_BUILD','parent_stage':str(old),'parent_analysis_sha256':sha(old/'analysis.json'),
        'binary_sha256':sha(stage/'source/bin/muxretro'),'candidate_stage':prior['candidate_stage'],
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),patch]},'device_written':False,'native_graphics_qualified':False}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest').write_text(str(stage)+'\n')
print('C44 private diagnostic host built:',stage)
