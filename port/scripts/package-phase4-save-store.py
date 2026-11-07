#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze the C52 transaction laboratory without image, bundle or binaries."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/save-store'
out=repo/'dist/phase4/save-store-laboratory';assert not out.exists()
stages={name:Path((area/('latest-'+key)).read_text().strip()) for name,key in [('checks','checks'),('ext4-build','ext4-build'),('native','native')]}
reports={name:json.loads((stage/'analysis.json').read_text()) for name,stage in stages.items()}
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));sources=set()
for label,stage in stages.items():
 r=reports[label];assert r['passed']
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h;sources.add(repo/n)
 target=public/label;target.mkdir();shutil.copyfile(stage/'analysis.json',target/'analysis.json')
 if label=='checks':
  assert r['case_count']==34
  lines=[s for s in (stage/'check.stdout').read_text().splitlines() if s.startswith('C52_')]
  assert len(lines)==35;(target/'markers.txt').write_text('\n'.join(lines)+'\n')
 if label=='ext4-build':
  for n,h in r['payload_sha256'].items():assert sha(stage/n)==h
  assert r['payload_sha256']['muos-save-store']==reports['checks']['binary_sha256']
  assert r['checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
 if label=='native':
  assert r['cleanup_passed'] and r['RAM_removed'] and r['after_image_fsck_passed'] and not r['real_card_saves_written']
  assert r['ext4_build_analysis_sha256']==sha(stages['ext4-build']/'analysis.json')
  assert r['after_image_sha256']==sha(stage/'after.ext4')
  lines=[s for s in (stage/'native.stdout').read_text().splitlines() if re.match(r'^(C52_|PASS owned-loop-detached$)',s)]
  (target/'markers.txt').write_text('\n'.join(lines)+'\n');shutil.copyfile(stage/'fsck-after.txt',target/'fsck-after.txt')
for p in [*repo.glob('port/scripts/*phase4-save-store*.py'),*repo.glob('port/device/rk-r35s-p0/save-store/*'),
          repo/'port/utils/muos-save-store.c',repo/'port/diagnostics/phase4-save-store-check.py',
          repo/'port/diagnostics/phase4-save-store-ext4.c',repo/'docs/analysis/phase4-save-store.md']:
 sources.add(p)
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
parent=repo/'dist/phase4/gameboy-ram-state'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
report={'passed':True,'experiment':'C52_SAVE_STORE_LABORATORY','QEMU_cases':34,
        'native_ext4_rw_ro_remount_and_explicit_recovery':True,'real_data_audit_RO_noload':True,
        'cleanup_passed':True,'real_card_saves_written':False,'real_game_persistence_qualified':False,
        'installed_or_rebooted':False,'raw_images_states_ROMs_binaries_included':False,
        'C51_proof_sha256':sha(parent/'SHA256SUMS')}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini'} for p in public.rglob('*'))
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C52 metadata-only proof frozen and verified:',out)
