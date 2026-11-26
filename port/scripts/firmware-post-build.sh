#!/bin/sh
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# Buildroot post-build (firmware.defconfig): install the SHA256-pinned
# prebuilt inputs from the build/m3a/inputs store into the target, then
# the port's adjustments to them (the rootfs overlay is already in TARGET):
# - the coredb's per-system governors from core-assign.txt;
# - the volume/brightness scripts wrapped with the input boost
#   (level-wrapper.sh as audio.sh/bright.sh, the originals as *-muos.sh);
# - the WirePlumber rules from core-wireplumber.conf;
# - hold-to-repeat for volume/brightness in the pinned hotkey map;
# - muxretro's provider metadata for the source build (M3e);
# - board/network = 1 (M4a: the port's Wi-Fi backend drives muOS's
#   Connectivity menu; the pinned device config says 0);
# - info_open/info_close.wav high-passed for the speaker (M4a, wav-highpass.py);
# - /etc/localtime -> the zone link on p3, RTC in UTC (M4d);
# - share/profile/state, share/news -> p3 MUOS/port/ (M5);
# - a save-state warm-up for mupen64plus-next (M7).
# $1 is TARGET_DIR. Runs inside the build container (paths as
# build-image.sh mounts).
set -eu
python3 /port/scripts/firmware-inputs.py install \
    /port/packaging/firmware-inputs.json /m3a/inputs "$1"
cp /port/device/rk-r35s-p0/rootfs/opt/muos/device/config/board/network "$1/opt/muos/device/config/board/network"
# M5: upstream profile.sh keeps its state in /opt/muos/share/profile/state
# (rw on upstream, the read-only p2 here): on p3 (muos-seed-share creates it)
ln -sfn /userdata/MUOS/port/profile-state "$1/opt/muos/share/profile/state"
# and muxnews caches the community posts in /opt/muos/share/news
ln -sfn /userdata/MUOS/port/news "$1/opt/muos/share/news"
# M11: PortMaster on p3 (muos-portmaster): ports fall back to
# /roms/ports/PortMaster/control.txt; the SDL controller file SDL ports
# read is written per launch (sdl-env.sh)
mkdir -p "$1/roms/ports"
ln -sfn /mnt/mmc/MUOS/PortMaster "$1/roms/ports/PortMaster"
ln -sfn /run/muos/gamecontrollerdb.txt "$1/usr/lib/gamecontrollerdb.txt"
# M5: mount point of the slot-2 card (script/device/storage.sh; the root
# is read-only, so it must exist in the image)
mkdir -p "$1/mnt/sdcard"
snd=$1/opt/muos/share/theme/MustardOS/sound
for n in info_open info_close; do
    python3 /port/scripts/wav-highpass.py "$snd/$n.wav" "$snd/$n.wav.tmp" && mv "$snd/$n.wav.tmp" "$snd/$n.wav"
done
# M7 T3: mupen64plus-next rejects a state loaded before its first frames
# (the exit autosave never resumed); muxretro runs this many frames first
# (coreinfo savestate_warmup_frames; 3 restored MK64 and DK64 on the device)
printf 'savestate_warmup_frames = "5"\n' >> "$1/opt/muos/share/emulator/retroarch/info/mupen64plus_next_libretro.info"
python3 /port/scripts/coredb-governors.py "$1/usr/share/muos-r35s/core-assign.txt" \
    "$1/opt/muos/share/info/manifest/core.json" "$1/opt/muos/share/core"
d=$1/opt/muos/script/device
for n in audio bright; do
    mv "$d/$n.sh" "$d/$n-muos.sh"
    cp /port/device/rk-r35s-p0/level-wrapper.sh "$d/$n.sh"
    chmod 0755 "$d/$n.sh" "$d/$n-muos.sh"
