#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C75 recipe/legal/ABI receipts, excluding ELF, rootfs and private ROMs."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import inventory, sha, sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gambatte-package'
stage=Path((area/'latest-build').read_text().strip());r=json.loads((stage/'analysis.json').read_text())
assert stage.is_relative_to(area) and r['passed'] and r['default_off'] and r['i386_refused']
assert r['real_Buildroot_download_extract_Kconfig_legal_info'] and r['actual_recipe_macros_built_with_existing_SDK']
assert not r['full_Buildroot_dependency_rebuild'] and not r['device_contacted'] and not r['device_written']
assert not r['ROM_loaded'] and not r['ROM_copied'] and r['combined_license_review_pending']
assert r['Buildroot_redistribution_disabled'] and r['exports_match_qualified_core']
assert r['files_added']==9 and r['existing_C69_items_preserved']==3386
assert sha(stage/'target/opt/muos/share/core/gambatte_libretro.so')==r['core_sha256']
assert inventory(stage/'composition')==json.loads((stage/'expected-tree.json').read_text())
for name,digest in r['parent_proofs_sha256'].items():
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 assert sha(proof/'SHA256SUMS')==digest
sources={Path(__file__),repo/'docs/archive/phase4/phase4-gambatte-package.md'}
for n,h in r['source_sha256'].items():assert sha(repo/n)==h;sources.add(repo/n)
out=repo/'dist/phase4/gambatte-package';assert not out.exists()
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for name in ['analysis.json','source-files.json','composition-added.json','package-info.json',
             'recipe.mk','default.config','opt-in.config','i386.config','exports.txt','prior-exports.txt']:
 shutil.copyfile(stage/name,public/name)
for label in ['source-and-kconfig','architecture-refusal','recipe','composition','ABI']:
 assert (stage/(label+'.exit')).read_text()=='0\n'
 for ext in ['sh','stdout','stderr','exit']:shutil.copyfile(stage/(label+'.'+ext),public/(label+'.'+ext))
for source in sources:
 dest=public/'source'/source.relative_to(repo);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C75_GAMBATTE_PACKAGE_SOURCE_PROOF',
 'source_metadata_and_logs_only':True,'binary_or_ROM_payload_included':False,
 'combined_license_review_pending':True,'new_native_gameplay_claimed':False},indent=2)+'\n')
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.o','.a','.img','.ext4','.png','.wav','.sav','.state','.gz','.tar'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C75 source/recipe/ABI proof frozen; no binary or ROM:',out)
