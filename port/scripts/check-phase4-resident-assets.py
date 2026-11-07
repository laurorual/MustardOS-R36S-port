#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C112 resident preparation, private ROM guards and transaction checks."""
import ast,json,os,subprocess,tempfile
from phase4_resident_assets import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);package=Path((AREA/'latest-package').read_text().strip());require(package.resolve().is_relative_to(AREA),'Known package')
 r=json.loads((package/'analysis.json').read_text())
 for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Package source changed')
 for n,h in r['package_files'].items():require(sha(package/'target'/PREFIX/n)==h,'Payload changed')
 target=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA));rel=lambda p:'/work/'+str(p.relative_to(WORK))
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=96m','--tmpfs','/run:rw,nosuid,nodev,size=64m',
 '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',(WORK/'rootfs-container.iid').read_text().strip(),
 'python3','/port/diagnostics/phase4-resident-fixture.py',rel(package/'target'/PREFIX),rel(target)]
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 for n,v in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]:write_new(target/n,v.encode())
 require(result.returncode==0,'Resident fixture failed: '+str(target))
 tests=json.loads((target/'fixture-results.json').read_text());ast.parse(rendered_installer())
 observation=current_observation();_,prior=qualified()
 for label,boot,uuid in [('boolean',True,observation['kernel_boot_id']),('old',prior['boot_sequence']-1,observation['kernel_boot_id']),
  ('bad-UUID',observation['boot_sequence'],'bad'),('old-counter-new-UUID',prior['boot_sequence'],observation['kernel_boot_id']),
  ('new-counter-old-UUID',observation['boot_sequence'],prior['kernel_boot_id'])]:
  try:observed_guard(boot,uuid)
  except (ValueError,AssertionError,TypeError):tests['cases'].append('current-boot-refuses-'+label)
  else:raise AssertionError(label)
 tests['case_count']=len(tests['cases'])
 tests.update(schema=112,package_analysis_sha256=sha(package/'analysis.json'),source_sha256=r['source_sha256'],device_or_network_accessed=False)
 write_new(target/'analysis.json',(json.dumps(tests,indent=2)+'\n').encode());sync_dir(target)
 (AREA/'latest-checks').write_text(str(target)+'\n');sync_dir(AREA)
 print('C112',tests['case_count'],'resident/ROM/transaction checks passed:',target)
if __name__=='__main__':main()
