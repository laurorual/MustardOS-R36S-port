#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render the low-battery poweroff splash as a raw framebuffer image (M4a).

    make-battery-splash.py FONT.ttf OUT.fb.gz [PREVIEW.png]

640x480, XRGB8888 little endian (fb0 on the R35S: 32 bpp, stride 2560),
gzip -9 without a timestamp so the output is reproducible. FONT is the muOS
theme's Noto Sans (OFL). muos-splash writes it to /dev/fb0 after the UI
has stopped (usr/libexec/muos-lowbattery, muos-rc).
"""
import gzip
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 640, 480
font, out = sys.argv[1], sys.argv[2]
img = Image.new('RGB', (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)
# An empty battery: outline, terminal, one red sliver.
bx, by, bw, bh = 220, 120, 180, 90
d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=10, outline=(230, 230, 230), width=6)
d.rectangle((bx + bw + 6, by + 28, bx + bw + 18, by + bh - 28), fill=(230, 230, 230))
d.rectangle((bx + 14, by + 14, bx + 30, by + bh - 14), fill=(220, 40, 40))
big = ImageFont.truetype(font, 40)
small = ImageFont.truetype(font, 24)
for text, f, y, col in (("Battery empty", big, 262, (240, 240, 240)),
                        ("Shutting down. Connect the charger.", small, 322, (170, 170, 170))):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=col)
if len(sys.argv) > 3:
    img.save(sys.argv[3])
raw = img.tobytes('raw', 'BGRX')
with open(out, 'wb') as fo:
    with gzip.GzipFile(fileobj=fo, mode='wb', compresslevel=9, mtime=0, filename='') as gz:
        gz.write(raw)
print(f'{out}: {len(raw)} bytes raw')
