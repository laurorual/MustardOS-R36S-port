#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C51 metadata-only proof; exclude commercial state and binaries."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-state'
out=repo/'dist/phase4/gameboy-ram-state';assert not out.exists()
parents={}
for name in ['gameboy-private-content','gameboy-hotkey-exit']:
 proof=out.parent/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
 parents[name]=sha(proof/'SHA256SUMS')
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
def sanitize(v):
 if isinstance(v,dict):return {k:('private' if k=='ROM_sha256' else sanitize(x)) for k,x in v.items()}
 if isinstance(v,list):return [sanitize(x) for x in v]
 return v
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['checks','dispatch-checks','observe']}
for label,source in stages.items():
 r=json.loads((source/'analysis.json').read_text());assert r['passed']
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h
 target=public/label;target.mkdir()
 (target/'analysis.json').write_text(json.dumps(sanitize(r),indent=2)+'\n')
 if label=='checks':
  lines=[s for s in (source/'check.stdout').read_text().splitlines() if s.startswith('C51_')]
  assert len(lines)==19
  (target/'markers.txt').write_text('\n'.join(lines)+'\n')
 if label=='observe':
  a=json.loads((source/'state-analysis.json').read_text());physical=json.loads((source/'physical-observation.json').read_text())
  assert r['cleanup_passed'] and r['RAM_removed'] and r['boot_sequence']==68
  assert a['manual_quicksave'] and a['manual_quickload'] and a['PKST_core_crc_valid'] and a['tmpfs_only']
  assert a['technical_launcher_return'] and a['reason']=='hotkey' and physical['qualified']
  assert sha(source/'analysis.json')==a['session_analysis_sha256']
  assert sha(source/'collected/game.log')==a['game_log_sha256']
  assert sha(source/'collected/performance.csv')==a['performance_csv_sha256']
  assert sha(source/'collected/state-metadata.txt')==a['metadata_sha256']
  for n in ['state-analysis.json','physical-observation.json']:
   (target/n).write_text(json.dumps(sanitize(json.loads((source/n).read_text())),indent=2,ensure_ascii=False)+'\n')
  assert r['state_checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
  lines=[]
  for n in ['game.log','core.log','return.log']:
   lines.extend(s for s in (source/'collected'/n).read_text().splitlines() if re.match(r'^(C(44|45|46|50|51)_|RETRO_RUNNER_EXIT=)',s))
  (target/'markers.txt').write_text('\n'.join(lines)+'\n')
  shutil.copyfile(source/'collected/state-metadata.txt',target/'state-metadata.txt')
  game=(source/'collected/game.log').read_text()
  (target/'native-state-receipts.json').write_text(json.dumps({
   'save_hotkey_logs':game.count('Quick Save (hotkey)'),
   'load_hotkey_logs':game.count('Quick Load (hotkey)'),
   'writer_completed_logs':game.count('Saved state to '),
   'restored_logs':game.count('Loaded state from ')},indent=2)+'\n')
for source in [*repo.glob('port/scripts/*phase4-gb-state*.py'),*repo.glob('port/device/rk-r35s-p0/gb-state/*.sh'),
               repo/'port/diagnostics/phase4-state-metadata.c',repo/'docs/analysis/phase4-gb-state.md']:
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
report={'experiment':'C51_NATIVE_RAM_STATE','passed':True,'physical_restore_and_exit_qualified':True,
        'metadata_validated_before_RAM_removal':True,'cleanup_passed':True,'parent_proof_sha256':parents,
        'private_ROM_states_images_PCM_binaries_included':False,'installed_files_modified':False,
        'rebooted':False,'persistent_saves_enabled':False,'audio_interaction_continuity_qualified':False,
        'audio_underrun_callbacks':8,'audio_underrun_events':5,'audio_missing_frames':3471,
        'underrun_cause_proven':False,'long_run_and_new_boot_qualified':False}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.so','.img','.png','.wav','.sav','.srm','.state','.ini'} for p in public.rglob('*'))
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C51 proof frozen and verified:',out)
