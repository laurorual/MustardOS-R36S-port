#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M9 item 5: write the third-party notice shipped in the image
# (rootfs/usr/share/muos-r35s/THIRD-PARTY.txt) from the pinned sources.
#   third-party.sh   rewrite it (run after changing a pin; commit the result)
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
out=$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/THIRD-PARTY.txt
declare -A lic=([snes9x2005]="Snes9x licence (non-commercial)" [gpsp]=GPL-2.0 [picodrive]="PicoDrive licence (non-commercial)"
  [pcsx_rearmed]=GPL-2.0 [stella2014]=GPL-2.0 [prosystem]=GPL-2.0 [handy]=Zlib [pce_fast]=GPL-2.0 [ngp]=GPL-2.0
  [wswan]=GPL-2.0 [bluemsx]=GPL-2.0 [gearcoleco]=GPL-3.0 [gearsystem]=GPL-3.0 [pokemini]=GPL-3.0
  [fbneo]="FBNeo licence (non-commercial)" [mame2003_plus]="MAME licence (non-commercial)" [mupen64plus_next]=GPL-2.0
  [dosbox_pure]=GPL-2.0 [flycast]=GPL-2.0 [ppsspp]=GPL-2.0+ [flycast2]=GPL-2.0 [ppsspp2021]=GPL-2.0+
  [melonds]=GPL-3.0 [flycast2022]=GPL-2.0 [yabasanshiro]=GPL-2.0)
rev() { awk -v p="$1" '$1 == p {print $2}' "$repo/docs/upstream-revisions.txt"; }
{
cat <<EOF
muOS for R36S/R35S (unofficial port): third-party components
=============================================================
Each component keeps its own licence. GPL/LGPL sources: the exact
revisions below, the port's patches and build scripts are published with
the release (source bundle on the project's GitHub page; on request for
three years after the last release, see the project page). Non-commercial
licences (marked) forbid selling this firmware or bundling it with a
commercial product.

System
- MustardOS frontend, GPL-3.0: https://github.com/MustardOS/frontend $(rev refs/muos/frontend)
- MustardOS internal scripts and share data, GPL-3.0: https://github.com/MustardOS/internal $(rev refs/muos/internal)
- MustardOS language pack, GPL-3.0: https://github.com/MustardOS/language ($(sed -n 's/^release //p' "$repo/port/packaging/muos-language.txt"))
- Linux kernel 4.4 (rk351 BSP), GPL-2.0: https://github.com/christianhaitian/linux $(git -C "$repo/build/phase4/linux-base" rev-parse HEAD 2>/dev/null || echo see-build-boot.sh)
- U-Boot, GPL-2.0+: built by port/scripts/build-phase4-uboot-sd.sh (source and patches in the bundle)
- Rockchip rkbin boot payloads (DDR init, miniloader, BL31, BL32), rkbin LICENSE: https://github.com/rockchip-linux/rkbin
- Buildroot 2025.02 root filesystem packages: licences and sources per package (Buildroot legal-info in the source bundle)
- Mali-G31 r13p0 userspace driver, Hardkernel/Arm (redistribution terms pending; not in the public image until answered)
- Fonts: Noto Sans SC/TC/JP/KR (SIL OFL-1.1), M+ (M+ FONT LICENSE), shipped by MustardOS

Libretro cores
EOF
bash -c 'source <(sed -n "/^table()/,/^}/p" "$1"); table' _ "$repo/port/scripts/build-cores.sh" |
while read -r n url commit _; do echo "- $n, ${lic[$n]:-see source}: $url $commit"; done
cat <<EOF

Standalone emulators
- Mupen64Plus (core, ui-console, audio/input-sdl, rsp-hle, video-rice) and GLideN64, GPL-2.0: https://github.com/mupen64plus, https://github.com/gonetz/GLideN64 (revisions in build-mupen64plus-sa.sh)
- PPSSPP standalone v1.12.3 and v1.20.4, GPL-2.0+: https://github.com/hrydgard/ppsspp
- Flycast standalone (dArkOSen build), GPL-2.0: https://github.com/flyinghead/flycast
- YabaSanshiro standalone (dArkOSen build), GPL-2.0: https://github.com/devmiyax/yabause
- ScummVM v2026.4.0, GPL-3.0+: https://github.com/scummvm/scummvm $(git -C "$repo/build/scummvm-src" rev-parse HEAD 2>/dev/null)
- DraStic r2.5.2.2 (Exophase), freeware, closed source (redistribution permission pending)
- advanced_drastic hook (trngaje) and drastic_layout art (steward-fu, trngaje), no licence file (permission pending):
  https://github.com/trngaje/advanced_drastic d445a56349cce68f5337d02c9fe890de9d390f3f
  https://github.com/trngaje/drastic_layout e8dc3eb5bb51351bf3e93229e388ae9e5fea9adc
EOF
} > "$out"
echo "wrote ${out#"$repo"/} ($(wc -l < "$out") lines)"
