#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C59 installed CLI session provenance; no shutdown method inferred."""
from pathlib import Path
import argparse,csv,io,json,re
from phase4_candidate import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);args=p.parse_args()
stage=args.stage.resolve();r=json.loads((stage/'analysis.json').read_text())
assert r['passed'] and r['cleanup_passed'] and r['RAM_removed']
game=(stage/'collected/game.log').read_text();ret=(stage/'collected/return.log').read_text()
exit_matches=re.findall(r'^C50_EXIT reason=(hotkey|deadline) frames=([1-9][0-9]*)$',game,re.M)
assert len(exit_matches)==1;reason,frames=exit_matches[0];frames=int(frames)
normal=re.search(r'^C44_NORMAL_EXIT expired=([01]) frames=([1-9][0-9]*)$',game,re.M)
assert normal and int(normal[2])==frames and int(normal[1])==(reason=='deadline')
assert 'C50_HOTKEY_READY seconds=45 modifier=menu button=start auto_save=0 timeline=0 sram_flush=0' in game
assert 'C45_LAUNCHER_EXIT action=port-cycle-done' in ret
if reason=='hotkey':assert r['mode'] in {'save','load'} and 'Quit (hotkey)' in game
raw=(stage/'collected/performance.csv').read_text();sections=raw.split('\n\n')
stages={x['stage']:x for x in csv.DictReader(io.StringIO(sections[0]))}
metrics=dict(csv.reader(io.StringIO(next(s for s in sections if s.startswith('metric,value\n')).split('\n',1)[1])))
report={'experiment':'C59_INSTALLED_CLI_PERSISTENCE','reason':reason,'core_frames':frames,'expired':bool(int(normal[1])),
        'maximum_seconds':45,'frames_per_deadline_second':frames/45 if reason=='deadline' else None,
        'voluntary_exit_wall_duration_measured':False,'frame_mean_ms':float(stages['frame']['mean_ms']),
        'reported_recent_core_hz':float(metrics['core_run_hz']),'audio_underruns':int(metrics['audio_underruns']),
        'audio_missing_frames':int(metrics['audio_underrun_missing_frames']),
        'technical_launcher_return':True,'preferences_persisted':False,
        'session_analysis_sha256':sha(stage/'analysis.json'),'game_log_sha256':sha(stage/'collected/game.log'),
        'performance_csv_sha256':sha(stage/'collected/performance.csv'),
        'source_sha256':{str(Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[2])):sha(Path(__file__))}}
assert reason=='hotkey'
role=r['mode'];assert role in {'save','load'}
metadata=(stage/'collected/state-metadata.txt').read_text()
assert re.fullmatch(r'C51_STATE_VALID version=1 core_bytes=([1-9][0-9]*) core_crc_valid=1 manifest_valid=1 thumbnail_signature_valid=1 tmpfs=1\n',metadata)
if role=='save':
 assert 'Quick Save (hotkey)' in game and 'Saved state to ' in game
 assert 'C53_COMMITTED current=1 source_tmpfs=1' in (stage/'collected/store-commit.log').read_text()
 assert 'C53_STORE_END operation=commit status=0 data_ro=1' in (stage/'collected/store-commit.log').read_text()
else:
 assert 'Quick Load (hotkey)' in game and 'Loaded state from ' in game
 assert 'Quick Save (hotkey)' not in game
 assert 'C53_SEEDED_FROM_EXT4 current=1 identity_matched=1 metadata_valid=1' in (stage/'collected/store-seed.log').read_text()
 assert 'C53_STORE_READONLY_BYTE_EXACT current=1' in (stage/'collected/store-verify.log').read_text()
 assert (stage/'collected/store-readonly-before.sha256').read_bytes()==(stage/'collected/store-readonly-after.sha256').read_bytes()
 assert (stage/'collected/seed-metadata.txt').read_text()==metadata
report.update(role=role,PKST_core_crc_valid=True,state_core_bytes=int(re.search('core_bytes=([0-9]+)',metadata)[1]),
              generation=1,snapshot_committed=(role=='save'),snapshot_loaded_from_ext4=(role=='load'),
              store_preserved_byte_exact=(role=='load'),commercial_state_exported=False,
              controlled_reboot_persistence_qualified=False,metadata_sha256=sha(stage/'collected/state-metadata.txt'))
assert r['experiment']=='C59_INSTALLED_CLI_GB_LOAD'
assert r['source_boot_sequence']+1==r['boot_sequence']
assert r['existing_new_boot_observed'] and not r['reboot_requested_by_this_task']
assert r['store_matches_previous_boot']
prior=json.loads((Path(r['source_C54_stage'])/'analysis.json').read_text())
assert r['kernel_boot_id']!=prior['kernel_boot_id']
report['kernel_boot_id_changed_from_C54']=True
assert r['installed_CLI_used'] and not r['store_ELF_transferred']
logs=(stage/'collected/store-seed.log').read_text()+(stage/'collected/store-verify.log').read_text()
assert logs.count('C58_INSTALLED_DISPATCH operation=status')==2 and logs.count('C58_INSTALLED_DISPATCH operation=export')==1
report.update(installed_CLI_used=True,store_ELF_transferred=False,native_dispatch_calls={'status':2,'export':1})
report.update(source_boot_sequence=r['source_boot_sequence'],boot_sequence=r['boot_sequence'],
              snapshot_matches_previous_boot=True,persistence_after_observed_new_boot_qualified=True,
              controlled_reboot_requested=False,shutdown_method_verified=False)
(stage/'persistence-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['reason','core_frames','expired','frames_per_deadline_second','reported_recent_core_hz','audio_underruns','technical_launcher_return']},indent=2))
