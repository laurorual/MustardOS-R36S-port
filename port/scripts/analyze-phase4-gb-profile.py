#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Analyze native perf CSV without confusing nominal Hz and wall throughput."""
from pathlib import Path
import argparse, csv, io, json, re
from phase4_candidate import sha

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
args = p.parse_args()
stage = args.stage.resolve()
session = json.loads((stage/'analysis.json').read_text())
assert session['passed'] and session['cleanup_passed'] and session['RAM_removed']
raw = (stage/'collected/performance.csv').read_text()
sections = raw.split('\n\n')
stages = {r['stage']:r for r in csv.DictReader(io.StringIO(sections[0]))}
metric_sections = [s for s in sections if s.startswith('metric,value\n')]
assert len(metric_sections) == 1
metrics = dict(csv.reader(io.StringIO(metric_sections[0].split('\n',1)[1])))
log = (stage/'collected/game.log').read_text()
frames = int(re.search(r'^C44_NORMAL_EXIT expired=1 frames=(\d+)$',log,re.M)[1])
seconds = int(re.search(r'^C44_FIRST_PRESENT seconds=(\d+) ',log,re.M)[1])
assert seconds == 45 and frames > 0
assert int(stages['frame']['samples']) > 500
callbacks = {m[0]:{'calls':int(m[1]), 'total_ms':float(m[2]), 'mean_ms':float(m[3])}
             for m in re.findall(r'^C48_CALLBACK name=(\w+) calls=(\d+) total_ms=([\d.]+) mean_ms=([\d.]+)$',log,re.M)}
keys = ['cpu_governor','cpu_frequency_khz','sdl_video_driver','sdl_audio_driver',
        'core_target_hz','panel_hz','core_run_hz','swap_interval','vsync_effective',
        'audio_underruns','audio_underrun_missing_frames','audio_rate_correction_percent',
        'audio_backpressure_wait_ms','frame_delay_ms','audio_freq','audio_channels',
        'video_source_resolution','video_output_resolution']
report = {'experiment':'C49_GB_PERFORMANCE','session_stage':str(stage),
          'session_analysis_sha256':sha(stage/'analysis.json'),
          'performance_csv_sha256':sha(stage/'collected/performance.csv'),
          'game_log_sha256':sha(stage/'collected/game.log'),
          'frames':frames,'deadline_seconds':seconds,'approximate_frames_per_second':frames/seconds,
          'stages':stages, 'metrics':{k:metrics[k] for k in keys if k in metrics},
          'callbacks_including_startup':callbacks,'audio_negotiation':re.findall(r'Audio device opened at (\d+) Hz \(core native (\d+) Hz\)',log),
          'limitations':['Wall rate uses bounded deadline; not hardware frame timestamps.',
                         'Stage rolling windows have at most 1024 samples; nested stages overlap.',
                         'Callback totals include priming/startup and cannot be subtracted from rolling-window totals.',
                         'Private Game Boy content; digital telemetry alone does not qualify acoustic output.'],
          'source_sha256':{str(Path(__file__).resolve().relative_to(Path(__file__).resolve().parents[2])):sha(Path(__file__))}}
(stage/'performance-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['frames','approximate_frames_per_second','metrics','callbacks_including_startup']},indent=2))
