#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C92 real regular-ext4 composition and fault tests; no physical device."""
from pathlib import Path
import ast,importlib,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'initial-migration'
os.umask(0o077);area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
parents={}
for name in ['initial-image','recovery-image','root-recovery','p2-recovery-native','p2-recovery-boot']:
    p=repo/'dist/phase4'/name
    for n,h in sums(p/'SHA256SUMS').items():require(sha(p/n)==h,'Prior proof changed')
    parents[name]=sha(p/'SHA256SUMS')
sources=[Path(__file__),repo/'port/diagnostics/phase4-initial-migration-fixture.py',
    *[repo/'port/scripts'/n for n in ['phase4_initial_migration.py','phase4-initial-migration.py',
      'phase4_initial_image.py','phase4_recovery_image.py','phase4_root_recovery.py','phase4_backup_core.py','phase4_root_migration.py']]]
hashes={str(p.relative_to(repo)):sha(p) for p in sources};container=(work/'rootfs-container.iid').read_text().strip()
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-initial-migration-fixture.py','/work/'+str(stage.relative_to(work))]
r=subprocess.run(cmd,capture_output=True,timeout=240)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',(str(r.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+ext),data)
require(r.returncode==0,'C92 fixtures failed; inspect private stage '+str(stage))
result=json.loads((stage/'fixture-results.json').read_text());require(result['passed'] is True,'C92 fixture result')
entry=importlib.import_module('phase4-initial-migration')
for path in ['/dev/mmcblk0','/tmp/image','/work/../dev/mmcblk0']:
    try:entry.work_path(path)
    except ValueError:result['cases'].append('finite-entry-rejects-'+path)
    else:raise AssertionError('Invalid input path')
for p in sources:ast.parse(p.read_text())
require(all(sha(repo/n)==h for n,h in hashes.items()),'Source changed during tests')
result.update({'case_count':len(result['cases']),'physical_device_or_network_contacted':False,
    'production_512MiB_images_composed':False,'parent_proofs_sha256':parents,'source_sha256':hashes})
write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode());(area/'latest-checks').write_text(str(stage)+'\n')
print('C92 initial migration image:',result['case_count'],'checks passed:',stage)
