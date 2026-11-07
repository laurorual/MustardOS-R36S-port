#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze the bounded C29 PCM timing isolation, including failed sampling."""
from pathlib import Path
import json, shutil, tempfile
from phase4_candidate import sha

repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
clock = work / 'audio-clock-audit'
failed = clock / 'silent.50_22hut'; baseline = clock / 'silent.bt7y1e3u'
current = clock / 'silent.kjral1dx'
session = work / 'audio-buffers/session.a6py0d1b'
trial = work / 'rootfs-candidate/c25-physical.mhdme9fw'
assert not json.loads((failed / 'analysis.json').read_text())['passed']
for stage in [baseline, current]:
    report = json.loads((stage / 'analysis.json').read_text())
    assert report['passed'] and report['mixer_restored_byte_exact'] and report['RAM_and_private_debugfs_cleaned']
    assert sha(stage / 'native-probe.sh') == json.loads((stage / 'intent.json').read_text())['source_sha256']
assert json.loads((session / 'analysis.json').read_text())['passed']
assert json.loads((session / 'clock-path-analysis.json').read_text())['audio_qualified'] is False
destination = repo / 'dist/phase4/pcm-clock-isolation'; assert not destination.exists()
public = Path(tempfile.mkdtemp(prefix='clock-proof.', dir=clock))
def copy(path, rel):
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_size < 262144, path
    target = public / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
for label, stage in [('sampling-failure', failed), ('direct-RW-default', baseline), ('direct-MMAP-small', current)]:
    for name in ['intent.json', 'analysis.json', 'native-probe.sh']:
        copy(stage / name, label + '/' + name)
    for prefix in ['preflight', 'prepare', 'probe', 'recovery-cleanup' if stage == failed else 'cleanup']:
        for ext in ['sh', 'stdout', 'stderr', 'exit']:
            copy(stage / (prefix + '.' + ext), label + '/' + prefix + '.' + ext)
    # Exact whitelist derived from the probe variant set, no raw recordings.
    formats = ['MMAP_S32_LE', 'MMAP_S16_LE', 'RW_SMALL_S32_LE'] if stage == current else ['S32_LE', 'S16_LE']
    for fmt in formats:
        for tail in ['player.log', 'params.txt', 'first.txt', 'second.txt', 'clocks.txt']:
            copy(stage / 'collected' / (fmt + '-' + tail), label + '/collected/' + fmt + '-' + tail)
    for name in ['mixer-before.txt', 'mixer-after.txt']:
        copy(stage / 'collected' / name, label + '/collected/' + name)
for name in ['analysis.json', 'clock-path-analysis.json', 'session.json', 'generation.json']:
    copy(session / name, 'PipeWire-idle/' + name)
for prefix in ['idle-clock-readback', 'idle-audio-registers', 'stop', 'health']:
    for ext in ['sh', 'stdout', 'stderr', 'exit']:
        copy(session / (prefix + '.' + ext), 'PipeWire-idle/' + prefix + '.' + ext)
for name in ['result', 'report.txt', 'preferences-loaded.txt', 'preferences-saved.txt',
             'brightness-before.txt', 'brightness-after.txt', 'mixer-before.txt', 'mixer-after.txt',
             'drm-before.txt', 'drm-after.txt', 'volume-before.sha256', 'volume-after.sha256',
             'wireplumber-before.sha256', 'wireplumber-after.sha256']:
    copy(session / 'collected' / name, 'PipeWire-idle/collected/' + name)
for prefix in ['fallback-clock-audit', 'fallback-clock-audit-ns']:
    for ext in ['sh', 'stdout', 'stderr', 'exit']:
        copy(trial / (prefix + '.' + ext), 'C07-clocks/' + prefix + '.' + ext)
for name in ['port/device/rk-r35s-p0/audio-buffers/silent-clock-probe.sh',
             'port/scripts/phase4-silent-clock-audit.py',
             'port/scripts/package-phase4-clock-audit-proofs.py']:
    copy(repo / name, 'source/' + name)
rates = json.loads((current / 'analysis.json').read_text())['direct_ALSA_frames_per_second']
assert all(abs(rate / 44100 - 1) < .01 for rate in rates.values())
analysis = {'passed': True, 'scope': 'diagnostic isolation and cleanup, not UI audio approval',
    'boot_sequence': 55, 'direct_ALSA_small_buffer_rates': rates,
    'direct_ALSA_rates_within_one_percent': True,
    'PipeWire_idle_pcm_rate': json.loads((session / 'clock-path-analysis.json').read_text())['measured_pcm_rate'],
    'declared_rate': 44100, 'audio_fix_installed': False, 'audio_qualified': False,
    'mixer_route_difference_not_isolated': True,
    'gain215_quantum1024_profile_unchanged': True, 'saved_pair': [55, 70],
    'no_new_user_sound_test_or_reboot': True, 'no_microphone_opened': True,
    'sampling_failure_and_recovery_preserved': True,
    'all_players_sessions_debugfs_and_RAM_cleaned': True}
(public / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
(public / 'NOTICE.txt').write_text('C29 direct digital-zero ALSA versus idle PipeWire PCM timing. No UI sound approval or electrical clock measurement. Mixer restored, profile215 unchanged, no new reboot or microphone recording. No image, raw audio, seed, SSH/network credentials or private backup. Current sources are included for reuse; each historical probe.sh is separately pinned by its own intent.\n')
(public / 'SHA256SUMS').write_text(''.join(sha(f) + '  ' + str(f.relative_to(public)) + '\n' for f in sorted(public.rglob('*')) if f.is_file()))
shutil.move(public, destination)
print('PCM timing isolation proof frozen:', destination)
