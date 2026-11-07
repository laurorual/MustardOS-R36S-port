#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C85 public evidence, never the real filesystem inventory/request/payloads."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require
import phase4_root_recovery as recovery

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/recovery-image'
    record=Path((area/'latest-reference').read_text().strip());check=Path((area/'latest-checks').read_text().strip())
    require(record.resolve().is_relative_to(area) and check.resolve().is_relative_to(area),'Evidence locations')
    host=json.loads((record/'host-analysis.json').read_text());native=json.loads((record/'analysis.json').read_text())
    cases=json.loads((check/'analysis.json').read_text());request=json.loads((record/'request.json').read_text())
    require(host['passed'] is True and host['operation']=='reference' and native['passed'] is True,'Reference required')
    require(host['consumer_analysis_sha256']==sha(record/'analysis.json') and host['request_sha256']==sha(record/'request.json'),'Reference binding')
    require(host['checks_sha256']==sha(check/'analysis.json') and cases['passed'] is True and cases['case_count']==len(cases['cases'])==host['component_checks'],'Check binding')
    for n,h in host['source_sha256'].items():require(sha(repo/n)==h,'Reference source changed')
    for n,h in cases['source_sha256'].items():require(host['source_sha256'][n]==h,'Tested source binding')
    require(native['root_image_bytes']==512*1024*1024 and native['root_fsck_exit']==0 and native['source_image_unchanged'] is True,'Reference scan')
    require(all(native[n] is False for n in ['recovery_image_created','postboot_observation_created','seed_generated_or_loaded','device_contacted_or_written','reboot_requested']),'Reference only')
    parents=host['parent_proofs_sha256']
    for name,h in parents.items():
        root=repo/'dist/phase4'/name;require(sha(root/'SHA256SUMS')==h,'Parent manifest changed')
        for n,value in sums(root/'SHA256SUMS').items():require(sha(root/n)==value,'Parent proof changed')
    tree=json.loads((record/'tree.json').read_text());history=[n for n in tree if n.startswith('var/lib/muos-diagnostic/c')]
    require(len(tree)==native['tree_entry_count'] and len(history)==9,'Real inventory counts')
    require(not any(tree[n]['external_xattrs'] for n in (recovery.CREDIT,recovery.NO_CREDIT,recovery.COUNTER) if n in tree),'Current replacement inode EA qualification')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area));out=repo/'dist/phase4/recovery-image';require(not out.exists(),'Existing proof must remain intact')
    result={'passed':True,'experiment':'C85_REGULAR_EXT4_RECOVERY_COLLECTOR_AND_COMPOSER','component_checks':cases['case_count'],
        'production_regular_image_composer_implemented':True,'regular_snapshot_postboot_collector_implemented':True,
        'physical_postboot_capture_backend_available':False,'physical_p2_writer_available':False,
        'real_reference_root_bytes':native['root_image_bytes'],'real_reference_tree_entries':len(tree),
        'real_reference_private_file_count':native['private_file_count'],'real_reference_consumed_markers':len(history),
        'real_reference_fsck_exit':0,'real_reference_backup_unchanged':True,
        'real_reference_replacement_private_inodes_external_EAs':False,
        'synthetic_composition_fsck_exit':0,'synthetic_public_tree_identity_links_and_xattrs_preserved':True,
        'synthetic_root0777_to0755_explicitly_verified':True,'C84_fixture_root_mode_claim_qualified_by_C85':True,
        'external_EAs_on_replaced_private_inodes_refused':True,'active_once_tokens_refused_consumed_history_preserved':True,
        'real_recovery_image_created':False,'real_seed_generated_or_loaded':False,'device_contacted_or_written':False,
        'candidate_provisioned':False,'reboot_requested':False,'parent_proofs_sha256':parents,
        'private_inventory_request_hashes_or_payloads_included':False}
    write_new(public/'analysis.json',(json.dumps(result,indent=2)+'\n').encode())
    shutil.copyfile(check/'analysis.json',public/'component-checks.json')
    for n in ['fixtures.stdout','fixtures.stderr','fixtures.exit']:shutil.copyfile(check/n,public/n)
    sources={repo/n for n in host['source_sha256']};sources.update([Path(__file__),repo/'docs/analysis/phase4-recovery-image.md'])
    for source in sorted(sources):
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    forbidden=[request['backup_sha256'],*(r['sha256'] for r in request['backup_private_files'].values())]
    old=Path((repo/'build/phase4/root-recovery/latest-readiness').read_text().strip())
    binding=json.loads((old/'binding.json').read_text());forbidden.append(binding['backup_prefix_sha256'])
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public symlink')
        if p.is_file():
            require(p.suffix.lower() not in {'.ext4','.img','.bin','.dat','.tar','.gb','.sav','.state'},'Public payload')
            require(not any(value.encode() in p.read_bytes() for value in forbidden),'Private hash in proof')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    shutil.move(str(public),out);print('C85 redacted reference/composer proof verified:',out)

if __name__=='__main__':main()
