#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build native and host fixtures for the session process owner in a container."""
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session';area.mkdir(exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='runner.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work))
code=f'''cc -O2 -Wall -Wextra -Werror /port/utils/muos-retro-runner.c -o {rel(stage)}/runner-host
/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc -O2 -Wall -Wextra -Werror -mcpu=cortex-a35 -fPIE -pie -Wl,-z,relro,-z,now /port/utils/muos-retro-runner.c -o {rel(stage)}/muos-retro-runner
'''
(stage/'build.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,text=True,capture_output=True,timeout=60)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('build.'+ext)).write_text(value)
assert r.returncode==0,r.stderr
report={'passed':True,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/utils/muos-retro-runner.c']},'native_sha256':sha(stage/'muos-retro-runner')}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-runner').write_text(str(stage)+'\n')
print('Host and AArch64 runner built:',stage)
