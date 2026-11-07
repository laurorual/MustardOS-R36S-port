#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise the actual direct-zero startup hook without opening hardware."""
from pathlib import Path
import json
import subprocess
import tempfile
from phase4_candidate import sha

repo = Path(__file__).resolve().parents[2]
source = repo / 'port/device/rk-r35s-p0/S95muos-core'
text = source.read_text(); prefix = text.split('case "${1:-}" in', 1)[0]
assert text.index('if ! audio_prime_pcm;') < text.index('if ! "$audio_service" start;')
area = repo / 'build/phase4/audio-clock-audit'
stage = Path(tempfile.mkdtemp(prefix='prime-checks.', dir=area)); cases = []
for label, quantum, before, after, player_rc, want in [
    ('legacy_disabled', 0, 'RUNNING', 'RUNNING', 0, 0),
    ('zero_cycle', 1024, 'closed', 'closed', 0, 0),
    ('foreign_pcm', 1024, 'RUNNING', 'closed', 0, 64),
    ('player_failure', 1024, 'closed', 'closed', 1, 1),
    ('pcm_left_open', 1024, 'closed', 'RUNNING', 0, 1),
]:
    state = stage / label; state.mkdir()
    # Only replace the fixed executable in the disposable shell fixture.
    fixture = prefix.replace('/usr/bin/aplay -q', 'fixture_aplay -q')
    code = fixture + f'''
state={state}; audio_quantum={quantum}; fixture_phase=before
cat() {{
 [ "$*" = /proc/asound/card0/pcm0p/sub0/status ] || return 99
 if [ "$fixture_phase" = before ]; then echo {before}; else echo {after}; fi
}}
fixture_aplay() {{
 printf '%s\\n' "$*" > "$state/arguments"
 fixture_phase=after
 return {player_rc}
}}
audio_prime_pcm
'''
    result = subprocess.run(['sh', '-c', code], capture_output=True, text=True)
    assert result.returncode == want, (label, result.stderr)
    called = (state / 'arguments').exists()
    assert called == (quantum == 1024 and before == 'closed')
    if called:
        assert (state / 'arguments').read_text().strip() == '-q -D hw:0,0 -M -t raw -f S32_LE -c 2 -r 44100 --period-size=1024 --buffer-size=4096 -d 1 /dev/zero'
    assert (state / 'pcm-prime.txt').exists() == (label == 'zero_cycle')
    (state / 'fixture.sh').write_text(code); cases.append(label)
report = {'passed': True, 'cases': cases, 'hardware_accessed': False,
          'before_PipeWire_checked': True,
          'source_sha256': {str(p.relative_to(repo)): sha(p) for p in [Path(__file__), source]}}
(stage / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
(area / 'latest-prime-checks').write_text(str(stage) + '\n')
print('PCM prime checks:', len(cases), stage)
