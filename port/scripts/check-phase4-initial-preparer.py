#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C93 freshness gates and production descriptor callback, isolated in container."""
from pathlib import Path
import ast,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'initial-migration'
os.umask(0o077);stage=Path(tempfile.mkdtemp(prefix='preparer-checks.',dir=area))
parents={}
for name in ['initial-migration','gambatte-card-image','p2-recovery-native','p2-recovery-boot']:
    root=repo/'dist/phase4'/name
    for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Frozen proof changed')
    parents[name]=sha(root/'SHA256SUMS')
old=Path((area/'latest-checks').read_text().strip());require(old.resolve().is_relative_to(area),'Synthetic C92 fixture location')
prior=json.loads((old/'analysis.json').read_text());require(prior['passed'] is True,'C92 checks required')
for n,h in prior['source_sha256'].items():require(sha(repo/n)==h,'C92 tested source changed')
sources=[Path(__file__),repo/'port/diagnostics/phase4-initial-preparer-fixture.py',
    *[repo/'port/scripts'/n for n in ['prepare-phase4-initial-migration.py','phase4_p2_initial.py',
      'phase4_initial_migration.py','phase4_initial_image.py','phase4_recovery_image.py','phase4_root_recovery.py',
      'phase4_backup_core.py','phase4_root_migration.py','prepare-phase4-p2-recovery.py','collect-phase4-p2-recovery.py']]]
hashes={str(p.relative_to(repo)):sha(p) for p in sources};container=(work/'rootfs-container.iid').read_text().strip()
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-initial-preparer-fixture.py','/work/'+str(stage.relative_to(work)),
    '/work/'+str(old.relative_to(work))]
r=subprocess.run(cmd,capture_output=True,timeout=240)
for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',(str(r.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+ext),data)
require(r.returncode==0,'C93 fixture failure; inspect private stage '+str(stage))
result=json.loads((stage/'fixture-results.json').read_text())
require(result['passed'] is True and result['case_count']==len(result['cases']),'C93 fixture result')
for p in sources:ast.parse(p.read_text())
require(all(sha(repo/n)==h for n,h in hashes.items()),'Source changed during tests')
result.update({'physical_device_or_network_contacted':False,'host_composition_main_executed_end_to_end':False,
    'parent_proofs_sha256':parents,'source_sha256':hashes})
write_new(stage/'analysis.json',(json.dumps(result,indent=2)+'\n').encode());(area/'latest-preparer-checks').write_text(str(stage)+'\n')
print('C93 initial preparer/descriptor:',result['case_count'],'checks passed:',stage)
