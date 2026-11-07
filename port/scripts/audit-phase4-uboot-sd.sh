#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Inspect the bare-metal ELF and separately compile the display DTB. No QEMU
# userspace execution of U-Boot, no vendor packers and no device access.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
stage=$(cat "$work/uboot-sd/latest-build")
[[ "$stage" == "$work/uboot-sd"/probe.* && $(cat "$stage/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-uboot-sd) == false ]]
mkdir -p "$stage/audit"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
 -e UBOOT_PROBE_REL="${stage#"$work/"}" "$(cat "$work/kernel-container.iid")" sh -eu -c '
 stage=/work/$UBOOT_PROBE_REL
 source=$stage/source
 output=$stage/output
 /work/linaro6/bin/aarch64-linux-gnu-readelf -h -l -S -sW "$output/u-boot" > "$stage/audit/elf.txt"
 /work/linaro6/bin/aarch64-linux-gnu-nm -n -S "$output/u-boot" > "$stage/audit/symbols.txt"
 gcc -E -nostdinc -undef -D__DTS__ -x assembler-with-cpp \
  -I "$source/arch/arm/dts" -I "$source/include" \
  "$source/arch/arm/dts/rk3326-muos-r35s-panel0-uboot.dts" > "$stage/audit/display.preprocessed.dts"
 dtc -I dts -O dtb -o "$stage/rk3326-muos-r35s-panel0-uboot.dtb" "$stage/audit/display.preprocessed.dts" > "$stage/audit/dtc.log" 2>&1
 ' > "$stage/audit/run.log" 2>&1
python3 "$repo/port/scripts/verify-phase4-uboot-panel.py" \
 "$stage/rk3326-muos-r35s-panel0-uboot.dtb" "$work/panel-reference/rg351mp-uboot.dtb" > "$stage/audit/display.json"
python3 "$repo/port/scripts/verify-phase4-uboot-sd.py" "$stage" > "$stage/audit/report.json"
printf '%s\n' 'Host U-Boot SD probe audit passed. No loader/trust packaging or boot test.'
