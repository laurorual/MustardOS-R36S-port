#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded native core UI; no alternate dispatcher or injected key events."""
import json
import hashlib
import os
from pathlib import Path
import re
import signal
import shutil
import stat
import subprocess
import time


def storage_start(command, jail, root):
    assert (jail / 'etc/muos-private-foundation').is_file()
    assert not any((jail / 'dev').glob('mmcblk*'))
    (jail / 'etc/default/muos-storage').write_text('fstype=tmpfs\n')
    command(['/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,size=16m', 'tmpfs', '/userdata'])
    command(['/etc/init.d/S90muos-storage', 'start'], capture=True)
    command(['/etc/init.d/S90muos-storage', 'status'], capture=True)


def cleanup(command, jail, root):
    command(['/etc/init.d/S90muos-storage', 'stop'], capture=True)
    command(['/bin/umount', '/userdata'])
    (root / 'frontend-storage-cleanup.txt').write_text('Private storage stopped and tmpfs unmounted\n')


def frontend(command, env, jail, root, mode, enter):
    env.update(SDL_JOYSTICK_HIDAPI='0', SDL_VIDEODRIVER='KMSDRM',
               SDL_VIDEO_EGL_DRIVER='libEGL.so', SDL_VIDEO_GL_DRIVER='libGLESv2.so',
               SDL_AUDIODRIVER='pipewire' if mode == 'frontend-audio' else 'dummy',
               LD_BIND_NOW='1', LD_LIBRARY_PATH='/opt/muos/frontend/lib', LC_ALL='C.UTF-8')
    pads = [p for p in Path('/sys/class/input').glob('js*/device/id/product')
            if p.read_text().strip() == '3504' and (p.parent / 'vendor').read_text().strip() == '756d']
    assert len(pads) == 1
    entry = pads[0].parents[2]
    major, minor = map(int, (entry / 'dev').read_text().split(':'))
    node = jail / 'dev/input' / entry.name
    if not node.exists():
        os.mknod(node, stat.S_IFCHR | 0o600, os.makedev(major, minor))
    result = command(['/opt/port-probes/muos-sdl-map'], capture=True)
    mapping = result.stdout.strip()
    assert re.fullmatch(r'[0-9a-f]{32},muOS-Keys,[^\n]+platform:Linux,', mapping), mapping
    settings = [('device', 'board/sdl_map', mapping),
                ('device', 'storage/rom/mount', '/mnt/mmc'),
                ('device', 'storage/sdcard/mount', '/mnt/sdcard'),
                ('system', 'debug_mode', '2'),
                ('global', 'settings/general/sound', '2' if mode == 'frontend-audio' else '0'),
                ('global', 'settings/advanced/incvolume', '5'),
                ('global', 'settings/advanced/incbright', '5'),
                ('global', 'settings/power/idle_display', '0'),
                ('global', 'settings/power/idle_sleep', '0')]
    for ns, key, value in settings:
        base = {'device':'device/config', 'global':'config', 'system':'config/system'}[ns]
        (jail / 'opt/muos' / base / key).parent.mkdir(parents=True, exist_ok=True)
        command(['/opt/muos/frontend/muvarctl', 'set', ns, key, value])
    stored = command(['/opt/muos/frontend/muvarctl', 'get', 'device', 'board/sdl_map'], capture=True)
    assert stored.stdout == mapping
    (root / 'frontend-sdl-map.txt').write_text(mapping + '\n')
    command(['/bin/mkdir', '-p', '/mnt/mmc/MUOS/log', '/mnt/mmc/ROMS'])
    command(['/opt/muos/script/system/assign.sh', '-p'], capture=True)
    assigns = json.loads((jail / 'run/muos/storage/info/manifest/assign.json').read_text())
    assert len(assigns) > 10
    command(['/opt/port-probes/frontend-contract'], capture=True)
    (root / 'frontend-runtime-inspect.json').write_text(json.dumps({
        'native_mapping_passed': True, 'assign_entries': len(assigns),
        'native_library_group_resolved': True, 'exec_wrappers': False,
        'block_devices_exposed': False, 'fb_device_exposed': False,
    }, indent=2) + '\n')
    if mode == 'frontend-inspect':
        return
    egl = command(['/opt/port-probes/egl-context'], capture=True)
    (root / 'frontend-egl.txt').write_text(egl.stdout)
    if mode == 'frontend-audio':
        sounds = jail / 'opt/muos/share/theme/MustardOS/sound'
        control = (sounds / 'confirm.wav').read_bytes()
        replaced = {}
        for name in ('info_open.wav', 'info_close.wav'):
            p = sounds / name
            replaced[name] = {'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                              'diagnostic_sha256':hashlib.sha256(control).hexdigest()}
            p.write_bytes(control)
        (root / 'diagnostic-help-waves.json').write_text(json.dumps(replaced,indent=2)+'\n')
        command(['/usr/bin/wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', '1.0'])
        # Exercise the real helpers and restore each baseline before input.
        command(['/opt/muos/script/device/audio.sh', 'D'], capture=True)
        volume_down = command(['/opt/muos/script/device/audio.sh', 'I'], capture=True).stdout.strip()
        assert volume_down == '95%', volume_down
        command(['/opt/muos/script/device/audio.sh', 'U'], capture=True)
        assert command(['/opt/muos/script/device/audio.sh', 'I'], capture=True).stdout.strip() == '100%'
        bright = jail / 'sys/class/backlight/backlight/brightness'
        level = int(bright.read_text())
        command(['/opt/muos/frontend/muvarctl', 'set', 'global', 'settings/general/brightness', str(level)])
        command(['/opt/muos/script/device/bright.sh', 'D'], capture=True)
        assert int(bright.read_text()) == level - 5
        command(['/opt/muos/script/device/bright.sh', 'U'], capture=True)
        assert int(bright.read_text()) == level
        (root / 'native-helpers.json').write_text(json.dumps({
            'volume_down_up': [100,95,100], 'brightness_down_up': [level,level-5,level],
            'native_helpers_passed': True, 'codec_level_changed_by_test': False,
        },indent=2)+'\n')
        # Only four reviewed bindings; no Power, idle, suspend or install action.
        hotkeys = jail / 'opt/muos/share/hotkey'
        if hotkeys.exists():
            shutil.rmtree(hotkeys)
        hotkeys.mkdir()
        shutil.copy2(root / 'session-hotkeys.json', hotkeys / 'r35s.json')
    transitions = []
    gui = root / 'frontend-native.txt'
    hotkey = None
    hotkey_output = None
    if mode == 'frontend-audio':
        hotkey_output = (root / 'hotkey-native.txt').open('w')
        hotkey = subprocess.Popen(['/opt/muos/frontend/muhotkey', '-v'], preexec_fn=enter,
                                  env=env, stdout=hotkey_output, stderr=subprocess.STDOUT)
        time.sleep(1)
        assert hotkey.poll() is None, (root / 'hotkey-native.txt').read_text()
    with gui.open('w') as output:
        # muxfrontend treats getppid()==1 as an orphan and raises SIGTERM.
        # Keep a real parent process below namespace PID1, as frontend.sh does.
        launcher = ('/opt/muos/frontend/muxfrontend & fe_pid=$!; '
                    'echo "$fe_pid" > /run/muos/frontend.pid; '
                    'wait "$fe_pid"; fe_status=$?; '
                    'rm -f /run/muos/frontend.pid; exit "$fe_status"')
        child = subprocess.Popen(['/bin/sh', '-c', launcher], preexec_fn=enter,
                                 env=env, stdout=output, stderr=subprocess.STDOUT)
        started = time.monotonic()
        last = None
        reason = 'process_exit'
        ready = False
        frontend_pid = None
        controls = []
        last_controls = None
        try:
            while child.poll() is None:
                elapsed = time.monotonic() - started
                try:
                    frontend_pid = int((jail / 'run/muos/frontend.pid').read_text())
                    module = (jail / f'proc/{frontend_pid}/comm').read_text().strip()
                except (FileNotFoundError, ValueError):
                    module = ''
                if module and module != last:
                    transitions.append({'elapsed': round(elapsed, 3), 'module': module})
                    last = module
                    (root / 'frontend-transitions.json').write_text(json.dumps(transitions, indent=2) + '\n')
                if mode == 'frontend-audio':
                    now_controls = {
                        'brightness': int((jail / 'sys/class/backlight/backlight/brightness').read_text()),
                        'saved_brightness': (jail / 'opt/muos/config/settings/general/brightness').read_text().strip(),
                        'saved_volume': (jail / 'opt/muos/config/settings/general/volume').read_text().strip(),
                    }
                    if now_controls != last_controls:
                        controls.append({'elapsed':round(elapsed,3), **now_controls})
                        last_controls = now_controls
                        (root / 'control-samples.json').write_text(json.dumps(controls,indent=2)+'\n')
                if not ready and module == 'muxlaunch' and elapsed > 2:
                    ready = True
                    (root / 'frontend-ready').write_text(mode + '\n')
                    print('PHASE4_FULL_FRONTEND_READY=' + mode, flush=True)
                limit = 110 if mode == 'frontend-audio' else 75
                if (root / 'frontend-stop.request').exists() or elapsed >= limit:
                    reason = 'stop_request' if elapsed < limit else 'time_limit'
                    if frontend_pid:
                        os.kill(frontend_pid, signal.SIGTERM)
                    break
                time.sleep(0.1)
            child.wait(timeout=5)
        finally:
            if child.poll() is None:
                if frontend_pid:
                    try:
                        os.kill(frontend_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                child.kill(); child.wait()
            if hotkey is not None:
                hotkey.terminate()
                try:
                    hotkey.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    hotkey.kill(); hotkey.wait()
                hotkey_output.close()
    logs = jail / 'opt/muos/log'
    if logs.exists():
        dest = root / 'frontend-logs'
        dest.mkdir(exist_ok=True)
        for p in logs.glob('*.log'):
            (dest / p.name).write_bytes(p.read_bytes())
    (root / 'frontend-result.json').write_text(json.dumps({
        'mode': mode, 'returncode': child.returncode, 'ready_observed': ready,
        'stop_reason': reason, 'duration_seconds': round(time.monotonic()-started, 3),
        'modules_observed': list(dict.fromkeys(t['module'] for t in transitions)),
        'firmware_boot_tested': False, 'audio_enabled': mode == 'frontend-audio',
    }, indent=2) + '\n')
    assert ready and child.returncode == 0, gui.read_text()[-8000:]
    print('PHASE4_FULL_FRONTEND_EXIT_STATUS=0', flush=True)
