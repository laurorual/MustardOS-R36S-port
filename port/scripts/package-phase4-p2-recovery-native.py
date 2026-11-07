#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze redacted C89 native recovery evidence after independent collection."""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_recovery as recovery

def main():
    os.umask(0o077)
    collector=importlib.import_module('collect-phase4-p2-recovery');prep=collector.prep
    repo,area=prep.REPO,prep.AREA;out=repo/'dist/phase4/p2-recovery-native'
    require(not out.exists(),'Do not replace a frozen native proof')
    stage=prep.prep.prep.latest(area,'latest-complete-recover')
    ack=json.loads((stage/'host-copy.json').read_text())
    for n in ['passed','physical_p2_recovery_verified','new_fence_independent_host_copy_verified',
              'all_receipts_and_directory_fsynced','all_card_aliases_RO_and_automount_guard_verified']:
        require(ack[n] is True,'Native independent recovery collection required')
    require(ack['physical_boot_after_recovery_qualified'] is False,'Recovery proof is separate from boot qualification')
    for n,h in ack['files'].items():require(sha(stage/n)==h,'Collected recovery evidence changed')
    require(sha(stage/'analysis.json')==ack['native_receipt_sha256'],'Native receipt binding')
    package=prep.prep.prep.latest(area,'latest-package-recover')
    package_report=json.loads((package/'analysis.json').read_text())
    require(package_report['passed'] is True and sha(package/'bundle/package.json')==
        ack['package_manifest_sha256']==package_report['package_manifest_sha256'],'Native package binding')
    bundle=package/'bundle';manifest=json.loads((bundle/'package.json').read_text())
    ctx=json.loads((bundle/'context.json').read_text());report=json.loads((stage/'analysis.json').read_text())
    for n,h in manifest['files'].items():
        require(sha(bundle/n)==h,'Native package changed')
        if n.endswith('.py'):require(sha(repo/'port/scripts'/n)==h,'Native source changed')
    journal={n:json.loads((stage/'write-journal'/f'{n}.json').read_text())
        for n in ['unlock-intent','write-intent','complete']}
    intent=recovery.load_attempt(stage/'handoff',ctx['next_attempt_id'],ack['next_attempt_sha256'])
    require(ack['next_attempt_id']==ctx['next_attempt_id'] and
        Path(ack['next_attempt_directory'])==stage/'handoff','Independent next fence location')
    collector.validate(report,ctx,manifest,journal,intent)
    capture=Path(package_report['C86_capture']);composed=Path(package_report['C85_composition'])
    require(capture.resolve().is_relative_to(prep.WORK/'physical-capture') and
        composed.resolve().is_relative_to(prep.WORK/'recovery-image'),'Known preflight records')
    ca=json.loads((capture/'host-copy.json').read_text());cr=json.loads((capture/'analysis.json').read_text())
    require(ca['passed'] is True and ca['physical_postboot_validated'] is True and
        ca['independent_C85_scan_verified'] is True and ca['complete_tree_matches_native'] is True and
        sha(capture/'analysis.json')==ca['native_receipt_sha256'],'Independent physical capture binding')
    for n,row in cr['artifacts'].items():require(sha(capture/n)==row['sha256'],'Physical capture artifact changed')
    for n in ['tree.json','private-files.json','capture-context.json','observation.json']:
        require(json.loads((stage/'capture'/n).read_text())==json.loads((capture/n).read_text()),'Fresh native capture differs')
    require(json.loads((capture/'tree.json').read_text())==json.loads((capture/'independent/tree.json').read_text()) and
        json.loads((capture/'observation.json').read_text())==json.loads((capture/'independent/observation.json').read_text()),
        'Independent scan changed')
    co=json.loads((composed/'analysis.json').read_text());ch=json.loads((composed/'host-analysis.json').read_text())
    request=json.loads((composed/'request.json').read_text())
    require(ch['passed'] is True and sha(composed/'analysis.json')==ch['consumer_analysis_sha256'] and
        sha(composed/'request.json')==ch['request_sha256'] and request['operation']=='compose' and
        request['observed_sha256']==ctx['expected_observed_sha256']==cr['root_sha256'] and
        request['capture_context']==json.loads((capture/'capture-context.json').read_text()),'Composed source binding')
    require(co['passed'] is True and co['fresh_no_credit_seed_verified'] is True and co['old_seeds_removed'] is True and
        co['seed_loaded'] is False and co['recovery_counter']==ctx['expected_recovery_counter'] and
        co['root_image_sha256']==ctx['recovery_sha256']==sha(composed/'recovery.ext4'),'Recovery composition changed')
    parents={}
    for name in ['p2-recovery-prepared','p2-controller','card-readiness','physical-capture','recovery-image','backup-native']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Prior proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    watch=prep.prep.prep.latest(area,'latest-watch-checks');wc=json.loads((watch/'analysis.json').read_text())
    require(wc['passed'] is True and wc['case_count']==len(wc['cases']),'Observer checks required')
    for n,h in wc['source_sha256'].items():require(sha(repo/n)==h,'Tested observer source changed')
    public=Path(tempfile.mkdtemp(prefix='public-native.',dir=area))
    result={'passed':True,'schema':89,'experiment':'C89_NATIVE_P2_RECOVERY_AND_INDEPENDENT_NEXT_FENCE',
        'physical_postboot_capture_and_independent_scan_verified':True,'captured_boot_sequence':cr['boot_sequence'],
        'root_fsck_exit':0,'recovery_counter':report['recovery_counter'],'written_bytes':report['written_bytes'],
        'new_no_credit_seed_verified_not_loaded':True,'fresh_capture_and_three_image_scans_verified':True,
        'p1_MBR_p3_full_complement_preserved':True,'cold_p2_readback_verified':True,
        'all_four_aliases_kernel_readonly':True,'new_fence_independent_host_copy_verified':True,
        'automatic_retry_or_rollback':False,'boot_handoff_authorized':False,
        'physical_boot_after_recovery_qualified':False,'initial_C79_migration_qualified':False,
        'observer_offline_check_count':wc['case_count'],
        'parent_proofs_sha256':parents,'private_images_payloads_contexts_trees_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    write_new(public/'observer-checks.json',(json.dumps(wc,indent=2)+'\n').encode())
    sources={Path(__file__),repo/'port/scripts/collect-phase4-p2-recovery.py',
        repo/'port/scripts/prepare-phase4-p2-recovery.py',repo/'docs/analysis/phase4-p2-recovery-native.md'}
    sources.update(repo/'port/scripts'/n for n in manifest['files'] if n.endswith('.py'))
    sources.update(repo/n for n in wc['source_sha256'])
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    forbidden=[ctx['recovery_sha256'],ctx['expected_observed_sha256'],ctx['next_attempt_id'],
        report['next_attempt_sha256'],ctx['physical_capture']['attempt_sha256']]
    forbidden.extend(v for k,v in ctx['physical_capture'].items() if k.endswith('sha256'))
    forbidden.extend(row['sha256'] for row in ctx['physical_capture']['backup_private_files'].values())
    forbidden.extend(row['sha256'] for row in json.loads((capture/'private-files.json').read_text()).values())
    for file in public.rglob('*'):
        require(not file.is_symlink(),'Public symlink')
        if file.is_file():
            require(file.suffix not in {'.img','.ext4','.raw','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(value.encode() in file.read_bytes() for value in forbidden),'Private hash or fence in proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);print('C89 native recovery proof:',out)

if __name__=='__main__':main()
