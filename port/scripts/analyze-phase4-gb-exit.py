#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C50 exit provenance; a voluntary exit is not a 45-second throughput sample."""
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
if reason=='hotkey':assert r['mode']=='observe' and 'Quit (hotkey)' in game
raw=(stage/'collected/performance.csv').read_text();sections=raw.split('\n\n')
stages={x['stage']:x for x in csv.DictReader(io.StringIO(sections[0]))}
metrics=dict(csv.reader(io.StringIO(next(s for s in sections if s.startswith('metric,value\n')).split('\n',1)[1])))
report={'experiment':'C50_EXIT_PROVENANCE','reason':reason,'core_frames':frames,'expired':bool(int(normal[1])),
        'maximum_seconds':45,'frames_per_deadline_second':frames/45 if reason=='deadline' else None,
        'voluntary_exit_wall_duration_measured':False,'frame_mean_ms':float(stages['frame']['mean_ms']),
        'reported_recent_core_hz':float(metrics['core_run_hz']),'audio_underruns':int(metrics['audio_underruns']),
        'audio_missing_frames':int(metrics['audio_underrun_missing_frames']),
        'technical_launcher_return':True,'preferences_persisted':False,
        'session_analysis_sha256':sha(stage/'analysis.json'),'game_log_sha256':sha(stage/'collected/game.log'),
        'performance_csv_sha256':sha(stage/'collected/performance.csv'),
        'source_sha256':{str(Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[2])):sha(Path(__file__))}}
(stage/'exit-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['reason','core_frames','expired','frames_per_deadline_second','reported_recent_core_hz','audio_underruns','technical_launcher_return']},indent=2))
