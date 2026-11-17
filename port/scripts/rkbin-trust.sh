#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M4d (decision 3): rebuild the card's trust image (sector 24576) from
# rkbin payloads and prove it equals the one every image ships.
#
#   rkbin-trust.sh [IMAGE.img.zst]   (default: the M2 base image)
#
# BL31 = rkbin efff42ab bin/rk33/rk3326_bl31_v1.14.elf (sha256 372d717c…,
# fetched once into build/m4d/rkbin with rkbin's LICENSE); BL32 v1.10 =
# rkbin a92d5e7d (identical to the pinned U-Boot-tree file). The U-Boot
# tree's BL31 differs only in debug sections: its LOAD segments are the
# same bytes, so trust_merger (built from the pinned U-Boot sources, run in
# the Phase 4 kernel container) produces the same trust.img.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
img=${1:-$repo/dist/recovery/test128-m2-20261111.img.zst}
rk=$repo/build/m4d/rkbin bl31_rev=efff42ab1b9c314c56f7b95ba77bf823534efd7e
bl31_sha=372d717c4965842f73f24279569fcfa3bd00b3a0a442e1d592c081393bfb2927
pkg=$repo/build/phase4/uboot-sd/probe.3utahq01/package.ou1j44x6
merger=$repo/build/m3b/uboot-boot/output/tools/trust_merger
ctr=sha256:3cd1cfa51f9ac90aa5ce793a2274d982b62c240c2897808e582e11fcc7737f49
mkdir -p "$rk"
if [ ! -f "$rk/rk3326_bl31_v1.14.elf" ]; then
    curl -fsSL -o "$rk/bl31.part" "https://raw.githubusercontent.com/rockchip-linux/rkbin/$bl31_rev/bin/rk33/rk3326_bl31_v1.14.elf"
    mv "$rk/bl31.part" "$rk/rk3326_bl31_v1.14.elf"
fi
[ -f "$rk/LICENSE" ] || curl -fsSL -o "$rk/LICENSE" https://raw.githubusercontent.com/rockchip-linux/rkbin/master/LICENSE
echo "$bl31_sha  $rk/rk3326_bl31_v1.14.elf" | sha256sum -c --quiet
w=$(mktemp -d "$repo/build/m4d/trust.XXXXXX"); trap 'rm -rf "$w"' EXIT
mkdir "$w/payloads"
cp "$rk/rk3326_bl31_v1.14.elf" "$pkg/payloads/rk3326_bl32_v1.10.bin" "$w/payloads/"
cp "$pkg/RK3326TRUST.ini" "$merger" "$w/"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$w:/w:rw,z" -w /w "$ctr" \
    sh -c './trust_merger --rsa 3 --sha 3 --size 2048 2 RK3326TRUST.ini > trust-pack.log 2>&1'
size=$(stat -c %s "$w/trust.img")
# dd stops early: zstd gets SIGPIPE, which pipefail must not count.
card=$(set +o pipefail; zstd -q -dc --long=27 "$img" 2>/dev/null | dd bs=512 skip=24576 count=$((size / 512)) status=none | sha256sum | cut -d' ' -f1)
built=$(sha256sum "$w/trust.img" | cut -d' ' -f1)
echo "trust from rkbin: $built"
echo "trust in image:   $card ($(basename "$img"))"
[ "$built" = "$card" ] && echo 'PASS: identical' || { echo 'FAIL: differs'; exit 1; }
