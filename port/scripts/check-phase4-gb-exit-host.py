#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C47 parser/ELF and fixed-content launcher checks; no device access."""
from pathlib import Path
import json,os,subprocess,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-exit'
host=Path((area/'latest-host').read_text().strip());hr=json.loads((host/'analysis.json').read_text());assert hr['passed']
for n,h in hr['source_sha256'].items():assert sha(repo/n)==h
proof=repo/'dist/phase4/native-app-selection'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));rel=lambda p:'/work/'+str(p.relative_to(work));root='/work/rootfs-candidate/composition.w59vz7vo/target';src=rel(host/'source/retro/core')
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
for pair in startup:phase4-muxretro-startup-check deadline:phase4-retro-deadline-check content:phase4-content-deadline-check hotkey:phase4-hotkey-exit-check;do
 name=${{pair%%:*}};test=${{pair#*:}}
 "$cc" -O2 -mcpu=cortex-a35 -I{src} /port/diagnostics/$test.c {src}/startup.c {rel(host/'source/retro/netplay/address.c')} -o {rel(stage)}/$name
 qemu-aarch64 -cpu cortex-a35 -L {root} {rel(stage)}/$name
done
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(host/'source/bin/muxretro')} --version
qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={root}/opt/muos/frontend/lib:{root}/lib:{root}/usr/lib {rel(host/'source/bin/muxretro')} --help
'''
(stage/'check.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+ext)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr[-2500:]);assert 'C47_CONTENT_PARSER_OK cases=11' in r.stdout and 'C44_DEADLINE_CASES_OK=11' in r.stdout and 'cases=18' in r.stdout and 'C50_EXIT_CHECK_OK parser=12 policy=26' in r.stdout
report={'passed':True,'build_stage':str(host),'binary_sha256':hr['binary_sha256'],'parser_regression_cases':40,'C50_parser_cases':12,'exit_policy_cases':26,'device_accessed':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-hotkey-exit-check.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n');print('C50 parser/exit policy/loader checks passed:',stage)
