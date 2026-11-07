#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C88 bounded real-ext4 fixtures in the existing rootless build container."""
from pathlib import Path
import ast,importlib,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_root_migration import require

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'initial-image'
os.umask(0o077);area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
container=(work/'rootfs-container.iid').read_text().strip()
sources=[Path(__file__),repo/'port/diagnostics/phase4-initial-image-fixture.py',repo/'port/scripts/phase4_initial_image.py',
    repo/'port/scripts/phase4-initial-image.py',repo/'port/scripts/prepare-phase4-initial-image.py',
    repo/'port/scripts/stage-phase4-initial-image.py',
    *[repo/'port/scripts'/n for n in ['phase4_recovery_image.py','phase4_root_recovery.py','phase4_backup_core.py','phase4_root_migration.py']]]
hashes={str(p.relative_to(repo)):sha(p) for p in sources}
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-initial-image-fixture.py','/work/'+str(stage.relative_to(work))]
p=subprocess.run(cmd,capture_output=True,timeout=240)
for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',(str(p.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+ext),data)
require(p.returncode==0,'C88 fixtures failed; inspect private stage '+str(stage))
cases=[s[len('C88_PASS_'):] for s in p.stdout.decode().splitlines() if s.startswith('C88_PASS_')]
require(len(cases)>=10 and len(set(cases))==len(cases),'C88 incomplete cases')
entry=importlib.import_module('phase4-initial-image');staging=importlib.import_module('stage-phase4-initial-image')
for path in ['/dev/mmcblk0','/tmp/image','/work/../dev/mmcblk0']:
    try:entry.work_path(path)
    except ValueError:cases.append('finite-entry-refuses-'+path)
    else:raise AssertionError('Unqualified input path')
ast.parse(staging.RECEIVE)
for digest,counter in [('bad','72'),('0'*64,'0')]:
    rejected=subprocess.run(['/usr/bin/python3','-c',staging.RECEIVE,digest,counter],capture_output=True)
    require(rejected.returncode!=0 and not rejected.stdout,'Staging invalid binding reached filesystem')
    cases.append('staging-invalid-binding-before-any-file-creation-'+str(len(cases)))
for path in sources:ast.parse(path.read_text())
require(all(sha(repo/n)==h for n,h in hashes.items()),'Source changed during tests')
write_new(stage/'analysis.json',(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'real_ext4_32MiB_fixture':True,'physical_device_or_network_contacted':False,'source_sha256':hashes},indent=2)+'\n').encode())
(area/'latest-checks').write_text(str(stage)+'\n');print('C88 initial image:',len(cases),'checks passed:',stage)
