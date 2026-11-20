#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M8 (decision 23, the user 2026-11-20: the fastest emulator, closed source
# allowed): DraStic r2.5.2.2 (NDS, closed source, free to use; the aarch64
# binary dArkOS ships) staged for the image, as dArkOS build_drastic.sh
# installs it, from the dArkOS clone build/darkos-src at a pinned commit:
#   tree  build/m8/drastic/tree/opt/muos/share/emulator/drastic/
#         (drastic, system/ BIOS replacements, game_database.xml, logos;
#         usrcheat.dat, 13.7 MB, left out)
#   cfg   port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/drastic/drastic.cfg
#         = dArkOS's RG351MP drastic.cfg with the controls moved to the
#         muOS-Keys pad (gamecontrollerdb retro.txt: b0 B, b1 A, b2 X, b3 Y,
#         b4/b5 L1/R1, b6/b7 L2/R2, b8 Select, b9 Start, b10 Fn, b11/b12
#         L3/R3, hat 0 = d-pad). DraStic codes: 1024 + button, 1088 + SDL hat
#         value (1 up, 2 right, 4 down, 8 left; dArkOS's 351v/rgb10 files),
#         1152 + axis (+), 1216 + axis (-).
#   build-drastic.sh stage
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
src=$repo/build/darkos-src commit=86bac70
tree=$repo/build/m8/drastic/tree dest=opt/muos/share/emulator/drastic
cfg=$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/drastic/drastic.cfg
case "${1:-}" in
stage)
    rm -rf "$tree"; mkdir -p "$tree/$dest/system" "${cfg%/*}"
    g() { git -C "$src" show "$commit:drastic/$1"; }
    g bin/drastic > "$tree/$dest/drastic"; chmod 755 "$tree/$dest/drastic"
    for f in game_database.xml drastic_logo_0.raw drastic_logo_1.raw; do g "$f" > "$tree/$dest/$f"; done
    for f in drastic_bios_arm7.bin drastic_bios_arm9.bin; do g "system/$f" > "$tree/$dest/system/$f"; done
    chmod 644 "$tree/$dest"/*.xml "$tree/$dest"/*.raw "$tree/$dest"/system/*
    # RG351MP: buttons 8-11 d-pad, 12 Select, 13 Start, 14 Fn, 15/16 L3/R3
    g configs/drastic.cfg.rg351mp | tr -d '\r' | sed -E \
        -e 's/^(controls_b\[CONTROL_INDEX_(UI_)?UP\]) = 1032$/\1 = 1089/' \
        -e 's/^(controls_b\[CONTROL_INDEX_(UI_)?DOWN\]) = 1033$/\1 = 1092/' \
        -e 's/^(controls_b\[CONTROL_INDEX_(UI_)?LEFT\]) = 1034$/\1 = 1096/' \
        -e 's/^(controls_b\[CONTROL_INDEX_(UI_)?RIGHT\]) = 1035$/\1 = 1090/' \
        -e 's/^(controls_a\[CONTROL_INDEX_START\]) = 1037$/\1 = 1033/' \
        -e 's/^(controls_a\[CONTROL_INDEX_SELECT\]) = 1036$/\1 = 1032/' \
        -e 's/^(controls_b\[CONTROL_INDEX_(MENU|UI_SWITCH)\]) = 1038$/\1 = 1034/' \
        -e 's/^(controls_[ab]\[CONTROL_INDEX_TOUCH_CURSOR_PRESS\]) = 1039$/\1 = 1035/' \
        -e 's/^(controls_b\[CONTROL_INDEX_SWAP_SCREENS\]) = 1040$/\1 = 1036/' > "$cfg"
    # every RG351MP-only code must be gone
    if grep -E '^controls_[ab]\[[A-Z_]+\] = 10(3[6-9]|40)$' "$cfg" | grep -v 'controls_b\[CONTROL_INDEX_SWAP_SCREENS\] = 1036\|TOUCH_CURSOR_PRESS\] = 1035'; then
        echo "unmapped RG351MP button codes left" >&2; exit 1
    fi
    (cd "$tree/$dest" && find . -type f | sort | xargs -d '\n' sha256sum) > "$repo/build/m8/drastic/SHA256SUMS"
    du -sh "$tree/$dest"; diff <(g configs/drastic.cfg.rg351mp | tr -d '\r') "$cfg" | grep -c '^>' ;;
*) sed -n '3,17p' "$0"; exit 2 ;;
esac
