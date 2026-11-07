#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile real patched parser/loader paths and exercise them under QEMU."""
from pathlib import Path
import json
import subprocess
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
build=Path((area/'latest-attempt').read_text().strip());assert build.resolve().is_relative_to(area)
source=build/'source';core=source/'retro/core'
patch=repo/'port/patches/0007-muxretro-no-content.patch'
subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],check=True)
stage=Path(tempfile.mkdtemp(prefix='no-content-checks.',dir=area))
text=(core/'core.c').read_text()
loader=text[text.index('int core_load_no_content(void) {'):text.index('int core_load_content(const char *content_path) {')]
environment=(core/'environment.c').read_text()
arms=environment[environment.index('        case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:'):environment.index('        case MUX_ENVIRONMENT_SET_SERIALIZATION_QUIRKS_LEGACY:')]
arms+=environment[environment.index('        case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:'):environment.index('        case RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:')]
(stage/'loader-under-test.inc').write_text(loader)
(stage/'environment-under-test.inc').write_text(arms)
smoke=Path((work/'libretro-smoke/latest').read_text().strip())
sm=json.loads((smoke/'analysis.json').read_text());assert sm['passed']
binary=smoke/'r35s_smoke_libretro.so';assert sha(binary)==sm['binary_sha256'][binary.name]
candidate=Path((work/'rootfs-candidate/latest-composition').read_text().strip())
rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''sdk=/work/graphics-config/output/host
cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
flags="-O2 -std=c11 -mcpu=cortex-a35 -Wall -Wextra -Werror -fPIE -pie -Wl,-z,relro,-z,now"
"$cc" $flags -I{rel(core)} /port/diagnostics/phase4-muxretro-startup-check.c {rel(core)}/startup.c {rel(source)}/retro/netplay/address.c -o {rel(stage)}/startup-check
"$cc" $flags -I{rel(core)} -I{rel(stage)} /port/diagnostics/phase4-muxretro-no-content-check.c -ldl -o {rel(stage)}/loader-check
qemu-aarch64 -cpu cortex-a35 -L {rel(candidate/'target')} -E LD_BIND_NOW=1 {rel(stage)}/startup-check
qemu-aarch64 -cpu cortex-a35 -L {rel(candidate/'target')} -E LD_BIND_NOW=1 {rel(stage)}/loader-check {rel(binary)}
'''
(stage/'check.sh').write_text(code)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
           '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
           '-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',
           (work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
result=subprocess.run(container,capture_output=True,text=True,timeout=90)
for ext,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:
    (stage/('check.'+ext)).write_text(value)
assert result.returncode==0,(stage,result.stdout,result.stderr)
assert 'MUXRETRO_STARTUP_CASES_OK cases=18' in result.stdout
assert 'MUXRETRO_REAL_NO_CONTENT_LOADER_AND_SMOKE_CORE_OK' in result.stdout
inputs=[core/n for n in ['startup.c','startup.h','core.c','core.h','environment.c','main.c']]
sources=[Path(__file__),patch,repo/'port/diagnostics/phase4-muxretro-startup-check.c',repo/'port/diagnostics/phase4-muxretro-no-content-check.c']
report={'passed':True,'build_stage':str(build),'parser_cases':18,
        'real_loader_exercised_with_C40_core':True,'capability_and_rejection_guards_passed':True,
        'native_console_tested':False,'device_written':False,
        'patched_source_sha256':{str(p.relative_to(source)):sha(p) for p in inputs},
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-no-content-checks').write_text(str(stage)+'\n')
print('C41 actual parser/loader QEMU checks passed:',stage)
print(result.stdout)
