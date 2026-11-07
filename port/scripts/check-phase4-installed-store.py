#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare C58 read-only backend and check installed-package dispatch policy."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile
from phase4_candidate import sha,sums
from phase4_installed_store import render_backend
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-installed';area.mkdir(exist_ok=True)
for name in ['gameboy-selective-persistence','gameboy-after-boot','save-store-installed']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
source=repo/'port/device/rk-r35s-p0/gb-persist/store.sh'
frozen=repo/'dist/phase4/gameboy-selective-persistence/source'/source.relative_to(repo)
assert source.read_bytes()==frozen.read_bytes()
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));stage.chmod(0o755)
(stage/'store-base.sh').write_text(render_backend(source.read_text()))
assets=list((repo/'port/device/rk-r35s-p0/gb-installed').glob('*.sh'))
for p in assets:shutil.copyfile(p,stage/p.name)
for p in stage.glob('*.sh'):subprocess.run(['sh','-n',str(p)],check=True)
fixture=repo/'port/diagnostics/phase4-installed-store-check.py';shutil.copyfile(fixture,stage/fixture.name)
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/run:rw,nosuid,nodev','--tmpfs','/tmp:rw,nosuid,nodev',
 '-v',f'{stage}:/payload:ro,z','-v',f'{work}/save-store-image/image.nlnmgzzb/target:/sysroot:ro,z',
 (work/'rootfs-container.iid').read_text().strip(),'python3','/payload/'+fixture.name]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/n).write_text(v)
assert r.returncode==0,(stage,r.stdout[-1500:],r.stderr[-2000:])
cases=re.findall('^C58_PASS (.+)$',r.stdout,re.M);assert len(cases)==34,len(cases)
sources=[Path(__file__),repo/'port/scripts/phase4_installed_store.py',fixture,source,*assets]
report={'passed':True,'experiment':'C58_INSTALLED_DISPATCH_CHECKS','case_count':len(cases),'cases':cases,
 'read_only_backend_sha256':sha(stage/'store-base.sh'),'C53_source_unchanged':True,'device_accessed':False,'private_content_used':False,
 'source_sha256':{str(p.relative_to(repo)):sha(p) for p in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C58 read-only backend/dispatch checks passed:',len(cases),stage)
