#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C63 installed-host session evidence without commercial content or IDs."""
from pathlib import Path
import json,re,shutil,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'installed-host-session'
out=repo/'dist/phase4/installed-host-session';assert not out.exists()
parents={}
for name in ['muxretro-package-session','muxretro-installed','muxretro-package','installed-store-backend']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h,n
 parents[name]=sha(proof/'SHA256SUMS')
stages={n:Path((area/('latest-'+n)).read_text().strip()) for n in ['checks','load']}
cr=json.loads((stages['checks']/'analysis.json').read_text());r=json.loads((stages['load']/'analysis.json').read_text())
assert cr['passed'] and r['passed'] and cr['case_count']==104
assert r['session_checks_analysis_sha256']==sha(stages['checks']/'analysis.json')
assert r['C60_proof_sha256']==parents['muxretro-package']
assert r['C62_proof_sha256']==parents['muxretro-installed']
assert r['host_binary_sha256']==json.loads((repo/'dist/phase4/muxretro-installed/plan.json').read_text())['files'][0]['sha256']!=r['old_host_binary_sha256']
assert r['installed_host_used'] and not r['host_ELF_transferred'] and r['installed_host_guard_passed']
assert 'muxretro' not in json.loads((stages['load']/'intent.json').read_text())['binary_sha256']
assert r['installed_CLI_used'] and not r['store_ELF_transferred']
assert r['exact_C59_boot_retained'] and r['native_ABI_passed'] and not r['new_ELF_transferred_to_RAM_only']
assert r['cleanup_passed'] and r['RAM_removed'] and r['root_ro'] and r['global_mountinfo_unchanged']
assert r['store_matches_previous_boot'] and not r['preferences_persisted']
public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
sources={Path(__file__),repo/'docs/analysis/phase4-installed-host-session.md'}
def clean(value):
 if isinstance(value,dict):return {k:('private' if k in {'private_identity','ROM_sha256','kernel_boot_id'} else clean(v)) for k,v in value.items()}
 if isinstance(value,list):return [clean(v) for v in value]
 return value
for label,stage in stages.items():
 report=cr if label=='checks' else r
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
 target=public/label;target.mkdir()
 (target/'analysis.json').write_text(json.dumps(clean(report),indent=2)+'\n')
 if label=='checks':
  for n in ['fixtures.stdout','fixtures.stderr','fixtures.exit','fixtures.py']:shutil.copyfile(stage/n,target/n)
  continue
 a=json.loads((stage/'persistence-analysis.json').read_text())
 physical=json.loads((stage/'physical-observation.json').read_text())
 for key in ['image_and_navigation_confirmed','sound_clean_and_audible_confirmed','restore_to_saved_position_confirmed','launcher_return_confirmed']:
  assert physical[key] is True,key
 assert physical['new_save_requested'] is False
 assert physical['session_analysis_sha256']==sha(stage/'analysis.json')==a['session_analysis_sha256']
 assert a['C59_exact_boot_retained'] and a['new_native_ABI_passed'] and a['reason']=='hotkey' and not a['expired']
 assert a['game_log_sha256']==sha(stage/'collected/game.log') and a['performance_csv_sha256']==sha(stage/'collected/performance.csv')
 assert a['metadata_sha256']==sha(stage/'collected/state-metadata.txt')
 assert a['old_host_tests_reused_for_new_ELF'] is False and a['installed_host_modified'] is False
 for n,h in a['source_sha256'].items():assert sha(repo/n)==h,n;sources.add(repo/n)
 for n in ['persistence-analysis.json','physical-observation.json']:
  (target/n).write_text(json.dumps(clean(json.loads((stage/n).read_text())),indent=2,ensure_ascii=False)+'\n')
 shutil.copyfile(stage/'collected/state-metadata.txt',target/'state-metadata.txt')
 shutil.copyfile(stage/'installed-host-check.stdout',target/'installed-host-check.stdout')
 assert (stage/'running-executable.exit').read_text()=='0\n'
 assert (stage/'running-executable.stdout').read_text()=='C63_RUNNING_EXE=/opt/muos/frontend/muxretro\n'
 shutil.copyfile(stage/'running-executable.stdout',target/'running-executable.stdout')
 marker='C63_FINAL_rootRO0755_PCMclosed_p3off_taint0_UIoff_installedHostValid\n'
 assert (stage/'final-health.exit').read_text()=='0\n'
 assert (stage/'final-health.stdout').read_text()==(stage/'preflight.stdout').read_text()+marker
 (target/'final-health-markers.txt').write_text(marker)
 lines=[]
 for n in ['game.log','core.log','return.log','store-seed.log','store-verify.log']:
  lines.extend(x for x in (stage/'collected'/n).read_text().splitlines() if re.match(r'^(C(44|45|46|50|51|53|58|63)_|RETRO_RUNNER_EXIT=)',x))
 (target/'markers.txt').write_text('\n'.join(lines)+'\n')
timeout=area/'load.2_wgmc5y/timeout-analysis.json'
tr=json.loads(timeout.read_text());assert tr['user_requested_repeat'] and tr['cleanup_passed'] and tr['RAM_removed']
assert not tr['passed'] and not tr['game_started'] and not tr['duration_extended']
shutil.copyfile(timeout,public/'initial-timeout.json')
for source in sorted(sources):
 target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(public/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C63_INSTALLED_HOST_NATIVE_SESSION','checks':104,
 'boot_sequence':r['boot_sequence'],'installed_host_GB_qualified':True,'host_ELF_transferred':False,'new_host_binary_sha256':r['host_binary_sha256'],
 'qualification_scope':'installed C62 host, C46 RAM menu selection and installed C57 CLI load-only',
 'physical_image_input_audio_restore_and_return_confirmed':True,'store_byte_identical':True,'root_read_only':True,
 'cleanup_passed':True,'RAM_removed':True,'installed_host_modified':False,'agent_requested_reboot':False,
 'cold_or_warm_boot_new_host_qualified':False,'continuous_audio_or_long_run_qualified':False,
 'new_host_internal_deadline_exercised':False,
 'raw_states_ROMs_PNGs_PCM_ELFs_private_IDs_included':False,'parent_proofs_sha256':parents},indent=2)+'\n')
for p in public.rglob('*'):
 assert not p.is_symlink()
 if p.is_file():
  assert p.suffix.lower() not in {'.gb','.gbc','.so','.img','.ext4','.png','.wav','.sav','.srm','.state','.bundle','.ini','.tar','.gz'}
  data=p.read_bytes();assert not data.startswith(b'\x7fELF')
  assert not any(v.encode() in data for v in [r['private_identity'],r['ROM_sha256'],r['kernel_boot_id']]),p
assert (work/'graphics-config/output/.config').read_bytes()==(work/'network-tools/baseline.config').read_bytes()
(public/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public,out)
for n,h in sums(out/'SHA256SUMS').items():assert sha(out/n)==h
print('C63 installed host source/metadata-only physical proof frozen:',out)
