#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M9 item 5: write the third-party notice shipped in the image
# (rootfs/usr/share/muos-r35s/THIRD-PARTY.txt) from the pinned sources.
#   third-party.sh   rewrite it (run after changing a pin; commit the result)
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
out=$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/THIRD-PARTY.txt
declare -A lic=([picante8]=GPL-3.0 [fake08]="MIT (z8lua MIT)" [snes9x2005]="Snes9x licence (non-commercial)" [gpsp]=GPL-2.0 [picodrive]="PicoDrive licence (non-commercial)"
  [pcsx_rearmed]=GPL-2.0 [stella2014]=GPL-2.0 [prosystem]=GPL-2.0 [handy]=Zlib [pce_fast]=GPL-2.0 [ngp]=GPL-2.0
  [wswan]=GPL-2.0 [bluemsx]=GPL-2.0 [gearcoleco]=GPL-3.0 [gearsystem]=GPL-3.0 [pokemini]=GPL-3.0
  [fbneo]="FBNeo licence (non-commercial)" [mame2003_plus]="MAME licence (non-commercial)" [mupen64plus_next]=GPL-2.0
  [dosbox_pure]=GPL-2.0 [flycast]=GPL-2.0 [ppsspp]=GPL-2.0+ [flycast2]=GPL-2.0 [ppsspp2021]=GPL-2.0+
  [melonds]=GPL-3.0 [flycast2022]=GPL-2.0 [yabasanshiro]=GPL-2.0 [gambatte]=GPL-2.0 [fceumm]=GPL-2.0)
rev() { awk -v p="$1" '$1 == p {print $2}' "$repo/docs/upstream-revisions.txt"; }
{
cat <<EOF
MustardOS for R36S/R35S (unofficial port): third-party components
==================================================================
This firmware is an UNOFFICIAL port of MustardOS (muOS) to the R36S/R35S.
It is not made, approved or supported by the MustardOS team: ask for
help at https://github.com/laurorual/MustardOS-R36S-port, not on the
MustardOS channels.

Each component keeps its own licence (details: docs/LICENSING.md in the
repository). GPL/LGPL sources: the exact revisions below, the port's
patches and build scripts are published as the source bundle of every
release on the project's GitHub page (also on request for three years
after the last release). Non-commercial licences (marked) forbid selling
this firmware or bundling it with a commercial product.

Closed components without published terms (Mali userspace, DraStic, the
DraStic hook and layout art) are included as other community firmwares
(dArkOS, ArkOS) do, with credit to their authors. Authors who want a
component removed: open an issue on the project page and it is removed
in the next release.

