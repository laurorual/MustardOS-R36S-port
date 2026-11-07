#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C59 installed-store session proof with commercial identities redacted."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-installed-session'
out=repo/'dist/phase4/gameboy-installed-store';assert not out.exists()
parents={}
for name in ['gameboy-after-boot','installed-store-backend','save-store-installed']:
 p=repo/'dist/phase4'/name
 for n,h in sums(p/'SHA256SUMS').items():assert sha(p/n)==h
 parents[name]=sha(p/'SHA256SUMS')
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['checks','load']}
cr=json.loads((stages['checks']/'analysis.json').read_text());r=json.loads((stages['load']/'analysis.json').read_text())
assert cr['passed'] and cr['case_count']==29 and r['passed']
assert r['installed_CLI_used'] and not r['store_ELF_transferred']
assert r['session_checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
assert r['boot_sequence']==70 and r['source_boot_sequence']==69 and r['original_save_boot_sequence']==68
assert r['cleanup_passed'] and r['RAM_removed'] and r['store_matches_previous_boot']
public=Path(tempfile.mkdtemp(prefix='public.',dir=area));sources={Path(__file__),repo/'docs/analysis/phase4-gb-installed-session.md',repo/'port/scripts/analyze-phase4-gb-installed-session.py'}
def clean(value):
 if isinstance(value,dict):return {k:('private' if k in {'private_identity','ROM_sha256','kernel_boot_id'} else clean(v)) for k,v in value.items()}
 if isinstance(value,list):return [clean(x) for x in value]
 return value
for label,stage in stages.items():
 report=cr if label=='checks' else r
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
 target=public/label;target.mkdir();(target/'analysis.json').write_text(json.dumps(clean(report),indent=2)+'\n')
 if label=='checks':continue
 a=json.loads((stage/'persistence-analysis.json').read_text());physical=json.loads((stage/'physical-observation.json').read_text())
 assert physical['restore_to_saved_position_confirmed'] and physical['launcher_return_confirmed']
 assert physical['session_analysis_sha256']==sha(stage/'analysis.json')==a['session_analysis_sha256']
 assert a['kernel_boot_id_changed_from_C54'] and a['installed_CLI_used'] and a['reason']=='hotkey' and not a['expired']
 assert a['game_log_sha256']==sha(stage/'collected/game.log') and a['performance_csv_sha256']==sha(stage/'collected/performance.csv')
 assert a['metadata_sha256']==sha(stage/'collected/state-metadata.txt')
 for n in ['persistence-analysis.json','physical-observation.json']:
  (target/n).write_text(json.dumps(clean(json.loads((stage/n).read_text())),indent=2,ensure_ascii=False)+'\n')
 shutil.copyfile(stage/'collected/state-metadata.txt',target/'state-metadata.txt')
 lines=[]
 for n in ['game.log','core.log','return.log','store-seed.log','store-verify.log']:
  lines.extend(x for x in (stage/'collected'/n).read_text().splitlines() if re.match(r'^(C(44|45|46|50|51|53|58|59)_|RETRO_RUNNER_EXIT=)',x))
 (target/'markers.txt').write_text('\n'.join(lines)+'\n')
for source in sorted(sources):
 to=public/'source'/source.relative_to(repo);to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,to)
(public/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C59_INSTALLED_CLI_GB_SESSION','checks':29,'boot_sequence':70,
 'installed_CLI_used':True,'store_ELF_transferred':False,'physical_restore_and_return_confirmed':True,'store_byte_identical':True,
 'root_read_only':True,'cleanup_passed':True,'RAM_removed':True,'agent_requested_reboot':False,'shutdown_method_verified':False,
 'raw_states_ROMs_PNGs_PCM_ELFs_private_IDs_included':False,'parent_proofs_sha256':parents},indent=2)+'\n')
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.tar','.gz'}
  data=p.read_bytes();assert not data.startswith(b'\x7fELF')
  assert not any(v.encode() in data for v in [r['private_identity'],r['ROM_sha256'],r['kernel_boot_id']]),p
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C59 source/metadata-only physical/native proof frozen:',out)
