#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C80 public policy proof; redact live identity and private-file metadata hashes."""
from pathlib import Path
import copy, json, shutil, tempfile
from phase4_candidate import sha, sums

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'root-migration'
stage=Path((area/'latest-plan').read_text().strip())
checks=Path((area/'latest-checks').read_text().strip())
assert stage.is_relative_to(area) and checks.is_relative_to(area)
r=json.loads((stage/'analysis.json').read_text());c=json.loads((checks/'analysis.json').read_text())
p=json.loads((stage/'migration-plan.json').read_text());observed=json.loads((stage/'survey.json').read_text())
assert r['passed'] and c['passed'] and c['case_count']==len(c['cases'])==84
assert sha(stage/'migration-plan.json')==r['plan_sha256']
assert r['boot_sequence']==p['survey_boot_sequence']==observed['boot_sequence']
assert r['root_read_only'] and r['installed40_and_preserved132_verified'] and r['infrastructure_and_mbr_unchanged']
assert r['bootchain_prefix_matches_C79_except_existing_p3_entry']
for key in ['private_file_contents_exported','offline_backup_created','candidate_provisioned','device_written','device_writer_available','execution_enabled']:
    assert r[key] is False,key
for label in ['preflight','boot-id','boot-prefix','survey','postflight','mbr-after']:
    assert (stage/(label+'.exit')).read_text()=='0\n',label
assert (stage/'preflight.stdout').read_bytes()==(stage/'postflight.stdout').read_bytes()
assert (stage/'mbr.bin').read_bytes()==(stage/'mbr-after.stdout').read_bytes()
assert sha(stage/'mbr.bin')==p['mbr_sha256'] and sha(stage/'boot-prefix.stdout')==p['boot_prefix_16MiB_sha256']
assert not p['execution_enabled'] and not p['raw_factory_whole_card_write_allowed'] and not p['automatic_rollback']
assert not p['byte_exact_rollback_after_candidate_boot_allowed']
for name,h in r['parent_proofs_sha256'].items():
    parent=repo/'dist/phase4'/name
    for n,d in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==d,(name,n)
    assert sha(parent/'SHA256SUMS')==h,name
sources={Path(__file__),repo/'docs/analysis/phase4-root-migration.md'}
for report in [r,c]:
    for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
out=repo/'dist/phase4/root-migration';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for n,report in [('analysis.json',r),('checks.json',c)]:
    (public/n).write_text(json.dumps(report,indent=2)+'\n')
redacted=copy.deepcopy(p)
for key in ['mbr_sha256','boot_prefix_16MiB_sha256']:redacted[key]='private'
for row in redacted['private_files_at_live_survey'].values():row['sha256']='private'
redacted['redacted_not_executable']=True
(public/'plan-redacted.json').write_text(json.dumps(redacted,indent=2)+'\n')
(public/'recorded-health.json').write_text(json.dumps({'passed':True,'boot_sequence':r['boot_sequence'],
    'closure_from_recorded_readonly_receipts':True,'new_SSH_or_boot_requested_by_packager':False,
    'receipt_sha256':{label+'.'+ext:('private' if label=='mbr-after' and ext=='stdout' else sha(stage/(label+'.'+ext))) for label in ['preflight','postflight','mbr-after'] for ext in ['stdout','stderr','exit']}},indent=2)+'\n')
for src in sorted(sources):
    dst=public/'source'/src.relative_to(repo);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C80_ROOT_ONLY_MIGRATION_POLICY_PROOF',
    'cases':84,'live_survey_readonly':True,'device_writer_or_provisioner_available':False,
    'backup_receipts_in_checks_are_synthetic':True,'real_offline_backup_created':False,
    'post_candidate_boot_byte_exact_rollback_allowed':False,'raw_private_inventory_or_UUID_included':False},indent=2)+'\n')
private=[observed['kernel_boot_id'],p['mbr_sha256'],p['boot_prefix_16MiB_sha256'],
         *(row['sha256'] for row in observed['private_files'].values())]
for path in public.rglob('*'):
    assert not path.is_symlink()
    if path.is_file():
        assert path.suffix not in {'.bin','.img','.ext4','.gb','.so','.tar','.gz','.sav','.state','.ini'}
        data=path.read_bytes();assert not data.startswith(b'\x7fELF')
        assert not any(v.encode() in data for v in private),path
(public/'SHA256SUMS').write_text(''.join(sha(path)+'  '+str(path.relative_to(public))+'\n' for path in sorted(public.rglob('*')) if path.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C80 sanitized plan/policy proof frozen; no device writer:',out)
