#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C122 offline resident adoption/partial refusal, nine-leaf rollback and recipe."""
import ast,json,os,subprocess,tempfile
from phase4_resident_batch import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);p=Path((AREA/'latest-package').read_text().strip());require(p.resolve().is_relative_to(AREA),'Known package')
 r=json.loads((p/'analysis.json').read_text())
 for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Package source unchanged')
 for n,h in r['package_files'].items():require(sha(p/'target'/PREFIX/n)==h,'Payload unchanged')
 stage=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA));rel=lambda q:'/work/'+str(q.relative_to(WORK))
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--cap-add=CHOWN','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--tmpfs','/run:rw,nosuid,nodev,size=64m',
 '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',(WORK/'rootfs-container.iid').read_text().strip(),
 'python3','/port/diagnostics/phase4-resident-batch-fixture.py',rel(p/'target'/PREFIX),rel(stage)]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
 for n,v in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:write_new(stage/n,v.encode())
 require(result.returncode==0,'C122 resident fixtures failed: '+str(stage))
 tests=json.loads((stage/'fixture-results.json').read_text());ast.parse(rendered_installer())
 tests.update(schema=122,package_analysis_sha256=sha(p/'analysis.json'),source_sha256=r['source_sha256'],device_or_network_accessed=False)
 write_new(stage/'analysis.json',(json.dumps(tests,indent=2)+'\n').encode());sync_dir(stage)
 (AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C122',tests['case_count'],'offline checks passed:',stage)
if __name__=='__main__':main()
