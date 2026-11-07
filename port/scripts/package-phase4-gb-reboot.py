#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C54 existing-new-boot proof, excluding commercial content and IDs."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/gb-reboot'
out=repo/'dist/phase4/gameboy-after-boot';assert not out.exists()
parent=repo/'dist/phase4/gameboy-selective-persistence'
for n,h in sums(parent/'SHA256SUMS').items():assert sha(parent/n)==h
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
def sanitize(v):
 if isinstance(v,dict):return {k:('private' if k in {'ROM_sha256','private_identity','kernel_boot_id'} else sanitize(x)) for k,x in v.items()}
 if isinstance(v,list):return [sanitize(x) for x in v]
 return v
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['checks','load']}
reports={n:json.loads((s/'analysis.json').read_text()) for n,s in stages.items()}
sources=set()
for label,source in stages.items():
 r=reports[label];assert r['passed']
 for n,h in r['source_sha256'].items():assert sha(repo/n)==h;sources.add(repo/n)
 target=public/label;target.mkdir();(target/'analysis.json').write_text(json.dumps(sanitize(r),indent=2)+'\n')
 if label=='checks':assert r['case_count']==26;continue
 assert r['cleanup_passed'] and r['RAM_removed'] and r['source_boot_sequence']==68 and r['boot_sequence']==69
 assert r['store_matches_previous_boot'] and not r['reboot_requested_by_this_task']
 assert r['reboot_checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
 a=json.loads((source/'persistence-analysis.json').read_text());physical=json.loads((source/'physical-observation.json').read_text())
 assert a['snapshot_matches_previous_boot'] and a['persistence_after_observed_new_boot_qualified']
 assert not a['shutdown_method_verified'] and not a['controlled_reboot_requested']
 assert physical['restore_after_observed_new_boot_qualified'] and physical['launcher_return_confirmed']
 assert a['session_analysis_sha256']==sha(source/'analysis.json')
 assert a['game_log_sha256']==sha(source/'collected/game.log') and a['performance_csv_sha256']==sha(source/'collected/performance.csv')
 assert a['metadata_sha256']==sha(source/'collected/state-metadata.txt')
 origin=Path(r['source_load_stage']);assert sha(origin/'analysis.json')==r['source_load_analysis_sha256']
 original=(origin/'collected/store-readonly-after.sha256').read_bytes()
 assert original==(source/'collected/store-readonly-before.sha256').read_bytes()==(source/'collected/store-readonly-after.sha256').read_bytes()
 for n in ['persistence-analysis.json','physical-observation.json']:
  (target/n).write_text(json.dumps(sanitize(json.loads((source/n).read_text())),indent=2,ensure_ascii=False)+'\n')
 shutil.copyfile(source/'collected/state-metadata.txt',target/'state-metadata.txt')
 lines=[]
 for n in ['game.log','core.log','return.log','store-seed.log','store-verify.log']:
  lines.extend(s for s in (source/'collected'/n).read_text().splitlines() if re.match(r'^(C(44|45|46|50|51|53|54)_|RETRO_RUNNER_EXIT=)',s))
 (target/'markers.txt').write_text('\n'.join(lines)+'\n')
for source in [*repo.glob('port/scripts/*phase4-gb-reboot*.py'),repo/'port/scripts/phase4_gb_reboot.py',
               *repo.glob('port/device/rk-r35s-p0/gb-reboot/*.sh'),repo/'docs/analysis/phase4-gb-after-boot.md']:
 sources.add(source)
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
r=reports['load']
report={'passed':True,'experiment':'C54_PRIOR_BOOT_GB_LOAD','source_boot_sequence':68,'observed_new_boot':69,
        'generation':1,'physical_restore_qualified':True,'store_matches_previous_boot':True,'cleanup_passed':True,
        'agent_requested_reboot':False,'shutdown_method_verified':False,'power_loss_qualified':False,
        'installed_files_or_store_modified':False,'raw_states_ROMs_images_PCM_binaries_IDs_included':False,
        'C53_proof_sha256':sha(parent/'SHA256SUMS')}
(public/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(p.suffix.lower() in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini'} for p in public.rglob('*'))
for p in public.rglob('*'):
 if p.is_file():assert not any(v.encode() in p.read_bytes() for v in [r['private_identity'],r['ROM_sha256'],r['kernel_boot_id']]),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C54 metadata-only proof frozen and verified:',out)
