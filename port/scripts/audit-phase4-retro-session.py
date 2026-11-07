#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,tempfile
from phase4_candidate import sha
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'retro-session'
build=Path((area/'latest').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
for n,h in br['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='audit.',dir=area));candidate=Path(br['candidate_stage'])
rel=lambda p:'/work/'+str(p.relative_to(work));root=rel(candidate/'target');core=rel(build/'source/retro/core')
libraries=root+'/opt/muos/frontend/lib:'+root+'/lib:'+root+'/usr/lib'
q=f'qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={libraries}'
code=f'''cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
"$cc" -O2 -mcpu=cortex-a35 -I{core} /port/diagnostics/phase4-muxretro-startup-check.c {core}/startup.c {rel(build/'source/retro/netplay/address.c')} -o {rel(stage)}/parser
"$cc" -O2 -mcpu=cortex-a35 -I{core} /port/diagnostics/phase4-retro-deadline-check.c {core}/startup.c {rel(build/'source/retro/netplay/address.c')} -o {rel(stage)}/deadline
{q} {rel(stage)}/parser
{q} {rel(stage)}/deadline
{q} {rel(build/'source/bin/muxretro')} --version
{q} {rel(build/'source/bin/muxretro')} --help
rc=0;{q} {rel(build/'source/bin/muxretro')} core.so game.rom --diagnostic-seconds=1 || rc=$?
[ "$rc" = 1 ]
'''
(stage/'audit.sh').write_text(code)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for ext,value in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('audit.'+ext)).write_text(value)
assert r.returncode==0,(r.stdout,r.stderr)
assert 'C44_DEADLINE_CASES_OK=11' in r.stdout and 'cases=18' in r.stdout
report={'passed':True,'build_stage':str(build),'binary_sha256':sha(build/'source/bin/muxretro'),'parser_cases':18,'deadline_cases':11,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/diagnostics/phase4-retro-deadline-check.c']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-audit').write_text(str(stage)+'\n');print('C44 final diagnostic host audit passed:',stage)
