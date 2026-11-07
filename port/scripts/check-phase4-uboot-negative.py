#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tamper temporary copies only, to verify the host audit gates fail closed."""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import struct
import tempfile

repo = Path(__file__).resolve().parents[2]
stage = Path((repo/'build/phase4/uboot-sd/latest-build').read_text().strip())
verify = runpy.run_path(str(repo/'port/scripts/verify-phase4-uboot-sd.py'))['verify']
record = json.loads((stage/'inputs.json').read_text())
results = {}
for name in ['compiled-devnum', 'panic-reset', 'weak-memory-hook']:
    test = Path(tempfile.mkdtemp(prefix='negative-uboot.', dir=stage))
    for p in ['inputs.json', 'build.exit']:
        shutil.copy2(stage/p, test/p)
    for p in record['source_files']:
        dest = test/'source'/p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage/'source'/p, dest)
    (test/'output').mkdir()
    for p in ['.config', 'u-boot.cfg', 'u-boot']:
        shutil.copy2(stage/'output'/p, test/'output'/p)
    if name == 'panic-reset':
        p = test/'output/.config'
        p.write_text(p.read_text().replace('CONFIG_PANIC_HANG=y', '# CONFIG_PANIC_HANG is not set'))
    else:
        p = test/'output/u-boot'
        raw = bytearray(p.read_bytes())
        if name == 'compiled-devnum':
            assert raw.count(b'devnum=1\0') == 1
            raw = raw.replace(b'devnum=1\0', b'devnum=0\0')
        else:
            shoff = struct.unpack_from('<Q', raw, 40)[0]
            shsize, shnum = struct.unpack_from('<HH', raw, 58)
            sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff+i*shsize) for i in range(shnum)]
            changed = 0
            for section in sections:
                if section[1] != 2:
                    continue
                strings = sections[section[6]]
                names = raw[strings[4]:strings[4]+strings[5]]
                for offset in range(section[4], section[4]+section[5], 24):
                    index = struct.unpack_from('<I', raw, offset)[0]
                    if names[index:].split(b'\0', 1)[0] == b'board_sysmem_reserve':
                        raw[offset+4] = (2 << 4) | (raw[offset+4] & 15)
                        changed += 1
            assert changed == 1
        p.write_bytes(raw)
    try:
        verify(test)
    except (AssertionError, KeyError) as error:
        results[name] = 'rejected ('+type(error).__name__+')'
    else:
        raise AssertionError(name+' accepted')
(stage/'negative-checks.json').write_text(json.dumps(results, indent=2)+'\n')

package = Path((stage/'latest-package').read_text().strip())
package_verify = runpy.run_path(str(repo/'port/scripts/verify-phase4-boot-package.py'))['verify']
package_report = package_verify(package)
(package/'audit.json').write_text(json.dumps(package_report, indent=2)+'\n')
results = {}
for name, filename, field, stride in [('uboot-crc', 'uboot.img', 24, 1024*1024),
                                      ('trust-component-hash', 'trust.img', 800, 2*1024*1024)]:
    test = Path(tempfile.mkdtemp(prefix='negative-package.', dir=stage))
    for p in package.iterdir():
        if p.name == 'audit.json':
            continue
        if p.is_dir():
            shutil.copytree(p, test/p.name)
        else:
            shutil.copy2(p, test/p.name)
    raw = bytearray((test/filename).read_bytes())
    for offset in range(field, len(raw), stride):
        raw[offset] ^= 1
    (test/filename).write_bytes(raw)
    manifest = json.loads((test/'manifest.json').read_text())
    manifest['outputs_sha256'][filename] = hashlib.sha256(raw).hexdigest()
    (test/'manifest.json').write_text(json.dumps(manifest))
    try:
        package_verify(test)
    except AssertionError:
        results[name] = 'rejected despite updated outer file checksum'
    else:
        raise AssertionError(name+' accepted')
(stage/'package-negative-checks.json').write_text(json.dumps(results, indent=2)+'\n')
print('Negative compiled-environment, panic, memory-hook and container checks passed')
