#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C41 loader and early CLI audit, never starts a graphical or physical session."""
from pathlib import Path
import json
import subprocess
import tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro'
build=Path((area/'latest').read_text().strip());assert build.resolve().is_relative_to(area)
report=json.loads((build/'analysis.json').read_text());assert report['passed']
for name,digest in report['source_sha256'].items():assert sha(repo/name)==digest,name
binary=build/'source/bin/muxretro';assert sha(binary)==report['binary_sha256']
checks=Path((area/'latest-no-content-checks').read_text().strip())
checked=json.loads((checks/'analysis.json').read_text());assert checked['passed']
for name,digest in checked['source_sha256'].items():assert sha(repo/name)==digest,name
for name,digest in checked['patched_source_sha256'].items():assert sha(build/'source'/name)==digest,name
candidate=Path(report['candidate_stage']);assert sha(candidate/'analysis.json')==report['candidate_analysis_sha256']
for name,digest in report['approved_frontend_libraries_preserved'].items():
    assert sha(candidate/'target/opt/muos/frontend/lib'/name)==digest
stage=Path(tempfile.mkdtemp(prefix='audit.',dir=area))
rel=lambda p:'/work/'+str(p.relative_to(work))
root=rel(candidate/'target');target=rel(binary)
libraries=root+'/opt/muos/frontend/lib:'+root+'/lib:'+root+'/usr/lib'
base=f'qemu-aarch64 -cpu cortex-a35 -L {root} -E LD_BIND_NOW=1 -E LD_LIBRARY_PATH={libraries}'
loader=root+'/lib/ld-linux-aarch64.so.1'
code=f'''{base} {loader} --inhibit-cache --library-path {libraries} --list {target}
{base} {target} --version
{base} {target} --help
for option in --unknown --netplay-host --subsystem=link --single-screen; do
 rc=0
 {base} {target} diagnostic.so --no-content "$option" || rc=$?
 [ "$rc" = 1 ]
done
echo MUXRETRO_FINAL_ELF_LOADER_AND_EARLY_CLI_OK
'''
(stage/'audit.sh').write_text(code)
container=['podman','run','--rm','--network=none','--read-only','--cap-drop=all',
           '--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev',
           '-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code]
result=subprocess.run(container,capture_output=True,text=True,timeout=60)
for ext,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:
    (stage/('audit.'+ext)).write_text(value)
assert result.returncode==0,(stage,result.stdout[-1500:],result.stderr[-2000:])
assert 'muxretro interface 1' in result.stdout and '<content|--no-content>' in result.stdout
assert 'MUXRETRO_FINAL_ELF_LOADER_AND_EARLY_CLI_OK' in result.stdout
output={'passed':True,'experiment':'C41_MUXRETRO_HOST_PREFLIGHT','build_stage':str(build),
        'build_analysis_sha256':sha(build/'analysis.json'),'binary_sha256':sha(binary),
        'component_check_stage':str(checks),'component_check_analysis_sha256':sha(checks/'analysis.json'),
        'tested_component_sources_identical_to_final_build':True,'parser_cases':checked['parser_cases'],
        'final_ELF_loader_and_early_CLI_passed':True,'QEMU_bind_now':True,
        'graphical_runtime_qualified':False,'native_console_tested':False,'device_written':False,
        'source_sha256':{str(Path(__file__).relative_to(repo)):sha(Path(__file__))}}
(stage/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
(area/'latest-audit').write_text(str(stage)+'\n')
print('C41 muxretro host preflight passed; native runtime remains untested:',stage)
