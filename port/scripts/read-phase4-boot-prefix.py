#!/usr/bin/env python3
"""Read only the pre-partition boot area of the identified test card to stdout."""
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

assert os.geteuid() == 0, 'sudo required for read-only block access'
assert Path('/sys/firmware/devicetree/base/model').read_bytes().rstrip(b'\0') == b'R36S-V12 2023-08-18 Panel 0'
assert Path('/proc/sys/kernel/tainted').read_text().strip() == '0'
root = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
assert root == '/dev/mmcblk0p2', root
length = 16 * 1024 * 1024
start = int(Path('/sys/block/mmcblk0/mmcblk0p1/start').read_text()) * 512
assert start >= length, 'Refusing to include the boot filesystem'
log = subprocess.check_output(['dmesg'], text=True)
assert not re.search(r'bad page|bad rss|mmc.*error|btrfs.*error|transaction aborted|forced readonly', log, re.I)
assert stat.S_ISBLK(os.stat('/dev/mmcblk0').st_mode)
fd = os.open('/dev/mmcblk0', os.O_RDONLY | os.O_CLOEXEC)
try:
    for offset in range(0, length, 1024 * 1024):
        data = os.pread(fd, 1024 * 1024, offset)
        assert len(data) == 1024 * 1024, 'Short read'
        sys.stdout.buffer.write(data)
finally:
    os.close(fd)
print('Read-only boot prefix: 16777216 bytes; no block writes', file=sys.stderr)
