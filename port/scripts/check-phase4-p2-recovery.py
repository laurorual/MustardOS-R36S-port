#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C89 eligibility/adapter tests; no SSH, sudo, mount, or physical devices."""
from pathlib import Path
import ast,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new
from phase4_root_migration import require

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'p2-recovery'
os.umask(0o077);area.mkdir(exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
fixture=Path((work/'recovery-image/latest-checks').read_text().strip());require(fixture.resolve().is_relative_to(work/'recovery-image'),'C85 fixture location')
sources=[Path(__file__),repo/'port/diagnostics/phase4-p2-recovery-fixture.py',repo/'port/scripts/phase4_p2_recovery.py',
    *[repo/'port/scripts'/n for n in ['phase4_recovery_image.py','phase4_root_recovery.py','phase4_p2_controller.py','phase4_p2_write_core.py']]]
hashes={str(p.relative_to(repo)):sha(p) for p in sources};container=(work/'rootfs-container.iid').read_text().strip()
cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
    '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
    '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
    '/port/diagnostics/phase4-p2-recovery-fixture.py','/work/'+str(stage.relative_to(work)),'/work/'+str(fixture.relative_to(work))]
p=subprocess.run(cmd,capture_output=True,timeout=240)
for ext,data in [('stdout',p.stdout),('stderr',p.stderr),('exit',(str(p.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+ext),data)
require(p.returncode==0,'C89 fixture failed; inspect '+str(stage))
cases=[line[len('C89_PASS_'):] for line in p.stdout.decode().splitlines() if line.startswith('C89_PASS_')]
require(len(cases)>=20 and len(set(cases))==len(cases),'C89 cases incomplete')
for path in sources:ast.parse(path.read_text())
require(all(sha(repo/n)==h for n,h in hashes.items()),'Tested sources changed')
write_new(stage/'analysis.json',(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'real_ext4_32MiB_inputs_scanned':True,'physical_device_or_network_contacted':False,'physical_guard_adapter_stubbed':True,
    'source_sha256':hashes},indent=2)+'\n').encode());(area/'latest-checks').write_text(str(stage)+'\n')
print('C89 recovery:',len(cases),'checks passed:',stage)
