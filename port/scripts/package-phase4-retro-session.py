#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C44 evidence; exclude preference fingerprints, ELFs and private data."""
from pathlib import Path
import json
import re
import shutil
import tempfile
from phase4_candidate import sha
from phase4_pcm_rate import measure

repo = Path(__file__).resolve().parents[2]
area = repo / 'build/phase4/retro-session'
out = repo / 'dist/phase4/retro-session-native'
assert not out.exists(), 'Evidence is immutable; choose a new version'
public = Path(tempfile.mkdtemp(prefix='public.', dir=area))
sources = {str(Path(__file__).relative_to(repo)), 'port/scripts/phase4_pcm_rate.py'}


def copy(src, dst):
    target = public / dst
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)


def report(stage, label, current=True, positive=True):
    data = json.loads((stage / 'analysis.json').read_text())
    assert data['passed'] is positive, (stage, data)
    if current:
        # Validate each report independently; never hide differing source pins.
        for name, digest in data['source_sha256'].items():
            assert sha(repo / name) == digest, (stage, name)
            sources.add(name)
    copy(stage / 'analysis.json', label + '/analysis.json')
    return data


for name, pointer in [('build', 'latest'), ('audit', 'latest-audit'),
                      ('runner', 'latest-runner'),
                      ('runner-checks', 'latest-runner-checks'),
                      ('worker-checks', 'latest-worker-checks')]:
    stage = Path((area / pointer).read_text().strip())
    report(stage, name)

build = Path((area / 'latest').read_text().strip())
audit = Path((area / 'latest-audit').read_text().strip())
br = json.loads((build / 'analysis.json').read_text())
ar = json.loads((audit / 'analysis.json').read_text())
assert ar['build_stage'] == str(build) and ar['binary_sha256'] == br['binary_sha256']
assert sha(build / 'source/bin/muxretro') == br['binary_sha256']
runner = Path((area / 'latest-runner').read_text().strip())
rr = json.loads((runner / 'analysis.json').read_text())
assert sha(runner / 'muos-retro-runner') == rr['native_sha256']


def native(stage, label, current=True, positive=True):
    data = report(stage, label, current, positive)
    assert data['cleanup_passed'] and data['RAM_removed'] and data['root_ro']
    assert data['global_mountinfo_unchanged'] and not data['preferences_persisted']
    if current:
        assert data['runner_sha256'] == rr['native_sha256']
    for name in ['intent.json', 'dispatch.json']:
        copy(stage / name, label + '/' + name)
    for prefix in ['preflight', 'prepare', 'native', 'postflight', 'mount-health', 'cleanup']:
        # No raw original preference hashes or copies are included.
        for suffix in ['sh', 'exit', 'stdout', 'stderr']:
            copy(stage / (prefix + '.' + suffix), label + '/' + prefix + '.' + suffix)
    collected = stage / 'collected'
    copy(collected / 'result.txt', label + '/result.txt')
    log = (collected / 'core.log').read_text() if (collected / 'core.log').exists() else ''
    selected = [line for line in log.splitlines() if
                re.search(r'^C44_|^RETRO_RUNNER_|Window Creation Failed|EGL not initialized|'
                          r'Controller opened:|Controller axis [0-9]+ active:|'
                          r'Audio device opened at|SDL Renderer Method:|Exit frame mirrored', line)]
    selected = [re.sub(r'\x1b\[[0-9;]*m', '', line) for line in selected]
    (public / label / 'core-markers.txt').write_text('\n'.join(selected) + '\n')
    if positive and data['mode'] == 'graphics':
        assert 'C44_FIRST_PRESENT seconds=45' in log
        assert re.search(r'^C44_NORMAL_EXIT expired=1 frames=[1-9][0-9]*$', log, re.M)
    return data


for mode in ['prepare-failure', 'signal-test', 'graphics']:
    stage = Path((area / ('latest-' + mode)).read_text().strip())
    native(stage, mode)

graphics = Path((area / 'latest-graphics').read_text().strip())
observation = json.loads((graphics / 'physical-observation.json').read_text())
assert observation['input_qualified'] and observation['image_expected_seen']
assert observation['activity_confirmed_before_prompt']
pcm = measure((graphics / 'pcm-live.stdout').read_text())
assert pcm['within_two_percent'] and pcm == json.loads((graphics / 'pcm-live.json').read_text())
for name in ['physical-observation.json', 'observation-active-receipt.stdout',
             'pcm-live.json', 'pcm-live.stdout', 'pcm-live.sh', 'pcm-live.exit']:
    copy(graphics / name, 'graphics/' + name)

# Keep the resolved failure and unqualified observation distinct from approval.
native(area / 'graphics.o761lya4', 'history/egl-failure', current=False, positive=False)
late = area / 'graphics.6mz7gxbz'
native(late, 'history/late-observation')
assert not json.loads((late / 'physical-observation.json').read_text())['input_qualified']
copy(late / 'physical-observation.json', 'history/late-observation/physical-observation.json')

for name in sorted(sources):
    copy(repo / name, 'source/' + name)
(public / 'NOTICE.txt').write_text(
    'C44 native Libretro diagnostic session, boot 65; original no-content core C40, '
    'no ROM/BIOS. Display and physical D-pad confirmed while process active. '
    '45-second normal exit, 2700 frames; cleanup/rootRO/foundation97/network preserved. '
    'Real preferences RO+noload, RAM copy only, global mounts unchanged. '
    'PCM approximately 44100 frames/s; core audio is digital zero, no acoustic approval. '
    'Failure and signal rollback rehearsed before graphics. Historical EGL failure '
    'and late unqualified observation retained separately. No installed firmware '
    'change, reboot or boot token. No ELF, image, GPU blob, private preference '
    'copy/fingerprint, backup, key, seed or credential included.\n')
(public / 'SHA256SUMS').write_text(''.join(
    sha(p) + '  ' + str(p.relative_to(public)) + '\n'
    for p in sorted(public.rglob('*')) if p.is_file()))
shutil.move(public, out)
print('C44 public evidence frozen:', out)
