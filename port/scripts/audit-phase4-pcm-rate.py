#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read two PCM pointers over pinned SSH; never equate metadata with clock health."""
from pathlib import Path
import argparse
import ipaddress
import json
import re
import subprocess
from phase4_candidate import sha
from phase4_pcm_rate import measure

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', required=True, type=ipaddress.IPv4Address)
parser.add_argument('--boot', required=True, type=int)
parser.add_argument('--generation', required=True)
parser.add_argument('--stage', required=True, type=Path)
parser.add_argument('--label', default='pcm-rate')
args = parser.parse_args()
assert 1 <= args.boot <= 9999
assert re.fullmatch(r'run-[0-9]{4}', args.generation)
assert re.fullmatch(r'[a-z][a-z0-9-]{0,47}', args.label)
repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
stage = args.stage.resolve()
assert stage.is_dir() and stage.is_relative_to(work)
target = stage / args.label
assert not target.with_suffix('.sh').exists(), 'Keep previous observations immutable; use a new label'
code = f'''set -eu
export PATH=/opt/muos/bin:/usr/sbin:/usr/bin:/sbin:/bin
export XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run
[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = {args.boot} ]
[ "$(cat /run/muos/session/current)" = {args.generation} ]
[ -f /run/muos/session/{args.generation}/ready ]
[ ! -e /run/muos/session/{args.generation}/done ]
echo FIRST
cat /proc/asound/card0/pcm0p/sub0/hw_params
cat /proc/asound/card0/pcm0p/sub0/sw_params
cat /proc/asound/card0/pcm0p/sub0/status
sleep 2
echo SECOND
cat /proc/asound/card0/pcm0p/sub0/status
echo END_PCM
[ "$(cat /run/muos/session/current)" = {args.generation} ]
[ -f /run/muos/session/{args.generation}/ready ]
[ ! -e /run/muos/session/{args.generation}/done ]
wpctl get-volume @DEFAULT_AUDIO_SINK@
amixer -c 0 cget name='Playback Volume'
pw-metadata -n settings 0 clock.force-quantum
'''
target.with_suffix('.sh').write_text(code)
ssh = ['ssh', '-p', '2222', '-i', str(work / 'private/c07-client'),
       '-oIdentitiesOnly=yes', '-oStrictHostKeyChecking=yes',
       '-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile=' + str(work / 'private/c07-known_hosts'),
       '-oBatchMode=yes', '-oConnectTimeout=6', 'root@' + str(args.host), 'sh -s']
result = subprocess.run(ssh, input=code, text=True, capture_output=True, timeout=18)
for suffix, value in [('stdout', result.stdout), ('stderr', result.stderr), ('exit', str(result.returncode) + '\n')]:
    target.with_suffix('.' + suffix).write_text(value)
assert result.returncode == 0, (result.returncode, result.stderr)
report = measure(result.stdout.split('END_PCM\n', 1)[0])
report.update({'boot_sequence': args.boot, 'generation': args.generation,
               'source_sha256': {str(p.relative_to(repo)): sha(p) for p in
                                  [Path(__file__), Path(__file__).with_name('phase4_pcm_rate.py')]},
               'device_modified': False, 'physical_audio_qualified': False})
target.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['within_two_percent'] else 2)
