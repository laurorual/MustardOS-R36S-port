#!/usr/bin/env bash
# Resolve/check the headless rootfs configuration; do not build or deploy it.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
if [[ -f "$work/core/active" ]]; then
    echo 'The additive core profile is active; use build-phase4-core.sh.' >&2
    exit 1
fi
revision=4f924fd52841608d68ac3dcb83fccee8b8c90316 # Buildroot 2025.02.19
if podman container exists muos-r35s-phase4-rootfs &&
    [[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-rootfs) == true ]]; then
    echo 'Refusing to reconfigure while a rootfs job is running.' >&2
    exit 1
fi
if [[ -f "$work/rootfs-output/build/build-time.log" && -f "$work/headless.defconfig" ]] &&
    ! cmp -s "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" "$work/headless.defconfig"; then
    echo 'Defconfig changed after package builds began. Preserve output and use a clean build directory.' >&2
    exit 1
fi
if [[ ! -d "$work/buildroot/.git" ]]; then
    git init "$work/buildroot"
    git -C "$work/buildroot" remote add origin https://github.com/buildroot/buildroot.git
fi
if ! git -C "$work/buildroot" cat-file -e "$revision^{commit}" 2>/dev/null; then
    git -C "$work/buildroot" fetch --depth=1 origin "$revision"
fi
git -C "$work/buildroot" checkout --detach "$revision"
[[ -z $(git -C "$work/buildroot" status --porcelain --untracked-files=no) ]]
cp "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" "$work/headless.defconfig"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
    -w /work/buildroot "$(cat "$work/kernel-container.iid")" sh -eu -c '
    make O=/work/rootfs-output BR2_DEFCONFIG=/work/headless.defconfig defconfig
    make O=/work/rootfs-output BR2_DEFCONFIG=/work/rootfs-resolved.defconfig savedefconfig
    ' > "$work/rootfs-configure.log" 2>&1
python3 - "$work/rootfs-output/.config" "$work/headless.defconfig" <<'PY'
from pathlib import Path
import sys
config = dict(line.split('=', 1) for line in Path(sys.argv[1]).read_text().splitlines()
              if line.startswith('BR2_') and '=' in line)
required = ['BR2_aarch64', 'BR2_cortex_a35', 'BR2_TOOLCHAIN_BUILDROOT_GLIBC',
            'BR2_GCC_VERSION_13_X', 'BR2_INIT_BUSYBOX',
            'BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_EUDEV', 'BR2_PACKAGE_DBUS',
            'BR2_PACKAGE_PIPEWIRE', 'BR2_PACKAGE_WIREPLUMBER',
            'BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_4_4', 'BR2_TARGET_ROOTFS_EXT2_4']
for key in required:
    assert config.get(key) == 'y', (key, config.get(key))
for line in Path(sys.argv[2]).read_text().splitlines():
    if line.startswith('BR2_') and '=' in line:
        key, expected = line.split('=', 1)
        assert config.get(key) == expected, (key, expected, config.get(key))
assert config['BR2_TOOLCHAIN_HEADERS_AT_LEAST'] == '"4.4"'
assert not any(config.get(key) == 'y' for key in
               ['BR2_LINUX_KERNEL', 'BR2_PACKAGE_SDL2', 'BR2_PACKAGE_ROCKCHIP_MALI'])
print('Headless Kconfig validated; this script only configures and does not build')
PY
