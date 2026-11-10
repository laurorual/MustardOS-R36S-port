#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C57 exact-plan/native receipts without ELF, archive or private state."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-install'
out=repo/'dist/phase4/save-store-installed';assert not out.exists()
parent=repo/'dist/phase4/save-store-image'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
stage=Path((area/'latest-plan').read_text().strip());plan=json.loads((stage/'plan.json').read_text())
installed=json.loads((stage/'install-analysis.json').read_text());checks=json.loads((stage/'checks/analysis.json').read_text())
assert installed['passed'] and installed['RAM_removed'] and installed['native_synthetic_tested']
assert installed['root_read_only'] and not installed['token_or_service_enabled'] and not installed['p3_mounted']
assert installed['global_mounts_unchanged'] and installed['private_state_fingerprint_matched']
assert installed['plan_sha256']==sha(stage/'plan.json')==checks['plan_sha256']
assert checks['passed'] and checks['case_count']==26 and plan['C56_proof_sha256']==sha(parent/'SHA256SUMS')
meta=json.loads((stage/'manifest.json').read_text())
for n,key in [('plan.json','plan_sha256'),('absence-backup.json','backup_sha256'),('deployment.tar','deployment_sha256')]:assert sha(stage/n)==meta[key]
sources={Path(__file__),repo/'docs/archive/phase4/phase4-save-store-installed.md'}
for report in [plan,checks]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for n in ['plan.json','manifest.json','absence-backup.json','install-analysis.json']:
 shutil.copyfile(stage/n,public/n)
for label in ['survey','inspect','result','after','synthetic','final-health','cleanup']:
 for ext in ['sh','stdout','stderr','exit']:
  name=label+'.'+ext;shutil.copyfile(stage/name,public/name)
(public/'checks').mkdir()
for n in ['analysis.json','fixtures.sh','stdout','stderr','exit']:shutil.copyfile(stage/'checks'/n,public/'checks'/n)
failed=area/'install.a4fy86sk';(public/'initial-readonly-refusal').mkdir()
for n in ['preinspect-failure.json','failed-inspect-cleanup.stdout']:
 shutil.copyfile(failed/n,public/'initial-readonly-refusal'/n)
for p in sorted(sources):
 to=public/'source'/p.relative_to(repo);to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,to)
result={'passed':True,'experiment':'C57_SELECTIVE_SAVE_STORE_INSTALLED','boot_sequence':installed['boot_sequence'],
 'files_added':4,'existing_files_replaced':0,'case_count':26,'native_RAM_only_test_passed':True,
 'root_read_only':True,'foundation_files':97,'p3_mounted':False,'RAM_removed':True,'reboot_requested':False,
 'original_32GB_or_Deck_accessed':False,'private_data_or_binaries_included':False,
 'C56_proof_sha256':sha(parent/'SHA256SUMS'),'new_boot_or_power_loss_tested':False}
(public/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz','.tar'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C57 source/native receipts frozen; no binary or private content:',out)
