#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Assemble the port U-Boot source tree (M3b) from the pinned base.

  uboot-tree.py ref|boot OUT_DIR

ref:  the M2 card's U-Boot (Phase 4 "ext4-diagnostic" profile: compiled-in
      asset pins, header taken from the Phase 4 probe tree); used only to
      prove this assembly reproduces the card's uboot.img byte for byte.
boot: the M3b U-Boot: boot records (uboot-boot/boot.c + bootrec), no pins;
      M8: no autoboot delay, no LCD text (probe-quiet.patch), boot logo.
Mirrors prepare-phase4-uboot-sd.py --linux-assets (ext4) otherwise.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
dev = repo/'port/device/rk-r35s-p0'
work = repo/'build/phase4'
REF_PROBE = work/'uboot-sd/probe.3utahq01'  # built the M2 card's uboot.img
profile, out = sys.argv[1], Path(sys.argv[2])
assert profile in ('ref', 'boot')
lock = json.loads((dev/'phase4-uboot-sources.json').read_text())
base = work/'uboot-base'
rev = subprocess.check_output(['git', '-C', str(base), 'rev-parse', 'HEAD'], text=True).strip()
assert rev == lock['revision'], 'uboot-base revision'
assert not subprocess.check_output(['git', '-C', str(base), 'status', '--porcelain'], text=True).strip()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name, digest in lock['recipe_payload_sha256'].items():
    assert sha(base/name) == digest, name

if out.exists():
    shutil.rmtree(out)
src = out/'source'
src.mkdir(parents=True)
subprocess.run(f"git -C '{base}' archive {rev} | tar -x -C '{src}'", shell=True, check=True)
subprocess.run(['git', 'init', '-q', str(src)], check=True)
patch = repo/'port/patches/0007-uboot-r35s-sd-probe.patch'
subprocess.run(['git', 'apply', str(patch)], cwd=src, check=True)

owned = {
    'uboot-sd/board.c': 'board/rockchip/odroidgoa/muos-r35s-probe.c',
    'uboot-sd/board.h': 'include/configs/muos-r35s-monitor.h',
    'uboot-sd/memory.h': 'include/configs/muos-r35s-memory.h',
    'rk3326-muos-r35s-panel0-uboot.dts': 'arch/arm/dts/rk3326-muos-r35s-panel0-uboot.dts',
    'uboot-linux/board.h': 'include/configs/muos-r35s-linux.h',
}
objects = ['muos-r35s-linux.o']
if profile == 'ref':
    owned['uboot-linux/boot.c'] = 'board/rockchip/odroidgoa/muos-r35s-linux.c'
    owned['uboot-ext4/board.h'] = 'include/configs/odroidgoa.h'
else:
    owned['uboot-boot/boot.c'] = 'board/rockchip/odroidgoa/muos-r35s-linux.c'
    owned['uboot-boot/board.h'] = 'include/configs/odroidgoa.h'
    owned['bootrec/bootrec.c'] = 'board/rockchip/odroidgoa/muos-bootrec.c'
    owned['bootrec/bootrec.h'] = 'board/rockchip/odroidgoa/bootrec.h'
    objects.append('muos-bootrec.o')
for name, target in owned.items():
    shutil.copy2(dev/name, src/target)
# M8: the product boot has no autoboot delay (as the stock odroidgoa
# config) and no diagnostic text on the LCD (muos_boot shows the logo).
delay = 3 if profile == 'ref' else 0
if profile == 'boot':
    subprocess.run(['git', 'apply', str(dev/'uboot-boot/probe-quiet.patch')], cwd=src, check=True)
with (src/'arch/arm/dts/rk3326-muos-r35s-panel0-uboot.dts').open('a') as f:
    f.write(f'\n/ {{ config {{ bootdelay = <{delay}>; }}; }};\n')
with (src/'board/rockchip/odroidgoa/Makefile').open('a') as f:
    f.write('\nobj-y += ' + ' '.join(objects) + '\n')
if profile == 'ref':
    hdr = 'include/configs/muos-r35s-linux-assets.h'
    shutil.copy2(REF_PROBE/'source'/hdr, src/hdr)

fragment = (dev/'uboot-sd/config.fragment').read_text().replace('CONFIG_BOOTDELAY=-1', f'CONFIG_BOOTDELAY={delay}')
key = lambda l: (m := re.match(r'(?:# )?(CONFIG_[A-Z0-9_]+)(?:=| is not set)', l)) and m[1]
keys = {key(l) for l in fragment.splitlines()} - {None}
config = '\n'.join(l for l in (base/'configs/odroidgoa_defconfig').read_text().splitlines() if key(l) not in keys)
(src/'configs/muos_r35s_panel0_sd_defconfig').write_text(config + '\n' + fragment)
(src/'.scmversion').write_text('')
epoch = subprocess.check_output(['git', '-C', str(base), 'show', '-s', '--format=%ct', rev], text=True).strip()
(out/'source_date_epoch').write_text(epoch + '\n')
if profile == 'ref':  # the assembled tree must equal the probe's, file for file
    record = json.loads((REF_PROBE/'inputs.json').read_text())
    strip = lambda p: re.sub(rb'/\*.*?\*/', b'', Path(p).read_bytes(), flags=re.S)
    for name, digest in record['source_files'].items():
        if sha(src/name) == digest:
            continue
        # Docs paths in comments moved since Phase 4: comment-only drift is
        # allowed; the probe's file is used so the build sees the same bytes.
        assert strip(src/name) == strip(REF_PROBE/'source'/name), f'ref tree differs: {name}'
        shutil.copy2(REF_PROBE/'source'/name, src/name)
        print(f'ref: comment-only drift in {name}: probe copy used')
print(f'{profile} tree: {src}')
