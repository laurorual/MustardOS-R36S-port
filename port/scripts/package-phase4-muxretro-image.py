#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C64 offline rootfs receipts/sources, never the private image payload."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'muxretro-image'
out=repo/'dist/phase4/muxretro-image';assert not out.exists()
stage=Path((area/'latest-image').read_text().strip());assert stage.is_relative_to(area)
r=json.loads((stage/'analysis.json').read_text());assert r['passed']
for name,digest in r['parent_proofs_sha256'].items():
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,(name,n)
 assert sha(proof/'SHA256SUMS')==digest,name
assert r['full_readback_inventory_matched'] and r['fsck_exit']==0 and r['factory_boot_counter']==0
assert r['base_C56_items_changed']==0 and r['readback_items']==3356 and r['base_C56_items_preserved']==3330
assert not r['device_contacted'] and not r['device_written'] and not r['candidate_boot_tested']
assert r['new_inodes_and_root_owned_by_root'] and r['C62_installed_bytes_matched'] and r['C63_native_host_evidence_reused']
assert r['new_dynamic_ELF_loader_checks']==0 and r['C38_loader_checks_reused']==172
assert r['C56_store_loader_checks_reused']==1 and r['C60_host_loader_checks_reused']==1
assert sha(stage/'images/rootfs.ext4')==r['image_sha256']
# Pin explicit receipts for each reused loader set; don't infer runtime success
# from compilation or from the integrity of a source manifest alone.
base=json.loads((repo/'dist/phase4/save-store-image/analysis.json').read_text())
host=json.loads((repo/'dist/phase4/muxretro-package/analysis.json').read_text())
assert base['new_dynamic_ELF_loader_checks']==1 and base['prior_C38_dynamic_ELF_loader_checks_reused']==172
assert host['private_composition_loader_passed'] and host['binary_sha256']==r['host_sha256']
added=json.loads((repo/'dist/phase4/muxretro-package/composition-added.json').read_text())
inodes=(stage/'inodes.stdout').read_text();file_count=0
for name,record in added.items():
 match=re.search(r'debugfs: stat /'+re.escape(name)+r'\n(.*?)(?=debugfs: |\Z)',inodes,re.S);assert match,name
 if record['type']=='file':
  assert re.search(r'\bType: regular\b',match[1]) and re.search(r'\bLinks:\s+1\b',match[1]),name
  file_count+=1
assert file_count==13
sources={Path(__file__),repo/'docs/analysis/phase4-muxretro-image.md'}
for n,h in r['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for name in ['analysis.json','static-audit.json','foundation.sha256']:
 shutil.copyfile(stage/name,public/name)
for label in ['planned-boot-contract','write-image','fsck','inodes','readback','readback-boot-contract']:
 for ext in ['sh','exit','stdout','stderr']:
  name=label+'.'+ext;shutil.copyfile(stage/name,public/name)
for name in ['debugfs.commands','inode.commands']:shutil.copyfile(stage/name,public/name)
(public/'proof.json').write_text(json.dumps({'passed':True,'experiment':'C64_OFFLINE_MUXRETRO_IMAGE_PROOF',
 'regular_new_files_with_single_link_verified':13,'private_image_payload_included':False,
 'dynamic_loader_checks_replayed':False,'candidate_boot_tested':False,'device_contacted':False},indent=2)+'\n')
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz','.tar'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C64 source/offline-image receipts frozen (no image/binary payload):',out)
