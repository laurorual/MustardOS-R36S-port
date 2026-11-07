#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise installed lifecycle services in a private mount/PID namespace."""
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import time

S96 = '/etc/init.d/S96muos-input-ready'
S99 = '/etc/init.d/S99muos-ui'


def storage_start(command, jail, root):
    assert (jail / 'etc/muos-private-foundation').is_file()
    assert not any((jail / 'dev').glob('mmcblk*'))
    (jail / 'etc/default/muos-storage').write_text('fstype=tmpfs\n')
    command(['/bin/mount', '-t', 'tmpfs', '-o', 'nosuid,nodev,size=16m', 'tmpfs', '/userdata'])
    command(['/etc/init.d/S90muos-storage', 'start'])


def cleanup(command, jail, root):
    command([S99, 'stop'], check=False, capture=True)
    command([S96, 'stop'], check=False, capture=True)
    command(['/etc/init.d/S90muos-storage', 'stop'], capture=True)
    command(['/bin/umount', '/userdata'])
    (root / 'init-storage-cleanup.txt').write_text('UI -> mapping -> core -> storage stopped\n')


def reap():
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if not pid:
            break


def live(jail, pid):
    path = jail / f'proc/{pid}/stat'
    try:
        return path.read_text().rsplit(')', 1)[1].split()[0] != 'Z'
    except FileNotFoundError:
        return False


def bridge(jail):
    # This replaces only devtmpfs/udev node publication in the private /dev.
    # It does not create a controller or inject input events.
    nodes = []
    for pattern in ['event*/device/name', 'js*/device/name']:
        for p in Path('/sys/class/input').glob(pattern):
            if p.read_text().strip() != 'muOS-Keys':
                continue
            ids = p.parent / 'id'
            assert (ids / 'vendor').read_text().strip() == '756d'
            assert (ids / 'product').read_text().strip() == '3504'
            entry = p.parents[1]
            major, minor = map(int, (entry / 'dev').read_text().split(':'))
            target = jail / 'dev/input' / entry.name
            if not target.exists():
                os.mknod(target, stat.S_IFCHR | 0o600, os.makedev(major, minor))
            nodes.append(str(target.relative_to(jail)))
    assert len(nodes) == 2, nodes
    return nodes


def config(jail, enabled=1, hotkeys=1, attempts=60):
    (jail / 'etc/default/muos-ui').write_text(f'enabled={enabled}\nhotkeys={hotkeys}\nattempts={attempts}\n')


