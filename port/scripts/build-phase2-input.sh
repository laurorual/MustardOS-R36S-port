#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase2-input"
output="$repo/dist/phase2-input"
revision=5e8635b3b485eec9ad2ace141c415fd2df47d8f1
mkdir -p "$work/source" "$output"
git -C "$repo/refs/muos/frontend" archive "$revision" input LICENSE > "$work/upstream-source.tar"
tar -xf "$work/upstream-source.tar" -C "$work/source"
git -C "$repo" apply --directory=build/phase2-input/source "$repo/port/patches/0002-muinput-r35s-panel0-profile.patch"
epoch=$(git -C "$repo/refs/muos/frontend" show -s --format=%ct "$revision")
image=$(podman image inspect localhost/muos-r35s-phase1-toolchain:20261023 --format '{{.Id}}')
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,Z" \
    -w /work/source/input -e SOURCE_DATE_EPOCH="$epoch" "$image" sh -eu -c '
    flags="-std=c11 -O2 -pipe -flto=auto -ffunction-sections -fdata-sections -fstack-protector-strong -D_FORTIFY_SOURCE=3 -D_GNU_SOURCE -DNDEBUG -Wall -Wextra -Wpedantic -march=armv8-a -fPIE -ffile-prefix-map=/work=."
    make -B -j2 CC=aarch64-linux-gnu-gcc CFLAGS="$flags" LDFLAGS="-flto=auto -Wl,--gc-sections -pie -Wl,-z,relro,-z,now" BUILDDIR=/work/objects
    aarch64-linux-gnu-readelf -h -l -d -n --version-info /work/objects/bin/muinput > /work/elf.txt
    aarch64-linux-gnu-readelf --dyn-syms --wide /work/objects/bin/muinput > /work/symbols.txt
    ' > "$work/compile.log" 2>&1
cp "$work/objects/bin/muinput" "$output/"
cp "$work/elf.txt" "$work/symbols.txt" "$work/upstream-source.tar" "$output/"
cp "$work/source/LICENSE" "$output/LICENSE.upstream"
cp "$repo/port/patches/0002-muinput-r35s-panel0-profile.patch" "$output/"
cp "$repo/port/device/rk-r35s-p0/input-profile.json" "$output/"
printf 'upstream_revision=%s\ntoolchain_image_id=%s\n' "$revision" "$image" > "$output/build-manifest.txt"
(
    cd "$output"
    sha256sum muinput elf.txt symbols.txt upstream-source.tar LICENSE.upstream *.patch build-manifest.txt input-profile.json > SHA256SUMS
)
printf 'R35S input build: %s\n' "$output"