System
- MustardOS frontend, GPL-3.0: https://github.com/MustardOS/frontend $(rev refs/muos/frontend)
- MustardOS internal scripts and share data, GPL-3.0: https://github.com/MustardOS/internal $(rev refs/muos/internal)
- MustardOS language pack, GPL-3.0: https://github.com/MustardOS/language ($(sed -n 's/^release //p' "$repo/port/packaging/muos-language.txt"))
- MustardOS themes (MustardOS, C64, Dracula, GB Dark, Orange, mubiOS), sounds, glyphs and the press-kit boot screen
  (the boot logo, with the port's text added below the badge), CC BY-NC 4.0
  (https://muos.dev/press), included with the MustardOS team's permission. Credits: MustardOS theme by
  Bitter Bizarro (boot logo LMarcoMiranda, icon glyphs Line Icons 5, overlay indicators AntiKk, navigation
  sounds Aedilic Inc.); C64, Dracula and Orange by antiKk; GB Dark by inteLLiAim (original: Alukim);
  mubiOS by RazamaBazakart.
- Linux kernel 4.4 (rk351 BSP), GPL-2.0: https://github.com/christianhaitian/linux $(git -C "$repo/build/phase4/linux-base" rev-parse HEAD 2>/dev/null || echo see-build-boot.sh)
- U-Boot, GPL-2.0+: https://github.com/christianhaitian/RG351MP-u-boot 5606e804ffe8f9e5427d55c8da04c638f01a9391 + the port's patches
- Rockchip rkbin boot payloads (DDR init, miniloader, BL31, BL32), rkbin LICENSE: https://github.com/rockchip-linux/rkbin
- Buildroot 2025.02 root filesystem packages: licences and sources per package (Buildroot legal-info in the source bundle)
- Mali-G31 r13p0 userspace driver (c) Arm Limited, as published by Hardkernel for the ODROID-GO Advance
  (rk3326_r13p0_gbm_with_vulkan_and_cl.zip), unmodified; proprietary, no terms were supplied with it
- Fonts: Noto Sans SC/TC/JP/KR (SIL OFL-1.1), M+ (M+ FONT LICENSE), shipped by MustardOS
- Model device trees (experimental, $(grep -vc '^#' "$repo/port/packaging/models.txt") R36S models): from dArkOSen (MIT, https://github.com/djparentx/dArkOSen-R36S
  $(awk '$1 == "refs/darkosen" {print substr($2, 1, 12)}' "$repo/docs/upstream-revisions.txt")) with the port's changes; derived from the GPL-2.0 kernel device trees, their source is in the bundle
- Wi-Fi firmware for the mainline USB drivers (mt7601u, rt2800usb, rt73usb, rtl8192cu, r8712u, r8723au):
  linux-firmware $(awk '$1 == "tag" {print $2}' "$repo/port/packaging/wifi-firmware.txt"), unmodified, (c) MediaTek/Ralink and Realtek, redistributable
  (LICENCE.ralink-firmware.txt, LICENCE.ralink_a_mediatek_company_firmware, LICENCE.rtlwifi_firmware.txt
  in /usr/share/licenses/linux-firmware): https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git
- PortMaster is NOT included: Applications -> PortMaster downloads it on its first start from
  https://github.com/PortsMaster/PortMaster-GUI (MIT; its tools carry their own licences in
  MUOS/PortMaster/licenses); its runtimes and ports come from the PortMaster project and their authors

Libretro cores
EOF
bash -c 'source <(sed -n "/^table()/,/^}/p" "$1"); table' _ "$repo/port/scripts/build-cores.sh" |
while read -r n url commit _; do echo "- $n, ${lic[$n]:-see source}: $url $commit"; done
cat <<EOF

Standalone emulators
- Mupen64Plus (core, ui-console, audio/input-sdl, rsp-hle, video-rice) and GLideN64, GPL-2.0: https://github.com/mupen64plus, https://github.com/gonetz/GLideN64 (revisions in build-mupen64plus-sa.sh)
- PPSSPP standalone v1.20.4 and v1.12.3, GPL-2.0+: https://github.com/hrydgard/ppsspp (built as dArkOS builds it, with its patches)
- Flycast standalone v2.7, GPL-2.0: https://github.com/flyinghead/flycast (built from source as dArkOS builds it)
- YabaSanshiro standalone, GPL-2.0: https://github.com/christianhaitian/yabasanshiro-standalone c7618d2ecbf77b1e8188fa8af4fa1cfb34833a72 (Boost 1.83.0 static, BSL-1.0)
- ScummVM v2026.4.0 (standalone and libretro core), GPL-3.0+: https://github.com/scummvm/scummvm $(git -C "$repo/build/scummvm-src" rev-parse HEAD 2>/dev/null) (libogg, libvorbis, FLAC: BSD-3-Clause)
- DraStic r2.5.2.2 (c) Exophase, freeware, closed source, unmodified: https://drastic-ds.com
- advanced_drastic hook libadvdrastic.so (trngaje, based on steward-fu's drastic-steward work), no licence file:
  https://github.com/trngaje/advanced_drastic d445a56349cce68f5337d02c9fe890de9d390f3f (libjson-c: MIT)
- DraStic 640x480 layout art by steward-fu, via https://github.com/trngaje/drastic_layout e8dc3eb5bb51351bf3e93229e388ae9e5fea9adc
EOF
} > "$out"
echo "wrote ${out#"$repo"/} ($(wc -l < "$out") lines)"
