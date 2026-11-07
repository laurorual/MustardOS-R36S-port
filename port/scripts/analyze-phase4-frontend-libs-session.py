#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C66 technical results; report audio counters without inferring acoustic quality."""
from pathlib import Path
import argparse, csv, io, json, re
from phase4_candidate import sha
from phase4_frontend_libs_session import WORK, REPO

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('stage', type=Path)
args = p.parse_args()
stage = args.stage.resolve()
r = json.loads((stage / 'analysis.json').read_text())
assert r['passed'] and r['experiment'] == 'C66_FRONTEND_PROVIDER_RAM'
for k in ['cleanup_passed', 'RAM_removed', 'root_ro', 'global_mountinfo_unchanged',
          'store_byte_identical_to_C63', 'native_eager_provider_and_installed_host_CLI_passed', 'process_maps_confirmed']:
    assert r[k] is True, k
assert r['new_boot_explicitly_bound'] and not r['exact_C63_boot_retained']
assert r['boot_sequence'] > r['prior_boot_sequence']
assert not r['agent_requested_reboot'] and not r['new_save_requested']
assert r['installed_host_used'] and not r['host_ELF_transferred'] and not r['store_ELF_transferred']
for n, h in r['source_sha256'].items():
    assert sha(REPO / n) == h
game = (stage / 'collected/game.log').read_text()
assert 'Quick Save (hotkey)' not in game and 'Quick Load (hotkey)' in game and 'Loaded state from ' in game
match = re.search(r'^C44_NORMAL_EXIT expired=0 frames=([1-9][0-9]*)$', game, re.M)
assert match and int(match[1]) == r['core_frames']
assert 'C45_LAUNCHER_EXIT action=port-cycle-done' in (stage / 'collected/return.log').read_text()
raw = (stage / 'collected/performance.csv').read_text()
sections = raw.split('\n\n')
stages = {x['stage']: x for x in csv.DictReader(io.StringIO(sections[0]))}
metrics = dict(csv.reader(io.StringIO(next(s for s in sections if s.startswith('metric,value\n')).split('\n', 1)[1])))
metadata = (stage / 'collected/state-metadata.txt').read_text()
assert re.fullmatch(r'C51_STATE_VALID version=1 core_bytes=26861 core_crc_valid=1 manifest_valid=1 thumbnail_signature_valid=1 tmpfs=1\n', metadata)
report = {'passed': True, 'experiment': 'C66_PROVIDER_TECHNICAL_QUALIFICATION',
          'session_analysis_sha256': sha(stage / 'analysis.json'), 'reason': 'hotkey',
          'core_frames': r['core_frames'], 'expired': False, 'maximum_seconds': 45,
          'frames_per_deadline_second': None, 'voluntary_exit_wall_duration_measured': False,
          'reported_recent_core_hz': float(metrics['core_run_hz']),
          'frame_mean_ms': float(stages['frame']['mean_ms']),
          'audio_underruns': int(metrics['audio_underruns']),
          'audio_missing_frames': int(metrics['audio_underrun_missing_frames']),
          'state_core_bytes': 26861, 'state_core_CRC_and_PNG_signature_valid': True,
          'installed_store_calls': {'status': 2, 'export': 1}, 'new_save_requested': False,
          'source_sha256': {str(Path(__file__).resolve().relative_to(REPO)): sha(Path(__file__))}}
(stage / 'technical-analysis.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['passed', 'core_frames', 'reported_recent_core_hz', 'audio_underruns', 'audio_missing_frames']}, indent=2))
