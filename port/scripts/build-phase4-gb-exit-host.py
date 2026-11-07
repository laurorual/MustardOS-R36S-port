#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C50 bounded native-hotkey exit; preserve C47 binaries and SDK."""
from pathlib import Path
import json, shutil, subprocess, tempfile
from phase4_candidate import sha

repo = Path(__file__).resolve().parents[2]
work = repo/'build/phase4'
area = work/'gb-exit'
area.mkdir(exist_ok=True)
old = Path((work/'nes-core/latest-host').read_text().strip())
prior = json.loads((old/'analysis.json').read_text())
assert prior['passed'] and sha(old/'source/bin/muxretro') == prior['binary_sha256']
for name, digest in prior['source_sha256'].items():
    assert sha(repo/name) == digest
stage = Path(tempfile.mkdtemp(prefix='host.', dir=area))
(area/'latest-host-attempt').write_text(str(stage)+'\n')
shutil.copytree(old, stage, dirs_exist_ok=True)
patch = repo/'port/patches/0015-muxretro-diagnostic-hotkey-exit.patch'
header = repo/'port/diagnostics/phase4-diagnostic-exit.h'
shutil.copyfile(header, stage/'source/retro/core'/header.name)
subprocess.run(['git', '-C', str(stage/'source'), 'apply', str(patch)], check=True)
for name in ['core/main.o','core/startup.o','input/hotkeys.o']:
    (stage/'source/retro'/name).unlink()
rel = lambda p: '/work/'+str(p.relative_to(work))
code = (old/'build.sh').read_text().replace(rel(old), rel(stage))
root = '/work/rootfs-candidate/composition.w59vz7vo/target'
code += f'''
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(stage/'source/bin/muxretro')} --version
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(stage/'source/bin/muxretro')} --help
'''
(stage/'build.sh').write_text(code)
cmd = ['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
       '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
       '-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
for ext, value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:
    (stage/('build.'+ext)).write_text(value)
assert r.returncode == 0, (stage, r.stderr[-2500:])
# Verify the patch only touches the five declared files; preserve all other
# frontend source and the C47 executable. The header contains exit policy only.
for p in (old/'source/retro').rglob('*'):
    if p.is_file() and p.suffix in {'.c','.h'} and p.relative_to(old/'source').as_posix() not in {'retro/core/main.c','retro/core/startup.h','retro/core/startup.c','retro/input/hotkeys.h','retro/input/hotkeys.c'}:
        assert sha(p) == sha(stage/'source'/p.relative_to(old/'source'))
assert sha(old/'source/bin/muxretro') == prior['binary_sha256']
assert (work/'graphics-config/output/.config').read_bytes() == (work/'network-tools/baseline.config').read_bytes()
report = {'passed':True,'experiment':'C50_HOTKEY_EXIT_HOST','parent_stage':str(old),
          'parent_analysis_sha256':sha(old/'analysis.json'),'binary_sha256':sha(stage/'source/bin/muxretro'),
          'loader_checked':True,'device_written':False,'source_sha256':{
              str(p.relative_to(repo)):sha(p) for p in [Path(__file__),patch,header]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(area/'latest-host').write_text(str(stage)+'\n')
print('C50 hotkey exit host built and loader checked:',stage)
