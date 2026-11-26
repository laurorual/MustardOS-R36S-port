#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M10 item 5: classify dArkOSen's Linux DTBs against the port's Panel 0 DTB
# (what the port's userspace depends on). One line per DTB:
#   RES  INPUT  KEYS  AUDIO  MMC  BATT  UBOOT  MODEL/DTB (the DTB its boot.ini loads)
#   RES    panel native mode (640x480, ...)
#   INPUT  "same" if the input device names (the gpio-keys node name, the
#          joypad's joypad-name) equal the port DTB's, else the names
#   KEYS   "same" if the set of linux,code values (gpio-keys and joypad
#          buttons) equals the port DTB's, else +added/-missing codes
#   AUDIO  hp-det (a headphone-detect GPIO in the sound node) or spk-only
#   MMC    the dwmmc nodes ff370000 (slot 1) / ff380000 (slot 2) present
#   BATT   design_capacity in mAh
#   UBOOT  the U-Boot DTB dArkOSen ships for the model (rg351mp = the
#          port's board type; rg351v = another board)
#   dtb-survey.sh [DTB_DIR] [PORT_DTB]  (defaults: refs/darkosen/boot/dtb,
#                                         build/m3b/boot/rk3326-muos-r35s-panel0.dtb)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
dir=$(realpath "${1:-$repo/refs/darkosen/boot/dtb}")
port=$(realpath "${2:-$repo/build/m3b/boot/rk3326-muos-r35s-panel0.dtb}")
podman run --rm --network=none -v "$dir:/d:ro,z" -v "$port:/port.dtb:ro,z" \
    localhost/muos-r35s-phase4-kernel:20261024 sh -euc '
props() { # DTB: the facts, one "key value" per line
    dtc -q -I dtb -O dts "$1" 2>/dev/null | awk "
        function v(s) { sub(/^[^=]*= */, \"\", s); sub(/;\$/, \"\", s); gsub(/[<>\"]/, \"\", s); return s }
        /display-timings/ { dt = 1 }
        dt && /hactive/ && !h { h = v(\$0) }
        dt && /vactive/ && !vv { vv = v(\$0) }
        /linux,code/ { print \"code\", v(\$0) }
        /^[ \t]*[^ \t=]+ \{\$/ { node = \$1 }
        /compatible = \"gpio-keys\"/ { print \"name\", node }
        /joypad-name/ { print \"name\", v(\$0) }
        /hp-det-gpio|hp-det-gpios/ { hp = 1 }
        /dwmmc@ff370000 \{/ { m1 = 1 } /dwmmc@ff380000 \{/ { m2 = 1 }
        /design_capacity/ { print \"batt\", v(\$0) }
        END { print \"res\", h \":\" vv; print \"audio\", (hp ? \"hp-det\" : \"spk-only\"); print \"mmc\", (m1 ? \"s1\" : \"-\") (m2 ? \"+s2\" : \"\") }"
}
props /port.dtb > /tmp/port.txt
pnames=$(grep "^name " /tmp/port.txt | sort -u | cut -d" " -f2- | tr "\n" ";")
hex() { while read -r x; do printf "%d\n" "$x"; done; }
grep "^code " /tmp/port.txt | cut -d" " -f2 | hex | sort -nu > /tmp/port.codes
cd /d
# One line per model folder: the DTB its boot.ini loads.
find . -name boot.ini | sort | while read -r ini; do
    d=${ini%/boot.ini}
    f=$d/$(sed -n "s/^load mmc [^ ]* [^ ]* \(.*\.dtb\)\r*\$/\1/p" "$ini" | sed "s/.* //" | head -1)
    [ -f "$f" ] || { echo "?\t-\t-\t-\t-\t0\t-\t${d#./} (no DTB in boot.ini)"; continue; }
    ub=$(ls "$d" | sed -n "s/-uboot\.dtb\$//p" | head -1)
    props "$f" > /tmp/x.txt
    names=$(grep "^name " /tmp/x.txt | sort -u | cut -d" " -f2- | tr "\n" ";")
    [ "$names" = "$pnames" ] && in=same || in=${names:-none}
    grep "^code " /tmp/x.txt | cut -d" " -f2 | hex | sort -nu > /tmp/x.codes
    add=$(comm -13 /tmp/port.codes /tmp/x.codes | sed "s/^/+/" | tr "\n" " ")
    mis=$(comm -23 /tmp/port.codes /tmp/x.codes | sed "s/^/-/" | tr "\n" " ")
    keys="$add$mis"; [ -n "$keys" ] || keys=same
    n=${d#./}
    res=$(sed -n "s/^res //p" /tmp/x.txt); w=${res%:*} hh=${res#*:}
    b=$(sed -n "s/^batt //p" /tmp/x.txt | head -1)
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$((w))x$((hh))" "$in" "$keys" \
        "$(sed -n "s/^audio //p" /tmp/x.txt)" "$(sed -n "s/^mmc //p" /tmp/x.txt)" "$((${b:-0}))" "${ub:--}" "$n/${f##*/}"
done'
