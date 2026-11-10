#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C53 selective persistence proof without private identities or states."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/gb-persist'
out=repo/'dist/phase4/gameboy-selective-persistence';assert not out.exists()
parent=repo/'dist/phase4/save-store-laboratory'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
def sanitize(v):
 if isinstance(v,dict):return {k:('private' if k in {'ROM_sha256','private_identity'} else sanitize(x)) for k,x in v.items()}
 if isinstance(v,list):return [sanitize(x) for x in v]
 return v
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['checks','prepare','save','load']}
reports={n:json.loads((s/'analysis.json').read_text()) for n,s in stages.items()}
for label,source in stages.items():
 r=reports[label];assert r['passed']
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h
 target=public/label;target.mkdir();(target/'analysis.json').write_text(json.dumps(sanitize(r),indent=2)+'\n')
 if label=='checks':
  assert r['case_count']==32
  lines=[s for s in (source/'check.stdout').read_text().splitlines() if s.startswith('C53_')]
  (target/'markers.txt').write_text('\n'.join(lines)+'\n')
  continue
 assert r['cleanup_passed'] and r['RAM_removed'] and r['boot_sequence']==68
 assert r['private_identity']==reports['prepare']['private_identity']
 assert r['integration_checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
 lines=[]
 for n in ['game.log','core.log','return.log','store-prepare.log','store-seed.log','store-commit.log','store-verify.log']:
  p=source/'collected'/n
  if p.is_file():lines.extend(s for s in p.read_text().splitlines() if re.match(r'^(C(44|45|46|50|51|53)_|RETRO_RUNNER_EXIT=)',s))
 (target/'markers.txt').write_text('\n'.join(lines)+'\n')
 if label in {'save','load'}:
  a=json.loads((source/'persistence-analysis.json').read_text());physical=json.loads((source/'physical-observation.json').read_text())
  assert a['technical_launcher_return'] and a['reason']=='hotkey' and a['PKST_core_crc_valid']
  assert a['session_analysis_sha256']==sha(source/'analysis.json')
  assert a['game_log_sha256']==sha(source/'collected/game.log')
  assert a['performance_csv_sha256']==sha(source/'collected/performance.csv')
  assert a['metadata_sha256']==sha(source/'collected/state-metadata.txt')
  if label=='load':assert a['store_preserved_byte_exact'] and a['snapshot_loaded_from_ext4'] and physical['cross_session_restore_qualified']
  else:assert a['snapshot_committed'] and physical['save_sequence_and_return_confirmed']
  for n in ['persistence-analysis.json','physical-observation.json']:
   (target/n).write_text(json.dumps(sanitize(json.loads((source/n).read_text())),indent=2,ensure_ascii=False)+'\n')
  shutil.copyfile(source/'collected/state-metadata.txt',target/'state-metadata.txt')
for source in [*repo.glob('port/scripts/*phase4-gb-persist*.py'),*repo.glob('port/device/rk-r35s-p0/gb-persist/*.sh'),
               repo/'port/diagnostics/phase4-save-directory.c',repo/'port/diagnostics/phase4-gb-persist-check.py',
               repo/'docs/archive/phase4/phase4-gb-persistence.md']:
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
report={'passed':True,'experiment':'C53_SELECTIVE_GB_PERSISTENCE','cross_session_restore_physically_qualified':True,
        'snapshot_retained_on_test128_p3':True,'generation':1,'original32_preserved':True,
        'runtime_writers_tmpfs_except_explicit_snapshot_commit':True,'cleanup_passed':True,
        'states_ROMs_IDs_images_PCM_binaries_included':False,'installed_files_modified':False,
        'rebooted':False,'reboot_or_power_loss_persistence_qualified':False,'long_run_qualified':False,
        'C52_proof_sha256':sha(parent/'SHA256SUMS')}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini'} for p in public.rglob('*'))
secret_values={reports['prepare']['private_identity'],reports['save']['ROM_sha256']}
for p in public.rglob('*'):
 if p.is_file():assert not any(s.encode() in p.read_bytes() for s in secret_values),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C53 selective persistence proof frozen and verified:',out)
