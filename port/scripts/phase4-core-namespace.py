#!/usr/bin/env python3
"""Run only the limited core/audio service in private mount/PID/net namespaces."""
import json
import os
from pathlib import Path
import runpy
import signal
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
if os.geteuid() or ROOT.parent != Path('/tmp') or not ROOT.name.startswith('muos-r35s-p4-core.'):
    raise SystemExit('Expected the root-owned worker in its temporary session')
if os.getpid() != 1:
    raise SystemExit('Expected PID 1 of a private PID namespace')
state = json.loads((ROOT / 'session-state.json').read_text())
if os.readlink('/proc/self/ns/mnt') == state['mount_namespace']:
    raise SystemExit('Refusing to mount in the original namespace')
mode = sys.argv[1]
if mode not in ('inspect', 'audio', 'audio-compare', 'graphics', 'input-smoke', 'input-capture', 'egl-context', 'graphics-r13', 'menu-inspect', 'menu-video', 'menu-audio', 'frontend-inspect', 'frontend-video', 'frontend-audio', 'init-lifecycle', 'init-video', 'init-audio'):
    raise SystemExit('Unknown mode')
compare = mode == 'audio-compare'
if compare:
    mode = 'audio'
needs_input = mode.startswith(('input-', 'menu-', 'frontend-', 'init-'))
needs_audio = mode in ('audio', 'menu-audio', 'frontend-audio', 'init-audio')
jail = ROOT / 'rootfs'
if jail.is_symlink() or not (jail / 'etc/init.d/S95muos-core').is_file():
    raise SystemExit('Missing staged rootfs')


def run(*args):
    subprocess.run(args, check=True)


run('mount', '--make-rprivate', '/')
for name in ('dev', 'dev/shm', 'proc', 'sys', 'tmp', 'run', 'run/udev'):
    (jail / name).mkdir(parents=True, exist_ok=True)
run('mount', '-t', 'tmpfs', '-o', 'mode=0755,nosuid', 'tmpfs', str(jail / 'dev'))
(jail / 'dev/shm').mkdir()
run('mount', '-t', 'tmpfs', '-o', 'mode=1777,nosuid,nodev', 'tmpfs', str(jail / 'dev/shm'))
run('mount', '-t', 'proc', '-o', 'ro,nosuid,nodev,noexec', 'proc', str(jail / 'proc'))
run('mount', '--bind', '/sys', str(jail / 'sys'))
run('mount', '-o', 'remount,bind,ro', str(jail / 'sys'))
if mode in ('frontend-audio','init-audio'):
    # Permit only this Panel 0 backlight value. Other sysfs files, including
    # framebuffer blank, clocks and power controls, retain the read-only bind.
    brightness = Path('/sys/class/backlight/backlight/brightness')
    saved = state['brightness']
    assert int(brightness.with_name('max_brightness').read_text()) == saved['maximum'] == 160
    target = jail / str(brightness.resolve()).lstrip('/')
    run('mount', '--bind', str(brightness), str(target))
    run('mount', '-o', 'remount,bind,rw', str(target))
if Path('/run/udev').is_dir():
    run('mount', '--bind', '/run/udev', str(jail / 'run/udev'))
    run('mount', '-o', 'remount,bind,ro', str(jail / 'run/udev'))
nodes = ['/dev/null', '/dev/zero', '/dev/random', '/dev/urandom']
if needs_audio:
    nodes += ['/dev/snd/controlC0', '/dev/snd/pcmC0D0p', '/dev/snd/timer']
if mode in ('graphics', 'egl-context', 'graphics-r13', 'menu-video', 'menu-audio', 'frontend-video', 'frontend-audio', 'init-video', 'init-audio'):
    nodes += ['/dev/dri/card0', '/dev/dri/renderD128', '/dev/mali0']
    assert all(Path(name).exists() for name in nodes), 'Missing required GPU/DRM device'
if needs_input:
    assert Path('/dev/uinput').exists(), 'Missing uinput'
    assert not any(p.read_text().strip() == 'muOS-Keys' for p in Path('/sys/class/input').glob('event*/device/name'))
    nodes += ['/dev/uinput']
    for entry in Path('/sys/class/input').glob('event*/device/name'):
        if entry.read_text().strip() in ('GO-Super Gamepad', 'odroidgo3-keys'):
            nodes.append('/dev/input/' + entry.parents[1].name)
    assert len([n for n in nodes if n.startswith('/dev/input/')]) == 2, 'Expected exactly gamepad and volume keys'
