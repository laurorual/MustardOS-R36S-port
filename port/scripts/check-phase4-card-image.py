#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise C70 image validation on sparse regular files, never block devices."""
from pathlib import Path
import copy, hashlib, json, os, tempfile
from phase4_candidate import sha
from phase4_card_image import (BOOT_OFFSETS, FAT_BYTES, FAT_OFFSET, IMAGE_BYTES,
                              ROOT_BYTES, ROOT_OFFSET, mbr_bytes, verify_image)

repo = Path(__file__).resolve().parents[2]
area = repo / 'build/phase4/card-image'
area.mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix='checks.', dir=area))
image = stage / 'fixture.img'
with image.open('xb') as stream:
    stream.truncate(IMAGE_BYTES)
    stream.write(mbr_bytes())
def zeros(length):
    digest = hashlib.sha256()
    chunk = b'\0' * (1024 * 1024)
    while length:
        data = chunk[:min(len(chunk), length)]
        digest.update(data)
        length -= len(data)
    return digest.hexdigest()
regions = {name: {'offset': offset, 'bytes': 512, 'sha256': zeros(512)} for name, offset in BOOT_OFFSETS.items()}
regions['boot.fat'] = {'offset': FAT_OFFSET, 'bytes': FAT_BYTES, 'sha256': zeros(FAT_BYTES)}
regions['rootfs.ext4'] = {'offset': ROOT_OFFSET, 'bytes': ROOT_BYTES, 'sha256': zeros(ROOT_BYTES)}
cases = []
def check(name, operation, accepted=False):
    try:
        result = operation()
    except (AssertionError, OSError):
        assert not accepted, name
    else:
        assert accepted and result['passed'], name
    cases.append({'name': name, 'expected': 'accept' if accepted else 'reject', 'passed': True})
check('valid sparse image and atime-only access', lambda: verify_image(image, regions), True)
for name, offset in [('MBR boot code', 0), ('disk signature', 440), ('partition active flag', 446),
                     ('partition start', 454), ('partition size', 458), ('third partition', 478),
                     ('MBR trailer', 510), ('gap before idbloader', 1024),
                     ('gap after idbloader', BOOT_OFFSETS['idbloader.img'] + 512),
                     ('gap before rootfs', FAT_OFFSET + FAT_BYTES)]:
    with image.open('r+b') as stream:
        stream.seek(offset); previous = stream.read(1)
        stream.seek(offset); stream.write(bytes([previous[0] ^ 1]))
    check(name, lambda: verify_image(image, regions))
    with image.open('r+b') as stream:
        stream.seek(offset); stream.write(previous)
for name, row in regions.items():
    with image.open('r+b') as stream:
        stream.seek(row['offset']); stream.write(b'\1')
    check('corrupt ' + name, lambda: verify_image(image, regions))
    with image.open('r+b') as stream:
        stream.seek(row['offset']); stream.write(b'\0')
with image.open('r+b') as stream:
    stream.truncate(IMAGE_BYTES - 1)
check('truncated image', lambda: verify_image(image, regions))
with image.open('r+b') as stream:
    stream.truncate(IMAGE_BYTES + 1)
check('oversized image', lambda: verify_image(image, regions))
with image.open('r+b') as stream:
    stream.truncate(IMAGE_BYTES)
link = stage / 'symlink.img'; link.symlink_to(image.name)
check('symlink image', lambda: verify_image(link, regions))
link = stage / 'hardlink.img'; os.link(image, link)
check('hard-linked image', lambda: verify_image(image, regions)); link.unlink()
for name, edit in [('missing region', lambda r: r.pop('trust.img')),
                   ('extra region', lambda r: r.update({'extra': dict(r['trust.img'])})),
                   ('moved root', lambda r: r['rootfs.ext4'].update(offset=ROOT_OFFSET - 512)),
                   ('oversized boot payload overlap', lambda r: r['idbloader.img'].update(bytes=FAT_OFFSET)),
                   ('negative region length', lambda r: r['trust.img'].update(bytes=-1)),
                   ('invalid digest', lambda r: r['trust.img'].update(sha256='z' * 64))]:
    changed = copy.deepcopy(regions); edit(changed)
    check(name, lambda: verify_image(image, changed))
check('restored image', lambda: verify_image(image, regions), True)
sources = [Path(__file__), repo / 'port/scripts/phase4_card_image.py']
(stage / 'analysis.json').write_text(json.dumps({'passed': True,
    'experiment': 'C70_FIXED_IMAGE_VALIDATOR_FIXTURES', 'cases': cases,
    'fixture_payloads_are_synthetic_zeroes': True, 'block_devices_accessed': False,
    'device_contacted': False, 'source_sha256': {str(p.relative_to(repo)): sha(p) for p in sources}}, indent=2) + '\n')
(area / 'latest-checks').write_text(str(stage) + '\n')
print('C70 regular-file image validator:', len(cases), 'cases passed:', stage)
