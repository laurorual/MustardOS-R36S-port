#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C62 exact additive installation evidence, excluding archive/ELF/data."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-install'
out=repo/'dist/phase4/muxretro-installed';assert not out.exists()
parents={}
for name in ['muxretro-package','muxretro-package-session','save-store-installed']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
 parents[name]=sha(proof/'SHA256SUMS')
stage=Path((area/'latest-plan').read_text().strip());assert stage.is_relative_to(area)
plan=json.loads((stage/'plan.json').read_text());installed=json.loads((stage/'install-analysis.json').read_text())
checks=json.loads((stage/'checks/analysis.json').read_text())
assert installed['passed'] and installed['RAM_removed'] and installed['installed_ABI_tested']
assert installed['root_read_only'] and not installed['token_or_service_enabled'] and not installed['p3_mounted']
assert installed['global_mounts_unchanged'] and installed['private_state_fingerprint_matched']
assert not installed['GUI_replayed'] and not installed['runtime_C46_override_installed']
assert installed['files_added']==13 and installed['directories_added']==13 and installed['existing_files_replaced']==0
assert installed['plan_sha256']==sha(stage/'plan.json')==checks['plan_sha256']
assert checks['passed'] and checks['case_count']==61
assert plan['C60_proof_sha256']==parents['muxretro-package'] and plan['C61_proof_sha256']==parents['muxretro-package-session']
assert plan['preserved_prerequisites']==105 and plan['runtime_contract']['activation']=='manual only'
assert plan['runtime_contract']['GUI_requires_C46_RAM_libmuxmod_sha256']=='1ec8acd906ee25bd83b59c0c5818e7310d62bfeaabadb2b473e03562d7d6bcc9'
meta=json.loads((stage/'manifest.json').read_text())
for n,key in [('plan.json','plan_sha256'),('absence-backup.json','backup_sha256'),('deployment.tar','deployment_sha256')]:assert sha(stage/n)==meta[key]
sources={Path(__file__),repo/'docs/archive/phase4/phase4-muxretro-installed.md'}
for report in [plan,checks]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for n in ['plan.json','manifest.json','absence-backup.json','install-analysis.json']:
 shutil.copyfile(stage/n,public/n)
for label in ['survey','inspect','result','after','native-ABI','final-health','cleanup']:
 for ext in ['sh','stdout','stderr','exit']:
  name=label+'.'+ext;shutil.copyfile(stage/name,public/name)
(public/'checks').mkdir()
for n in ['analysis.json','fixtures.sh','stdout','stderr','exit']:shutil.copyfile(stage/'checks'/n,public/'checks'/n)
for p in sorted(sources):
 target=public/'source'/p.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
result={'passed':True,'experiment':'C62_SELECTIVE_MUXRETRO_INSTALLED','boot_sequence':installed['boot_sequence'],
 'files_added':13,'directories_added':13,'existing_files_replaced':0,'case_count':61,
 'installed_version_help_only_passed':True,'native_GUI_replayed':False,'C61_RAM_override_scope_preserved':True,
 'root_read_only':True,'foundation_files':97,'preserved_public_prerequisites':105,
 'p3_mounted':False,'RAM_removed':True,'reboot_requested':False,'autostart_or_writer_enabled':False,
 'original_32GB_or_Deck_accessed':False,'private_data_or_binaries_included':False,
 'parent_proofs_sha256':parents,'new_boot_or_power_loss_tested':False}
(public/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz','.tar'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C62 source/native receipts frozen; no binary/private payload:',out)
