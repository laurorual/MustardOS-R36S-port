# Licensing

Single source for the licences of everything the public image
distributes (decisions 34–38 in [decisions.md](decisions.md)).
`port/packaging/pending-licenses.json` mirrors the non-open rows;
`THIRD-PARTY.txt` in the image (`port/scripts/third-party.sh`) is the
user-facing notice generated from the same pins. Update all three
together. Checked 2026-11-25.

**States:** **open** = an open-source licence; we ship the corresponding
source in the release's source bundle (`make-source-bundle.sh`) where the
licence asks for it. **permitted** = the rights holder or the licence
grants redistribution explicitly. **community practice** = closed or
unlicensed, no answer to our request; bundled as dArkOS/ArkOS do, with
credits and the known terms; removed if the author asks (decision 35).
**removed** = not in the public image.

Non-commercial licences (NC below) forbid selling the firmware or bundling
it with a commercial product. The port itself is free and must stay so.

## System

| Component | Version / pin | Licence | State |
|---|---|---|---|
| Port code (scripts, device files, patches, own tools) | this repository | MIT (`LICENSE`); patches to GPL code follow that code's licence | open |
| MustardOS frontend (muxfrontend, muxretro, libui, libmuxcom, libmuxmod, muhotkey, mubattery) | MustardOS/frontend `5e8635b3`, built from source + `port/patches/frontend`, `port/patches/muxretro` | GPL-3.0 (vendored deps: their own, e.g. rcheevos MIT) | open |
| MustardOS internal scripts, configs, share data | MustardOS/internal `550cc58f` (640x480 subset) | GPL-3.0 | open |
| MustardOS language pack | `release-main-3db301a-20261112-073445` | GPL-3.0 | open |
| MustardOS themes (MustardOS, C64, Dracula, GB Dark, Orange, mubiOS), sounds, glyphs, name | internal `550cc58f` share/theme | CC BY-NC 4.0 (muos.dev); credits below | permitted (MustardOS team, 2026-11-25, on the conditions of decision 34) |
| Linux kernel (rk351 BSP) + in-tree modules incl. rtl8821cu Wi-Fi | christianhaitian/linux `d8402159` + `port/patches/kernel`; also the M2 Image (`780935823…`, reproduced by `build-boot.sh kernel-ref`) as the previous boot record | GPL-2.0 | open |
| U-Boot | christianhaitian/RG351MP-u-boot `5606e804` + the port's tree (`uboot-tree.py`), `uboot.img` `159e086c…` built by `build-boot.sh uboot` | GPL-2.0+ | open (the old "dirty" banner = a patched tree; source and patches are in the bundle) |
| Rockchip boot payloads (DDR 333 MHz v1.10, miniloader v1.12, BL31 v1.14, BL32 v1.10) | rkbin (byte-identical; trust.img `3531668a…`) | rkbin LICENSE: use, copy, distribute; no reverse engineering | permitted |
| Buildroot root filesystem (63 packages: glibc, busybox, SDL2, PipeWire, wpa_supplicant, dropbear, curl, ffmpeg, …) | Buildroot 2025.02.19 | per package (`legal-info/manifest.csv` in the bundle) | open |
| Mali-G31 userspace driver | Hardkernel `rk3326_r13p0_gbm_with_vulkan_and_cl.zip` (sha256 `ef1a18fa…`), aarch64 member `2a067ea3…`, shipped **unmodified** as `/usr/lib/libmali-bifrost-g31-rxp0-gbm.so` (+ links) | Arm proprietary; no terms in the archive | community practice |
| Fonts: Noto Sans (SC/TC/JP/KR), M+ | from MustardOS | SIL OFL-1.1, M+ FONT LICENSE | open |
| Boot logo (U-Boot and the splash until the menu) | MustardOS press-kit boot screen `images/mustardos-boot-screen-640x480.png` (sha256 `84b30eb3…`, badge as supplied) + the port's text "R36S / R35S", "unofficial port" (`make-boot-logo.py`) | CC BY-NC 4.0 (MustardOS); the text MIT | permitted (decision 34) |
| Model DTBs (M10, experimental; 22 R36S models) | dArkOSen `28f5427` `boot/dtb` (pinned by sha256 in `port/packaging/models.txt`) + the port's deltas (mmc aliases, no GPU 600 MHz OPP; `make-dtb-model.sh`) | dArkOSen repository MIT; the device trees derive from the GPL-2.0 kernel DTS: their decompiled DTS is in the source bundle (`model-dts`) | open |
| Wi-Fi firmware for the mainline USB drivers (mt7601u, rt2800usb, rt73usb, rtl8192cu, r8712u, r8723au; M10) | linux-firmware tag `20261019`, 11 files pinned in `port/packaging/wifi-firmware.txt`, shipped **unmodified** in `/lib/firmware` with the 3 licence files in `/usr/share/licenses/linux-firmware` | MediaTek/Ralink and Realtek redistributable binary licences (keep the notice; no reverse engineering) | permitted |
| Bluetooth firmware `rtl_bt/rtl8821c_*` | — | — | removed (decision 38) |
| Python 3.12 (M11, for PortMaster) and libjpeg-turbo (SDL2_image JPEG) | Buildroot 2025.02.19 packages `python3` (pyc only), `jpeg-turbo` | Python-2.0 (PSF); IJG + BSD-3-Clause + zlib | open (legal-info) |
| PortMaster (M11) | **not distributed**: `muos-portmaster` downloads PortsMaster/PortMaster-GUI `2026.11.17-0700` `muos.portmaster.zip` (sha256 `e2d3af3a…`) to the user's card on its first start (or takes the user's own copy from `MUOS/update`); its updates, runtimes and ports come from PortMaster's servers | MIT (PortMaster); its bundled tools carry their own licences in `MUOS/PortMaster/licenses` (gptokeyb/gptokeyb2 GPL-3.0, 7zzs LGPL-2.1, …) | no distribution duty (the user's download) |
| Official PICO-8 (M12) | **not distributed** (Lexaloffle, commercial): the user copies their own Raspberry Pi build to `MUOS/bios/pico8`; `muos-pico8` and the Splore app (MIT) only launch it | Lexaloffle's licence (the user's) | no distribution |
| GNU wget (M12, HTTPS for Splore and ports) | Buildroot `wget` with OpenSSL | GPL-3.0+ | open (legal-info) |
| PortMaster launcher, installer, muOS shims (`/usr/libexec/muos-portmaster*`, `muos-session`, `/opt/muos/script/var/func.sh`, `/usr/bin/retroarch` shim, the PortMaster app folder) | this repository | MIT | open |

