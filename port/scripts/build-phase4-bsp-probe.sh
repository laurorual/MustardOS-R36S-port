#!/usr/bin/env bash
# Build isolated kernel evidence. Never deploy or access a block device.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
output="$repo/dist/phase4/bsp-probe"
lock="$repo/port/device/rk-r35s-p0/phase4-sources.json"
mkdir -p "$work" "$output"
read_lock() {
    python3 - "$lock" "$1" "$2" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))[sys.argv[2]][sys.argv[3]])
PY
}
fetch_source() {
    local destination=$1 url=$2 revision=$3
    if [[ ! -d "$destination/.git" ]]; then
        git init "$destination"
        git -C "$destination" remote add origin "$url"
    fi
    if ! git -C "$destination" cat-file -e "$revision^{commit}" 2>/dev/null; then
        git -C "$destination" fetch --depth=1 origin "$revision"
    fi
    git -C "$destination" checkout --detach "$revision"
    [[ $(git -C "$destination" rev-parse HEAD) == "$revision" ]]
    [[ -z $(git -C "$destination" status --porcelain --untracked-files=no) ]]
}
fetch_source "$work/linux-base" "$(read_lock linux url)" "$(read_lock linux revision)"
fetch_source "$work/linaro6" "$(read_lock kernel_compiler url)" "$(read_lock kernel_compiler revision)"
git -C "$work/linux-base" submodule update --init --depth=1 fs/exfat
[[ $(git -C "$work/linux-base/fs/exfat" rev-parse HEAD) == "$(read_lock exfat revision)" ]]
parent_id=$(podman image inspect --format '{{.Id}}' "$(read_lock container_parent tag)")
expected_parent=$(read_lock container_parent image_id)
[[ ${parent_id#sha256:} == "${expected_parent#sha256:}" ]]
podman build --pull=never --iidfile "$work/kernel-container.iid" \
    -t localhost/muos-r35s-phase4-kernel:20261024 \
    -f "$repo/port/packaging/phase4-kernel.Containerfile" "$repo/port/packaging" \
    > "$work/container-build.log" 2>&1
cp "$repo/port/device/rk-r35s-p0/phase4-bsp.fragment" "$work/probe.fragment"
cp "$repo/port/device/rk-r35s-p0/rk3326-muos-r35s-panel0.dts" \
    "$work/linux-base/arch/arm64/boot/dts/rockchip/"
epoch=$(git -C "$work/linux-base" show -s --format=%ct HEAD)
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
    -e SOURCE_DATE_EPOCH="$epoch" -e PHASE4_JOBS="${PHASE4_JOBS:-6}" \
    -w /work/linux-base "$(cat "$work/kernel-container.iid")" sh -eu -c '
    export ARCH=arm64 CROSS_COMPILE=/work/linaro6/bin/aarch64-linux-gnu-
    # The in-tree esp8089 Makefile needs an explicit out-of-tree config path.
    export KBUILD=/work/kernel-output
    export KBUILD_BUILD_USER=muos KBUILD_BUILD_HOST=r35s-port KBUILD_BUILD_VERSION=1
    export KBUILD_BUILD_TIMESTAMP="$(date -u --date="@$SOURCE_DATE_EPOCH" "+%a %b %d %T UTC %Y")"
    /work/linaro6/bin/aarch64-linux-gnu-gcc --version > /work/kernel-compiler.txt
    make O=/work/kernel-output HOSTCFLAGS="-O2 -fcommon" rg351p_tweaked_defconfig
    cd /work/kernel-output
    /work/linux-base/scripts/kconfig/merge_config.sh -m .config /work/probe.fragment
    cd /work/linux-base
    make O=/work/kernel-output HOSTCFLAGS="-O2 -fcommon" olddefconfig
    make O=/work/kernel-output HOSTCFLAGS="-O2 -fcommon" -j"$PHASE4_JOBS" \
        Image modules rockchip/rk3326-r35s-linux.dtb rockchip/rk3326-muos-r35s-panel0.dtb
    make O=/work/kernel-output HOSTCFLAGS="-O2 -fcommon" \
        INSTALL_MOD_PATH=/work/probe-modules INSTALL_MOD_STRIP=1 modules_install
    make -s O=/work/kernel-output kernelrelease > /work/kernel-release.txt
    /work/linaro6/bin/aarch64-linux-gnu-readelf -h /work/kernel-output/vmlinux > /work/vmlinux.elf.txt
    cp /usr/local/share/phase4-packages.txt /work/kernel-packages.txt
    ' > "$work/kernel-build.log" 2>&1
release=$(cat "$work/kernel-release.txt")
[[ $release == 4.4.189-muos-r35s-p4 ]]
cp "$work/kernel-output/arch/arm64/boot/Image" "$output/"
cp "$work/kernel-output/arch/arm64/boot/dts/rockchip/rk3326-r35s-linux.dtb" "$output/"
cp "$work/kernel-output/arch/arm64/boot/dts/rockchip/rk3326-muos-r35s-panel0.dtb" "$output/"
cp "$repo/port/device/rk-r35s-p0/rk3326-muos-r35s-panel0.dts" "$output/"
cp "$work/kernel-output/.config" "$output/kernel.config"
cp "$work/linux-base/COPYING" "$output/COPYING.linux"
cp "$lock" "$output/sources.json"
cp "$work/kernel-release.txt" "$work/kernel-compiler.txt" "$work/kernel-packages.txt" \
    "$work/vmlinux.elf.txt" "$output/"
rm -f "$work/probe-modules/lib/modules/$release/build" "$work/probe-modules/lib/modules/$release/source"
tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner \
    -C "$work/probe-modules" -czf "$output/modules.tar.gz" lib
printf '%s\n' 'HOST BUILD PROBE ONLY. The port Panel 0 DTB has NOT been boot-tested.' \
    'The generic R35S DTB is included only for comparison.' \
    'No bootloader, firmware rootfs, proven GPU userspace or boot configuration is included.' \
    'Do not copy this package to the test device.' > "$output/NOT-FOR-DEVICE-BOOT.txt"
tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner -C "$repo" \
    -czf "$output/port-source.tar.gz" \
    port/packaging/phase4-kernel.Containerfile \
    port/device/rk-r35s-p0/phase4-bsp.fragment \
    port/device/rk-r35s-p0/phase4-sources.json \
    port/device/rk-r35s-p0/phase4-rootfs.defconfig \
    port/device/rk-r35s-p0/rk3326-muos-r35s-panel0.dts \
    port/scripts/build-phase4-bsp-probe.sh \
    port/scripts/configure-phase4-rootfs.sh port/scripts/verify-phase4-dtb.py
python3 - "$repo" "$work" "$output" "$epoch" <<'PY'
from pathlib import Path
import hashlib, json, sys, tarfile
repo, work, output = map(Path, sys.argv[1:4])
with tarfile.open(output / 'port-source.tar.gz') as archive:
    hashes = {item.name: hashlib.sha256(archive.extractfile(item).read()).hexdigest()
              for item in archive if item.isfile()}
manifest = {'purpose': 'host-only BSP probe', 'boot_tested': False,
            'installed_kernel_reproduced': False, 'rootfs_built': False,
            'kernel_release': (work / 'kernel-release.txt').read_text().strip(),
            'container_image_id': (work / 'kernel-container.iid').read_text().strip(),
            'source_date_epoch': int(sys.argv[4]), 'port_source_sha256': hashes,
            'source_lock': json.loads((output / 'sources.json').read_text())}
(output / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
(cd "$output" && sha256sum Image rk3326-r35s-linux.dtb rk3326-muos-r35s-panel0.dtb \
    rk3326-muos-r35s-panel0.dts kernel.config COPYING.linux \
    sources.json kernel-release.txt kernel-compiler.txt kernel-packages.txt vmlinux.elf.txt \
    modules.tar.gz NOT-FOR-DEVICE-BOOT.txt port-source.tar.gz build-manifest.json > SHA256SUMS)
printf 'Host BSP probe artifacts: %s\n' "$output"
