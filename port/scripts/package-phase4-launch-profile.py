#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C117 sanitized check-only measurements, explicitly not graphical approval."""
import json,os,shutil,tempfile
from pathlib import Path
import phase4_launch_profile as m
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);out=m.REPO/'dist/phase4/launch-profile'
    m.require(not out.exists(),'Never replace frozen C117 proof');m.qualified()
    stage=Path((m.AREA/'latest-complete').read_text().strip())
    m.require(stage.resolve().is_relative_to(m.AREA),'Known C117 stage')
    r=json.loads((stage/'analysis.json').read_text());intent=json.loads((stage/'intent.json').read_text())
    m.require(r['passed'] is True and r['schema']==117 and r['metrics']==m.metrics((stage/'profile.stdout').read_text()),'Native C117 metrics')
    for n in ['before','mounts-before','allocate','prepare','validate','profile','validate-after','after','mounts-after','cleanup','post-cleanup-health']:
        m.require((stage/(n+'.exit')).read_text()=='0\n','All C117 receipts passed')
    m.require((stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==(stage/'post-cleanup-health.stdout').read_bytes(),'Identical native infrastructure')
    m.require((stage/'mounts-before.stdout').read_bytes()==(stage/'mounts-after.stdout').read_bytes(),'Identical global mounts')
    m.require((stage/'cleanup.stdout').read_text()=='C117_RAM_REMOVED_ROOT_RO_NO_UI\n','Authentic RAM cleanup')
    checks=Path((m.AREA/'latest-checks').read_text().strip());tested=json.loads((checks/'analysis.json').read_text())
    m.require(checks.resolve().is_relative_to(m.AREA) and tested['passed'] and r['checks_analysis_sha256']==m.sha(checks/'analysis.json'),'Bound tests')
    sources={Path(__file__),m.REPO/'docs/archive/phase4/phase4-launch-profile.md'}
    for n,h in r['source_sha256'].items():m.require(m.sha(m.REPO/n)==h,'Frozen C117 source');sources.add(m.REPO/n)
    public=Path(tempfile.mkdtemp(prefix='public.',dir=m.AREA))
    report={k:v for k,v in r.items() if k not in ['kernel_boot_id','C116_analysis_sha256','checks_analysis_sha256','source_sha256']}
    report['parent_proof_sha256']=m.sha(m.session.proof('resident-boot-session')/'SHA256SUMS')
    report['offline_cases']=tested['case_count']
    write_new(public/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({k:v for k,v in tested.items() if k!='source_sha256'},indent=2)+'\n').encode())
    for source in sources:
        target=public/'source'/source.relative_to(m.REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    private=m.session.previous.resident.qualified_rom()[1]
    forbidden=[r['kernel_boot_id'].encode(),private['ROM_sha256'].encode()]
    for p in public.rglob('*'):
        m.require(not p.is_symlink(),'No public aliases')
        if p.is_file():
            data=p.read_bytes();m.require(p.suffix in {'.py','.md','.json'} and not any(v in data for v in forbidden),'No private content')
    write_new(public/'SHA256SUMS',''.join(m.sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    for p in public.rglob('*'):
        if p.is_file():
            with p.open('rb') as f:os.fsync(f.fileno())
    for p in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(p)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C117 sanitized check-only proof:',out)
if __name__=='__main__':main()
