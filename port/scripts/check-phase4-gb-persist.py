#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C53 initializer, bridge and dispatch fixtures. Synthetic content only."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-persist';area.mkdir(exist_ok=True)
source=repo/'port/device/rk-r35s-p0/gb-persist';parent=source.with_name('gb-state')
assert (source/'app-launch.sh').read_text()==(parent/'app-launch.sh').read_text().replace('C51','C53')
for f in source.glob('*.sh'):subprocess.run(['sh','-n',str(f)],check=True)
for proof in ['gameboy-ram-state','save-store-laboratory']:
 for n,h in sums(repo/'dist/phase4'/proof/'SHA256SUMS').items():assert sha(repo/'dist/phase4'/proof/n)==h
store=Path((work/'save-store/latest-checks').read_text().strip());sr=json.loads((store/'analysis.json').read_text())
metadata=Path((work/'gb-state/latest-checks').read_text().strip());mr=json.loads((metadata/'analysis.json').read_text())
for report in [sr,mr]:
 assert report['passed']
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));stage.chmod(0o755);rel='/work/'+str(stage.relative_to(work))
helper=repo/'port/diagnostics/phase4-save-directory.c';shutil.copyfile(helper,stage/helper.name)
shutil.copyfile(store/'muos-save-store',stage/'save-store');shutil.copyfile(metadata/'state-metadata',stage/'state-metadata')
for f in source.glob('*.sh'):shutil.copyfile(f,stage/f.name)
code=f'''
cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
flags='-O2 -mcpu=cortex-a35 -std=c11 -Wall -Wextra -Werror -fPIE -pie -fstack-protector-strong -Wl,-z,relro,-z,now'
"$cc" $flags {rel}/phase4-save-directory.c -o {rel}/save-directory
"$cc" $flags -DSTORE_DIRECTORY_TEST {rel}/phase4-save-directory.c -o {rel}/save-directory-test
'''
(stage/'build.sh').write_text(code)
container=(work/'rootfs-container.iid').read_text().strip()
common=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id']
r=subprocess.run(common+['--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',container,'sh','-eu','-c',code],capture_output=True,text=True,timeout=45)
(stage/'build.stderr').write_text(r.stderr);assert r.returncode==0,(stage,r.stderr)
fixture=repo/'port/diagnostics/phase4-gb-persist-check.py';shutil.copyfile(fixture,stage/fixture.name)
r=subprocess.run(common+['--user=0','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{stage}:/payload:ro,z','-v',f'{work}/rootfs-candidate/composition.w59vz7vo/target:/sysroot:ro,z',container,'python3','/payload/'+fixture.name],capture_output=True,text=True,timeout=90)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/('check.'+n)).write_text(v)
assert r.returncode==0,(stage,r.stderr[-3000:])
cases=re.findall(r'^C53_FIXTURE_PASS (.+)$',r.stdout,re.M);assert len(cases)>=20
report={'passed':True,'experiment':'C53_INTEGRATION_CHECKS','cases':cases,'case_count':len(cases),
        'directory_binary_sha256':sha(stage/'save-directory'),'store_binary_sha256':sr['binary_sha256'],
        'metadata_binary_sha256':mr['binary_sha256'],'native_or_commercial_content_used':False,
        'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),helper,fixture,*source.glob('*.sh')]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C53 integration checks passed:',len(cases),stage)
