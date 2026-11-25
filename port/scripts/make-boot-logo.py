#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render the port's boot logo (M8): one picture, two encodings.

    make-boot-logo.py FONT.ttf BASE.png OUT_DIR [PREVIEW.png]
    make-boot-logo.py --bmp FB.gz OUT.bmp   (stdlib only: the image build
                                             derives p1's BMP from the
                                             committed bootlogo.fb.gz)

OUT_DIR/bootlogo.bmp   640x480, 24-bit, uncompressed, bottom-up: U-Boot
                       shows it from p1 (uboot-boot/boot.c accepts only this
                       format) until the kernel takes the display.
OUT_DIR/bootlogo.fb.gz 640x480 XRGB8888 little endian, gzip -9 without a
                       timestamp: muos-splash writes it to /dev/fb0 at the
                       start of muos-rc, until the frontend draws.
M9 (rc1 T3, decision 34): BASE is MustardOS's own boot screen from the
press kit (https://muos.dev/press, images/mustardos-boot-screen-640x480.png,
CC BY-NC 4.0; the badge is used as supplied); the port adds only text
below it, in the kit's Text Grey: the device and "unofficial port" (the
Terms of Use forbid presenting the port as official). FONT is the
MustardOS theme's Noto Sans (OFL). Output is reproducible.
"""
import gzip
import io
import struct
import sys
from pathlib import Path

W, H = 640, 480


def bmp_from_fb(fb):
    """XRGB8888 top-down -> 24-bit BMP bottom-up (BGR, 1920-byte rows)."""
    assert len(fb) == W * H * 4
    rows = b''.join(bytes(b for i in range(0, W * 4, 4) for b in fb[y * W * 4 + i:y * W * 4 + i + 3])
                    for y in reversed(range(H)))
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(rows), 0, 0, 54)
    info = struct.pack('<IiiHHIIiiII', 40, W, H, 1, 24, 0, len(rows), 2835, 2835, 0, 0)
    return hdr + info + rows


if sys.argv[1] == '--bmp':
    Path(sys.argv[3]).write_bytes(bmp_from_fb(gzip.decompress(Path(sys.argv[2]).read_bytes())))
    sys.exit(0)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402 (only to render)

import hashlib  # noqa: E402

BASE_SHA256 = '84b30eb313155603ce4297d7233cb6d6439e2a8a114ac226a107458dd47d7950'
font, base, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
assert hashlib.sha256(base.read_bytes()).hexdigest() == BASE_SHA256, 'not the press-kit boot screen'
img = Image.open(base).convert('RGB')
assert img.size == (W, H)
d = ImageDraw.Draw(img)
TEXT_GREY = (0xB8, 0xB8, 0xB8)  # press kit "Text Grey"


def centred(text, size, y):
    f = ImageFont.truetype(font, size)
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=TEXT_GREY)


# the badge occupies y 80..239; the text stays well clear of it
centred('R36S / R35S', 28, 300)
centred('unofficial port', 20, 420)

out.mkdir(parents=True, exist_ok=True)
# BMP: rows bottom-up, BGR, 1920 bytes per row (no padding at 640 px).
fb = img.convert('RGBA').tobytes('raw', 'BGRA')  # XRGB8888 little endian
(out / 'bootlogo.bmp').write_bytes(bmp_from_fb(fb))
buf = io.BytesIO()
with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=9, mtime=0) as g:
    g.write(fb)
(out / 'bootlogo.fb.gz').write_bytes(buf.getvalue())
if len(sys.argv) > 4:
    img.save(sys.argv[4])
