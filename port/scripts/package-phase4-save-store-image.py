#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C56 offline-image receipts and sources; never publish the rootfs."""
from pathlib import Path
import json,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store-image'
out=repo/'dist/phase4/save-store-image';assert not out.exists()
parent=repo/'dist/phase4/save-store-package'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
stage=Path((area/'latest-image').read_text().strip());r=json.loads((stage/'analysis.json').read_text())
assert r['passed'] and r['C55_proof_sha256']==sha(parent/'SHA256SUMS')
assert r['full_readback_inventory_matched'] and r['fsck_exit']==0 and r['factory_boot_counter']==0
assert r['base_C38_files_changed']==0 and not r['device_contacted'] and not r['device_written']
assert not r['candidate_boot_tested'] and r['new_inodes_and_root_owned_by_root']
assert sha(stage/'images/rootfs.ext4')==r['image_sha256']
sources={Path(__file__),repo/'docs/analysis/phase4-save-store-image.md'}
for n,h in r['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
for name in ['analysis.json','static-audit.json','foundation.sha256']:
 shutil.copyfile(stage/name,public/name)
for label in ['planned-boot-contract','write-image','fsck','inodes','readback','readback-boot-contract','new-CLI-loader']:
 for ext in ['sh','exit','stdout','stderr']:
  name=label+'.'+ext;shutil.copyfile(stage/name,public/name)
for name in ['debugfs.commands','inode.commands']:
 shutil.copyfile(stage/name,public/name)
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.gz'}
  assert not p.read_bytes().startswith(b'\x7fELF')
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C56 source/offline-image receipts frozen (no image payload):',out)
