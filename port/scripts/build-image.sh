#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M3a: build the whole firmware (p2 rootfs + card image) from one entry point.
#
#   build-image.sh prepare        configure build/m3a/output from firmware.defconfig
#   build-image.sh inputs         fill the content-addressed input store
#   build-image.sh source|build   Buildroot job (detached; source may use the network;
#                                 GOAL="pkg-reconfigure" runs that first in build)
#   build-image.sh status|stop
#   build-image.sh image NAME [--public]
#                                 card image dist/firmware/NAME.img.zst (+ .sha256, .manifest);
#                                 --public: no developer identity (firmware-image.sh)
#
# Buildroot runs in the phase4-rootfs container with build/phase4 read-only
# (only its download cache is writable) and the port tree read-only. Prebuilt
# inputs (kernel modules, muOS frontend, muxretro, cores, assets) are pinned
# by SHA256 in port/packaging/firmware-inputs.json and copied (reflink) into
# build/m3a/inputs/<sha256>, so old build/phase4 outputs can be retired.
# The image stage takes the bootloader prefix, p1 and p3 from the pinned M2
# recovery image and the private identity (host key, Wi-Fi config,
# authorized key) from its p2; the result is PRIVATE like the recovery images.
set -euo pipefail
export LC_ALL=C
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work=$repo/build/phase4 m3a=$repo/build/m3a out=$m3a/output
defconfig=$repo/port/device/rk-r35s-p0/firmware.defconfig
inputs=$repo/port/packaging/firmware-inputs.json
name=muos-r35s-firmware
br_rev=4f924fd52841608d68ac3dcb83fccee8b8c90316 # Buildroot 2025.02.19
base_img=$repo/dist/recovery/test128-m2-20261111.img.zst
base_raw=34beb417 # prefix of the M2 raw_sha256, checked against its manifest
mkdir -p "$m3a/logs"

running() { podman container exists "$name" && [ "$(podman inspect --format '{{.State.Running}}' "$name")" = true ]; }
iid() { cat "$work/rootfs-container.iid"; }
# shellcheck disable=SC2054 # commas are inside option values
ctr_opts() { # common options of every Buildroot container (never touches block devices)
    opts=(--read-only --cap-drop=all --security-opt=no-new-privileges --userns=keep-id
        --memory=12g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g
        -v "$work:/work:ro,z" -v "$work/rootfs-downloads:/work/rootfs-downloads:rw,z"
        -v "$m3a:/m3a:rw,z" -v "$repo/port:/port:ro,z" -w /work/buildroot
        -e SOURCE_DATE_EPOCH="$(git -C "$work/buildroot" show -s --format=%ct HEAD)")
}
make_args='O=/m3a/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads'
# SDL must register the pipewire driver (muOS runs SDL_AUDIODRIVER=pipewire);
# checked by running the target's own probe under qemu-user.
sdl_check='qemu-aarch64 -L /m3a/output/target /m3a/output/target/usr/libexec/muos-sdl-audio-probe --require pipewire'

stage_overlay() { # the port rootfs with its init-script symlinks resolved
    rm -rf "$m3a/overlay.tmp"
    cp -a -L --reflink=auto "$repo/port/device/rk-r35s-p0/rootfs" "$m3a/overlay.tmp"
    # M4f: upstream muOS scripts the pinned set lacked (hash-checked list).
    local want path src
    while read -r want path; do
        case "$want" in ''|'#'*) continue ;; esac
        src=$repo/refs/muos/internal/$path
        [ "$(sha256sum < "$src" | cut -d' ' -f1)" = "$want" ] ||
            { echo "stage_overlay: $src does not match $want" >&2; return 1; }
        install -D -m 0755 "$src" "$m3a/overlay.tmp/opt/muos/$path"
    done < "$repo/port/packaging/muos-internal-extra.txt"
    rm -rf "$m3a/overlay"; mv "$m3a/overlay.tmp" "$m3a/overlay"
}

case "${1:-status}" in
prepare)
    ! running || { echo 'a job is running' >&2; exit 1; }
    [ "$(git -C "$work/buildroot" rev-parse HEAD)" = "$br_rev" ]
    [ -z "$(git -C "$work/buildroot" status --porcelain --untracked-files=no)" ]
    stage_overlay
    cp "$defconfig" "$m3a/firmware.defconfig"
    ctr_opts
    podman run --rm --network=none "${opts[@]}" "$(iid)" sh -euc "make $make_args BR2_DEFCONFIG=/m3a/firmware.defconfig defconfig" \
        > "$m3a/logs/prepare.log" 2>&1
    # The resolved config must keep every option the defconfig asks for.
    while IFS= read -r l; do
        case "$l" in BR2_*=*) grep -qxF "$l" "$out/.config" || { echo "not applied: $l" >&2; exit 1; } ;; esac
    done < "$defconfig"
    echo "prepared $(grep -c '^BR2_PACKAGE_.*=y' "$out/.config") package options"
    ;;
