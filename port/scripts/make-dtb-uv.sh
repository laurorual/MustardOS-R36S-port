#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M8 thermal block T6: undervolted trial DTB. Lowers the target and
# minimum voltage of every CPU OPP from 1008 MHz up by CPU_MV and of
# every GPU OPP by GPU_MV (opp-microvolt and its L0..L3 bins; the maximum
# stays), nothing else. RK817 bucks step 12.5 mV, so use multiples of it.
#   make-dtb-uv.sh IN.dtb OUT.dtb CPU_MV GPU_MV
set -euo pipefail
in=$(realpath "$1") out=$(realpath -m "$2") cpu=$3 gpu=$4
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp "$in" "$work/in.dtb"
podman run --rm --network=none -v "$work:/d:z" -e CPU="$cpu" -e GPU="$gpu" \
    localhost/muos-r35s-phase4-kernel:20261024 sh -euc '
    cd /d; cp in.dtb out.dtb
    lower() { # TABLE MV MIN_HZ
        for n in $(fdtget -l out.dtb "$1"); do
            hz=$(fdtget -t x out.dtb "$1/$n" opp-hz | awk "{print \$2}")
            [ $((0x$hz)) -ge "$3" ] || continue
            for p in opp-microvolt opp-microvolt-L0 opp-microvolt-L1 opp-microvolt-L2 opp-microvolt-L3; do
                v=$(fdtget -t u out.dtb "$1/$n" "$p" 2>/dev/null) || continue
                t=$((${v%% *} - $2 * 1000))
                case $v in
                *" "*" "*) fdtput -t u out.dtb "$1/$n" "$p" $t $t "${v##* }" ;; # <target min max>
                *) fdtput -t u out.dtb "$1/$n" "$p" $t ;;
                esac
            done
            echo "$1/$n $((0x$hz / 1000000)) MHz: $(fdtget -t u out.dtb "$1/$n" opp-microvolt)"
        done
    }
    lower /cpu0-opp-table "$CPU" 1008000000
    lower /gpu-opp-table "$GPU" 0
    dtc -q -I dtb -O dts -o in.dts in.dtb; dtc -q -I dtb -O dts -o out.dts out.dtb
    diff in.dts out.dts > diff.txt || :
'
# Only opp-microvolt lines may differ.
if grep '^[<>]' "$work/diff.txt" | grep -v -q 'opp-microvolt'; then
    cat "$work/diff.txt" >&2; echo "unexpected DTB diff" >&2; exit 1
fi
cp "$work/out.dtb" "$out"
echo "OK $out sha256=$(sha256sum "$out" | cut -c1-12) ($(grep -c '^>' "$work/diff.txt") voltage lines)"
