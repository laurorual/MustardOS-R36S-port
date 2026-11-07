#!/usr/bin/env python3
"""Bounded Phase 3 session; reuse the framebuffer/service restoration from Phase 2."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
if os.geteuid() or ROOT.parent != Path('/tmp') or not ROOT.name.startswith('muos-r35s-phase3.'):
    raise SystemExit('Expected sudo in the temporary Phase 3 directory')
spec = importlib.util.spec_from_file_location('phase2_restore', ROOT / 'phase2-device-session.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def bench_health():
    roots = [line.split() for line in Path('/proc/mounts').read_text().splitlines() if line.split()[1] == '/']
    if len(roots) != 1 or 'ro' in roots[0][3].split(','):
        raise SystemExit('Refusing tests: root filesystem is read-only; preserve storage before recovery')
    kernel = subprocess.check_output(['dmesg'], text=True)
    problems = [line for line in kernel.splitlines() if any(marker in line for marker in
                ('BUG: Bad page map', 'BUG: Bad rss-counter', 'forced readonly', 'Transaction aborted'))
                or re.search(r'mmcblk0: error -\d+', line)]
    if problems:
        raise SystemExit('Refusing tests: kernel/MMC errors in this boot:\n' + '\n'.join(problems[-12:]))

def restore():
    state_path = ROOT / 'session-state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text())
        pid = state.get('worker_pid')
        proc = Path('/proc') / str(pid)
        try:
            same = (proc / 'stat').read_text().split()[21] == state.get('worker_starttime')
        except FileNotFoundError:
            same = False
        if same:
            os.killpg(pid, signal.SIGTERM)
            time.sleep(1)
            try: os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError: pass
    core.restore()
    if state_path.exists():
        volume = json.loads(state_path.read_text()).get('playback_volume')
        if volume is not None:
            subprocess.run(['amixer','-c','0','cset','name=Playback Volume',','.join(map(str,volume))],check=True,stdout=subprocess.DEVNULL)
            print('playback_volume_restored='+repr(volume),flush=True)

def interrupted(sig, frame):
    raise SystemExit(128 + sig)

if len(sys.argv) == 2 and sys.argv[1] == '--restore':
    restore()
    raise SystemExit(0)
if len(sys.argv) != 2 or sys.argv[1] not in ('inspect', 'menu', 'audio'):
    raise SystemExit('Expected inspect, menu or audio')
model = Path('/sys/firmware/devicetree/base/model').read_bytes().rstrip(b'\0').decode()
if model != 'R36S-V12 2023-08-18 Panel 0': raise SystemExit('Unexpected target model')
bench_health()
control = subprocess.check_output(['amixer','-c','0','cget','name=Playback Volume'],text=True)
match = re.search(r'^\s*: values=(\d+),(\d+)$',control,re.MULTILINE)
if not match: raise SystemExit('Cannot save Playback Volume before testing')
volume = [int(value) for value in match.groups()]
active = [unit for unit in core.SERVICES if core.systemctl('is-active', unit, check=False).returncode == 0]
with open('/dev/fb0', 'rb', buffering=0) as fb:
    var, fix = bytearray(160), bytearray(80)
    fcntl.ioctl(fb, 0x4600, var)
    fcntl.ioctl(fb, 0x4602, fix)
    size = struct.unpack_from('I', fix, 24)[0]
    if not 640*480*2 <= size <= 16*1024*1024: raise SystemExit('Unexpected fb memory')
    image = os.pread(fb.fileno(), size, 0)
    if len(image) != size: raise SystemExit('Cannot save framebuffer')
    (ROOT / 'fb-before.bin').write_bytes(image)
state = {'active_services': active, 'fb_var': var.hex(), 'mount_namespace': os.readlink('/proc/self/ns/mnt'), 'playback_volume':volume}
(ROOT / 'session-state.json').write_text(json.dumps(state))
unit = 'muos-r35s-restore-p3-' + str(os.getpid())
subprocess.run(['systemd-run','--quiet','--unit='+unit,'--on-active=210s','/usr/bin/python3',str(Path(__file__).resolve()),'--restore'],check=True)
for sig in [signal.SIGHUP, signal.SIGINT, signal.SIGTERM]: signal.signal(sig, interrupted)
child = None
try:
    if active: core.systemctl('stop', *active)
    subprocess.run(['amixer','-c','0','cset','name=Playback Volume',','.join(map(str,volume))],check=True,stdout=subprocess.DEVNULL)
    print('playback_volume_before_child='+repr(volume),flush=True)
    child = subprocess.Popen(['systemd-inhibit','--what=handle-power-key:handle-suspend-key','--mode=block',
                              '--who=muOS Phase 3','--why=Temporary native menu test',
                              'unshare','--mount','--fork','/usr/bin/python3',str(ROOT/'phase3-namespace.py'),sys.argv[1]], start_new_session=True)
    state.update(worker_pid=child.pid, worker_starttime=(Path('/proc')/str(child.pid)/'stat').read_text().split()[21])
    (ROOT / 'session-state.json').write_text(json.dumps(state))
    status = child.wait(timeout=170)
    print('PHASE3_SESSION_EXIT_STATUS=' + str(status), flush=True)
    if status: raise SystemExit(status)
    bench_health()
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    restore()
    core.systemctl('stop',unit+'.timer',check=False)
    core.systemctl('reset-failed',unit+'.service',check=False)
