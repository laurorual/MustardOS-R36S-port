#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M10 item 5: the model DTBs (port/packaging/models.txt): each pinned
# dArkOSen DTB plus the port's DT deltas, nothing else:
#   - /aliases mmc0 = slot 1 (dwmmc@ff370000), mmc1 = slot 2
#     (dwmmc@ff380000): kernel patch 0009 numbers the cards by them, the
#     root is /dev/mmcblk0p2 (hardware-findings "Linux mmc numbering")
#   - no GPU 600 MHz OPP (dArkOSen's overclock; the port's GPU tops out at
#     520 MHz on every model, as on Panel 0)
# A derived line "ID +BASE NODE:PROP=N NAME..." (BASE listed above it) is
# BASE's DTB with one more delta, the u32 PROP of NODE set to N, shown as
# NAME (2026-11-27: Panel 4 with vfront-porch 16, a user's dArkOSen DTB).
#   make-dtb-model.sh OUTDIR   writes OUTDIR/ID.dtb, its source OUTDIR/ID.dts
#                              and OUTDIR/ID.dts.diff (dts-delta.py lines),
#                              prints "ID SHA256 NAME" per model
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
list=$repo/port/packaging/models.txt src=$repo/refs/darkosen/boot/dtb
out=$(realpath -m "$1"); mkdir -p "$out"
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
# pinned inputs, copied so the container sees plain names
while read -r id want path; do
    case "$id" in ''|'#'*) continue ;; esac
    if [ "${want#+}" != "$want" ]; then
        base=${want#+} delta=${path%% *}
        [ -f "$work/$base.in.dtb" ] || { echo "make-dtb-model: $id: base $base not above it" >&2; exit 1; }
        case "$delta" in /*:*=*) ;; *) echo "make-dtb-model: $id: bad delta $delta" >&2; exit 1 ;; esac
        cp "$work/$base.in.dtb" "$work/$id.in.dtb"; printf '%s\n' "$delta" > "$work/$id.delta"
        printf '%s\t%s\n' "$id" "${path#* }" >> "$work/names"
        continue
    fi
    [ "$(sha256sum < "$src/$path" | cut -d' ' -f1)" = "$want" ] ||
        { echo "make-dtb-model: $path does not match its pin" >&2; exit 1; }
    cp "$src/$path" "$work/$id.in.dtb"
    n=${path%/*}; printf '%s\t%s\n' "$id" "${n#*/}" >> "$work/names"
done < "$list"
podman run --rm --network=none -v "$work:/d:z" localhost/muos-r35s-phase4-kernel:20261024 sh -euc '
cd /d
for in in *.in.dtb; do
    id=${in%.in.dtb}; o=$id.dtb
    cp "$in" "$o"
    for n in /dwmmc@ff370000 /dwmmc@ff380000; do
        fdtget -l "$o" "$n" > /dev/null 2>&1 || fdtget "$o" "$n" compatible > /dev/null ||
            { echo "$id: no $n" >&2; exit 1; }
    done
    fdtget -p "$o" /aliases > /dev/null 2>&1 || fdtput -c "$o" /aliases
    fdtput -t s "$o" /aliases mmc0 /dwmmc@ff370000
    fdtput -t s "$o" /aliases mmc1 /dwmmc@ff380000
    ! fdtget -l "$o" /gpu-opp-table/opp-600000000 > /dev/null 2>&1 &&
        ! fdtget "$o" /gpu-opp-table/opp-600000000 opp-hz > /dev/null 2>&1 ||
        fdtput -r "$o" /gpu-opp-table/opp-600000000
    if [ -f "$id.delta" ]; then
        d=$(cat "$id.delta"); np=${d%%=*}
        fdtput -t u "$o" "${np%:*}" "${np##*:}" "${d#*=}"
    fi
    dtc -q -I dtb -O dts -o "$id.in.dts" "$in"; dtc -q -I dtb -O dts -o "$id.dts" "$o"
done'
# Only the aliases and the removed OPP (its node and a __symbols__ entry
# naming it) may differ (dts-delta.py: structural, exact).
while IFS=$'\t' read -r id name; do
    d=$work/$id.dts.diff
    python3 "$repo/port/scripts/dts-delta.py" "$work/$id.in.dts" "$work/$id.dts" > "$d"
    extra='^$'
    if [ -f "$work/$id.delta" ]; then # exactly its one extra property
        dl=$(cat "$work/$id.delta"); np=${dl%%=*}
        extra="^prop ${np%:*} ${np##*:}: <0x[0-9a-f]+> => <$(printf '0x%x' "${dl#*=}")>\$"
        grep -qE "$extra" "$d" || { echo "make-dtb-model: $id: delta $dl not applied" >&2; exit 1; }
    fi
    bad=$(grep -vE -e "$extra" -e '^prop /aliases mmc0: <none> => "/dwmmc@ff370000"$|^prop /aliases mmc1: <none> => "/dwmmc@ff380000"$|^-node /gpu-opp-table/opp-600000000$|^prop /__symbols__ [a-z0-9_]+: "/gpu-opp-table/opp-600000000" => <none>$' "$d" || :)
    [ -z "$bad" ] || { echo "make-dtb-model: $id: unexpected DTB diff:" >&2; echo "$bad" | head >&2; exit 1; }
    [ "$(grep -c '^prop /aliases mmc[01]: ' "$d")" = 2 ] || { echo "make-dtb-model: $id: aliases not added" >&2; exit 1; }
    cp "$work/$id.dtb" "$out/$id.dtb"; cp "$work/$id.dts" "$out/$id.dts"; cp "$d" "$out/$id.dts.diff"
    printf '%s %s %s\n' "$id" "$(sha256sum < "$out/$id.dtb" | cut -d' ' -f1)" "$name"
done < "$work/names"