## Libretro cores

All built by `port/scripts/build-cores.sh` from pinned commits (tarballs in
the bundle), patches in `port/patches/cores`.

| Core | Upstream @ commit | Licence | State |
|---|---|---|---|
| snes9x2005 | libretro/snes9x2005 `a79dfe90` | Snes9x licence (NC) | open |
| gpsp | libretro/gpsp `5819380c` | GPL-2.0 | open |
| picodrive | libretro/picodrive `1890c293` | PicoDrive licence (NC) | open |
| pcsx_rearmed | libretro/pcsx_rearmed `7b0e8f8f` | GPL-2.0 | open |
| stella2014 | libretro/stella2014-libretro `7d1361e4` | GPL-2.0 | open |
| prosystem | libretro/prosystem-libretro `8a880142` | GPL-2.0 | open |
| handy | libretro/libretro-handy `bc55d462` | Zlib | open |
| pce_fast, ngp, wswan | libretro/beetle-* `2de1ce1c`, `a50d5ac2`, `4b012958` | GPL-2.0 | open |
| bluemsx | libretro/blueMSX-libretro `e3086eb5` | GPL-2.0 | open |
| gearcoleco, gearsystem | drhelius `8e866783`, `4b3b1b26` | GPL-3.0 | open |
| pokemini | libretro/PokeMini `132111b7` | GPL-3.0 | open |
| fbneo | libretro/FBNeo `12ec3ca2` | FBNeo licence (NC) | open |
| mame2003_plus | libretro/mame2003-plus-libretro `dce2e9a2` | MAME licence (NC) | open |
| mupen64plus_next | libretro/mupen64plus-libretro-nx `15bada85` | GPL-2.0 | open |
| dosbox_pure | libretro/dosbox-pure `e39497e7` | GPL-2.0 | open |
| flycast (parallel_dc), flycast2022 | libretro/flycast `328a768a`, libretro/parallel-dc `4c293f30` | GPL-2.0 | open |
| flycast2 (v2.7) | flyinghead/flycast `5aa091fd` | GPL-2.0 | open |
| ppsspp, ppsspp2021 | hrydgard/ppsspp `fa50bb19` (v1.20.4), `ce0a45cf` (v1.12.3) | GPL-2.0+ (bundled FFmpeg LGPL) | open |
| melonds | libretro/melonds `4081e835` | GPL-3.0 | open |
| yabasanshiro | libretro/yabause `09ed8e5b` | GPL-2.0 | open |
| gambatte | libretro/gambatte-libretro `77f2567d` | GPL-2.0 | open (moved to `build-cores.sh` 2026-11-25) |
| fceumm | libretro/libretro-fceumm `ac0d00a7` | GPL-2.0 | open (moved to `build-cores.sh` 2026-11-25) |
| picante8 (PICO-8, M12; the default) | MustardOS/picante8 `86236842` | GPL-3.0 | open |
| fake08 (PICO-8, M12) | jtothebell/fake-08 `814991a2` | MIT (with z8lua, MIT) | open |
| scummvm (core) | scummvm/scummvm `7d2709da` (v2026.4.0) + libretro deps | GPL-3.0+ | open |

