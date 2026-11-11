#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: the M3b boot-record U-Boot on the device (3 reboots). Needs valid main
# and previous records with different kernels (the M3b card layout).
#   1. a normal boot is main, with the TRNG as the current hwrng
#   2. a corrupt main record boots previous (main restored afterwards)
#   3. an armed trial whose Image SHA256 is wrong is consumed and main boots
#   4. back on main; records as at the start
set -euo pipefail
dev=$(dirname "$0")/device.sh
pass() { printf 'PASS %s\n' "$*"; }
fail() { printf 'FAIL %s\n' "$*"; exit 1; }
r() { "$dev" run "$*"; }
slot() { r 'sed -n "s/.*muos_slot=\([a-z]*\).*/\1/p" /proc/cmdline'; }
boot() { "$dev" reboot >/dev/null; "$dev" wait 240 >/dev/null || fail "no SSH after reboot"; }
recs() { r 'dd if=/dev/mmcblk0 bs=512 skip=32 count=2 2>/dev/null | sha256sum | cut -c1-16'; }

[ "$(slot)" = main ] || fail "not booted from main (got '$(slot)')"
r 'for s in 32 33; do dd if=/dev/mmcblk0 bs=512 skip=$s count=1 2>/dev/null > /run/r$s; /usr/libexec/muos-bootrec decode /run/r$s >/dev/null || exit 1; done' ||
    fail "main/previous records not valid"
start=$(recs)
[ "$(r 'cat /sys/class/misc/hw_random/rng_current')" = rockchip ] || fail "hwrng is not the TRNG"
pass "main boot, TRNG current, records valid ($start)"

r 'mkdir -p /userdata/MUOS/boot; dd if=/dev/mmcblk0 bs=512 skip=32 count=1 of=/userdata/MUOS/boot/main.rec conv=fsync 2>/dev/null
   cp /userdata/MUOS/boot/main.rec /run/bad.rec; printf X | dd of=/run/bad.rec bs=1 seek=200 conv=notrunc 2>/dev/null
   dd if=/run/bad.rec of=/dev/mmcblk0 bs=512 seek=32 conv=notrunc,fsync 2>/dev/null; sync'
boot
got=$(slot)
r 'dd if=/userdata/MUOS/boot/main.rec of=/dev/mmcblk0 bs=512 seek=32 conv=notrunc,fsync 2>/dev/null; sync; echo 3 > /proc/sys/vm/drop_caches'
[ "$got" = previous ] || fail "corrupt main record booted '$got', not previous"
[ "$(recs)" = "$start" ] || fail "main record not restored"
pass "corrupt main record -> previous; main restored"

r 'dd if=/dev/mmcblk0 bs=512 skip=32 count=1 2>/dev/null > /run/r32  # /run is gone after the reboot
   /usr/libexec/muos-bootrec decode /run/r32 > /run/r32.txt; v() { sed -n "s/^$1=//p" /run/r32.txt; }
   /usr/libexec/muos-bootrec encode trial "$(v image)" "$(v image_bytes)" 0000000000000000000000000000000000000000000000000000000000000000 \
       "$(v fdt)" "$(v fdt_bytes)" "$(v fdt_sha256)" "t2 bad sha" /run/t.rec
   dd if=/run/t.rec of=/dev/mmcblk0 bs=512 seek=34 conv=notrunc,fsync 2>/dev/null; sync'
boot
got=$(slot)
st=$(r 'dd if=/dev/mmcblk0 bs=512 skip=34 count=1 2>/dev/null > /run/t; /usr/libexec/muos-bootrec decode /run/t | sed -n "s/^state=//p"')
[ "$got" = main ] || fail "bad-SHA trial: booted '$got', not main"
[ "$st" = trial-consumed ] || fail "bad-SHA trial left '$st'"
pass "bad-SHA trial consumed -> main"

boot
[ "$(slot)" = main ] && [ "$(recs)" = "$start" ] || fail "final boot not main or records changed"
pass "main again; records unchanged"
