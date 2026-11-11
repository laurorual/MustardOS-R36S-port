#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M3b: build the boot chain (kernel Image, DTB, U-Boot) from pinned sources.
#
#   build-boot.sh kernel-ref   from scratch: must reproduce the M2 card's Image
#                              and DTB byte for byte (once; ~15 min)
#   build-boot.sh kernel       + m3b-kernel.fragment and the port DTS
#                              (incremental); Module.symvers must equal the
#                              reference, so the pinned modules stay valid
#   build-boot.sh uboot-ref    must reproduce the M2 card's uboot.img
#   build-boot.sh uboot        the M3b boot-records U-Boot
#   build-boot.sh all          kernel + uboot
#
# Outputs in build/m3b/boot: Image, rk3326-muos-r35s-panel0.dtb, uboot.img,
# kernel.config, SHA256SUMS. Containers: the Phase 4 kernel container with
# the pinned Linaro 6.3.1; build/phase4 (sources) is mounted read-only.
# shellcheck disable=SC2016 # the container scripts expand inside the container
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 m3b=$repo/build/m3b out=$repo/build/m3b/boot
dev=$repo/port/device/rk-r35s-p0
# The M2 card's boot assets (identical to the Phase 4 outputs).
ref_image=780935823cb8c86e4330c8c8157ebb4005fb5580e68e72c4b0c4e480bab42d2f
ref_dtb=496bbe3591f8619f059ebc384277ecdd17fd41f956aef40de20afb46b92d5b49
ref_uboot=$work/uboot-sd/probe.3utahq01/package.ou1j44x6/uboot.img
mkdir -p "$m3b/logs" "$m3b/kernel-output" "$out"
iid=$(cat "$work/kernel-container.iid")
[ "$iid" = "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["container_image_id"])' "$dev/phase4-uboot-sources.json")" ]
[ -z "$(git -C "$work/linux-base" status --porcelain --untracked-files=no)" ]
kepoch=$(git -C "$work/linux-base" show -s --format=%ct HEAD)

ctr() { # the common sandbox; extra -v/-e options, then the script
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id --memory=8g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g "$@"
}

kernel() { # MODE=ref|m3b
    local mode=$1
    ctr -v "$work:/work:ro,z" -v "$m3b/kernel-output:/work/kernel-output:rw,z" -v "$out:/out:rw,z" \
        -v "$repo/port:/port:ro,z" -e SOURCE_DATE_EPOCH="$kepoch" -e MODE="$mode" -e JOBS="${JOBS:-$(nproc)}" \
        -w /work/linux-base "$iid" sh -euc '
        export ARCH=arm64 CROSS_COMPILE=/work/linaro6/bin/aarch64-linux-gnu-
        export KBUILD=/work/kernel-output  # the in-tree esp8089 Makefile needs it
        export KBUILD_BUILD_USER=muos KBUILD_BUILD_HOST=r35s-port KBUILD_BUILD_VERSION=1
        export KBUILD_BUILD_TIMESTAMP="$(date -u --date="@$SOURCE_DATE_EPOCH" "+%a %b %d %T UTC %Y")"
        mk() { make O=/work/kernel-output HOSTCFLAGS="-O2 -fcommon" "$@"; }
        dtb() { # the kernel cmd_dtc, outside the read-only tree
            L=/work/linux-base
            ${CROSS_COMPILE}gcc -E -nostdinc -I$L/arch/arm64/boot/dts -I$L/scripts/dtc/include-prefixes \
                -I$L/drivers/of/testcase-data -I$L/arch/arm64/boot/dts/rockchip -undef -D__DTS__ \
                -x assembler-with-cpp -o /tmp/dt.tmp "$1"
            /work/kernel-output/scripts/dtc/dtc -O dtb -o "$2" -b 0 -i $L/arch/arm64/boot/dts/rockchip/ -@ \
                -Wno-unit_address_vs_reg -Wno-simple_bus_reg -Wno-unit_address_format -Wno-pci_bridge \
                -Wno-pci_device_bus_num -Wno-pci_device_reg /tmp/dt.tmp
        }
        cd /work/linux-base
        mk rg351p_tweaked_defconfig
        frags=/port/device/rk-r35s-p0/phase4-bsp.fragment
        [ "$MODE" = ref ] || frags="$frags /port/device/rk-r35s-p0/m3b-kernel.fragment"
        (cd /work/kernel-output && /work/linux-base/scripts/kconfig/merge_config.sh -m .config $frags)
        mk olddefconfig
        mk -j"$JOBS" Image modules
        [ "$(mk -s kernelrelease)" = 4.4.189-muos-r35s-p4 ]
        if [ "$MODE" = ref ]; then
            cp /work/kernel-output/Module.symvers /out/ref.Module.symvers
            cp /work/kernel-output/arch/arm64/boot/Image /out/ref.Image
            dtb /work/linux-base/arch/arm64/boot/dts/rockchip/rk3326-muos-r35s-panel0.dts /out/ref.dtb
        else
            cmp /work/kernel-output/Module.symvers /out/ref.Module.symvers
            cp /work/kernel-output/arch/arm64/boot/Image /out/Image
            cp /work/kernel-output/.config /out/kernel.config
            dtb /port/device/rk-r35s-p0/rk3326-muos-r35s-panel0.dts /out/rk3326-muos-r35s-panel0.dtb
        fi' > "$m3b/logs/kernel-$mode.log" 2>&1 || { tail -20 "$m3b/logs/kernel-$mode.log"; exit 1; }
    if [ "$mode" = ref ]; then
        [ "$(sha256sum < "$out/ref.Image" | cut -d' ' -f1)" = "$ref_image" ] || { echo 'kernel-ref: Image differs from the card' >&2; exit 1; }
        [ "$(sha256sum < "$out/ref.dtb" | cut -d' ' -f1)" = "$ref_dtb" ] || { echo 'kernel-ref: DTB differs from the card' >&2; exit 1; }
        echo 'kernel-ref: Image and DTB identical to the M2 card'
    else
        python3 "$repo/port/scripts/bootrec.py" image-fits "$out/Image"
        echo "kernel: Image $(sha256sum < "$out/Image" | cut -c1-16) DTB $(sha256sum < "$out/rk3326-muos-r35s-panel0.dtb" | cut -c1-16); Module.symvers = reference"
    fi
}

