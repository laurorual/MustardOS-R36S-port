#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Derive the M2 1512 MHz DTB from the port DTB: copy the stock dArkOSen
# Panel 0 CPU OPPs above 1296 MHz (1368..1512 MHz, 1.35/1.40 V, identical
# L0..L3 bins) and raise vdd_arm (RK817 DCDC_REG2) max to 1.40 V, as stock.
# Nothing else changes (verified by diffing the decompiled trees).
#   make-dtb-opp.sh PORT.dtb OUT.dtb [STOCK.dtb]
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
in=$(realpath "$1") out=$(realpath -m "$2")
stock=$(realpath "${3:-$repo/refs/darkosen/boot/dtb/r36s/R36S-V12 2023-08-18 Panel 0/rk3326-r36s-linux.dtb}")
[ "$(sha256sum "$stock" | cut -c1-16)" = 5634eb3eb5688355 ] || { echo "unexpected stock DTB" >&2; exit 1; }
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp "$in" "$work/in.dtb"; cp "$stock" "$work/stock.dtb"
podman run --rm --network=none -v "$work:/d:z" localhost/muos-r35s-phase4-kernel:20261024 sh -euc '
    cd /d; cp in.dtb out.dtb
    t=/cpu0-opp-table
    for f in 1368 1416 1440 1464 1488 1512; do
        n=$t/opp-${f}000000
        fdtput -c out.dtb "$n"
        for p in opp-hz opp-microvolt opp-microvolt-L0 opp-microvolt-L1 opp-microvolt-L2 opp-microvolt-L3 clock-latency-ns; do
            fdtput -t x out.dtb "$n" "$p" $(fdtget -t x stock.dtb "$n" "$p")
        done
    done
    fdtput -t x out.dtb /i2c@ff180000/pmic@20/regulators/DCDC_REG2 regulator-max-microvolt 155cc0
    dtc -q -I dtb -O dts -o in.dts in.dtb; dtc -q -I dtb -O dts -o out.dts out.dtb
    diff in.dts out.dts > diff.txt || :
    fdtget -l out.dtb $t | tr "\n" " "; echo
'
# Only the six new OPP nodes and the regulator max may differ.
removed=$(grep -c '^<' "$work/diff.txt" || :)
if [ "$removed" != 1 ] || ! grep -q "^< .*regulator-max-microvolt = <0x149970>" "$work/diff.txt"; then
    cat "$work/diff.txt" >&2; echo "unexpected DTB diff" >&2; exit 1
fi
cp "$work/out.dtb" "$out"
echo "OK $out sha256=$(sha256sum "$out" | cut -c1-16) (+$(grep -c '^> .*opp-hz' "$work/diff.txt") OPPs)"
