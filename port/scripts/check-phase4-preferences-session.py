#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C21 boundary fixtures: canonical pairs, live volume, and explicit opt-in."""
from pathlib import Path
import json, subprocess, tempfile

repo = Path(__file__).resolve().parents[2]
area = repo / 'build/phase4/preferences'
stage = Path(tempfile.mkdtemp(prefix='session-checks.', dir=area))
helper = repo / 'port/device/rk-r35s-p0/session/preferences.sh'
cases = {}
for name, text, valid in [
    ('saved-pair', 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\n', True),
    ('lower-bound', 'MUOS-PREFS-1\nVOLUME=0\nBRIGHTNESS=40\n', True),
    ('upper-bound', 'MUOS-PREFS-1\nVOLUME=100\nBRIGHTNESS=160\n', True),
    ('shutdown-blank', 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=0\n', False),
    ('overdrive', 'MUOS-PREFS-1\nVOLUME=101\nBRIGHTNESS=75\n', False),
    ('future-schema', 'MUOS-PREFS-2\nVOLUME=60\nBRIGHTNESS=75\n', False),
    ('extra-field', 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75\nPOLICY=3\n', False),
    ('duplicate', 'MUOS-PREFS-1\nVOLUME=60\nVOLUME=61\nBRIGHTNESS=75\n', False),
    ('shell-input', 'MUOS-PREFS-1\nVOLUME=$(touch BAD)\nBRIGHTNESS=75\n', False),
    ('missing-newline', 'MUOS-PREFS-1\nVOLUME=60\nBRIGHTNESS=75', False),
]:
    fixture = stage / name; fixture.write_text(text)
    r = subprocess.run(['sh', '-c', '. "$1"; session_preferences_pair "$2"', 'fixture', str(helper), str(fixture)], capture_output=True)
    assert (r.returncode == 0) == valid, name
    cases[name] = True
for name, live, valid in [
    ('live-matches', 'Volume: 0.60', True),
    ('live-drift', 'Volume: 1.00', False),
    ('muted-transient', 'Volume: 0.60 [MUTED]', False),
    ('missing-sink', '', False),
]:
    r = subprocess.run(['sh', '-c', '. "$1"; prefs_volume=60; wpctl() { printf "%s\\n" "$2"; }; live=$2; wpctl() { printf "%s\\n" "$live"; }; session_preferences_software_volume', 'fixture', str(helper), live], capture_output=True)
    assert (r.returncode == 0) == valid, name
    cases[name] = True
assert not (repo / 'BAD').exists()
report = {'passed': True, 'cases': cases, 'hardware_tested': False}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-session-checks').write_text(str(stage) + '\n')
print('C21 preference boundary fixtures passed:', len(cases), stage)
