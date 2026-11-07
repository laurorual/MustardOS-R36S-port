#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C96 real ext4 coordinator/fault tests, isolated and without physical media."""
from pathlib import Path
import ast,importlib,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'root-repair-current';area.mkdir(exist_ok=True)
    helper=importlib.import_module('phase4-root-repair-current');sources={repo/'port/scripts'/n for n in helper.SOURCES if n.endswith('.py')}
    sources.update([Path(__file__),repo/'port/scripts/prepare-phase4-root-repair-current.py',repo/'port/diagnostics/phase4-root-repair-current-fixture.py'])
    hashes={str(p.relative_to(repo)):sha(p) for p in sources};parents={}
    for name in ['card-rearm-native','root-permissions','p2-controller','card-readiness','p2-initial-prepared']:
        root=repo/'dist/phase4'/name
        for n,d in sums(root/'SHA256SUMS').items():require(sha(root/n)==d,'Frozen parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));container=(work/'rootfs-container.iid').read_text().strip()
    cmd=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
        '/port/diagnostics/phase4-root-repair-current-fixture.py','/work/'+str(stage.relative_to(work))]
    result=subprocess.run(cmd,capture_output=True,timeout=300)
    for n,raw in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+n),raw)
    require(result.returncode==0,'C96 fixture failed; inspect '+str(stage))
    r=json.loads((stage/'fixture-results.json').read_text());require(r['passed'] is True and r['case_count']==len(set(r['cases'])),'Complete unique cases')
    for p in sources:ast.parse(p.read_text())
    require(all(sha(repo/n)==d for n,d in hashes.items()),'Tested source changed')
    r.update(source_sha256=hashes,parent_proofs_sha256=parents,network_or_physical_media_contacted=False)
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (area/'latest-checks').write_text(str(stage)+'\n');sync_dir(area);print('C96',r['case_count'],'offline checks passed:',stage)

if __name__=='__main__':main()
