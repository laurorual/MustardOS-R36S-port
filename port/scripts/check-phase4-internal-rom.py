#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C113 private import control-flow tests; no physical card accessed."""
import json,os,subprocess,tempfile
from phase4_internal_rom import *
from phase4_backup_core import write_new,sync_dir

def main():
 os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
 stage=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA));rel=lambda p:'/work/'+str(p.relative_to(WORK))
 package=Path((assets.AREA/'latest-package').read_text().strip());binary=package/'target'/assets.PREFIX/'sync-path'
 for p in NATIVE.glob('*.sh'):subprocess.run(['sh','-n',str(p)],check=True)
 cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
 '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
 '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',(WORK/'rootfs-container.iid').read_text().strip(),
 'python3','/port/diagnostics/phase4-internal-rom-fixture.py','/port/device/rk-r35s-p0/internal-rom/functions.sh',rel(stage),rel(binary)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/n,v.encode())
 require(r.returncode==0,'C113 fixture failed: '+str(stage))
 report=json.loads((stage/'analysis.json').read_text());report.update(schema=113,source_sha256={str(p.relative_to(REPO)):sha(p) for p in sources()},
 sync_binary_sha256=sha(binary))
 (stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');sync_dir(stage)
 (AREA/'latest-checks').write_text(str(stage)+'\n');sync_dir(AREA)
 print('C113',report['case_count'],'private ROM import checks passed:',stage)
if __name__=='__main__':main()