done
# M7 T3 ("the screen blinks once after the fade-in"): `bright.sh N` forces
# fb0/blank 0 (the frontend runs it when a screen starts, tweak.sh after a
# theme save); on this kernel that restores the fbdev mode over the UI's
# plane for one frame (DRM log: FB:69, other planes off). Skip the forced
# unblank as upstream does for rk-g350-v; a real blank/unblank (brightness
# 0 and back) still goes through.
grep -qF 'elif [ "$FORCE" -eq 1 ] && [ "$BOARD_NAME" != rk-g350-v ]; then' "$d/bright-muos.sh"
sed -i 's/elif \[ "$FORCE" -eq 1 \] && \[ "$BOARD_NAME" != rk-g350-v \]; then/elif [ "$FORCE" -eq 1 ] \&\& [ "$BOARD_NAME" != rk-g350-v ] \&\& [ "$BOARD_NAME" != rk-r35s-p0 ]; then/' "$d/bright-muos.sh"
grep -qF '[ "$BOARD_NAME" != rk-r35s-p0 ]; then' "$d/bright-muos.sh"
# The WirePlumber rules S80pipewire installs at start: the port's copy
# (state.restore-props off for the sink, M3d step 3) over the pinned one.
cp /port/device/rk-r35s-p0/core-wireplumber.conf "$1/opt/muos/device/control/wireplumber.conf"
chmod 0644 "$1/opt/muos/device/control/wireplumber.conf"
# Hold-to-repeat (M3e): upstream's volume.json/bright.json set handle_hold
# on these combos; the port's pinned map doesn't. muhotkey coalesces
# repeats while the previous command still runs.
python3 - "$1/opt/muos/share/hotkey/r35s-bringup.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as f:
    m = json.load(f)
for k in ("VOL_DOWN", "VOL_UP", "BRIGHT_DOWN", "BRIGHT_UP"):
    m[k]["handle_hold"] = True
with open(path, "w") as f:
    json.dump(m, f, indent=2)
    f.write("\n")
PY
# muxretro is built from source since M3d step 3 (build-muxretro.sh), but
# the pinned provider metadata describes the Phase 4 binary: recompute
# payload.sha256 from the target and record the source build.
python3 - "$1" /port/patches/muxretro <<'PY'
import hashlib, json, os, sys
root, patches = sys.argv[1], sys.argv[2]
d = os.path.join(root, "usr/share/muos-muxretro-provider")
def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
pv = os.path.join(d, "provenance.json")
with open(pv) as f:
    m = json.load(f)
m["muxretro_build"] = {
    "builder": "port/scripts/build-muxretro.sh (Phase 4 provider source + port patches)",
    "muxretro_sha256": sha(os.path.join(root, "opt/muos/frontend/muxretro")),
    "patches": {n: sha(os.path.join(patches, n))
                for n in sorted(os.listdir(patches)) if n.endswith(".patch")},
}
with open(pv, "w") as f:
    json.dump(m, f, indent=2)
    f.write("\n")
# Last: payload.sha256 lists provenance.json too.
lines = []
with open(os.path.join(d, "payload.sha256")) as f:
    for line in f:
        _, path = line.rstrip("\n").split("  ", 1)
        lines.append(f"{sha(root + path)}  {path}\n")
with open(os.path.join(d, "payload.sha256"), "w") as f:
    f.writelines(lines)
PY
# Time zone (M4d): /etc/localtime follows the link on p3 that the menu's
# Timezone screen rewrites (frontend 0004; muos-clock zone creates it, UTC);
# the RTC is kept in UTC for busybox hwclock (the kernel reads it as UTC).
ln -sfn /opt/muos/config/localtime "$1/etc/localtime"
rm -f "$1/etc/timezone"
mkdir -p "$1/var/lib/hwclock"
printf '0.0 0 0.0\n0\nUTC\n' > "$1/var/lib/hwclock/adjtime"
# M7: mount point for the archive install marks (S91 binds p3 there;
# script/mux/extract.sh writes update/installed/<archive>.done).
mkdir -p "$1/opt/muos/update"
echo "post-build: board/network, info sounds high-passed, coredb governors, level-script boost wrappers, wireplumber rules, hotkey hold, muxretro provenance, localtime link + RTC in UTC, update mount point, N64 state warm-up"
# M9 (decision 35, LICENSING.md): the Mali userspace ships unmodified, the
# exact Hardkernel r13p0 binary (sha256 2a067ea3...) instead of the copy the
# rockchip-mali recipe gave a SONAME with patchelf; programs find it by the
# libmali.so.1 link (the sysroot keeps the SONAME for linking).
mali=/work/foundation/provider-source/lib/aarch64-linux-gnu/libmali-bifrost-g31-rxp0-gbm.so
[ "$(sha256sum < "$mali" | cut -d' ' -f1)" = 2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea ]
cp "$mali" "$1/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
chmod 755 "$1/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
# M9 rc1 T3: first-boot defaults of a fresh card (p3 seeds its config from
# these once). Some pinned config files carried the bench's own values:
# English (upstream), the saved volume at 50 % and startup volume
# "previous" (settings/advanced/volume 3 = the device maximum, 100 %),
# upstream's debug_mode 0 (2 logs every module to the card).
c=$1/opt/muos/config
printf 'English\n' > "$c/settings/general/language"
printf '50\n' > "$c/settings/general/volume"
printf '0\n' > "$c/settings/advanced/volume"
printf '0\n' > "$c/system/debug_mode"