inputs)
    python3 "$repo/port/scripts/firmware-inputs.py" store "$inputs" "$m3a/inputs"
    ;;
source|build)
    stage=$1
    ! running || { echo 'a job is running; use status' >&2; exit 1; }
    podman container exists "$name" && podman rm "$name" >/dev/null
    [ -f "$out/.config" ] || { echo 'run prepare first' >&2; exit 1; }
    cmp -s "$defconfig" "$m3a/firmware.defconfig" || { echo 'defconfig changed: run prepare' >&2; exit 1; }
    # GOAL: extra make goals before `all` (e.g. util-linux-reconfigure after a
    # package option changed; Buildroot doesn't rebuild a built package).
    net=none target="${GOAL:+$GOAL }all"
    if [ "$stage" = source ]; then net=pasta target=source; fi
    if [ "$stage" = build ]; then
        [ "$(cat "$m3a/logs/source.exit" 2>/dev/null)" = 0 ] || { echo 'run source first' >&2; exit 1; }
        stage_overlay
        python3 "$repo/port/scripts/firmware-inputs.py" verify "$inputs" "$m3a/inputs"
    fi
    avail=$(df --output=avail -k "$m3a" | tail -1)
    (( avail > 20 * 1024 * 1024 )) || { echo 'need 20 GiB free' >&2; exit 1; }
    rm -f "$m3a/logs/$stage.exit"
    ctr_opts
    podman run --detach --name "$name" --network="$net" "${opts[@]}" -e M3A_STAGE="$stage" \
        -e M3A_GOAL="$target" -e M3A_JOBS="${JOBS:-$(nproc)}" "$(iid)" sh -c "
        mk() { make $make_args BR2_JLEVEL=\$M3A_JOBS \
            BR2_WGET='wget --passive-ftp -nd -t 3 --connect-timeout=10 --read-timeout=30' \
            \"\$@\" >> /m3a/logs/\$M3A_STAGE.log 2>&1; }
        : > /m3a/logs/\$M3A_STAGE.log; mk \$M3A_GOAL; r=\$?
        # pipewire depends on sdl2, so a clean build configures SDL2 before
        # PipeWire is in staging and SDL2 drops its pipewire audio driver
        # (silent M3a). Rebuild SDL2 from scratch once PipeWire is there:
        # sdl2-reconfigure is not enough, Buildroot's
        # --disable-dependency-tracking leaves SDL_audio.o (the driver table)
        # stale.
        if [ \$r = 0 ] && [ \$M3A_STAGE = build ] && ! $sdl_check >> /m3a/logs/build.log 2>&1; then
            echo '>>> m3a: SDL2 lacks pipewire: sdl2-dirclean + rebuild' >> /m3a/logs/build.log
            mk sdl2-dirclean && mk all; r=\$?
            [ \$r != 0 ] || $sdl_check >> /m3a/logs/build.log 2>&1 || r=1
        fi
        echo \$r > /m3a/logs/\$M3A_STAGE.exit; exit \$r" >/dev/null
    echo "started $stage; use: build-image.sh status"
    ;;
status)
    if podman container exists "$name"; then
        podman inspect --format '{{if .State.Running}}running{{else}}exited={{.State.ExitCode}}{{end}} since={{.State.StartedAt}}' "$name"
        for s in source build; do
            [ -f "$m3a/logs/$s.log" ] || continue
            printf '%s: exit=%s last=%s\n' "$s" "$(cat "$m3a/logs/$s.exit" 2>/dev/null || echo pending)" \
                "$(grep '^>>>' "$m3a/logs/$s.log" | tail -1 | cut -c1-120)"
        done
    else
        echo 'no job container'
    fi
    ;;
stop) podman stop --time=30 "$name" ;;
image)
    variant=developer
    [ "${3:-}" = --public ] && variant=public
    [ $# -eq 2 ] || [ "$variant" = public ] || { echo 'usage: image NAME [--public]' >&2; exit 2; }
    ctr_opts
    podman run --rm --network=none "${opts[@]}" "$(iid)" sh -c "$sdl_check" ||
        { echo 'SDL2 lacks the pipewire audio driver: rebuild' >&2; exit 1; }
    [ -f "$repo/build/m3b/boot/SHA256SUMS" ] || { echo 'run build-boot.sh all first' >&2; exit 1; }
    exec bash "$repo/port/scripts/firmware-image.sh" "$out/images/rootfs.ext4" "$base_img" "$base_raw" \
        "$repo/dist/firmware/$2.img.zst" "$repo/build/m3b/boot" "$variant"
    ;;
*) sed -n '3,10p' "$0"; exit 2 ;;
esac
