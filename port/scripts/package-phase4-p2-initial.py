#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C94 offline preparation only; never claim a physical migration."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/p2-initial'
    out=repo/'dist/phase4/p2-initial-prepared';require(not out.exists(),'Frozen proof must not be replaced')
    reports={};sources={Path(__file__),repo/'docs/archive/phase4/phase4-p2-initial.md'}
    for kind in ['entry','transport']:
        stage=Path((area/('latest-'+kind+'-checks')).read_text().strip())
        require(stage.resolve().is_relative_to(area),'Private test record location')
        r=json.loads((stage/'analysis.json').read_text())
        require(r['passed'] is True and r['case_count']==len(r['cases']) and r['physical_device_or_network_contacted'] is False,
            'Current isolated checks required')
        for n,h in r['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed');sources.add(repo/n)
        for name,h in r['parent_proofs_sha256'].items():
            root=repo/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent proof binding changed')
            for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
        reports[kind]=(stage,r)
    audit=area/'actual-stale-refusal.json';a=json.loads(audit.read_text())
    require(a['passed'] is True and a['actual_stale_capture_refused_before_SSH_RNG_or_stage'] is True,
        'Actual stale capture refusal required')
    public=Path(tempfile.mkdtemp(prefix='public-prepared.',dir=area))
    summary={'passed':True,'schema':94,'experiment':'C94_FINITE_INITIAL_P2_WRITER_PREPARED_OFFLINE',
        'offline_case_count':sum(r['case_count'] for _,r in reports.values()),
        'real_32MiB_ext4_coordination_with_stubbed_card':True,'regular_file_stream_receiver_checks':True,
        'actual_stale_capture_refused_before_SSH_RNG_or_stage':True,'finite_initial_operation_separate_from_recovery':True,
        'production_512MiB_candidate_composed':False,'privileged_namespace_and_physical_adapters_executed':False,
        'positive_deployment_collection_and_native_proof_mains_executed_end_to_end':False,
        'physical_card_written':False,'physical_boot_after_initial_migration_qualified':False,'boot_handoff_authorized':False,
        'parent_proofs_sha256':reports['entry'][1]['parent_proofs_sha256'],
        'private_images_payloads_contexts_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode());shutil.copyfile(audit,public/audit.name)
    for kind,(stage,r) in reports.items():
        for n in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit']:
            shutil.copyfile(stage/n,public/(kind+'-'+('checks.json' if n=='analysis.json' else n)))
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():require(p.suffix not in {'.ext4','.img','.raw','.dat','.bin','.tar','.gb','.sav','.state'},'Public payload')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C94 offline initial migration preparation:',out)

if __name__=='__main__':main()
