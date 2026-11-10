#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C86 freeze redacted native reference evidence; no private capture payloads."""
from pathlib import Path
import argparse,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require
from importlib import import_module
prep=import_module('prepare-phase4-physical-capture');collector=import_module('collect-phase4-physical-capture')

def main(host):
    os.umask(0o077);repo=prep.REPO;area=prep.AREA
    capture=prep.latest(area,'latest-complete-reference');ack=json.loads((capture/'host-copy.json').read_text())
    require(ack['passed'] is True and ack['mode']=='reference','Completed independent reference required')
    for k in ['independent_C85_scan_verified','all_artifact_hashes_and_fsync_verified','complete_tree_matches_native','physical_reference_validated']:
        require(ack[k] is True,'Independent verification incomplete')
    require(ack['physical_postboot_validated'] is False,'Reference only')
    receipt=json.loads((capture/'analysis.json').read_text());require(sha(capture/'analysis.json')==ack['native_receipt_sha256'],'Capture receipt changed')
    package=prep.latest(area,'latest-package-reference');package_report=json.loads((package/'analysis.json').read_text());bundle=package/'bundle'
    require(sha(bundle/'package.json')==ack['package_manifest_sha256']==package_report['package_manifest_sha256'],'Package binding')
    manifest=json.loads((bundle/'package.json').read_text());context=json.loads((bundle/'context.json').read_text())
    collector.validate(receipt,manifest,context)
    for n,row in receipt['artifacts'].items():require(sha(capture/n)==row['sha256'] and (capture/n).stat().st_size==row['bytes'],'Private capture changed')
    independent=capture/'independent';require(json.loads((independent/'analysis.json').read_text())['passed'] is True,'Independent C85 scan')
    require(json.loads((capture/'tree.json').read_text())==json.loads((independent/'tree.json').read_text()),'Independent tree mismatch')
    check=prep.latest(area,'latest-checks');cases=json.loads((check/'analysis.json').read_text())
    require(cases['passed'] is True and cases['case_count']==len(cases['cases']) and sha(check/'analysis.json')==package_report['checks_sha256'],'Tested package binding')
    for n,h in cases['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    parents={}
    for name in ['recovery-image','root-recovery','root-permissions','backup-native']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS')
    t=prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    protection=t.native(host,"from pathlib import Path; import json,hashlib; p=Path('/run/udev/rules.d/99-holo-automount.rules'); print(json.dumps({'guard_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ro':{n:int((Path('/sys/class/block')/n/'ro').read_text()) for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3']}}))")
    require(protection['guard_sha256']==context['automount_guard_sha256'] and set(protection['ro'].values())=={1},'Final Deck protection changed')
    if not (capture/'postflight.json').exists():write_new(capture/'postflight.json',(json.dumps({'inspection':survey,'protection':protection},indent=2)+'\n').encode())
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area));out=repo/'dist/phase4/physical-capture'
    require(not out.exists(),'Proof exists; do not overwrite')
    result={'passed':True,'experiment':'C86_PHYSICAL_REFERENCE_CAPTURE_AND_INDEPENDENT_C85_SCAN',
        'component_checks':cases['case_count'],'physical_capture_helper_implemented':True,'physical_reference_validated':True,
        'root_capture_bytes':receipt['root_bytes'],'boot_sequence':receipt['boot_sequence'],
        'private_file_count':receipt['private_file_count'],'tree_entry_count':receipt['tree_entry_count'],
        'root_fsck_exit':0,'physical_p2_double_read_and_guarded_capture_verified':True,
        'MBR_and_16MiB_boot_prefix_preserved':True,'independent_host_copy_hash_fsync_and_C85_tree_scan_verified':True,
        'card_unmounted_and_all_four_aliases_kernel_readonly':True,'runtime_guard_unchanged':True,'root_snapshot_removed':True,
        'physical_postboot_path_validated':False,'postboot_path_synthetic_protocol_tested':True,
        'postboot_context_or_handoff_fence_created':False,'device_payload_written':False,'userdata_mounted_or_copied':False,
        'seed_generated_or_loaded':False,'candidate_provisioned':False,'device_writer_available':False,'reboot_requested':False,
        'parent_proofs_sha256':parents,'private_snapshot_context_tree_or_hashes_included':False}
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    shutil.copyfile(check/'analysis.json',public/'component-checks.json')
    for n in ['fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(check/n,public/n)
    sources={repo/n for n in cases['source_sha256']};sources.update([Path(__file__),repo/'docs/archive/phase4/phase4-physical-capture.md'])
    for src in sorted(sources):
        dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    forbidden=[context[n] for n in ['mbr_sha256','boot_prefix_16MiB_sha256','automount_guard_sha256','backup_prefix_sha256','reference_root_sha256']]
    forbidden.extend(row['sha256'] for row in context['backup_private_files'].values())
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():
            require(p.suffix.lower() not in {'.ext4','.img','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(h.encode() in p.read_bytes() for h in forbidden),'Private hash in proof')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);print('C86 physical reference and redacted proof verified:',out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