uboot() { # PROFILE=ref|boot
    local profile=$1 dir=$m3b/uboot-$1
    python3 "$repo/port/scripts/uboot-tree.py" "$profile" "$dir" > "$m3b/logs/uboot-$profile.log"
    # Same in-container path as the Phase 4 probe that built the card's U-Boot.
    ctr -v "$work/linaro6:/work/linaro6:ro,z" -v "$dir:/work/uboot-sd/probe.3utahq01:rw,z" \
        -e SOURCE_DATE_EPOCH="$(cat "$dir/source_date_epoch")" "$iid" sh -euc '
        export KBUILD_BUILD_USER=muos KBUILD_BUILD_HOST=r35s-port
        export CROSS_COMPILE=/work/linaro6/bin/aarch64-linux-gnu-
        s=/work/uboot-sd/probe.3utahq01
        cd $s/source
        make O=$s/output HOSTCFLAGS="-O2 -fcommon" muos_r35s_panel0_sd_defconfig
        make O=$s/output HOSTCFLAGS="-O2 -fcommon" -j6 u-boot.bin u-boot.dtb System.map u-boot.cfg
        cd $s && output/tools/loaderimage --pack --uboot output/u-boot.bin uboot.img 0x00200000 --size 1024 4
        ' >> "$m3b/logs/uboot-$profile.log" 2>&1 || { tail -20 "$m3b/logs/uboot-$profile.log"; exit 1; }
    if [ "$profile" = ref ]; then
        cmp "$dir/uboot.img" "$ref_uboot" || { echo 'uboot-ref: uboot.img differs from the card' >&2; exit 1; }
        echo 'uboot-ref: uboot.img identical to the M2 card'
    else
        grep -q ' do_muos_boot$' "$dir/output/System.map" || { echo 'uboot: muos_boot missing' >&2; exit 1; }
        cp "$dir/uboot.img" "$out/uboot.img"
        echo "uboot: uboot.img $(sha256sum < "$out/uboot.img" | cut -c1-16)"
    fi
}

case "${1:-}" in
kernel-ref) kernel ref ;;
kernel) [ -f "$out/ref.Module.symvers" ] || { echo 'run kernel-ref first' >&2; exit 1; }; kernel m3b ;;
uboot-ref) uboot ref ;;
uboot) uboot boot ;;
all) "$0" kernel; "$0" uboot ;;
*) sed -n '3,13p' "$0"; exit 2 ;;
esac
if [ -f "$out/Image" ] && [ -f "$out/uboot.img" ]; then
    (cd "$out" && sha256sum Image rk3326-muos-r35s-panel0.dtb uboot.img kernel.config > SHA256SUMS)
fi
