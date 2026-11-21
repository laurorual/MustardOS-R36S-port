#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M8 item 5): the ScummVM libretro core before it is in an image. The
# core from build-scummvm.sh libretro is laid over /opt/muos/share/core for
# the run (a tmpfs directory of links to the image's cores plus the new
# one, bind-mounted; undone on exit), the game folder from port/roms is
# pushed to ROMS/SCUMMVM once, and the game starts from a NAME.scummvm
# file with its game id inside the folder (what muos-frontend hands the
# core). Measures SECS seconds: real speed (t2-coremeter.sh), present Hz,
# SoC temperature and CPU clock; muxretro must stay up.
#   t2-scummvm.sh [SECS] [GAMEDIR [GAMEID]]
set -euo pipefail
cd "$(dirname "$0")/../.."
dev=port/scripts/device.sh
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
secs=${1:-60} name=${2:-The Secret of Monkey Island (CD DOS VGA)} id=${3:-monkey}
so=build/m8f/scummvm/scummvm_libretro.so out=build/logs/m8f/scummvm; mkdir -p "$out"
[ -s "$so" ] || fail "no $so (build-scummvm.sh libretro)"
c=/opt/muos/share/core info=/opt/muos/share/info/content/SCUMMVM
r "test -d '/userdata/ROMS/SCUMMVM/$name'" || {
    r 'mkdir -p /userdata/ROMS/SCUMMVM'; "$dev" push "port/roms/ScummVM/$name" /userdata/ROMS/SCUMMVM >/dev/null; }
"$dev" push "$so" /run/t2sv >/dev/null
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol=$(r 'cat /opt/muos/config/settings/general/volume')
had_info=$(r "if test -e $info/core.cfg; then rm -rf /run/t2sv-info; cp -a $info /run/t2sv-info; echo 1; else echo 0; fi")
cleanup() {
    port/scripts/t2-coremeter.sh disarm || :
    r "umount $c 2>/dev/null || umount -l $c 2>/dev/null; umount /run/t2core-orig 2>/dev/null || umount -l /run/t2core-orig 2>/dev/null; rm -rf /run/t2core
       rm -rf $info; [ $had_info = 0 ] || cp -a /run/t2sv-info $info
       $env_pw; /opt/muos/script/device/audio.sh $vol >/dev/null 2>&1" || :
}
trap cleanup EXIT
r "set -e; mkdir -p /run/t2core-orig /run/t2core; mountpoint -q /run/t2core-orig || mount --bind $c /run/t2core-orig
   for f in /run/t2core-orig/*; do ln -sf \"\$f\" /run/t2core/; done
   cp /run/t2sv/scummvm_libretro.so /run/t2core/; mountpoint -q $c || mount --bind /run/t2core $c
   mkdir -p $info; printf '%s\n' scummvm_libretro.so ScummVM ScummVM 0 mu-scummvm > $info/core.cfg
   printf '%s\n' $id > '/userdata/ROMS/SCUMMVM/$name/$name.scummvm'
   $env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1"
port/scripts/t2-coremeter.sh arm
game_start "$name/$name.scummvm" SCUMMVM
sleep 20
r 'rm -f /run/muos/storage/pickles/performance.csv'
port/scripts/t2-coremeter.sh mark
sleep "$((secs - 6))"
"$dev" run "sh -s muxretro" < port/scripts/t2-threads.sh > "$out/threads.txt" || :
sleep 1
port/scripts/t2-coremeter.sh report > "$out/speed.txt" || :
r 'cat /run/muos/storage/pickles/performance.csv' > "$out/perf.csv" || :
t=$(r 'echo $(($(cat /sys/class/thermal/thermal_zone0/temp) / 1000)) C $(($(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq) / 1000)) MHz')
alive=$(module)
n0=$(r 'grep -n "" /opt/muos/log/frontend.log | tail -n 200 | head -n1 | cut -d: -f1')
r "tail -n +$n0 /opt/muos/log/frontend.log | grep -a -i scummvm | tail -n 20" > "$out/frontend.txt" || :
game_stop
echo "module during the run: $alive; $t"
awk -F, '/^observed_present_hz,/{print "present Hz", $2} /^core,/{print "core ms mean", $4}' "$out/perf.csv"
tail -1 "$out/speed.txt"
[ "$alive" = muxretro ] || fail "muxretro not running (got $alive)"
echo PASS
