#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016,SC2034
# T2: Dreamcast (libretro Flycast) speed per core-option set (M8 T3 8:
# "not playable"). The core is the DC folder's assignment (core.cfg):
# Flycast v2.7 (flycast) or Flycast 2022 (flycast2022, M8c). Each VARIANT
# writes pickles/coreopt/core/<core>.ini, starts Power Stone 2 from a test
# state (p3 MUOS/t2/dc-fight for v2.7: the user's mid-fight state, paused:
# A = Cancel; MUOS/t2/dc-fight-2022 for 2022: the user's M8c T3 fight),
# runs SECS seconds and reads muxretro's performance.csv (present Hz,
# core ms per frame). The user's ini is restored afterwards.
#   t2-dc-fps.sh [SECS] VARIANT...   variants: see opts() below
#   env: T2_DC_SO=host .so: bind-mounted over the image's
#        flycast_libretro.so for the run (another Flycast build);
#        T2_DC_STATE=none: no test state (attract loop from boot; the
#        user's autosave is moved aside for the run and put back)
set -euo pipefail
dev=port/scripts/device.sh
cd "$(dirname "$0")/../.."
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
secs=${1:-60}; shift || :
[ $# -gt 0 ] || set -- base dark
out=build/logs/m8/dc-fps; mkdir -p "$out"
dccore=$(r "sed -n 1p /opt/muos/share/info/content/DC/core.cfg") dccore=${dccore%_libretro.so}
ini=/userdata/MUOS/pickles/coreopt/core/$dccore.ini
p=reicast
dark="${p}_frame_skipping=1
${p}_auto_skip_frame=more
${p}_alpha_sorting=per-strip (fast, least accurate)
${p}_delay_frame_swapping=enabled
${p}_enable_dsp=disabled
${p}_threaded_rendering=enabled
${p}_anisotropic_filtering=off
${p}_mipmapping=enabled"
opts() {
    case $1 in
    base) : ;;
    dark) echo "$dark" ;;                       # dArkOSen standalone emu.cfg
    half) echo "$dark"; echo "${p}_internal_resolution=320x240" ;;
    auto) grep -v frame_skipping <<< "$dark" ;; # auto skip only
    skip2) sed 's/frame_skipping=1/frame_skipping=2/' <<< "$dark" ;;
    halfauto) grep -v frame_skipping <<< "$dark"; echo "${p}_internal_resolution=320x240" ;;
    # Flycast 2022 (LOW_RES build: 320x240 default; M8c T3 7: text
    # unreadable, uneven speed)
    r640) echo "${p}_internal_resolution=640x480" ;;
    r640n) echo "${p}_internal_resolution=640x480"; echo "${p}_framerate=normal" ;;
    r640s) echo "${p}_internal_resolution=640x480"; echo "${p}_synchronous_rendering=enabled" ;;
    r640nt) echo "${p}_internal_resolution=640x480"; echo "${p}_framerate=normal"; echo "${p}_threaded_rendering=disabled" ;;
    r640f1) echo "${p}_internal_resolution=640x480"; echo "${p}_frame_skipping=1" ;;
    r480) echo "${p}_internal_resolution=480x360" ;;
    norm) echo "${p}_framerate=normal" ;;
    *) fail "unknown variant $1" ;;
    esac
}
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol=$(r 'cat /opt/muos/config/settings/general/volume')
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1" || :
r "test -f $ini && cp $ini /run/t2-flycast.ini || rm -f /run/t2-flycast.ini"
echo "core $dccore"
trap 'cleanup; r "$env_pw; /opt/muos/script/device/audio.sh $vol >/dev/null 2>&1; if test -f /run/t2-flycast.ini; then cp /run/t2-flycast.ini '$ini'; else rm -f '$ini'; fi" || :' EXIT
game_state=/userdata/MUOS/t2/dc-fight; [ "$dccore" = flycast ] || game_state=$game_state-2022
core=/opt/muos/share/core/${dccore}_libretro.so
st="/userdata/MUOS/pickles/state/$dccore/DC/Power Stone 2 (USA)"
if [ -n "${T2_DC_SO:-}" ]; then
    "$dev" push "$T2_DC_SO" /run/t2dc >/dev/null
    r "mount --bind '/run/t2dc/${T2_DC_SO##*/}' $core"
fi
if [ "${T2_DC_STATE:-}" = none ]; then
    game_state=
    r "mkdir -p /run/t2dc/state; for f in '$st'/autosave.*; do [ -e \"\$f\" ] && mv \"\$f\" /run/t2dc/state/; done; :"
fi
cleanup() {
    r "umount $core 2>/dev/null; for f in /run/t2dc/state/autosave.*; do [ -e \"\$f\" ] && mv \"\$f\" '$st'/; done; :" || :
}
rom="Power Stone 2 (USA).cue"
printf '%-9s %6s %6s %6s %6s %6s %5s %5s %5s %5s %5s\n' variant hz mean p95 peak core 18-25 25-50 50+ temp mhz
for v in "$@"; do
    { echo '[options]'; opts "$v"; } | r "mkdir -p ${ini%/*}; cat > $ini"
    game_start "$rom" DC
    if [ -n "$game_state" ]; then
        sleep 15                       # state load (36 MB)
        r '/usr/libexec/muos-press a'  # in-game pause menu: Cancel
    else
        sleep 30                       # BIOS logo, title, into the attract loop
    fi
    r 'rm -f /run/muos/storage/pickles/performance.csv'
    sleep "$secs"
    t=$(r 'cat /sys/class/thermal/thermal_zone0/temp')
    f=$(r 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq')
    r 'cat /run/muos/storage/pickles/performance.csv' > "$out/$v.csv" || :
    r 'cat /proc/loadavg' > "$out/$v.load" || :
    game_stop
    awk -F, -v v="$v" -v t="$t" -v f="$f" '
        /^frame,/{mean=$4; p95=$7; pk=$9}
        /^core,/{core=$4}
        /^observed_present_hz,/{hz=$2}
        /^frame_histogram_18_5_to_25_ms,/{a=$2}
        /^frame_histogram_25_to_50_ms,/{b=$2}
        /^frame_histogram_50_to_250_ms,/{c=$2}
        END{printf "%-9s %6s %6s %6s %6s %6s %5s %5s %5s %5d %5d\n", v, hz, mean, p95, pk, core, a, b, c, t/1000, f/1000}' "$out/$v.csv"
done
