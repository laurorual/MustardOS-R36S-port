#!/usr/bin/env python3
"""Bounded native core test; separate timer restores host services and mixer."""
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'session-state.json'
SERVICES = ['emulationstation.service', 'ogage.service', 'fn-menu-watcher.service']
if os.geteuid() or ROOT.parent != Path('/tmp') or not ROOT.name.startswith('muos-r35s-p4-core.'):
    raise SystemExit('Expected sudo in a temporary core session')
os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'


def systemctl(*args, check=True):
    return subprocess.run(['systemctl', *args], check=check, capture_output=True, text=True)


def health():
    assert Path('/sys/firmware/devicetree/base/model').read_bytes().rstrip(b'\0') == b'R36S-V12 2023-08-18 Panel 0'
    assert Path('/proc/sys/kernel/tainted').read_text().strip() == '0'
    options = subprocess.check_output(['findmnt', '-n', '-o', 'OPTIONS', '/'], text=True).strip().split(',')
    assert 'rw' in options and 'ro' not in options
    assert subprocess.check_output(['findmnt', '-n', '-o', 'FSTYPE', '-T', str(ROOT)], text=True).strip() == 'tmpfs'
    log = subprocess.check_output(['dmesg'], text=True)
    bad = [line for line in log.splitlines() if re.search(r'bad page|bad rss|mmc.*error|btrfs.*error|transaction aborted|forced readonly', line, re.I)]
    assert not bad, bad


def restore():
    if not STATE.exists():
        return
    with (ROOT / 'restore.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text())
        pid = state.get('worker_pid')
        try:
            same = Path(f'/proc/{pid}/stat').read_text().split()[21] == state.get('worker_starttime')
        except FileNotFoundError:
            same = False
        if same:
            os.killpg(pid, signal.SIGTERM)
            time.sleep(2)
            try:
                if Path(f'/proc/{pid}/stat').read_text().split()[21] == state.get('worker_starttime'):
                    os.killpg(pid, signal.SIGKILL)
            except FileNotFoundError:
                pass
        if state['mode'] != 'inspect':
            subprocess.run(['alsactl', '-U', '-f', str(ROOT / 'mixer-before.state'), 'restore'], check=True)
            for service in state['active_services']:
                systemctl('start', service)
            # Launcher startup can apply its persisted level after systemctl
            # returns. Reapply and verify the user's actual pre-test snapshot.
            time.sleep(1)
            expected = (ROOT / 'mixer-before.state').read_bytes()
            verified = ROOT / 'mixer-restore-verified.state'
            for attempt in range(6):
                subprocess.run(['alsactl', '-U', '-f', str(ROOT / 'mixer-before.state'), 'restore'], check=True)
                stable = True
                for _ in range(2):
                    time.sleep(0.5)
                    subprocess.run(['alsactl', '-U', '-f', str(verified), 'store'], check=True)
                    stable = stable and verified.read_bytes() == expected
                if stable:
                    break
            else:
                raise RuntimeError('Mixer did not remain equal to its pre-test snapshot after service startup')
            print('MIXER_AND_SERVICES_RESTORED_AND_VERIFIED', flush=True)
        if state.get('brightness'):
            saved = state['brightness']
            path = Path('/sys/class/backlight/backlight/brightness')
            assert saved['path'] == str(path) and saved['maximum'] == 160
            assert 10 <= saved['value'] <= 160
            for attempt in range(6):
                path.write_text(str(saved['value']) + '\n')
                time.sleep(0.3)
                if int(path.read_text()) == saved['value']:
                    break
            else:
                raise RuntimeError('Brightness restore did not match the snapshot')
            (ROOT / 'brightness-after.json').write_text(json.dumps(saved, indent=2)+'\n')
            print('BRIGHTNESS_RESTORED_AND_VERIFIED', flush=True)


if len(sys.argv) == 2 and sys.argv[1] == '--restore':
    restore()
    raise SystemExit(0)
if len(sys.argv) != 2 or sys.argv[1] not in ('inspect', 'audio', 'audio-compare', 'graphics', 'input-smoke', 'input-capture', 'egl-context', 'graphics-r13', 'menu-inspect', 'menu-video', 'menu-audio', 'frontend-inspect', 'frontend-video', 'frontend-audio', 'init-lifecycle', 'init-video', 'init-audio'):
    raise SystemExit('Unknown session mode')
mode = sys.argv[1]
audio = mode in ('audio', 'audio-compare', 'menu-audio', 'frontend-audio', 'init-audio')
exclusive = mode != 'inspect'
health()
active = [s for s in SERVICES if systemctl('is-active', s, check=False).returncode == 0]
if audio:
    jack = subprocess.check_output(['amixer', '-c', '0', 'cget', "iface=CARD,name=Headphone Jack"], text=True)
    assert ': values=off' in jack, 'Speaker test requires headphones unplugged'
if exclusive:
    subprocess.run(['alsactl', '-U', '-f', str(ROOT / 'mixer-before.state'), 'store'], check=True)
state = {'mode': mode, 'active_services': active, 'mount_namespace': os.readlink('/proc/self/ns/mnt')}
if mode.startswith(('frontend-', 'init-')):
    brightness = Path('/sys/class/backlight/backlight/brightness')
    maximum = int(brightness.with_name('max_brightness').read_text())
    value = int(brightness.read_text())
    assert maximum == 160 and 10 <= value <= maximum
    state['brightness'] = {'path':str(brightness), 'value':value, 'maximum':maximum}
    (ROOT / 'brightness-before.json').write_text(json.dumps(state['brightness'],indent=2)+'\n')
STATE.write_text(json.dumps(state))
unit = 'muos-r35s-p4-core-restore-' + str(os.getpid())
if exclusive:
    restore_delay = '200s' if mode.startswith(('frontend-', 'init-')) else '150s'
    subprocess.run(['systemd-run', '--quiet', '--unit=' + unit, '--on-active=' + restore_delay,
                    '/usr/bin/python3', str(Path(__file__).resolve()), '--restore'], check=True)


def interrupted(signum, frame):
    raise SystemExit(128 + signum)


for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
    signal.signal(sig, interrupted)
child = None
try:
    if exclusive and active:
        systemctl('stop', *active)
        subprocess.run(['alsactl', '-U', '-f', str(ROOT / 'mixer-before.state'), 'restore'], check=True)
    # util-linux --kill-child now requires pidfd_open, absent in Linux 4.4.
    # Both processes share the supervised process group; namespace PID1 exiting
    # kills its remaining descendants. The independent restore timer also
    # terminates this group if the SSH supervisor disappears.
    child = subprocess.Popen(['unshare', '--mount', '--pid', '--fork', '--net', '--ipc', '--uts',
                              '/usr/bin/python3', str(ROOT / 'phase4-core-namespace.py'), mode],
                             start_new_session=True)
    state.update(worker_pid=child.pid, worker_starttime=Path(f'/proc/{child.pid}/stat').read_text().split()[21])
    STATE.write_text(json.dumps(state))
    result = child.wait(timeout=160 if mode.startswith(('frontend-', 'init-')) else 110)
    print('PHASE4_CORE_WORKER_EXIT_STATUS=' + str(result), flush=True)
    if result:
        raise SystemExit(result)
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    restore()
    if exclusive:
        systemctl('stop', unit + '.timer', check=False)
        systemctl('reset-failed', unit + '.service', check=False)
    health()
