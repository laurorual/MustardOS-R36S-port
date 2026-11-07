#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reject clock measurements across PCM resets, stopped streams or short samples."""
from pathlib import Path
import json
import tempfile
from phase4_pcm_rate import measure

sample = '''FIRST
rate: 44100 (44100/1)
state: RUNNING
owner_pid   : 123
trigger_time: 1.000000000
tstamp      : 2.000000000
hw_ptr      : 44100
SECOND
state: RUNNING
owner_pid   : 123
trigger_time: 1.000000000
tstamp      : 4.000000000
hw_ptr      : 132300
'''
cases = {'correct_rate': measure(sample)['within_two_percent']}
cases['half_rate_detected'] = not measure(sample.replace('132300', '88200'))['within_two_percent']
for name, changed in {
    'changed_owner': sample.replace('SECOND\nstate: RUNNING\nowner_pid   : 123', 'SECOND\nstate: RUNNING\nowner_pid   : 124'),
    'changed_trigger': sample.replace('SECOND\nstate:', 'SECOND\ntrigger_time: 8.000000000\nstate:').replace('trigger_time: 1.000000000\ntstamp      : 4.', 'tstamp      : 4.'),
    'stopped_stream': sample.replace('state: RUNNING', 'state: PREPARED', 1),
    'pointer_reset': sample.replace('132300', '100'),
    'short_interval': sample.replace('4.000000000', '2.500000000'),
    'clock_reversed': sample.replace('4.000000000', '1.500000000'),
    'missing_timestamp': sample.replace('tstamp      : 4.000000000\n', ''),
    'duplicate_owner': sample + 'owner_pid : 123\n',
}.items():
    try:
        measure(changed)
    except (AssertionError, ValueError):
        cases[name] = True
    else:
        raise AssertionError(name)
assert all(cases.values())
repo = Path(__file__).resolve().parents[2]
area = repo / 'build/phase4/audio-clock-audit'
stage = Path(tempfile.mkdtemp(prefix='pcm-rate-checks.', dir=area))
from phase4_candidate import sha
report = {'passed': True, 'cases': cases, 'device_accessed': False,
          'source_sha256': {str(p.relative_to(repo)): sha(p) for p in [Path(__file__), Path(__file__).with_name('phase4_pcm_rate.py')]}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-pcm-rate-checks').write_text(str(stage) + '\n')
print('PCM rate checks:', len(cases), stage)