for name in nodes:
    source = Path(name)
    if not source.exists():
        continue
    metadata = source.stat()
    if not stat.S_ISCHR(metadata.st_mode):
        raise RuntimeError('Expected char device: ' + name)
    target = jail / name.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    os.mknod(target, stat.S_IFCHR | 0o660, metadata.st_rdev)
# A private snapshot is restored by native muOS, without maxing the codec gain.
if needs_audio:
    (jail / 'opt/muos/device/control/asound.state').write_bytes((ROOT / 'mixer-before.state').read_bytes())
    if mode == 'audio':
        (jail / 'opt/muos/core-tone.wav').write_bytes((ROOT / 'core-tone.wav').read_bytes())
    # Use the user's existing hardware level; only the private PW stream has
    # its own 35% startup software volume from the board profile.
(jail / 'etc/default/muos-core').write_text('audio=' + ('1' if needs_audio else '0') + '\ninput=' + ('1' if needs_input else '0') + '\n')


def enter():
    os.chroot(jail)
    os.chdir('/')


env = {'PATH': '/opt/muos/bin:/opt/muos/frontend:/usr/sbin:/usr/bin:/sbin:/bin',
       'HOME': '/root', 'LC_ALL': 'C', 'XDG_RUNTIME_DIR': '/run',
       'PIPEWIRE_RUNTIME_DIR': '/run', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/dbus/system_bus_socket'}


def command(args, *, check=True, capture=False, timeout=25):
    result = subprocess.run(args, preexec_fn=enter, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None, timeout=timeout)
    if capture:
        print(result.stdout, flush=True)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} returned {result.returncode}')
    return result


def interrupted(signum, frame):
    raise SystemExit(128 + signum)


for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
    signal.signal(sig, interrupted)
