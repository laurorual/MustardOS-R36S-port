#!/usr/bin/env bash
# Separate candidate output; pinned providers, no device access or deployment.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
name=muos-r35s-phase4-graphics
case "${1:-status}" in
    fetch|build)
        stage=$1
        [[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
        for job in muos-r35s-phase4-core muos-r35s-phase4-rootfs muos-r35s-phase4-rootfs-legal muos-r35s-phase4-graphics-legal; do
            if podman container exists "$job"; then
                [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
            fi
        done
        [[ -f "$work/graphics-config/report.json" ]]
        if podman container exists "$name"; then
            [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
            podman rm "$name" >/dev/null
        fi
        python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import hashlib, json, sys
repo,work=map(Path,sys.argv[1:])
manifest=json.loads((work/'core/source-manifest.json').read_text())
assert (work/'core/source-manifest.json').read_bytes()==(work/'graphics-config/core-source-manifest.json').read_bytes(), 'Reconfigure graphics after changing the core source'
for name,sha in manifest['port_input_sha256'].items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha, name
patches=json.loads((work/'graphics-config/report.json').read_text()).get('global_patch_sha256',{})
assert set(patches)=={str(p.relative_to(repo)) for p in (repo/'port/patches/phase4-graphics').rglob('*.patch')}
for name,sha in patches.items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha,name
assert (work/'graphics-config/candidate.defconfig').read_bytes()==(
    (repo/'port/device/rk-r35s-p0/phase4-rootfs.defconfig').read_bytes()+
    (repo/'port/device/rk-r35s-p0/phase4-graphics.fragment').read_bytes())
PY
        network=none; target=all
        if [[ $stage == fetch ]]; then network=slirp4netns; target=source; fi
        if [[ $stage == build ]]; then [[ $(cat "$work/graphics-config/fetch.exit") == 0 ]]; fi
        python3 - "$work/graphics-config/$stage.exit" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
        epoch=$(git -C "$work/buildroot" show -s --format=%ct HEAD)
        podman run --detach --name "$name" --network="$network" --read-only \
            --cap-drop=all --security-opt=no-new-privileges --userns=keep-id --memory=12g --pids-limit=2048 \
            --tmpfs /tmp:rw,nosuid,nodev,size=2g -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
            -w /work/buildroot -e GRAPHICS_STAGE="$stage" -e GRAPHICS_TARGET="$target" \
            -e SOURCE_DATE_EPOCH="$epoch" "$(cat "$work/rootfs-container.iid")" sh -c '
            unset PKG_CONFIG_LIBDIR PKG_CONFIG_SYSROOT_DIR PKG_CONFIG_PATH
            if [ "$GRAPHICS_STAGE" = build ]; then
                make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot muos-core-dirclean \
                    > /work/graphics-config/build.log 2>&1 || exit 1
                # Build the real SDK providers first, then prove every mandatory
                # SDL KMSDRM GBM import before using the local version-floor patch.
                make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
                    BR2_JLEVEL=8 sdl2-depends >> /work/graphics-config/build.log 2>&1 || exit 1
                out=/work/graphics-config/output
                PKG_CONFIG_LIBDIR= PKG_CONFIG_SYSROOT_DIR= "$out/host/bin/pkg-config" --modversion gbm \
                    > /work/graphics-config/gbm-sdk-version.txt || exit 1
                "$out/host/bin/aarch64-buildroot-linux-gnu-gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
                    /port/probes/phase4-gbm-contract.c -Wl,-z,relro,-z,now \
                    $("$out/host/bin/pkg-config" --cflags --libs gbm) \
                    -o /work/graphics-config/gbm-contract >> /work/graphics-config/build.log 2>&1 || exit 1
                make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot sdl2-dirclean \
                    >> /work/graphics-config/build.log 2>&1 || exit 1
            fi
            make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot \
                BR2_DL_DIR=/work/rootfs-downloads BR2_JLEVEL=8 \
                BR2_WGET="wget -nd -t 3 --connect-timeout=10 --read-timeout=30" \
                "$GRAPHICS_TARGET" >> /work/graphics-config/"$GRAPHICS_STAGE".log 2>&1
            result=$?
            if [ "$result" = 0 ] && [ "$GRAPHICS_STAGE" = fetch ]; then
                printf "%s  %s\n" \
                    0647d3804fafeb4647af9c16a1182c98e9e45193fea377421517f795269f777e \
                    /work/rootfs-downloads/linux/d8402159c04b1044106b4f27b7ed7c22ed09228f.tar.gz \
                    | sha256sum -c >> /work/graphics-config/fetch.log 2>&1
                result=$?
            fi
            printf "%s\n" "$result" > /work/graphics-config/"$GRAPHICS_STAGE".exit
            exit "$result"
            '
        ;;
    status)
        if podman container exists "$name"; then
            podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$name"
            for stage in fetch build; do
                [[ ! -f "$work/graphics-config/$stage.log" ]] || tail -3 "$work/graphics-config/$stage.log" | cut -c1-180
            done
        else echo 'No graphics job; configure-phase4-graphics.sh, then fetch/build.'; fi
        ;;
    stop)
        podman stop --time=30 "$name"
        ;;
    *) echo 'Usage: fetch|build|status|stop' >&2; exit 2 ;;
esac