def readiness(command, env, jail, root, enter, failures):
    checks = []
    if failures:
        config(jail, enabled=0)
        command([S99, 'start'])
        assert command([S99, 'status'], check=False).returncode == 3
        checks.append('disabled autostart does not start UI')
        config(jail)
        ready = jail / 'run/muos/core/ready'
        ready.rename(ready.with_name('ready.saved'))
        try:
            assert command([S96, 'start'], check=False, capture=True).returncode != 0
            assert command([S99, 'start'], check=False, capture=True).returncode != 0
        finally:
            ready.with_name('ready.saved').rename(ready)
        checks.append('UI/mapping reject missing core readiness')
        config(jail, attempts=3)
        assert command([S96, 'start'], check=False, capture=True).returncode != 0
        assert not (jail / 'run/muos/input-ready/ready').exists()
        checks.append('missing device nodes time out without ready marker')
    config(jail)
    if failures:
        # Start waiting before publishing the virtual nodes, as udev would.
        (jail / 'run/muos/input-ready/attempts').unlink(missing_ok=True)
        wait_log = (root / 'mapping-wait.log').open('w')
        child = subprocess.Popen([S96, 'start'], preexec_fn=enter, env=env,
                                 stdout=wait_log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 5
            attempts = jail / 'run/muos/input-ready/attempts'
            while time.monotonic() < deadline:
                if attempts.exists() and int(attempts.read_text() or '0') >= 2:
                    break
                time.sleep(.05)
            assert child.poll() is None and not (jail / 'run/muos/input-ready/ready').exists()
            nodes = bridge(jail)
            assert child.wait(timeout=15) == 0
        finally:
            if child.poll() is None:
                child.terminate(); child.wait(timeout=4)
            wait_log.close()
    else:
        nodes = bridge(jail)
        command([S96, 'start'], capture=True)
    command([S96, 'start'])
    command([S96, 'status'])
    mapping = command(['/opt/muos/frontend/muvarctl','get','device','board/sdl_map'],capture=True).stdout
    assert 'volumedown:b13,volumeup:b14' in mapping
    (root / 'init-readiness.json').write_text(json.dumps({'passed':True,'nodes':nodes,
        'checks':checks,'mapping':mapping,'mapping_attempts':(jail/'run/muos/input-ready/attempts').read_text().strip(),
        'scope':'real muinput and SDL; node publication replaces udev in private /dev'},indent=2)+'\n')


def fixture_pids(jail):
    found = []
    for p in (jail / 'run/muos/ui').glob('fixture-*'):
        if p.name == 'fixture-exit':
            continue
        found.extend(int(s) for s in p.read_text().split())
    return found


def stopped(command, jail, pids):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        reap()
        manager = jail/'run/muos/ui/manager'
        identity = manager.read_text().split() if manager.exists() else []
        manager_live = bool(identity) and live(jail,int(identity[0]))
        if not manager_live and not any(live(jail, p) for p in pids):
            break
        time.sleep(.1)
    assert not any(live(jail, p) for p in pids), pids
    assert command([S99, 'status'], check=False).returncode == 3


def exercise(command, env, jail, root, mode, enter):
    lifecycle = mode == 'init-lifecycle'
    readiness(command, env, jail, root, enter, lifecycle)
    if not lifecycle:
        return visual(command, env, jail, root, mode)
    frontend = jail / 'opt/muos/frontend/muxfrontend'
    hotkey = jail / 'opt/muos/frontend/muhotkey'
    originals = {p:p.read_bytes() for p in (frontend,hotkey)}
    fixture = (jail / 'opt/port-probes/service-child').read_bytes()
    checks = []
    try:
        for p in originals:
            p.write_bytes(fixture)
        command([S99,'start'],capture=True)
        first = (jail/'run/muos/ui/manager').read_text()
        command([S99,'start'])
        assert (jail/'run/muos/ui/manager').read_text() == first
        pids = fixture_pids(jail)
        assert len(pids) == 4 and all(live(jail,p) for p in pids)
        manager_pid = int(first.split()[0])
        manager_sid = (jail/f'proc/{manager_pid}/stat').read_text().rsplit(')',1)[1].split()[3]
        detached = [pid for pid in pids if (jail/f'proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[3] != manager_sid]
        assert len(detached) == 2, 'Expected two double-fork helpers in distinct sessions'
        assert all((jail/f'proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[1] == str(manager_pid) for pid in detached)
        command([S99,'stop'])
        command([S99,'stop'])
        stopped(command,jail,pids)
        checks.append('idempotent start/stop; TERM-resistant setsid/double-fork helpers removed by subreaper ownership')
        trigger = jail/'run/muos/ui/fixture-exit'
        trigger.touch()
        assert command([S99,'start'],check=False,capture=True).returncode != 0
        assert (jail/'run/muos/ui/failed').read_text().strip() == 'child_exited'
        trigger.unlink()
        checks.append('early child exit prevents ready and records failure')
        no_paint = jail/'run/muos/ui/fixture-no-paint'
        no_paint.touch()
        (jail/'run/muos/first_paint').write_text('stale paint must not qualify\n')
        assert command([S99,'start'],check=False,capture=True).returncode != 0
        assert (jail/'run/muos/ui/failed').read_text().strip() == 'first_paint_timeout'
        assert not (jail/'run/muos/ui/ready').exists()
        no_paint.unlink()
        checks.append('stale first_paint removed; live process without fresh frame fails before deadline')
        command([S99,'start'])
        pids = fixture_pids(jail)
        # Read the actual frontend PID from the manager's latest CHILD record.
        log = (jail/'run/muos/ui/supervisor.log').read_text().splitlines()
        victim = int(next(l for l in reversed(log) if l.startswith('CHILD frontend ')).split()[-1])
        os.kill(victim,signal.SIGKILL)
        stopped(command,jail,pids)
        assert (jail/'run/muos/ui/failed').read_text().strip() == 'child_exited'
        checks.append('unexpected frontend death stops sibling and descendants; no restart loop')
        command([S99,'start'])
        pids = fixture_pids(jail)
        input_pid = int((jail/'run/muos/core/input.pid').read_text())
        os.kill(input_pid,signal.SIGTERM)
        stopped(command,jail,pids)
        assert (jail/'run/muos/ui/failed').read_text().strip() == 'input_or_core_lost'
        assert command([S96,'status'],check=False).returncode != 0
        command([S96,'stop'])
        checks.append('loss of actual muinput stops UI and invalidates mapping readiness')
        (root/'init-lifecycle-result.json').write_text(json.dumps({'passed':True,'checks':checks,
            'ui_executable_replaced_only_in_fixture':True,'real_frontend_display_tested':False},indent=2)+'\n')
        print('PHASE4_INIT_LIFECYCLE_PASSED',flush=True)
    finally:
        command([S99,'stop'],check=False,capture=True)
        for p,data in originals.items():
            temp = p.with_name(p.name+'.restore')
            temp.write_bytes(data); temp.chmod(0o755); temp.replace(p)
        log = jail/'run/muos/ui/supervisor.log'
        if log.exists(): (root/'init-supervisor.log').write_bytes(log.read_bytes())


def visual(command, env, jail, root, mode):
    variables = [('system','debug_mode','2'),
                 ('global','settings/general/sound','2' if mode=='init-audio' else '0'),
                 ('global','settings/general/brightness',(jail/'sys/class/backlight/backlight/brightness').read_text().strip())]
    for ns,key,value in variables:
        command(['/opt/muos/frontend/muvarctl','set',ns,key,value])
    if mode=='init-audio':
        command(['/usr/bin/wpctl','set-volume','@DEFAULT_AUDIO_SINK@','1.0'])
        command(['/opt/muos/frontend/muvarctl','set','global','settings/general/volume','100'])
    config(jail,hotkeys=1 if mode=='init-audio' else 0)
    command([S99,'start'],capture=True)
    started=time.monotonic()
    log=jail/'run/muos/ui/supervisor.log'
    text=log.read_text()
    frontend_pid=int(next(l for l in reversed(text.splitlines()) if l.startswith('CHILD frontend ')).split()[-1])
    manager=int((jail/'run/muos/ui/manager').read_text().split()[0])
    assert int((jail/f'proc/{frontend_pid}/stat').read_text().rsplit(')',1)[1].split()[1])==manager
    paint=(jail/'run/muos/first_paint').read_text()
    assert paint.strip()
    (root/'init-ui-ready').write_text(mode+'\n')
    print('PHASE4_INIT_UI_READY='+mode,flush=True)
    transitions=[]
    controls=[]
    previous=None
    previous_controls=None
    reason='time_limit'
    try:
        while time.monotonic()-started<100:
            assert (jail/'run/muos/ui/ready').exists() and live(jail,manager),'Lost UI service'
            now=(jail/f'proc/{frontend_pid}/comm').read_text().strip()
            elapsed=round(time.monotonic()-started,3)
            if now!=previous:
                transitions.append({'elapsed':elapsed,'module':now});previous=now
                (root/'init-ui-transitions.json').write_text(json.dumps(transitions,indent=2)+'\n')
            sample={'brightness':(jail/'sys/class/backlight/backlight/brightness').read_text().strip(),
                    'volume':(jail/'opt/muos/config/settings/general/volume').read_text().strip()}
            if sample!=previous_controls:
                controls.append({'elapsed':elapsed,**sample});previous_controls=sample
            if mode=='init-audio' and not (root/'init-audio-during.json').exists() and elapsed>3:
                volume=command(['/usr/bin/amixer','-c','0','cget','name=Playback Volume'],capture=True).stdout
                params=(jail/'proc/asound/card0/pcm0p/sub0/hw_params').read_text()
                (root/'init-audio-during.json').write_text(json.dumps({'codec_volume':volume,'pcm':params},indent=2)+'\n')
            if (root/'init-stop.request').exists():
                reason='stop_request';break
            time.sleep(.1)
    finally:
        command([S99,'stop'],capture=True)
        command([S99,'stop'])
        assert command([S99,'status'],check=False).returncode==3
        (root/'init-supervisor.log').write_bytes(log.read_bytes())
        (root/'init-controls.json').write_text(json.dumps(controls,indent=2)+'\n')
    assert not live(jail,frontend_pid) and not live(jail,manager)
    assert not (jail/'run/muos/ui/failed').exists()
    (root/'init-ui-result.json').write_text(json.dumps({'passed':True,'mode':mode,'duration_seconds':round(time.monotonic()-started,3),
        'stop_reason':reason,'manager_pid':manager,'frontend_pid':frontend_pid,'first_paint':paint,
        'modules_observed':list(dict.fromkeys(t['module'] for t in transitions)),
        'stopped_via_installed_service':True,'firmware_boot_tested':False,'original_help_waves':True},indent=2)+'\n')
    print('PHASE4_INIT_UI_STOP_PASSED',flush=True)
