#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C102 sanitized native installation evidence, without private guard/identity."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_candidate import sha,sums
from phase4_backup_core import sync_dir

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/c79-layout-install'
    stage=Path((area/'latest-complete').read_text().strip());assert stage.resolve().is_relative_to(area)
    out=repo/'dist/phase4/c79-layout-installed';assert not out.exists(),'Frozen proof must not be replaced'
    report=json.loads((stage/'analysis.json').read_text());plan=json.loads((stage/'plan.json').read_text())
    manifest=json.loads((stage/'manifest.json').read_text())
    assert report['passed'] and report['schema']==102 and report['RAM_capsule_removed'] and report['root_read_only']
    assert report['plan_sha256']==manifest['plan_sha256']==sha(stage/'plan.json')
    assert report['source_sha256']==plan['source_sha256'] and report['parent_proofs_sha256']==plan['parent_proofs_sha256']
    for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n
    for name,h in report['parent_proofs_sha256'].items():
        root=repo/'dist/phase4'/name;assert sha(root/'SHA256SUMS')==h
        for n,digest in sums(root/'SHA256SUMS').items():assert sha(root/n)==digest,n
    checks=Path((area/'latest-checks').read_text().strip());assert checks.resolve().is_relative_to(area)
    tested=json.loads((checks/'analysis.json').read_text())
    assert tested['passed'] and tested['case_count']==35 and report['checks_sha256']==sha(checks/'analysis.json')
    assert tested['source_sha256']==report['source_sha256']
    assert (stage/'collected-result.txt').read_text()=='0\nC102_INSTALLED_444_BYTES_ONE_DIRECTORY_ROOT_RO\n'
    assert (stage/'cleanup.stdout').read_text()=='C102_RAM_REMOVED_ROOT_RO\n'
    assert (stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==(stage/'post-cleanup-health.stdout').read_bytes()
    for label in ['survey','before','inspect','dispatch','result','after','mounts-private','cleanup','post-cleanup-health']:
        assert (stage/(label+'.exit')).read_text()=='0\n'
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
    summary={**report,'private_stage_or_runtime_identity_included':False,'raw_ROM_ELF_or_state_included':False,
        'transaction_checks':35,'private_only':True,'redistribution_approved':False}
    (public/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    (public/'checks.json').write_text(json.dumps(tested,indent=2)+'\n')
    for source in [repo/n for n in report['source_sha256']]+[Path(__file__),repo/'docs/archive/phase4/phase4-c79-layout-install.md']:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    files=sorted(p for p in public.rglob('*') if p.is_file())
    assert all(not p.is_symlink() and p.suffix in {'.py','.sh','.json','.md'} for p in files)
    (public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in files))
    for p in [*files,public/'SHA256SUMS']:
        with p.open('rb') as stream:os.fsync(stream.fileno())
    for d in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(d)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
    print('C102 sanitized native proof frozen:',out)

if __name__=='__main__':main()
