#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the explicit physical sequence; retain duplicates rather than filter."""
from collections import Counter
import json
from pathlib import Path
import sys

events = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
expected = [305, 304, 307, 308, 310, 311, 312, 313, 314, 315, 316, 317, 318, 114, 115]
presses = [e['code'] for e in events if e['type'] == 1 and e['value'] == 1]
releases = [e['code'] for e in events if e['type'] == 1 and e['value'] == 0]
state = {}
for event in events:
    if event['type'] == 1 and event['value'] != 2:
        state[event['code']] = event['value']
checks = {'exact_button_order': presses == expected,
          'balanced_releases': Counter(presses) == Counter(releases),
          'no_stuck_keys': not any(state.values()),
          'no_syn_dropped': not any(e['type'] == 0 and e['code'] == 3 for e in events)}
axes = {}
for code in (0, 1, 3, 4):
    values = [e['value'] for e in events if e['type'] == 3 and e['code'] == code]
    axes[str(code)] = {'values': values}
    checks['axis_' + str(code)] = (bool(values) and next((v for v in values if v), 0) < 0
                                  and min(values) < -25000 and max(values) > 25000 and values[-1] == 0)
for code in (16, 17):
    values = [e['value'] for e in events if e['type'] == 3 and e['code'] == code]
    axes[str(code)] = {'values': values}
    checks['hat_' + str(code)] = values == [-1, 0, 1, 0]
l3 = [e for e in events if e['type'] == 1 and e['code'] == 317]
checks['l3_single_pair'] = [e['value'] for e in l3] == [1, 0]
report = {'scope': 'evdev/uinput mapping only; no SDL/frontend or power-key validation',
          'event_count': len(events), 'press_codes': presses, 'release_codes': releases,
          'checks': checks, 'axes': axes, 'l3_events': l3, 'pass': all(checks.values())}
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['pass'] else 1)
