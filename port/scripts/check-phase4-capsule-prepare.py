#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C107 preparation and C108 installation-scope checks; no device or ROM run."""
import ast,json,os,subprocess,tempfile
from phase4_capsule_prepare import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);package=Path((AREA/'latest-package').read_text().strip())
    require(package.resolve().is_relative_to(AREA),'Known package');r=json.loads((package/'analysis.json').read_text())
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Package source changed')
    for n,h in r['package_files'].items():require(sha(package/'target'/PREFIX/n)==h,'Package changed')
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA))
    old=target/'caller-payload';old.mkdir()
    import shutil
    for p in (base.proof('manual-caller-installed')/'payload').iterdir():shutil.copyfile(p,old/p.name)
    rel=lambda p:'/work/'+str(p.relative_to(WORK))
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--tmpfs','/run:rw,nosuid,nodev,size=32m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',(WORK/'rootfs-container.iid').read_text().strip(),
        'python3','/port/diagnostics/phase4-capsule-prepare-fixture.py',rel(package/'target'/PREFIX),rel(target),rel(old)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    for n,value in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:write_new(target/n,value.encode())
    require(result.returncode==0,'Preparer fixture failed: '+str(target))
    tests=json.loads((target/'fixture-results.json').read_text())
    ast.parse(rendered_installer())
    tests.update(schema=107,package_analysis_sha256=sha(package/'analysis.json'),source_sha256=r['source_sha256'],
        device_or_network_accessed=False,identity_crosschecked_with_Python=True,transaction_scope_files=6)
    write_new(target/'analysis.json',(json.dumps(tests,indent=2)+'\n').encode());sync_dir(target)
    (AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(AREA)
    print('C107/C108',tests['case_count'],'preparer/transaction checks passed:',target)

if __name__=='__main__':main()
