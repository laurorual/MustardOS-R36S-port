#!/usr/bin/env python3
"""Inspect/capture the controller made by the new rootfs; never inject keys."""
import errno
import fcntl
import json
import os
from pathlib import Path
import selectors
import stat
import struct
import time

# Linux input.h ABI: _IOW('E', 0x90, int), _IOR('E', 0x02, struct input_id).
EVIOCGRAB = 0x40044590
EVIOCGID = 0x80084502
EVENT = struct.Struct('@llHHi')


def grabbed(path, expected):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        try:
            fcntl.ioctl(fd, EVIOCGRAB, 1)
        except OSError as exc:
            if exc.errno != errno.EBUSY:
                raise
            assert expected, 'Physical source is still grabbed after stop'
            return
        fcntl.ioctl(fd, EVIOCGRAB, 0)
        assert not expected, 'Physical source was not grabbed by muinput'
    finally:
        os.close(fd)


def capture(command, jail, root, seconds):
    deadline = time.monotonic() + 8
    node = None
    while time.monotonic() < deadline:
        for name in Path('/sys/class/input').glob('event*/device/name'):
            if name.read_text().strip() != 'muOS-Keys':
                continue
            identity = name.parent / 'id'
            if (identity / 'product').read_text().strip() != '3504':
                continue
            major, minor = map(int, (name.parents[1] / 'dev').read_text().split(':'))
            node = jail / 'dev/input' / name.parents[1].name
            if not node.exists():
                os.mknod(node, stat.S_IFCHR | 0o600, os.makedev(major, minor))
            break
        if node and (jail / 'dev/muinput/rk-r35s-p0-source').exists():
            break
        time.sleep(0.05)
    assert node and (jail / 'dev/muinput/rk-r35s-p0-source').exists(), 'No matching virtual pad and isolated source'
    grabbed(jail / 'dev/muinput/rk-r35s-p0-source', True)
    command(['/lib/ld-linux-aarch64.so.1', '--list', '/opt/muos/frontend/muinput'], capture=True)
    fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK)
    selector = selectors.DefaultSelector()
    try:
        identity = bytearray(8)
        fcntl.ioctl(fd, EVIOCGID, identity)
        actual = struct.unpack('@4H', identity)
        assert actual == (0x06, 0x756d, 0x3504, 0x736f), actual
        record = {'virtual_node': str(node.relative_to(jail)), 'identity': actual,
                  'physical_source_grabbed': True, 'event_size': EVENT.size,
                  'duration_seconds': seconds, 'recorder': 'host Python; muinput uses candidate loader/libraries'}
        (root / 'input-device.json').write_text(json.dumps(record, indent=2) + '\n')
        selector.register(fd, selectors.EVENT_READ)
        print('PHASE4_INPUT_CAPTURE_READY', flush=True)
        started = time.monotonic()
        with (root / 'normalized-events.jsonl').open('w') as output:
            while time.monotonic() - started < seconds:
                assert (jail / 'run/muos/core/input.pid').exists(), 'Lost daemon pidfile'
                for key, _ in selector.select(timeout=0.2):
                    data = os.read(key.fd, EVENT.size * 128)
                    assert len(data) % EVENT.size == 0 and data, 'Unexpected input_event stream'
                    for offset in range(0, len(data), EVENT.size):
                        _, _, kind, code, value = EVENT.unpack_from(data, offset)
                        if kind in (1, 3) or (kind == 0 and code == 3):
                            output.write(json.dumps({'elapsed': round(time.monotonic()-started, 4),
                                                     'type': kind, 'code': code, 'value': value}) + '\n')
                    output.flush()
        print('PHASE4_INPUT_CAPTURE_FINISHED', flush=True)
    finally:
        selector.close()
        os.close(fd)


def released(jail, root):
    # Upstream isolation leaves the source under its private name until this
    # /dev namespace exits. Check that closing the daemon really released it.
    source = jail / 'dev/muinput/rk-r35s-p0-source'
    if not source.exists():
        entry = next(p for p in Path('/sys/class/input').glob('event*/device/name')
                     if p.read_text().strip() == 'GO-Super Gamepad')
        source = jail / 'dev/input' / entry.parents[1].name
    grabbed(source, False)
    (root / 'input-stop.json').write_text(json.dumps({'virtual_pad_removed': True, 'physical_grab_released': True}) + '\n')
    print('PHASE4_INPUT_STOP_AND_RELEASE=OK', flush=True)
