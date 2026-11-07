#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C94 isolated offline entry and transport checks; no media/network access."""
from pathlib import Path
import argparse,ast,importlib,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums

def main(kind):
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'p2-initial';area.mkdir(exist_ok=True)
    parent=Path((work/'initial-migration/latest-checks').read_text().strip())
    require(parent.resolve().is_relative_to(work/'initial-migration'),'Known C92 synthetic trees')
    parents={}
    for name in ['initial-preparer','initial-migration','p2-controller','card-readiness','p2-recovery-native','p2-recovery-boot']:
        root=repo/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Frozen parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
    helper=importlib.import_module('phase4-p2-initial')
    scripts={n for n in helper.SOURCES if n.endswith('.py')}
    scripts.update(['prepare-phase4-p2-initial.py','collect-phase4-p2-initial.py','watch-phase4-p2-initial.py',
        'package-phase4-p2-initial-native.py','package-phase4-p2-initial.py','check-phase4-p2-initial.py','prepare-phase4-initial-migration.py',
        'collect-phase4-p2-recovery.py','watch-phase4-p2-recovery.py','stage-phase4-initial-image.py'])
    sources=[*[repo/'port/scripts'/n for n in sorted(scripts)],repo/'port/diagnostics'/('phase4-p2-initial-'+kind+'-fixture.py')]
    hashes={str(p.relative_to(repo)):sha(p) for p in sources};stage=Path(tempfile.mkdtemp(prefix=kind+'-checks.',dir=area))
    container=(work/'rootfs-container.iid').read_text().strip()
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
        '/port/diagnostics/phase4-p2-initial-'+kind+'-fixture.py','/work/'+str(stage.relative_to(work)),
        '/work/'+str(parent.relative_to(work))]
    result=subprocess.run(argv,capture_output=True,timeout=600)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+n),data)
    require(result.returncode==0,'C94 '+kind+' fixture failed; inspect '+str(stage))
    report=json.loads((stage/'fixture-results.json').read_text())
    require(report['passed'] is True and report['case_count']==len(report['cases']) and len(set(report['cases']))==report['case_count'],'Complete unique checks')
    for path in sources:ast.parse(path.read_text())
    require(all(sha(repo/n)==h for n,h in hashes.items()),'Source changed during tests')
    report.update(physical_device_or_network_contacted=False,parent_proofs_sha256=parents,source_sha256=hashes)
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (area/('latest-'+kind+'-checks')).write_text(str(stage)+'\n');sync_dir(area)
    print('C94',kind,report['case_count'],'checks passed:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kind',choices=['entry','transport']);main(p.parse_args().kind)