## Standalone emulators

| Component | Version / pin | Licence | State |
|---|---|---|---|
| Mupen64Plus core, ui-console, audio-sdl, input-sdl, rsp-hle, video-rice; GLideN64 | pins in `build-mupen64plus-sa.sh` | GPL-2.0 | open |
| PPSSPP standalone v1.20.4, v1.12.3 | the ppsspp/ppsspp2021 tarballs + `port/patches/ppsspp*` (dArkOS's patches) | GPL-2.0+ | open |
| Flycast standalone v2.7 | flycast2 tarball + dArkOS patch 003 (rk3326_core_builds, MIT) | GPL-2.0 | open |
| YabaSanshiro standalone | christianhaitian/yabasanshiro-standalone `c7618d2e` + dArkOS patches + `port/patches/yabasanshiro-sa`; Boost 1.83.0 static | GPL-2.0; Boost BSL-1.0 | open |
| ScummVM standalone | v2026.4.0 `7d2709da`; libogg 1.3.5, libvorbis 1.3.7, FLAC 1.4.3 static | GPL-3.0+; BSD-3-Clause | open |
| DraStic r2.5.2.2 (aarch64) | `drastic_v2522` from trngaje/advanced_drastic `d445a563` (md5 `17550db7…`, sha256 `dab3275e…`), with its `system/`, `game_database.xml`, `microphone/` | freeware, closed source (Exophase) | community practice |
| advanced_drastic hook `libadvdrastic.so` (dArkOS build) | trngaje/advanced_drastic `d445a563` `libs/arkos` (sha256 `ffa77841…`), with its `resources/` menu, pen, lang | no licence file, no published source; README: based on steward-fu's drastic-steward hook (steward-fu/nds is LGPL-2.1) | community practice |
| `libjson-c.so.5` (in the hook's folder) | trngaje/advanced_drastic `libs/arkos` (sha256 `35c940c7…`) | MIT (json-c) | open |
| DraStic 640x480 layout art | trngaje/drastic_layout `e8dc3eb5` `bg/640x480` (by steward-fu, per trngaje) | no licence file | community practice |
| drastic_layout other resolutions (1024x768, 720x720, 1280x720, 720x480, …; other authors) | — | — | removed (never shipped; `build-drastic.sh` copies only 640x480) |
| Noto Sans KR (in the hook's resources) | — | SIL OFL-1.1 | open |

## Theme and asset credits (CC BY-NC 4.0, MustardOS)

From each theme's `credits.txt`: MustardOS theme by Bitter Bizarro (boot
logo LMarcoMiranda, icon glyphs Line Icons 5, overlay indicators AntiKk,
navigation sounds Aedilic Inc.); C64, Dracula and Orange by antiKk;
GB Dark by inteLLiAim (original: Alukim); mubiOS by RazamaBazakart.
MustardOS name and assets per https://muos.dev/press: "MustardOS" (short
form "muOS"), logos unmodified; the port does not use the MustardOS logos
outside the themes.

## Conditions we follow

- **MustardOS (decision 34, Terms of Use §3, §5):** the full name
  "MustardOS", never "Mustard OS", "MUOS" or "Muos"; the image, README and
  release notes say it is an **unofficial port, not supported by the
  MustardOS team**, support only on the port's GitHub (also in the help
  texts of Information → Device Details, EN and pt-BR); changes are
  identified (patches in
  the repository); exact corresponding source in every release.
