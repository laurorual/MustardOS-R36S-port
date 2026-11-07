#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C40 private SDK build and QEMU ABI check; no device access or ROM needed."""
from pathlib import Path
import json
import subprocess
import tarfile
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4'
baseline=work/'network-tools/baseline.config';config=work/'graphics-config/output/.config'
assert config.read_bytes()==baseline.read_bytes()
archive=work/'menu/frontend-source.tar';origin=json.loads((work/'menu/source-manifest.json').read_text())
assert sha(archive)==origin['frontend_archive_sha256']
header=work/'foundation/frontend-source/retro/core/libretro.h'
with tarfile.open(archive) as source:
    assert source.extractfile('retro/core/libretro.h').read()==header.read_bytes()
candidate=Path((work/'rootfs-candidate/latest-composition').read_text().strip())
assert candidate.resolve().is_relative_to(work/'rootfs-candidate')
image=json.loads((candidate/'analysis.json').read_text());assert image['passed']
area=work/'libretro-smoke';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='build.',dir=area))
(area/'latest-attempt').write_text(str(stage)+'\n')
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''sdk=/work/graphics-config/output/host
cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
flags="-O2 -Wall -Wextra -Werror -mcpu=cortex-a35 -fstack-protector-strong -ffile-prefix-map=/work=."
include=/work/foundation/frontend-source/retro/core
"$cc" $flags -I"$include" -fPIC -shared -Wl,-z,relro,-z,now -Wl,-soname,r35s_smoke_libretro.so /port/diagnostics/phase4-libretro-smoke.c -o {rel(stage)}/r35s_smoke_libretro.so
"$cc" $flags -I"$include" -fPIE -pie -Wl,-z,relro,-z,now /port/diagnostics/phase4-libretro-smoke-check.c -ldl -o {rel(stage)}/check
"$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d {rel(stage)}/r35s_smoke_libretro.so {rel(stage)}/check
qemu-aarch64 -cpu cortex-a35 -L {rel(candidate/'target')} -E LD_BIND_NOW=1 {rel(stage)}/check {rel(stage)}/r35s_smoke_libretro.so
'''
(stage/'build.sh').write_text(code)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
           '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
           '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
           (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
result=subprocess.run(container,capture_output=True,text=True,timeout=90)
for ext,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:
    (stage/('build.'+ext)).write_text(value)
assert config.read_bytes()==baseline.read_bytes()
assert result.returncode==0,(stage,result.stderr)
marker='LIBRETRO_SMOKE_ABI_RGB565_INPUT_RESET_ZERO_AUDIO_OK frames=11 samples=8085'
assert marker in result.stdout
sources=[Path(__file__),repo/'port/diagnostics/phase4-libretro-smoke.c',repo/'port/diagnostics/phase4-libretro-smoke-check.c']
for p in sources:
    target=stage/'source'/p.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
report={'passed':True,'experiment':'C40_LIBRETRO_SMOKE_PREPARATION',
        'core_version':1,'video':'RGB565/160x120/60fps','audio':'44100Hz stereo digital zero',
        'verified_frames':11,'verified_audio_frames':8085,'input_changes_frame':True,
        'reset_restores_frame':True,'batch_and_sample_audio_checked':True,
        'content_file_refused':True,'no_content_load_passed':True,
        'ELF_architecture':'AArch64/Cortex-A35','linker':'PIE or shared/RELRO/NOW',
        'QEMU_loader_and_API_passed':True,'SDK_baseline_preserved':True,
        'native_console_tested':False,'muxretro_built':False,'device_written':False,
        'ROM_or_BIOS_included':False,'factory_image_changed':False,
        'frontend_revision':origin['frontend_revision'],'frontend_archive_sha256':sha(archive),
        'libretro_header_sha256':sha(header),'candidate_analysis_sha256':sha(candidate/'analysis.json'),
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources},
        'binary_sha256':{n:sha(stage/n) for n in ['r35s_smoke_libretro.so','check']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest').write_text(str(stage)+'\n')
print('C40 core + ABI checker passed under QEMU:',stage)
print(marker)
