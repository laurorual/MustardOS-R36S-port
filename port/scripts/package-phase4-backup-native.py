#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C82 freeze redacted native backup/host-copy evidence; never backup payloads."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'offline-backup'
record=Path((area/'latest-host-copy').read_text().strip())
assert record.resolve().is_relative_to(area)
ack=json.loads((record/'analysis.json').read_text());download=Path(ack['download'])
assert download.resolve().is_relative_to(area) and ack['passed'] is True and ack['independent_host_copy_verified'] is True
receipt=json.loads((download/'backup.json').read_text());assert sha(download/'backup.json')==ack['helper_receipt_sha256']
for name,row in receipt['artifacts'].items():assert sha(download/name)==row['sha256'] and (download/name).stat().st_size==row['bytes'],name
assert receipt['passed'] is True and receipt['experiment']=='C81_OFFLINE_BACKUP_ONLY'
assert receipt['prefix_sha256']==ack['prefix_sha256'] and receipt['plan_sha256']==ack['plan_sha256']
assert all(receipt[k] is True for k in ['all_namespaces_checked','alias_cache_synchronized','private_state_from_fresh_backup','userdata_archive_verified','p3_unmounted'])
assert all(type(receipt[k]) is int and receipt[k]==0 for k in ['fat_fsck_exit','root_fsck_exit','data_fsck_exit'])
assert not any(receipt[k] for k in ['device_payload_writer_available','device_format_or_restore_available','candidate_provisioned','seed_loaded','reboot_requested'])
package=Path((area/'latest-package').read_text().strip());manifest=json.loads((package/'bundle/package.json').read_text())
assert sha(package/'bundle/migration-plan.json')==receipt['plan_sha256']
assert manifest['survey_boot_sequence']==receipt['boot_sequence']
assert receipt['source_root_modes']==ack['source_root_modes']=={'p2':0o777,'p3':0o777}
assert receipt['metadata_repair_required_before_boot'] is True and ack['metadata_repair_required_before_boot'] is True
assert receipt['source_root_policy_sha256']==hashlib.sha256((json.dumps(manifest['source_root_policy'],sort_keys=True)+'\n').encode()).hexdigest()
component_checks=Path((area/'latest-checks').read_text().strip());components=json.loads((component_checks/'analysis.json').read_text())
assert components['passed'] is True and components['case_count']==len(components['cases'])==86
for name,h in components['source_sha256'].items():assert sha(repo/name)==h,name
assert ack['transport_source_sha256']==sha(repo/'port/scripts/run-phase4-offline-backup.py')
checks=Path((area/'latest-transport-checks').read_text().strip());c=json.loads((checks/'analysis.json').read_text())
assert c['passed'] is True and c['case_count']==len(c['cases']) and c['network_or_device_contacted'] is False
for name,h in c['source_sha256'].items():assert sha(repo/name)==h,name
final=Path((area/'latest-deck-inspect').read_text().strip());post=json.loads((final/'inspect.json').read_text())
assert not post['card_mounts'] and not post['run_task_paths']
spec=importlib.util.spec_from_file_location('backup_transport',repo/'port/scripts/run-phase4-offline-backup.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport);transport.validate_inspection(post)
parents={}
for name in ['offline-backup','root-migration','gambatte-card-image']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,(name,n)
 parents[name]=sha(proof/'SHA256SUMS')
out=repo/'dist/phase4/backup-native';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public-native.',dir=area))
userdata=json.loads((download/'userdata-manifest.json').read_text())
result={'passed':True,'experiment':'C82_DECK_OFFLINE_BACKUP_AND_INDEPENDENT_HOST_COPY',
 'boot_sequence':receipt['boot_sequence'],'prefix_backup_bytes':receipt['artifacts']['prefix.backup']['bytes'],
 'private_file_count':len(json.loads((download/'private-files.json').read_text())['files']),
 'userdata_file_count':userdata['file_count'],'userdata_archive_bytes':receipt['artifacts']['userdata.tar']['bytes'],
 'fat_fsck_exit':0,'root_fsck_exit':0,'data_fsck_exit':0,'prefix_double_read_and_final_readback_verified':True,
 'independent_host_copy_hashes_and_fsync_verified':True,'private_state_from_offline_backup_verified':True,
 'card_partitions_unmounted':True,'root_snapshot_removed':True,'seed_loaded_or_key_generated':False,
 'candidate_provisioned':False,'device_payload_written':False,'reboot_requested':False,
 'device_writer_available':False,'execution_enabled':False,'post_boot_recovery_implemented':False,
 'backup_component_checks':86,'new_transport_checks':c['case_count'],'parent_proofs_sha256':parents,
 'source_root_modes':receipt['source_root_modes'],'source_root_metadata_repair_required_before_any_boot':True,
 'automount_chmod777_explicit_backup_policy_verified':True,'source_root_permissions_changed_by_this_helper':False,
 'live_UUID_private_leaf_or_prefix_hashes_and_backup_payloads_included':False}
(public/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
shutil.copyfile(checks/'analysis.json',public/'transport-checks.json')
shutil.copyfile(component_checks/'analysis.json',public/'component-checks.json')
for name in ['filesystem-fixtures.py','filesystem-fixtures.stdout','filesystem-fixtures.stderr','filesystem-fixtures.exit']:
 shutil.copyfile(component_checks/name,public/name)
sources={repo/'port/scripts'/name for name in ['run-phase4-offline-backup.py','check-phase4-backup-transport.py',Path(__file__).name]}
sources.add(repo/'docs/archive/phase4/phase4-backup-native.md')
sources.update(repo/name for name in components['source_sha256'])
for name in ['audit-phase4-backup-private.py','check-phase4-backup-audit.py','prepare-phase4-backup-audit.py','collect-phase4-backup-audit.py','validate-phase4-partial-root.py']:
 sources.add(repo/'port/scripts'/name)
native_audit=Path((area/'latest-native-audit').read_text().strip())
partial_validation=json.loads((native_audit/'private-validation.json').read_text());assert partial_validation['passed'] is True
for n,h in partial_validation['source_sha256'].items():assert sha(repo/n)==h,n
shutil.copyfile(native_audit/'private-validation.json',public/'partial-root-validation.json')
diagnostic=json.loads((native_audit/'diagnostic.json').read_text())
(public/'source-parents.json').write_text(json.dumps({'parents':diagnostic['parents'],'same_boot':diagnostic['same_boot'],
 'refusal_under_original_policy':diagnostic['refusal'],'source_root_metadata_repaired':False},indent=2)+'\n')
for src in sorted(sources):
 dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
private_plan=json.loads((package/'bundle/migration-plan.json').read_text())
forbidden=[private_plan['mbr_sha256'],private_plan['boot_prefix_16MiB_sha256'],receipt['prefix_sha256'],
           *(v['sha256'] for v in private_plan['private_files_at_live_survey'].values()),
           *(v['sha256'] for v in json.loads((download/'private-files.json').read_text())['files'].values())]
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.dat','.tar','.ext4','.fat','.img','.bin','.gb','.sav','.state','.bundle','.ini'}
  assert not any(value.encode() in p.read_bytes() for value in forbidden),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h,n
print('C82 native backup proof frozen; private backups excluded:',out)
