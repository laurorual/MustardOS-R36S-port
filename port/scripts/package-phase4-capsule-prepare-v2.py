#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C110 public script package and sanitized installation proof."""
import json,os,shutil,tempfile
from phase4_capsule_prepare_v2 import *
from phase4_backup_core import write_new,sync_dir

def main():
    os.umask(0o077);out=REPO/'dist/phase4/capsule-preparer-v2-installed'
    require(not out.exists(),'Never replace a frozen proof')
    stage=Path((AREA/'latest-complete').read_text().strip());package=Path((AREA/'latest-package').read_text().strip())
    checks=Path((AREA/'latest-checks').read_text().strip())
    require(all(p.resolve().is_relative_to(AREA) for p in [stage,package,checks]),'Known preparer stages')
    r=json.loads((stage/'analysis.json').read_text());p=json.loads((package/'analysis.json').read_text())
    tested=json.loads((checks/'analysis.json').read_text());plan=json.loads((stage/'plan.json').read_text())
    require(r['passed'] is p['passed'] is tested['passed'] is True and r['schema']==110 and p['schema']==110,'Qualified preparation and installation')
    require(r['files_added']==6 and r['directories_added']==1 and r['existing_files_replaced']==0 and
        r['root_read_only'] is r['RAM_removed'] is r['private_state_fingerprint_matched'] is
        r['infrastructure_and_global_mounts_preserved'] is r['native_empty_preparation_refused_without_mutation'] is True,
        'Exact six-leaf native installation')
    require(r['plan_sha256']==sha(stage/'plan.json') and r['checks_sha256']==sha(checks/'analysis.json') and
        plan['package_analysis_sha256']==tested['package_analysis_sha256']==sha(package/'analysis.json') and
        r['source_sha256']==p['source_sha256']==tested['source_sha256'],'Native/package/test binding')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Qualified source changed')
    for label in ['survey','before','inspect','dispatch','result','after','mounts-private','caller-check','native-stage',
                  'cleanup-stage','cleanup','post-cleanup-health']:
        require((stage/(label+'.exit')).read_text()=='0\n','Successful native receipt')
    require((stage/'before.stdout').read_bytes()==(stage/'after.stdout').read_bytes()==
        (stage/'post-cleanup-health.stdout').read_bytes(),'Infrastructure unchanged')
    require((stage/'caller-check.stdout').read_text()=='C107_PREPARER_CHECK_OK_NO_UI\n' and
        (stage/'native-stage.stdout').read_text()=='C110_EMPTY_PREPARATION_REFUSED_NO_MUTATION\n','Native preparer checks')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=AREA))
    summary={**r,'preparation_schema':110,'checks':tested['case_count'],'public_assets_local':7,'public_assets_input':4,
        'identity_derived_on_device':True,'ROM_persistent_or_image_ELF_seed_included':False,'private_identity_included':False,
        'redistribution_approved':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({k:tested[k] for k in ['passed','case_count','cases',
        'identity_crosschecked_with_Python','transaction_scope_files','device_or_network_accessed']},indent=2)+'\n').encode())
    for n,h in p['package_files'].items():
        f=package/'target'/PREFIX/n;require(sha(f)==h,'Payload changed')
        dest=public/'payload'/n;dest.parent.mkdir(exist_ok=True);shutil.copyfile(f,dest)
    for n,h in p['adapter_sha256'].items():
        require(sha(package/n)==h,'Adapter changed');dest=public/'adapter'/n;dest.parent.mkdir(exist_ok=True);shutil.copyfile(package/n,dest)
    for source in [REPO/n for n in r['source_sha256']]+[Path(__file__),REPO/'docs/archive/phase4/phase4-local-preparation-v2.md']:
        dest=public/'source'/source.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    meta=json.loads((stage/'manifest.json').read_text())
    for f in public.rglob('*'):
        require(not f.is_symlink(),'No public aliases')
        if f.is_file():require(not f.read_bytes().startswith(b'\x7fELF') and meta['kernel_boot_id'].encode() not in f.read_bytes(),'No binary/private identity')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    for f in public.rglob('*'):
        if f.is_file():
            with f.open('rb') as stream:os.fsync(stream.fileno())
    for d in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(d)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C110 sanitized preparer proof:',out)

if __name__=='__main__':main()
