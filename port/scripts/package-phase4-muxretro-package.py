#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C60 host-recipe evidence, excluding ELFs, SDK blobs and private data."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-package'
out=repo/'dist/phase4/muxretro-package';assert not out.exists()
stage=Path((area/'latest-build').read_text().strip());assert stage.is_relative_to(area)
r=json.loads((stage/'analysis.json').read_text());assert r['passed']
for n in ['real_Kconfig_rsync_legal_info','wrong_arch_refused','source_only_legal_archive_verified',
          'frontend_source_matches_C50','missing_and_changed_SDK_refused_before_compiler',
          'C07_boot_contract_preserved','private_composition_loader_passed','SDK_config_unchanged']:assert r[n],n
assert r['composition_added_files']==13 and r['C56_existing_items_preserved']==3330
assert not any(r[n] for n in ['full_frontend_library_provider_integrated','device_accessed',
                             'new_native_runtime_qualified','new_image_built','full_Buildroot_rebuild'])
parents={}
for name in ['gameboy-installed-store','gameboy-hotkey-exit','save-store-image']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
 parents[name]=sha(proof/'SHA256SUMS')
assert (work/'gb-exit/host.uuixcmie/analysis.json').read_bytes()==(repo/'dist/phase4/gameboy-hotkey-exit/host/analysis.json').read_bytes()
assert sha(stage/'target/opt/muos/frontend/muxretro')==r['binary_sha256']
sources={Path(__file__),repo/'docs/archive/phase4/phase4-muxretro-package.md',repo/'port/scripts/phase4_candidate.py'}
for n,h in r['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for name in ['analysis.json','source-files.json','composition-added.json','elf.stdout','package-info.json','minimal.defconfig','loader.stdout','recipe.stderr']:
 shutil.copyfile(stage/name,public/name)
for label in ['missing-sdk','changed-sdk','composition-contract']:
 for ext in ['exit','stdout','stderr']:shutil.copyfile(stage/(label+'.'+ext),public/(label+'.'+ext))
rows=[]
for name in ['default.config','without-sdk.config','opt-in.config','wrong-arch.config']:
 rows.append('['+name+']')
 rows.extend(v for v in (stage/name).read_text().splitlines() if any(k in v for k in [
  'BR2_aarch64=','BR2_i386=','BR2_MUOS_PRIVATE_','BR2_PACKAGE_MUOS_',
  'BR2_PACKAGE_SDL2','BR2_PACKAGE_HARFBUZZ','BR2_PACKAGE_FREETYPE','BR2_PACKAGE_LIBPNG',
  'BR2_PACKAGE_LIBCURL','BR2_PACKAGE_LIBARCHIVE','BR2_PACKAGE_OPENSSL','BR2_PACKAGE_ZLIB',
  'BR2_PACKAGE_HAS_LIBEGL','BR2_PACKAGE_HAS_LIBGLES']))
(public/'kconfig-evidence.txt').write_text('\n'.join(rows)+'\n')
target=stage/'target'
for name in ['payload.sha256','platform.sha256','provenance.json']:
 shutil.copyfile(target/'usr/share/muos-muxretro'/name,public/name)
shutil.copytree(target/'usr/share/licenses/muos-muxretro',public/'licenses')
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C60_MUXRETRO_RECIPE_PROOF',
 'private_data_or_binaries_included':False,'parent_proofs_sha256':parents,
 'new_host_runtime_qualified':False,'private_SDK_required':True,
 'full_frontend_library_provider_integrated':False},indent=2)+'\n')
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C60 source/license/metadata proof frozen and verified:',out)
