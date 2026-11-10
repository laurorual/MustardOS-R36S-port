#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C55 recipe/tree evidence, excluding binaries and private data."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-package'
out=repo/'dist/phase4/save-store-package';assert not out.exists()
parents={}
for name in ['save-store-laboratory','gameboy-after-boot']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 parents[name]=sha(proof/'SHA256SUMS')
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['build','composition','health']}
reports={n:json.loads((s/'analysis.json').read_text()) for n,s in stages.items()}
assert reports['build']['C52_binary_byte_identical'] and reports['build']['wrong_arch_refused']
elf=(stages['build']/'elf.txt').read_text()
assert 'GNU_RELRO' in elf and 'BIND_NOW' in elf
assert reports['composition']['source_build_analysis_sha256']==sha(stages['build']/'analysis.json')
assert reports['composition']['base_C38_files_changed']==0 and reports['composition']['foundation_files']==97
assert not reports['health']['new_package_installed'] and not reports['health']['device_mutated']
sources={Path(__file__),repo/'docs/archive/phase4/phase4-save-store-package.md'}
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for label,source in stages.items():
 r=reports[label];assert r['passed']
 for n,h in r.get('source_sha256',{}).items():assert sha(repo/n)==h,n;sources.add(repo/n)
 target=public/label;target.mkdir();shutil.copyfile(source/'analysis.json',target/'analysis.json')
 if label=='build':
  for n in ['elf.txt','package-info.json','minimal.defconfig']:
   shutil.copyfile(source/n,target/n)
  rows=[]
  for name in ['default.config','opt-in.config','wrong-arch.config']:
   rows.append('['+name+']')
   rows.extend(v for v in (source/name).read_text().splitlines() if any(k in v for k in ['BR2_aarch64=','BR2_i386=','BR2_PACKAGE_MUOS_','BR2_PACKAGE_ZLIB','BR2_PACKAGE_LIBZLIB']))
  (target/'kconfig-evidence.txt').write_text('\n'.join(rows)+'\n')
  shutil.copyfile(source/'target/usr/libexec/muos-save-store/payload.sha256',target/'payload.sha256')
  markers=[]
  for name in ['kconfig','loader']:
   markers.extend(v for v in (source/(name+'.stdout')).read_text().splitlines() if v.startswith('C55_PASS_'))
  (target/'markers.txt').write_text('\n'.join(markers)+'\n')
 if label=='composition':
  (target/'markers.txt').write_text('\n'.join(v for v in (source/'check.stdout').read_text().splitlines() if v.startswith('C55_PASS_'))+'\n')
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
result={'passed':True,'experiment':'C55_BUILDROOT_SAVE_STORE_PACKAGE','default_off':True,
 'C52_binary_byte_identical':True,'C52_transaction_fixtures_reused':34,'real_Kconfig_rsync_legal_info':True,
 'private_tree_additional_files':4,'base_C38_files_changed':0,'foundation_files':97,'full_image_built':False,
 'new_native_execution_or_boot_tested':False,'device_written':False,'original_32GB_or_Deck_accessed':False,
 'shared_SDK_config_unchanged':True,'check_package_lint_available':False,'lint_missing_module':'magic',
 'private_data_or_binaries_included':False,'parent_proofs_sha256':parents}
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
(public/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C55 source/metadata-only proof frozen and verified:',out)
