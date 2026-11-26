#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# v1.1.1: build port/utils/muos-levelbar.c (the volume/brightness bar that
# muos-frontend preloads into ports, applications and the official PICO-8)
# with the SDK's cross compiler, offline, into
# build/m12/levelbar/tree/usr/lib/muos-levelbar.so. The image takes it as a
# pinned input:
#   firmware-inputs.py pin-file port/packaging/firmware-inputs.json \
#       /usr/lib/muos-levelbar.so build/m12/levelbar/tree/usr/lib/muos-levelbar.so
#   firmware-inputs.py store port/packaging/firmware-inputs.json build/m3a/inputs
# Quick test: device.sh push it to /run and bind-mount it over the file.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
gfx=$repo/build/phase4/graphics-config
out=$repo/build/m12/levelbar/tree/usr/lib
log=$repo/build/logs/levelbar-build.log
iid=$(cat "$repo/build/phase4/rootfs-container.iid")
mkdir -p "$out" "${log%/*}"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev \
    -v "$gfx/output/host:/work/graphics-config/output/host:ro,z" \
    -v "$repo/port/utils:/src:ro,z" -v "$out:/out:rw,z" "$iid" sh -euc '
    cc=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-gcc
    $cc -mcpu=cortex-a35 -std=c11 -O2 -pipe -Wall -Wextra -Werror -fstack-protector-strong \
        -D_FORTIFY_SOURCE=2 -fno-ident -shared -fPIC -fvisibility=default \
        /src/muos-levelbar.c -o /out/muos-levelbar.so.tmp -ldl -Wl,-z,relro,-z,now -s
    mv /out/muos-levelbar.so.tmp /out/muos-levelbar.so' > "$log" 2>&1 || { tail -30 "$log" >&2; exit 1; }
l=$out/muos-levelbar.so
echo "muos-levelbar.so: $(sha256sum "$l" | cut -c1-16) ($(stat -c %s "$l") bytes)"
