#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T0: host tests of the M3b boot path, in the rootfs container.
#   t0-boot.sh OLD_IMAGE OLD_DTB NEW_IMAGE NEW_DTB
# 1. uboot-boot/boot.c against mock U-Boot APIs (tests/uboot-boot/test.c),
#    with ASan/UBSan: trial once (consumed first), main, previous, windows.
# 2. bootrec.c (muos-bootrec, host build) against port/scripts/bootrec.py:
#    both encoders agree byte for byte, each decodes the other, and every
#    single-byte corruption of a record is rejected.
set -euo pipefail
[ $# -eq 4 ] || { sed -n '4p' "$0"; exit 2; }
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
tmp=$(mktemp -d "$repo/build/.t0-boot.XXXXXX"); trap 'rm -rf "$tmp"' EXIT
for i in 1 2 3 4; do cp --reflink=auto "${!i}" "$tmp/in$i"; done
python3 "$repo/port/scripts/bootrec.py" encode valid "$tmp/in3" "$tmp/in4" 'm3b test' "$tmp/py.rec" \
    --image-name Image-new --fdt-name panel0-new.dtb
podman run --rm --network=none --read-only --userns=keep-id --tmpfs /tmp:rw,exec \
    -v "$repo/port:/port:ro,z" -v "$tmp:/t:rw,z" "$(cat "$repo/build/phase4/rootfs-container.iid")" bash -euc '
    D=/port/device/rk-r35s-p0 cf="-std=gnu11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all"
    gcc $cf -Wno-unused-parameter -I/port/tests/uboot-boot/mock -I$D/uboot-boot -I$D/bootrec \
        /port/tests/uboot-boot/test.c $D/bootrec/bootrec.c -o /tmp/boot-test
    ASAN_OPTIONS=detect_leaks=0 /tmp/boot-test /t/in1 /t/in2 /t/in3 /t/in4
    gcc $cf -I$D/bootrec $D/bootrec/muos-bootrec.c $D/bootrec/bootrec.c -o /tmp/muos-bootrec
    b=/tmp/muos-bootrec
    $b decode /t/py.rec > /t/c.txt
    sha() { sha256sum "$1" | cut -d" " -f1; }
    $b encode valid Image-new "$(stat -c %s /t/in3)" "$(sha /t/in3)" panel0-new.dtb \
        "$(stat -c %s /t/in4)" "$(sha /t/in4)" "m3b test" /t/c.rec
    cmp /t/py.rec /t/c.rec && echo "ok   C and Python encoders agree"
    head -c 512 /dev/zero > /t/zero.rec; rc=0; $b decode /t/zero.rec >/dev/null || rc=$?
    [ $rc = 1 ] && echo "ok   empty sector = no record"
    bad=0
    for off in $(seq 0 511); do
        cp /t/c.rec /t/x.rec
        v=$(( ( $(od -An -tu1 -j$off -N1 /t/c.rec) + 1 ) % 256 ))
        printf "\\$(printf %03o $v)" | dd of=/t/x.rec bs=1 seek=$off conv=notrunc status=none
        rc=0; $b decode /t/x.rec >/dev/null || rc=$?
        [ $rc = 2 ] || { echo "FAIL corruption at $off accepted"; bad=1; }
    done
    [ $bad = 0 ] && echo "ok   all 512 single-byte corruptions rejected"
    rc=0; $b encode valid ../Image 1000 "$(sha /t/in3)" x.dtb 1000 "$(sha /t/in4)" l /t/n.rec 2>/dev/null || rc=$?
    [ $rc = 2 ] && echo "ok   unsafe file name refused"
    exit $bad'
python3 "$repo/port/scripts/bootrec.py" decode "$tmp/c.rec" | grep -q '^image=Image-new$' && echo 'ok   Python decodes the C record'
grep -q '^record=ok$' "$tmp/c.txt" && echo 'ok   C decodes the Python record'
