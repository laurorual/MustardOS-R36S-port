#!/usr/bin/env python3
"""Diagnostic hooks for the private core worker; no mixer writes here."""
import json
from pathlib import Path
import struct
import subprocess
import time
import wave


def snapshot(command, jail, root, label):
    result = {}
    for key, control in [('playback', 'name=Playback Volume'),
                         ('route', 'name=Playback Path'),
                         ('headphone', 'iface=CARD,name=Headphone Jack')]:
        answer = command(['/usr/bin/amixer', '-c', '0', 'cget', control], capture=True)
        result[key] = answer.stdout
    result['pcm_hw_params'] = (jail / 'proc/asound/card0/pcm0p/sub0/hw_params').read_text()
    result['monotonic'] = time.monotonic()
    command(['/usr/sbin/alsactl', '-U', '-f', '/tmp/' + label + '.state', 'store'])
    (root / (label + '.state')).write_bytes((jail / 'tmp' / (label + '.state')).read_bytes())
    (root / (label + '.json')).write_text(json.dumps(result, indent=2) + '\n')


def direct(command, enter, env, jail, root):
    # Expand the identical quantized S16 samples into signed S32 with no gain
    # change. This isolates the PCM format from waveform/route differences.
    with wave.open(str(root / 'core-tone.wav'), 'rb') as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (2, 2, 48000)
        samples = struct.iter_unpack('<h', wav.readframes(wav.getnframes()))
        raw = b''.join(struct.pack('<i', value << 16) for (value,) in samples)
    (jail / 'opt/muos/core-tone-s32.raw').write_bytes(raw)
    for label, args in [
        ('A', ['/usr/bin/aplay', '-D', 'hw:0,0', '/opt/muos/core-tone.wav']),
        ('B', ['/usr/bin/aplay', '-D', 'hw:0,0', '-t', 'raw', '-f', 'S32_LE',
               '-r', '48000', '-c', '2', '/opt/muos/core-tone-s32.raw']),
    ]:
        snapshot(command, jail, root, label + '-before')
        print('AUDIO_COMPARE_' + label + '_DIRECT_ALSA', flush=True)
        tone = subprocess.Popen(args, preexec_fn=enter, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            time.sleep(0.8)
            snapshot(command, jail, root, label + '-during')
            output, _ = tone.communicate(timeout=12)
            (root / (label + '-aplay.txt')).write_text(output)
            print(output, flush=True)
            assert tone.returncode == 0, tone.returncode
        finally:
            if tone.poll() is None:
                tone.kill()
                tone.wait()
        snapshot(command, jail, root, label + '-after')
        time.sleep(3)
