#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# t2-levelbar.sh: does a grabbed frame (PPM, P6) show the level bar where
# /run/muos/levelbar/levelbar.conf (muxretro --level-assets) puts it? The
# progress track's right end and the fill's left end (volume 5 %) must be the
# theme's colours where they are opaque; the conf is in theme units, scaled
# to the frame.
#   t2-levelbar-check.py FRAME.ppm levelbar.conf
import sys

data = open(sys.argv[1], 'rb').read()
head = data.split(b'\n', 3)
w, h = map(int, head[1].split())
px = head[3]
conf = {}
for line in open(sys.argv[2]):
    f = line.split()
    if not f:
        continue
    if f[0] == 'image':
        if f[1:3] == ['0', '1']:
            conf['off'] = int(f[3])
    else:
        conf[f[0]] = f[1:]
mw, mh = map(int, conf['mux'])
x0, y0, pw, ph = map(int, conf['panel'])
bw, bh = map(int, conf['bar'])
sx, sy = w / mw, h / mh
bx = x0 + conf.get('off', 0)
by = y0 + (ph - bh) // 2 + bh // 2


def at(x, y):
    o = (int(y * sy) * w + int(x * sx)) * 3
    return px[o:o + 3]


ok = True
for name, x in (('main', bx + bw - 3), ('active', bx + 2)):
    rgb, alpha = conf[name][0], int(conf[name][1])
    got = at(x, by)
    if alpha == 255 and not all(abs(a - b) <= 10 for a, b in zip(got, bytes.fromhex(rgb))):
        print(f'{name}: expected {rgb}, got {got.hex()} at {x},{by}')
        ok = False
sys.exit(0 if ok else 1)
