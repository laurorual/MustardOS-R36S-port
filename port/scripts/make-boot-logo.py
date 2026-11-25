#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render the port's boot logo (M8): one picture, two encodings.

    make-boot-logo.py FONT.ttf OUT_DIR [PREVIEW.png]
    make-boot-logo.py --bmp FB.gz OUT.bmp   (stdlib only: the image build
                                             derives p1's BMP from the
                                             committed bootlogo.fb.gz)

OUT_DIR/bootlogo.bmp   640x480, 24-bit, uncompressed, bottom-up: U-Boot
                       shows it from p1 (uboot-boot/boot.c accepts only this
                       format) until the kernel takes the display.
OUT_DIR/bootlogo.fb.gz 640x480 XRGB8888 little endian, gzip -9 without a
                       timestamp: muos-splash writes it to /dev/fb0 at the
                       start of muos-rc, until the frontend draws.
Greys only, so the picture is the same whatever channel order the U-Boot
display path uses. FONT is the muOS theme's Noto Sans (OFL). Output is
reproducible.
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

font, out = sys.argv[1], Path(sys.argv[2])
img = Image.new('RGB', (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)


def text_font(size):
    return ImageFont.truetype(font, size)


def centred(text, f, y, grey):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=(grey, grey, grey))


# muos.dev/press: the full name "MustardOS" where there is room (decision 34)
centred('MustardOS', text_font(84), 158, 240)
d.rectangle((W / 2 - 60, 282, W / 2 + 60, 284), fill=(110, 110, 110))
centred('R36S / R35S', text_font(28), 300, 190)
centred('unofficial port', text_font(20), 420, 110)

out.mkdir(parents=True, exist_ok=True)
# BMP: rows bottom-up, BGR, 1920 bytes per row (no padding at 640 px).
fb = img.convert('RGBA').tobytes('raw', 'BGRA')  # XRGB8888 little endian
(out / 'bootlogo.bmp').write_bytes(bmp_from_fb(fb))
buf = io.BytesIO()
with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=9, mtime=0) as g:
    g.write(fb)
(out / 'bootlogo.fb.gz').write_bytes(buf.getvalue())
if len(sys.argv) > 3:
    img.save(sys.argv[3])
