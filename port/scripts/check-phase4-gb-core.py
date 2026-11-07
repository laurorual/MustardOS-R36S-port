#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-core';build=Path((area/'latest').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
for n,h in br['source_sha256'].items():assert sha(repo/n)==h
assert sha(Path(br['source_stage'])/'gambatte_libretro.so')==br['core_sha256']
rom=repo/'port/roms/gb/Super Mario Land (World) (Rev 1).gb'
assert rom.is_file() and not rom.is_symlink() and rom.stat().st_size==65536
subprocess.run(['git','check-ignore','--quiet',str(rom)],check=True)
import shlex
private_rom_sha=sha(rom)
stage=Path(tempfile.mkdtemp(prefix='api.',dir=area));(stage/'system').mkdir();rel=lambda p:'/work/'+str(p.relative_to(work));root='/work/rootfs-candidate/composition.w59vz7vo/target'
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -O2 -Wall -Wextra -Werror -Wno-misleading-indentation -mcpu=cortex-a35 -I/work/foundation/frontend-source/retro/core /port/diagnostics/phase4-gb-core-check.c -ldl -o {rel(stage)}/check
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 {rel(stage)}/check {rel(Path(br['source_stage'])/'gambatte_libretro.so')} {shlex.quote('/port/'+str(rom.relative_to(repo/'port')))} {rel(stage/'system')}
'''
(stage/'check.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr[-2500:]);assert 'C49_GB_API_OK' in r.stdout
report={'passed':True,'build_stage':str(build),'core_sha256':br['core_sha256'],'ROM_sha256':private_rom_sha,'real_core_and_ROM_executed':True,'RAM_serialize_and_input_callbacks_verified':True,'acoustic_qualified':False,'private_content':True,'device_written':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-gb-core-check.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-api').write_text(str(stage)+'\n');print('C49 private Game Boy API passed:',stage)
