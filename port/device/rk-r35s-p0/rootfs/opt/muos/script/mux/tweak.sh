#!/bin/sh
# SPDX-License-Identifier: MIT
# muOS R35S port: the frontend runs script/mux/tweak.sh after saving Power,
# Custom, Theme and Danger settings (muxshare run_tweak_script), then
# re-reads its config. The pinned script set lacked it (M4f). Upstream's
# tweak.sh restarts muOS services the port replaced (hotkey via process.sh,
# USB gadget, speaker/sdl_map/swap scripts, card scheduler); this applies
# what has an effect here:
#   - audio/max from settings/advanced/overdrive (1 = 200 %, as upstream);
#     the device config is S91's tmpfs copy, so the boot needs it too
#   - the saved brightness (device/bright.sh, the port's)
#   - the default CPU governor (muos-governor, as SET_DEFAULT_GOVERNOR),
#     only while no content runs
# Hotkeys come from the port's own JSON (S99 loop); the Danger CPU/GPU caps
# and core count are not applied by the port (not in its config).
#   tweak.sh          after a save (frontend)
#   tweak.sh boot     audio/max only (S97 start)
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
cfg=/opt/muos/config dev=/opt/muos/device/config
get() { v=$(head -n1 "$1" 2>/dev/null); echo "${v:-$2}"; }
say() { echo "tweak: $*"; }
max=100
[ "$(get $cfg/settings/advanced/overdrive 0)" != 1 ] || max=200
if [ -d "$dev/audio" ] && [ "$(get $dev/audio/max)" != "$max" ]; then
    printf '%s\n' "$max" > "$dev/audio/max" && say "audio/max $max"
fi
[ "${1:-}" != boot ] || exit 0
b=$(get $cfg/settings/general/brightness)
case "$b" in ''|*[!0-9]*) ;; *) /opt/muos/script/device/bright.sh "$b" > /dev/null 2>&1 || say "brightness $b failed" ;; esac
if ! pidof muxretro > /dev/null 2>&1; then
    /usr/libexec/muos-governor "$(get $dev/cpu/default schedutil)" > /dev/null 2>&1 || say 'governor failed'
fi
say applied
