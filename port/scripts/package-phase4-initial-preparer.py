#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C93 offline checks and real read-only asset/refusal audits only."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/initial-migration'
    check=Path((area/'latest-preparer-checks').read_text().strip())
    require(check.resolve().is_relative_to(area),'Private test record location')
    report=json.loads((check/'analysis.json').read_text())
    require(report['passed'] is True and report['case_count']==len(report['cases']) and
        report['physical_device_or_network_contacted'] is False and
        report['host_composition_main_executed_end_to_end'] is False,'Offline checks required')
    for n,h in report['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    for name,h in report['parent_proofs_sha256'].items():
        root=repo/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent proof binding changed')
        for n,wanted in sums(root/'SHA256SUMS').items():require(sha(root/n)==wanted,'Parent proof changed')
    audits={n:json.loads((check/n).read_text()) for n in
        ['actual-backup-check.json','actual-stale-refusal.json','actual-factory-check.json']}
    for r in audits.values():require(r['passed'] is True,'Read-only actual asset/refusal audit required')
    require(audits['actual-backup-check.json']['all_current_host_backup_artifacts_reverified'] is True and
        audits['actual-stale-refusal.json']['no_container_RNG_stage_device_or_deployment_started'] is True and
        audits['actual-factory-check.json']['existing_private_factory_copy_reverified_against_C79'] is True,
        'Actual read-only audit claims incomplete')
    out=repo/'dist/phase4/initial-preparer';require(not out.exists(),'Do not replace a frozen proof')
    public=Path(tempfile.mkdtemp(prefix='public-preparer.',dir=area))
    summary={'passed':True,'schema':93,'experiment':'C93_FRESH_INITIAL_PREPARER_AND_DESCRIPTOR_CALLBACK_OFFLINE',
        'component_check_count':report['case_count'],'real_32MiB_ext4_fixtures':True,
        'actual_existing_host_backup_artifact_count':audits['actual-backup-check.json']['artifact_count'],
        'actual_host_backup_and_private_C79_factory_bytes_reverified':True,'actual_stale_capture73_refused':True,
        'physical_device_or_network_contacted':False,'host_composition_main_executed_end_to_end':False,
        'production_512MiB_candidate_composed':False,'physical_card_writer_available':False,
        'privileged_initial_entrypoint_executed':False,'boot_handoff_authorized':False,
        'parent_proofs_sha256':report['parent_proofs_sha256'],'private_images_payloads_contexts_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    for name in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit',*audits]:
        shutil.copyfile(check/name,public/('component-checks.json' if name=='analysis.json' else name))
    sources={repo/n for n in report['source_sha256']}
    sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-initial-preparer.md'])
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():require(p.suffix.lower() not in {'.ext4','.img','.raw','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n'
        for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C93 offline preparer proof:',out)

if __name__=='__main__':main()