started = False
storage_diagnostic = None
try:
    command(['/lib/ld-linux-aarch64.so.1', '--list', '/opt/muos/frontend/muinput'], capture=True)
    command(['/opt/muos/frontend/muinput', '--list-devices'], capture=True)
    result = command(['/opt/muos/bin/fnv1a', 'abc'], capture=True)
    assert result.stdout == '1a47e90b'
    if compare:
        diagnostic = runpy.run_path(str(ROOT / 'phase4-audio-compare.py'))
        diagnostic['direct'](command, enter, env, jail, ROOT)
    if needs_audio:
        command(['/etc/init.d/S30dbus-daemon', 'start'], capture=True)
    if mode == 'inspect' and (jail / 'etc/muos-private-foundation').is_file():
        storage_diagnostic = runpy.run_path(str(ROOT / 'phase4-storage-native.py'))
        storage_diagnostic['exercise'](command, jail, ROOT)
    if mode.startswith('frontend-'):
        storage_diagnostic = runpy.run_path(str(ROOT / 'phase4-frontend-native.py'))
        storage_diagnostic['storage_start'](command, jail, ROOT)
    if mode.startswith('init-'):
        storage_diagnostic = runpy.run_path(str(ROOT / 'phase4-init-native.py'))
        storage_diagnostic['storage_start'](command, jail, ROOT)
    command(['/etc/init.d/S95muos-core', 'start'], capture=True)
    started = True
    command(['/etc/init.d/S95muos-core', 'start'], capture=True)  # Idempotent start.
    result = command(['/opt/muos/frontend/muvarctl', 'get', 'device', 'board/name'], capture=True)
    assert result.stdout == 'rk-r35s-p0'
    command(['/opt/muos/frontend/muvarctl', 'set', 'global', 'boot/device_mode', '0'])
    command(['/etc/init.d/S95muos-core', 'status'], capture=True)
    if mode == 'graphics':
        diagnostic = runpy.run_path(str(ROOT / 'phase4-graphics-native.py'))
        diagnostic['render'](command, env, ROOT)
    if mode in ('egl-context', 'graphics-r13'):
        diagnostic = runpy.run_path(str(ROOT / 'phase4-r13-native.py'))
        diagnostic['probe'](command, env, ROOT, mode == 'graphics-r13')
    if needs_input:
        input_diagnostic = runpy.run_path(str(ROOT / 'phase4-input-native.py'))
        if not mode.startswith('init-'):
            input_diagnostic['capture'](command, jail, ROOT, 80 if mode == 'input-capture' else 1)
    if mode.startswith('menu-'):
        diagnostic = runpy.run_path(str(ROOT / 'phase4-menu-native.py'))
        diagnostic['menu'](command, env, jail, ROOT, mode, enter)
    if mode.startswith('frontend-'):
        storage_diagnostic['frontend'](command, env, jail, ROOT, mode, enter)
    if mode.startswith('init-'):
        storage_diagnostic['exercise'](command, env, jail, ROOT, mode, enter)
        command(['/etc/init.d/S99muos-ui','stop'])
        command(['/etc/init.d/S96muos-input-ready','stop'])
    if mode == 'audio':
        result = command(['/usr/bin/pw-dump'], capture=True)
        (ROOT / 'pw-dump.json').write_text(result.stdout)
        command(['/usr/bin/wpctl', 'status'], capture=True)
        # Diagnostic control: the board's 35% boot setting maps to only
        # 0.042875 linear gain. Keep hardware gain unchanged and test the same
        # -14 dBFS tone at unity software gain in this private session only.
        command(['/usr/bin/wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', '1.0'])
        command(['/usr/bin/wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture=True)
        (ROOT / 'tone-software-volume.txt').write_text('1.0; diagnostic override; firmware boot setting remains 35%\n')
        if compare:
            diagnostic['snapshot'](command, jail, ROOT, 'C-before')
            print('AUDIO_COMPARE_C_PIPEWIRE', flush=True)
        print('PHASE4_CORE_AUDIO_READY', flush=True)
        # Three bounded beeps; no volume or power-key daemon runs in this test.
        tone = subprocess.Popen(['/usr/bin/aplay', '-D', 'pipewire', '/opt/muos/core-tone.wav'],
                                preexec_fn=enter, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            time.sleep(0.8)
            (ROOT / 'pcm-hw-params.txt').write_text((jail / 'proc/asound/card0/pcm0p/sub0/hw_params').read_text())
            if compare:
                diagnostic['snapshot'](command, jail, ROOT, 'C-during')
            output, _ = tone.communicate(timeout=14)
            print(output, flush=True)
            assert tone.returncode == 0, tone.returncode
        finally:
            if tone.poll() is None:
                tone.kill()
                tone.wait()
        print('PHASE4_CORE_TONE_FINISHED', flush=True)
        if compare:
            diagnostic['snapshot'](command, jail, ROOT, 'C-after')
    command(['/etc/init.d/S95muos-core', 'stop'], capture=True)
    started = False
    if needs_input:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and any(p.read_text().strip() == 'muOS-Keys' for p in Path('/sys/class/input').glob('event*/device/name')):
            time.sleep(0.1)
        assert not any(p.read_text().strip() == 'muOS-Keys' for p in Path('/sys/class/input').glob('event*/device/name'))
        input_diagnostic['released'](jail, ROOT)
    assert command(['/etc/init.d/S95muos-core', 'status'], check=False).returncode == 3
    command(['/etc/init.d/S95muos-core', 'stop'], capture=True)
    if needs_audio:
        result = command(['/bin/pgrep', '-x', 'pipewire|wireplumber'], check=False, capture=True)
        states = {}
        for pid in result.stdout.split():
            status = (jail / 'proc' / pid / 'status').read_text()
            states[pid] = [line for line in status.splitlines() if line.startswith(('Name:', 'State:', 'PPid:'))]
        (ROOT / 'post-stop-processes.json').write_text(json.dumps(states, indent=2) + '\n')
        # This Python worker is namespace PID1, so orphaned service children
        # remain zombies until it reaps them; they are no longer running.
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if not pid:
                break
        result = command(['/bin/pgrep', '-x', 'pipewire|wireplumber'], check=False, capture=True)
        assert result.returncode == 1, result.stdout
    print('PHASE4_CORE_LIFECYCLE_EXIT_STATUS=0', flush=True)
finally:
    if mode.startswith('init-'):
        command(['/etc/init.d/S99muos-ui','stop'],check=False,capture=True)
        command(['/etc/init.d/S96muos-input-ready','stop'],check=False,capture=True)
    if started:
        command(['/etc/init.d/S95muos-core', 'stop'], check=False, capture=True)
    if storage_diagnostic is not None:
        storage_diagnostic['cleanup'](command, jail, ROOT)
    if needs_audio:
        command(['/etc/init.d/S30dbus-daemon', 'stop'], check=False, capture=True)
    logs = jail / 'run/muos/core'
    if logs.is_dir():
        for path in logs.iterdir():
            if path.is_file() and path.suffix in ('.log', '.json', '.txt'):
                (ROOT / path.name).write_bytes(path.read_bytes())
    # Reap exited descendants; exiting namespace PID1 kills anything remaining.
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if not pid:
            break
