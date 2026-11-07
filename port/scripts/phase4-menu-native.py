#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Discover the new SDL mapping and run only the bounded native menu."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import time


def menu(command, env, jail, root, mode, enter):
    env.update(SDL_JOYSTICK_HIDAPI='0', SDL_VIDEODRIVER='KMSDRM',
               SDL_VIDEO_EGL_DRIVER='libEGL.so', SDL_VIDEO_GL_DRIVER='libGLESv2.so',
               LD_BIND_NOW='1', LC_ALL='C.UTF-8')
    result = command(['/opt/muos/frontend/phase4-menu', '--inspect-input'], capture=True)
    (root / 'sdl-input.txt').write_text(result.stdout)
    match = re.search(r'SDL_JOYSTICK name=muOS-Keys guid=([0-9a-f]{32}) buttons=15 axes=4 hats=1', result.stdout)
    assert match, 'Unexpected descriptor in the new SDL build'
    entries = [p for p in Path('/sys/class/input').glob('js*/device/id/product') if p.read_text().strip() == '3504']
    assert len(entries) == 1
    entry = entries[0].parents[2]
    major, minor = map(int, (entry / 'dev').read_text().split(':'))
    node = jail / 'dev/input' / entry.name
    if not node.exists():
        os.mknod(node, stat.S_IFCHR | 0o600, os.makedev(major, minor))
    button_map, count = bytearray(1024), bytearray(1)
    with node.open('rb', buffering=0) as joystick:
        fcntl.ioctl(joystick, 0x80016a12, count)
        fcntl.ioctl(joystick, 0x84006a34, button_map)
    codes = list(struct.unpack('@512H', button_map)[:count[0]])
    expected = {'a':305,'b':304,'x':307,'y':308,'leftshoulder':310,'rightshoulder':311,
                'lefttrigger':312,'righttrigger':313,'back':314,'start':315,'guide':316,
                'leftstick':317,'rightstick':318,'volumedown':114,'volumeup':115}
    assert len(codes) == 13 and set(codes) == {c for c in expected.values() if c >= 256}
    # SDL's Linux evdev backend appends KEY_VOLUME* after the BTN_* indices;
    # the interactive test must check these two independently as before.
    codes += [114, 115]
    mapping = match[1] + ',muOS-Keys,' + ','.join(f'{name}:b{codes.index(code)}' for name,code in expected.items())
    mapping += ',leftx:a0,lefty:a1,rightx:a2,righty:a3,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,platform:Linux,'
    command(['/opt/muos/frontend/muvarctl', 'set', 'device', 'board/sdl_map', mapping])
    stored = command(['/opt/muos/frontend/muvarctl', 'get', 'device', 'board/sdl_map'], capture=True)
    assert stored.stdout == mapping
    (root / 'sdl-mapping.json').write_text(json.dumps({'guid':match[1], 'joydev_codes':codes, 'mapping':mapping}, indent=2)+'\n')
    if mode == 'menu-inspect':
        return
    egl = command(['/opt/port-probes/egl-context'], capture=True)
    (root / 'egl-before-menu.txt').write_text(egl.stdout)
    args = ['/opt/muos/frontend/phase4-menu']
    if mode == 'menu-audio':
        # The codec is untouched. Private software gain is unity for this test.
        command(['/usr/bin/wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', '1.0'])
        command(['/usr/bin/wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture=True)
        env['SDL_AUDIODRIVER'] = 'pipewire'
        sounds = jail / 'opt/muos/share/theme/MustardOS/sound'
        confirm = (sounds / 'confirm.wav').read_bytes()
        replacements = {}
        for name in ('info_open.wav', 'info_close.wav'):
            path = sounds / name
            replacements[name] = {'original_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'diagnostic_sha256': hashlib.sha256(confirm).hexdigest()}
            path.write_bytes(confirm)
        (root / 'diagnostic-help-waves.json').write_text(json.dumps(replacements, indent=2)+'\n')
        args.append('--audio')
    print('PHASE4_MENU_SESSION_READY=' + mode, flush=True)
    path = root / 'menu-native.txt'
    with path.open('w') as output:
        child = subprocess.Popen(args, preexec_fn=enter, env=env, stdout=output, stderr=subprocess.STDOUT)
        started, sampled = time.monotonic(), False
        try:
            while child.poll() is None:
                assert time.monotonic() - started < 100, 'Menu timed out'
                if mode == 'menu-audio' and not sampled and time.monotonic() - started > 4:
                    evidence = {}
                    for name,control in [('playback','name=Playback Volume'),('route','name=Playback Path')]:
                        result = command(['/usr/bin/amixer','-c','0','cget',control], capture=True)
                        evidence[name] = result.stdout
                    evidence['hw_params'] = (jail / 'proc/asound/card0/pcm0p/sub0/hw_params').read_text()
                    (root / 'audio-during-menu.json').write_text(json.dumps(evidence,indent=2)+'\n')
                    graph = command(['/usr/bin/pw-dump'], capture=True)
                    (root / 'pw-dump-menu.json').write_text(graph.stdout)
                    sampled = True
                time.sleep(0.1)
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait()
    text = path.read_text()
    print(text, flush=True)
    assert child.returncode == 0, 'Menu returned ' + str(child.returncode)
    assert 'PHASE4_MENU_END status=0 selected=1' in text, 'Menu ended without a selection'
