#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Install the latest FCEUmm build (build-phase4-nes-core.py) as the muOS NES
# core, its MIT demo cartridge and any private ROMs in port/roms/nes/ (Git-
# ignored, never in images for distribution) into p3 ROMS/NES/.
#   install-nes.sh [BUILD_STAGE_DIR]
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
stage=${1:-$(cat "$repo/build/phase4/nes-core/latest")}
core=$(find "$stage" -maxdepth 2 -name fceumm_libretro.so | head -n1)
rom=$stage/r35s-flight.nes
[ -f "$core" ] && [ -f "$rom" ] || { echo "no core/ROM in $stage" >&2; exit 1; }
tree=$repo/build/m2/nes-tree
rm -rf "$tree"; mkdir -p "$tree/opt/muos/share/core"
cp "$core" "$tree/opt/muos/share/core/fceumm_libretro.so"
"$repo/port/scripts/install-rootfs.sh" --tree "$tree"
rm -rf "$repo/build/m2/nes-rom"; mkdir -p "$repo/build/m2/nes-rom/NES"; cp "$rom" "$repo/build/m2/nes-rom/NES/"
for f in "$repo"/port/roms/nes/*.nes; do [ -f "$f" ] && cp "$f" "$repo/build/m2/nes-rom/NES/"; done
"$repo/port/scripts/device.sh" push "$repo/build/m2/nes-rom/NES" /userdata/ROMS
"$repo/port/scripts/device.sh" run 'chmod 755 /userdata/ROMS/NES; chmod 644 /userdata/ROMS/NES/*; sync; sha256sum /opt/muos/share/core/fceumm_libretro.so /userdata/ROMS/NES/*.nes | cut -c1-16,65-'
