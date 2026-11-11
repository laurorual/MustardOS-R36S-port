#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Host encoder/decoder for the muOS R35S boot records (layout in
port/device/rk-r35s-p0/bootrec/bootrec.h; keep both in sync).

  bootrec.py encode STATE IMAGE_FILE FDT_FILE LABEL OUT [--image-name N] [--fdt-name N]
  bootrec.py decode FILE
  bootrec.py image-fits IMAGE_FILE [SPAN]   arm64 header: text_offset+image_size <= SPAN
"""
import argparse
import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b'MUOSBREC'
STATES = {'valid': 1, 'trial': 2}
NAMES = {1: 'valid', 2: 'trial-armed', 3: 'trial-consumed'}
NAME_RE = re.compile(r'^[A-Za-z0-9_-][A-Za-z0-9._-]{0,46}$')
IMAGE_MAX, FDT_MAX = 0x02000000, 0x3c000
SECTORS = {'main': 32, 'previous': 33, 'trial': 34}
KERNEL_SPAN = 0x02000000  # U-Boot's wide window (fallback 0xec0000)


def encode(state, image, image_bytes, image_sha, fdt, fdt_bytes, fdt_sha, label):
    if not NAME_RE.match(image) or not NAME_RE.match(fdt):
        raise ValueError('bad file name')
    if not (64 <= image_bytes <= IMAGE_MAX and 64 <= fdt_bytes <= FDT_MAX):
        raise ValueError('bad size')
    if len(label) > 31 or not all(0x20 <= ord(c) <= 0x7e for c in label):
        raise ValueError('bad label')
    body = (MAGIC + struct.pack('<II', 1, state) + image.encode().ljust(48, b'\0')
            + struct.pack('<I', image_bytes) + bytes.fromhex(image_sha)
            + fdt.encode().ljust(48, b'\0') + struct.pack('<I', fdt_bytes)
            + bytes.fromhex(fdt_sha) + label.encode().ljust(32, b'\0'))
    assert len(body) == 216
    body = body.ljust(508, b'\0')
    return body + struct.pack('<I', zlib.crc32(body))


def decode(sector):
    if len(sector) != 512:
        raise ValueError('not 512 bytes')
    if not any(sector):
        return None
    if sector[:8] != MAGIC or struct.unpack_from('<I', sector, 8)[0] != 1:
        raise ValueError('bad magic/version')
    if struct.unpack_from('<I', sector, 508)[0] != zlib.crc32(sector[:508]) or any(sector[216:508]):
        raise ValueError('bad crc/padding')
    name = lambda off: sector[off:off + 48].rstrip(b'\0').decode()
    return {'state': NAMES.get(struct.unpack_from('<I', sector, 12)[0], '?'),
            'image': name(16), 'image_bytes': struct.unpack_from('<I', sector, 64)[0],
            'image_sha256': sector[68:100].hex(), 'fdt': name(100),
            'fdt_bytes': struct.unpack_from('<I', sector, 148)[0],
            'fdt_sha256': sector[152:184].hex(), 'label': sector[184:216].rstrip(b'\0').decode()}


def image_end(path):
    head = Path(path).read_bytes()[:64]
    text_offset, image_size = struct.unpack_from('<QQ', head, 8)
    if head[56:60] != b'ARMd' or not image_size:
        raise ValueError(f'{path}: not an arm64 Image with image_size')
    return text_offset + image_size


def record_for(state, image_file, fdt_file, label, image_name=None, fdt_name=None):
    image, fdt = Path(image_file).read_bytes(), Path(fdt_file).read_bytes()
    if image_end(image_file) > KERNEL_SPAN:
        raise ValueError('Image does not fit the kernel window')
    return encode(STATES[state], image_name or Path(image_file).name, len(image),
                  hashlib.sha256(image).hexdigest(), fdt_name or Path(fdt_file).name,
                  len(fdt), hashlib.sha256(fdt).hexdigest(), label)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('encode')
    e.add_argument('state', choices=STATES)
    e.add_argument('image_file'); e.add_argument('fdt_file'); e.add_argument('label'); e.add_argument('out')
    e.add_argument('--image-name'); e.add_argument('--fdt-name')
    d = sub.add_parser('decode'); d.add_argument('file')
    f = sub.add_parser('image-fits'); f.add_argument('image_file'); f.add_argument('span', nargs='?', default=str(KERNEL_SPAN))
    a = p.parse_args()
    if a.cmd == 'encode':
        Path(a.out).write_bytes(record_for(a.state, a.image_file, a.fdt_file, a.label, a.image_name, a.fdt_name))
    elif a.cmd == 'decode':
        r = decode(Path(a.file).read_bytes()[:512])
        print('record=empty' if r is None else '\n'.join(f'{k}={v}' for k, v in r.items()))
    else:
        end, span = image_end(a.image_file), int(a.span, 0)
        print(f'end=0x{end:x} span=0x{span:x} headroom=0x{span - end:x}')
        sys.exit(0 if end <= span else 1)


if __name__ == '__main__':
    main()
