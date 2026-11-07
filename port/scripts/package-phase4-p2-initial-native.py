#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Publish C94 redacted native evidence only after independent collection."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums
import phase4_root_recovery as recovery

def main():
    os.umask(0o077);collector=importlib.import_module('collect-phase4-p2-initial');prep=collector.prep
    out=prep.REPO/'dist/phase4/p2-initial-native';require(not out.exists(),'Frozen proof must not be replaced')
    stage=prep.initial.latest(prep.AREA,'latest-complete');ack=json.loads((stage/'host-copy.json').read_text())
    require(type(ack['schema']) is int and ack['schema']==94 and
        ack['physical_boot_after_initial_migration_qualified'] is False,'Native migration is separate from boot qualification')
    for n in ['passed','physical_initial_p2_migration_verified','new_fence_independent_host_copy_verified',
        'all_receipts_and_directory_fsynced','all_card_aliases_RO_and_automount_guard_verified']:
        require(ack[n] is True,'Independent migration collection required')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Collected evidence changed')
    package=prep.initial.latest(prep.AREA,'latest-package');bundle=package/'bundle'
    p=json.loads((package/'analysis.json').read_text());manifest=json.loads((bundle/'package.json').read_text())
    require(p['passed'] is True and ack['package_manifest_sha256']==p['package_manifest_sha256']==sha(bundle/'package.json'),
        'Collected package binding')
    for n,h in manifest['files'].items():
        require(sha(bundle/n)==h,'Deployed package changed')
        if n.endswith('.py'):require(sha(prep.REPO/'port/scripts'/n)==h,'Deployed source changed')
    ctx=json.loads((bundle/'context.json').read_text());report=json.loads((stage/'analysis.json').read_text())
    require(sha(stage/'analysis.json')==ack['native_receipt_sha256'],'Native receipt binding')
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text()) for n in ['unlock-intent','write-intent','complete']}
    intent=recovery.load_attempt(stage/'handoff',ctx['next_attempt_id'],ack['next_attempt_sha256'])
    require(ack['next_attempt_id']==ctx['next_attempt_id'] and Path(ack['next_attempt_directory'])==stage/'handoff','Independent next fence')
    collector.validate(report,ctx,manifest,journal,intent)
    # Revalidate the composed candidate and capture rather than trusting a
    # successful collection pointer alone. No access to physical media here.
    value=prep.initial.inputs();composition,co=prep.composed(value)
    require(str(composition)==p['C93_composition'] and str(value['capture'])==p['C86_capture'] and
        co['candidate_sha256']==ctx['candidate_sha256'] and co['migration_counter']==ctx['expected_migration_counter'],
        'Initial composition/capture lineage changed')
    for name in ['tree.json','private-files.json','capture-context.json','observation.json']:
        require(json.loads((stage/'capture'/name).read_text())==json.loads((value['capture']/name).read_text()),'Fresh native scan differs')
    parents={}
    for name in ['p2-initial-prepared','initial-preparer','initial-migration','p2-controller','card-readiness',
        'p2-recovery-native','p2-recovery-boot','physical-capture','backup-native']:
        root=prep.REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
    public=Path(tempfile.mkdtemp(prefix='public-native.',dir=prep.AREA))
    summary={'passed':True,'schema':94,'experiment':'C94_NATIVE_INITIAL_C79_P2_MIGRATION',
        'captured_boot_sequence':value['native']['boot_sequence'],'migration_counter':report['migration_counter'],
        'written_bytes':report['written_bytes'],'pinned_C79_factory_verified':True,
        'independent_postboot_capture_and_three_image_scans_verified':True,'new_no_credit_seed_verified_not_loaded':True,
        'p1_MBR_p3_full_complement_preserved':True,'cold_p2_readback_verified':True,
        'all_four_aliases_kernel_readonly':True,'new_fence_independent_host_copy_verified':True,
        'automatic_retry_or_rollback':False,'boot_handoff_authorized':False,
        'physical_boot_after_initial_migration_qualified':False,'parent_proofs_sha256':parents,
        'private_images_payloads_contexts_trees_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    sources={Path(__file__),prep.REPO/'docs/analysis/phase4-p2-initial.md',
        *[prep.REPO/'port/scripts'/n for n in manifest['files'] if n.endswith('.py')],
        *[prep.REPO/'port/scripts'/n for n in ['collect-phase4-p2-initial.py','prepare-phase4-p2-initial.py','watch-phase4-p2-initial.py']]}
    for source in sources:
        target=public/'source'/source.relative_to(prep.REPO);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden={ctx['candidate_sha256'],ctx['expected_observed_sha256'],ctx['next_attempt_id'],report['next_attempt_sha256']}
    forbidden.update(v for n,v in ctx['physical_capture'].items() if n.endswith('sha256'))
    forbidden.update(row['sha256'] for row in ctx['physical_capture']['backup_private_files'].values())
    forbidden.update(row['sha256'] for row in json.loads((value['capture']/'private-files.json').read_text()).values())
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public symlink')
        if f.is_file():
            require(f.suffix not in {'.img','.ext4','.raw','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(v.encode() in f.read_bytes() for v in forbidden),'Private hash/fence in public proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);sync_dir(out.parent);print('C94 native initial migration proof:',out)

if __name__=='__main__':main()
