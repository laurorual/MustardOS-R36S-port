#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze full-UI proof and matching source, excluding private GPU/runtime."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import tarfile

repo = Path(__file__).resolve().parents[2]
work = repo / 'build/phase4'
f = work / 'frontend-session'
approved = json.loads((f / 'audio-approved.json').read_text())
assert approved['user_confirmed']
final = f / approved['session'] / 'evidence'
result = json.loads((final / 'frontend-result.json').read_text())
assert result['returncode'] == 0 and result['ready_observed']
assert (final / 'mixer-before.state').read_bytes() == (final / 'mixer-after.state').read_bytes()
health = json.loads((final / 'health-after.json').read_text())
assert health['taint'] == '0' and health['backlight_brightness'] == health['backlight_expected']
stage = Path((f / 'latest-staging').read_text().strip())
staging = json.loads((stage / 'staging-manifest.json').read_text())
assert staging['staging_sha256'] == approved['staging_sha256']
out = repo / 'dist/phase4/frontend-full-native'
out.mkdir()  # Freeze a new checkpoint; do not overwrite historical evidence.
for name in ['inspect-approved.json', 'video-approved.json', 'audio-approved.json', 'resource-blobs.json']:
    shutil.copy2(f / name, out / name)
shutil.copy2(stage / 'staging-manifest.json', out / 'staging-manifest.json')
shutil.copy2(repo / 'port/packaging/pending-licenses.json', out / 'pending-licenses.json')
sessions = []
for p in sorted(f.glob('frontend-*.*')):
    if not p.is_dir():
        continue
    evidence = p / 'evidence'
    assert (evidence / 'health-after.json').exists(), p
    assert not (p / 'core-staging.tar.gz').is_symlink()
    dest = out / 'sessions' / p.name
    shutil.copytree(evidence, dest)
    shutil.copy2(p / 'native-session.log', dest / 'native-session.log')
    sessions.append({'session':p.name,
                     'worker_status0':'PHASE4_CORE_WORKER_EXIT_STATUS=0' in (p/'native-session.log').read_text(),
                     'final_approved_audio':p.name==approved['session']})
shutil.copytree(work / 'foundation/frontend-bin', out / 'frontend-bin')
(out / 'helpers').mkdir()
for name in ['muos-sdl-map', 'frontend-contract', 'egl-context']:
    shutil.copy2(stage / 'rootfs/opt/port-probes' / name, out / 'helpers' / name)
shutil.copy2(work / 'menu/frontend-source.tar', out / 'frontend-source.tar')
shutil.copy2(work / 'foundation/deps/mojibake-0.3.6.tar.gz', out / 'mojibake-0.3.6.tar.gz')
shutil.copy2(f / 'resources/script/system/assign.sh', out / 'assign.sh')
with tarfile.open(out / 'internal-resources-source.tar.gz', 'w:gz') as archive:
    archive.add(f / 'resources/script', arcname='script')
    archive.add(work / 'foundation/core-manifest-upstream.json', arcname='share/info/manifest/core.json')
    archive.add(repo / 'refs/muos/internal/LICENSE', arcname='LICENSE')
with tarfile.open(out / 'port-source.tar.gz', 'w:gz') as archive:
    for p in sorted((repo / 'port').rglob('*')):
        if p.is_file() and '__pycache__' not in str(p) and p.suffix != '.pyc':
            archive.add(p, arcname=str(p.relative_to(repo)), recursive=False)
shutil.copy2(work / 'foundation/frontend-compile.log', out / 'frontend-compile.log')
record = {'scope':'bounded full native frontend and real volume/brightness on installed BSP',
          'user_video':json.loads((f/'video-approved.json').read_text()),
          'user_audio_controls':approved,'sessions':sessions,
          'firmware_boot_tested':False,'candidate_kernel_tested':False,
          'private_gpu_runtime_included':False,'redistribution_approved':False,
          'help_original_wave_approved':False,'help_control_wave_tested':True,
          'power_blank_suspend_tested':False,'native_sessions_cleaned':True,
          'next_image_requires_board_patch_and_runtime_resources':True}
(out / 'native-results.json').write_text(json.dumps(record,indent=2)+'\n')
(out / 'NOT-A-FIRMWARE.txt').write_text(
    'Private full-UI proof; no rootfs image, staging runtime tar, Mali ELF or vendor ZIP.\n'
    'Executables require the recorded Buildroot libraries; Debian compatibility is not assumed.\n'
    'Failed preflights and the double-volume session are retained, not approved.\n'
    'The final audio session uses board patch0006 and temporary help WAV controls.\n'
    'No independent boot or candidate-kernel runtime is validated.\n'
    'Source: frontend/internal GPLv3, Mojibake MIT, original mapping utility MIT.\n')
with (out / 'SHA256SUMS').open('w') as sums:
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name != 'SHA256SUMS':
            with p.open('rb') as stream:
                sums.write(f'{hashlib.file_digest(stream,"sha256").hexdigest()}  {p.relative_to(out)}\n')
print('Full native frontend proof/source frozen:', out)
