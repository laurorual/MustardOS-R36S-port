#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C81 freeze source and synthetic evidence only; exclude the private bundle."""
from pathlib import Path
import importlib.util, json, shutil, tempfile
from phase4_candidate import sha, sums

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'offline-backup'
stage=Path((area/'latest-package').read_text().strip());checks=Path((area/'latest-checks').read_text().strip())
assert stage.resolve().is_relative_to(area) and checks.resolve().is_relative_to(area)
r=json.loads((stage/'analysis.json').read_text());c=json.loads((checks/'analysis.json').read_text())
assert r['passed'] is True and c['passed'] is True and r['checks_sha256']==sha(checks/'analysis.json')
assert c['case_count']==len(c['cases'])==r['checks_case_count'] and c['case_count']>=65
assert c['real_ext4_debugfs_fsck_and_tar_in_container'] is True
assert c['physical_block_opened'] is False and c['media_modified'] is False
assert r['bundle_inventory_verified'] is True
for key in ['native_qualified','SSH_requested','real_backup_created','device_written','candidate_provisioned','execution_enabled','device_writer_available']:assert r[key] is False,key
for n,h in r['parent_proofs_sha256'].items():
    parent=repo/'dist/phase4'/n
    for leaf,wanted in sums(parent/'SHA256SUMS').items():assert sha(parent/leaf)==wanted,(n,leaf)
    assert sha(parent/'SHA256SUMS')==h,n
assert sha(stage/'bundle/package.json')==r['bundle_manifest_sha256']
spec=importlib.util.spec_from_file_location('prepare_backup',repo/'port/scripts/prepare-phase4-offline-backup.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
prep.verify_bundle(stage/'bundle')
assert r['source_sha256']==c['source_sha256']
sources={Path(__file__),repo/'docs/analysis/phase4-offline-backup.md'}
for name,h in c['source_sha256'].items():assert sha(repo/name)==h,name;sources.add(repo/name)
assert (checks/'filesystem-fixtures.exit').read_text()=='0\n'
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
out=repo/'dist/phase4/offline-backup';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for name,report in [('analysis.json',r),('checks.json',c)]:
    (public/name).write_text(json.dumps(report,indent=2)+'\n')
for name in ['filesystem-fixtures.py','filesystem-fixtures.stdout','filesystem-fixtures.stderr','filesystem-fixtures.exit']:
    shutil.copyfile(checks/name,public/name)
for src in sorted(sources):
    dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C81_OFFLINE_BACKUP_SOURCE_PROOF',
    'synthetic_cases':c['case_count'],'real_small_ext4_tested':True,'real_userdata_tar_tested':True,
    'host_copy_receipt_fixture_is_synthetic':True,'source_and_sanitized_metadata_only':True,
    'private_bundle_plan_or_payload_included':False,'Steam_Deck_or_R35S_contacted':False,
    'native_backup_qualified':False,'real_offline_backup_created':False,'candidate_provisioned':False,
    'device_writer_available':False,'post_candidate_boot_recovery_implemented':False,
    'SDK_config_matches_baseline':True},indent=2)+'\n')
# Same privacy boundary as C80: never publish raw live UUID/private-leaf hashes.
prior=Path((work/'root-migration/latest-plan').read_text().strip())
observed=json.loads((prior/'survey.json').read_text());plan=json.loads((stage/'bundle/migration-plan.json').read_text())
private=[observed['kernel_boot_id'],plan['mbr_sha256'],plan['boot_prefix_16MiB_sha256'],
         *(row['sha256'] for row in observed['private_files'].values())]
for p in public.rglob('*'):
    assert not p.is_symlink()
    if p.is_file():
        assert p.suffix.lower() not in {'.img','.bin','.fat','.ext4','.tar','.gz','.gb','.so','.dat','.sav','.state','.ini','.bundle'}
        data=p.read_bytes();assert not data.startswith(b'\x7fELF')
        assert not any(value.encode() in data for value in private),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h,n
print('C81 sanitized offline source/checks proof frozen; no native backup:',out)
