#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C105 installed caller checks and new finite installation scope fixtures."""
import ast,json,os,subprocess,tempfile
from phase4_manual_caller import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);stage=Path((AREA/'latest-package').read_text().strip())
    require(stage.resolve().is_relative_to(AREA),'Known C105 package');report=json.loads((stage/'analysis.json').read_text())
    for n,h in report['source_sha256'].items():require(sha(REPO/n)==h,'Package source changed')
    for n,h in report['package_files'].items():require(sha(stage/'target'/PREFIX/n)==h,'Package changed')
    for n,h in report['adapter_sha256'].items():require(sha(stage/n)==h,'Transaction changed')
    target=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA))
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '--tmpfs','/run:rw,nosuid,nodev,size=32m','-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',
        (WORK/'rootfs-container.iid').read_text().strip(),'python3','/port/diagnostics/phase4-manual-caller-fixture.py',
        '/work/'+str((stage/'target'/PREFIX).relative_to(WORK)),'/work/'+str(target.relative_to(WORK))]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(target/n,v.encode())
    require(r.returncode==0,'C105 caller fixture failed: '+str(target))
    tests=json.loads((target/'fixture-results.json').read_text())
    for p in source_files():
        if p.suffix=='.py':ast.parse(p.read_text())
        else:subprocess.run(['sh','-n',str(p)],check=True)
    tests.update(schema=105,package_analysis_sha256=sha(stage/'analysis.json'),source_sha256=report['source_sha256'],
        actual_device_accessed=False,installed_scripts_byte_identical_to_C104=True)
    write_new(target/'analysis.json',(json.dumps(tests,indent=2)+'\n').encode());sync_dir(target)
    (AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(AREA)
    print('C105',tests['case_count'],'caller contract checks passed:',target)

if __name__=='__main__':main()
