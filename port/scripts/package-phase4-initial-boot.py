#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Publish redacted C97 evidence from an already-qualified first C79 boot.

Host files only. Never connects to, reboots or modifies the handheld.
"""
from pathlib import Path
import importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums


def main():
    os.umask(0o077)
    boot=importlib.import_module('collect-phase4-initial-boot')
    out=boot.REPO/'dist/phase4/initial-boot-native'
    require(not out.exists(),'Frozen first boot proof must not be replaced')
    stage,ack,expected,stable,old,common,matching=boot.lineage()
    collected=boot.prep.initial.latest(boot.AREA,'latest-complete')
    report=json.loads((collected/'analysis.json').read_text())
    binding=json.loads((collected/'binding.json').read_text())
    tests=boot.prep.initial.latest(boot.AREA,'latest-checks')
    checks=json.loads((tests/'analysis.json').read_text())
    require(report['passed'] is True and type(report['schema']) is int and report['schema']==97 and
        checks['passed'] is True and report['checks_sha256']==sha(tests/'analysis.json') and
        report['source_sha256']==checks['source_sha256'],'Qualified C97 receipt and tested sources')
    for n,h in checks['source_sha256'].items():
        require(sha(boot.REPO/n)==h,'Tested first boot source changed')
    require(report['boot_sequence']==expected and report['guard_match']==matching and
        report['stable_identity_files_verified']==len(stable) and
        report['initial_host_copy_sha256']==binding['initial_host_copy_sha256']==sha(stage/'host-copy.json') and
        binding['initial_host_copy']==str(stage) and binding['next_attempt_id']==ack['next_attempt_id'] and
        binding['next_attempt_sha256']==ack['next_attempt_sha256'] and
        binding['expected_counter']==expected and binding['guard_match']==matching,'Independent migration/first boot binding')
    require((collected/'exit').read_text()=='0\n' and
        (collected/'checks.sh').read_text()==boot.entropy.render(common,expected,stable,old),
        'Successful SSH execution of the derived read-only checks')
    observed=boot.entropy.decoded((collected/'stdout').read_text(),expected)
    require(report['kernel_boot_id']==observed['boot_id'],'Observed boot identity binding')
    flags=['physical_boot_after_initial_migration_qualified','seedless_no_credit_2048bits_path_verified',
        'rng_ready_before_new_creditable_seed_and_stop_verified','candidate_and_known_old_seed_hashes_absent',
        'root0755_readonly_p3_unmounted_PCM_closed_no_UI_or_once']
    for n in flags:require(report[n] is True,'Incomplete first boot qualification')
    require(report['device_written_rebooted_or_tests_rearmed_by_collector'] is False,
        'Qualification must remain read-only')
    parents={}
    for name in ['p2-initial-native',*checks['parent_proofs_sha256']]:
        root=boot.REPO/'dist/phase4'/name
        for n,h in sums(root/'SHA256SUMS').items():require(sha(root/n)==h,'Frozen parent proof changed')
        parents[name]=sha(root/'SHA256SUMS')
        if name in checks['parent_proofs_sha256']:
            require(parents[name]==checks['parent_proofs_sha256'][name],'Tested parent proof binding')
    # Never export generated shell, binding, boot ID, receipt hashes,
    # image hashes, trees, or the private check-analysis fields.
    public=Path(tempfile.mkdtemp(prefix='public-native.',dir=boot.AREA))
    summary={'passed':True,'schema':97,'experiment':report['experiment'],'boot_sequence':expected,
        'guard_match':matching,'stable_identity_files_verified':len(stable),
        **{n:True for n in flags},'device_written_rebooted_or_tests_rearmed_by_collector':False,
        'native_positive_lineage_and_SSH_main_executed':True,'parent_proofs_sha256':parents,
        'new_audio_game_or_control_tests_performed':False,'private_runtime_data_included':False}
    sanitized_checks={n:checks[n] for n in ['passed','case_count','cases','source_sha256',
        'parent_proofs_sha256','network_or_physical_media_contacted']}
    write_new(public/'analysis.json',boot.recovery.encoded(summary))
    write_new(public/'checks.json',boot.recovery.encoded(sanitized_checks))
    sources={Path(__file__),boot.REPO/'docs/archive/phase4/phase4-initial-boot.md',
        *[boot.REPO/n for n in checks['source_sha256']]}
    for source in sources:
        target=public/'source'/source.relative_to(boot.REPO)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden={report['kernel_boot_id'],ack['next_attempt_id'],ack['next_attempt_sha256'],
        report['initial_host_copy_sha256'],checks['composition_receipt_sha256'],
        checks['common_sha256'],checks['guard_tree_sha256'],*old,
        *[row['sha256'] for row in stable.values()]}
    package=boot.prep.initial.latest(boot.prep.AREA,'latest-package')
    metadata=json.loads((package/'analysis.json').read_text())
    ctx=json.loads((package/'bundle/context.json').read_text())
    forbidden.update([ctx['candidate_sha256'],ctx['expected_observed_sha256']])
    for rows in [ctx['physical_capture']['backup_private_files'],
        json.loads((Path(metadata['C93_composition'])/'private-files.json').read_text())]:
        forbidden.update(row['sha256'] for row in rows.values())
    for f in public.rglob('*'):
        require(not f.is_symlink(),'Public proof symlink')
        if f.is_file():
            require(f.suffix in {'.py','.md','.json'},'Unexpected public payload')
            data=f.read_bytes();require(not any(v.encode() in data for v in forbidden),'Private data in public proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n'
        for f in sorted(public.rglob('*')) if f.is_file()).encode())
    for f in public.rglob('*'):
        if f.is_file():
            fd=os.open(f,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(fd)
            finally:os.close(fd)
    for folder in sorted((f for f in public.rglob('*') if f.is_dir()),key=lambda f:len(f.parts),reverse=True):sync_dir(folder)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C97 native first C79 boot proof:',out)


if __name__=='__main__':main()