- **GPL/LGPL:** the source bundle is attached to every release
  (`make-source-bundle.sh bundle`), and THIRD-PARTY.txt offers it.
- **NC cores:** no sale, no commercial bundling (stated in THIRD-PARTY.txt
  and the README).
- **Community practice:** credits and known terms in THIRD-PARTY.txt; a
  removal request is honoured in the next release, and Plan B
  (`prepare-image.sh`, decision 36) can then supply the component from its
  official source on the user's PC.

## Community-practice reference (checked 2026-11-25)

- **dArkOS** (christianhaitian/rk3326_core_builds, MIT): `builds.sh`
  installs `mali/aarch64/libmali-bifrost-g31-rxp0-gbm.so` (also a
  `g13p0` build) into the image with the libMali/EGL/GLES/gbm links; the
  `mali/` folder has no licence or origin file. `scripts/advanced_drastic.sh`
  clones trngaje/advanced_drastic, takes `drastic_v2522` as `drastic`,
  `libs/arkos/*`, and **all** of trngaje/drastic_layout's `bg/`; no licence
  file is added. dArkOSen (the R36S fork the port references) ships the
  same.
- **ArkOS** (christianhaitian/arkos, MIT, archived 2025-12-30): the same
  build scripts; its wiki does not mention the Mali or DraStic terms.
- **ROCKNIX:** RK3326 builds package libmali bifrost-g31 (MALI_FAMILY)
  next to Panfrost.
- **MustardOS** itself ships a `drastic-trngaje` configuration for its
  H700 devices (internal `device/rg35xx-h/control/drastic-trngaje`).

## Request log

| # | To | Component | Sent | Answer |
|---|---|---|---|---|
| 1 | Hardkernel (odroid@hardkernel.com) | Mali r13p0 userspace | e-mail 2026-11-14, follow-up after 2026-11-22; forum https://forum.odroid.com/viewtopic.php?t=51472 | 2026-11-26 (forum): Hardkernel gets the drivers from the SoC vendor and can't speak to redistribution; ask Rockchip (who rarely answers individuals). No change: the driver stays shipped unmodified as community practice (decision 47) |
| 2 | Exophase | DraStic r2.5.2.2 | e-mail (by 2026-11-25) | none as of 2026-11-25 |
| 3 | trngaje | drastic_layout art | issue trngaje/drastic_layout#3, 2026-11-23 | 2026-11-23: "None of it is my own work"; 640x480 by steward-fu, 1024x768 resized from it, 720x720 duncanyoyo1/Vidnez/anbernic, 1280x720 crossmix, 720x480 tamarindojuice ([comment](https://github.com/trngaje/drastic_layout/issues/3#issuecomment-7116865774)) |
| 3b | trngaje | libadvdrastic.so | — (checked the repository 2026-11-25) | no LICENSE, no source in the repository, README credits steward-fu's drastic-steward |
| 4 | steward-fu | 640x480 layout art | issue steward-fu/nds#110, 2026-11-23 | none as of 2026-11-25 |
| 5 | MustardOS team | name, port, bundled themes | 2026-11-22/23 | 2026-11-25: allowed on the conditions of decision 34 |

Earlier request texts: git history of `docs/license-requests.md`
(removed 2026-11-25).
