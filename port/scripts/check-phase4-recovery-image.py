#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C85 container integration tests for production regular-image functions."""
from pathlib import Path
import ast,json,os,subprocess,tempfile
from phase4_backup_core import sha
from phase4_candidate import sums

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'recovery-image'
os.umask(0o077);area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
proof=repo/'dist/phase4/root-recovery'
for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
sources=[Path(__file__),repo/'port/scripts/phase4_recovery_image.py',repo/'port/diagnostics/phase4-recovery-image-fixture.py',
    repo/'port/scripts/phase4_root_recovery.py',repo/'port/scripts/phase4_root_migration.py',repo/'port/scripts/phase4_backup_core.py',
    repo/'port/scripts/phase4-recovery-image.py',repo/'port/scripts/prepare-phase4-recovery-image.py',
    repo/'port/device/rk-r35s-p0/launcher-once/policy.sh',repo/'port/device/rk-r35s-p0/boot/select-functions.sh']
source_hashes={str(p.relative_to(repo)):sha(p) for p in sources}
container=(work/'rootfs-container.iid').read_text().strip()
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-recovery-image-fixture.py','/work/'+str(stage.relative_to(work))]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',str(p.returncode)+'\n')]: (stage/('fixtures.'+ext)).write_text(data)
assert p.returncode==0,(stage,p.stdout[-800:],p.stderr[-2000:])
result=json.loads((stage/'fixture-results.json').read_text())
assert result['passed'] is True and result['case_count']==len(result['cases'])
for s in sources:
    if s.suffix=='.py':ast.parse(s.read_text())
assert all(sha(repo/n)==h for n,h in source_hashes.items()),'Sources changed during checks'
result.update({'physical_device_contacted_or_written':False,'synthetic_regular_images_only':True,
    'prior_C84_proof_sha256':sha(proof/'SHA256SUMS'),'source_sha256':source_hashes})
(stage/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C85 regular-image checks:',result['case_count'],'passed:',stage)
