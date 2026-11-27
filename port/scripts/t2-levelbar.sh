#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# v1.1.1 T3 fixes, T2 on the bench (developer image; PortMaster with
# turbotabletennis, see t2-portmaster.sh; the official PICO-8 optional):
#   1. mapping: with the store's muOS-Keys line taken out (as on a fresh
#      card; restored afterwards) PortMaster's GUI gets the board mapping
#      (a:b1 = the physical A) in SDL_GAMECONTROLLERCONFIG
#   2. level bar (muos-levelbar.so, the active theme's bar written by
#      `muxretro --level-assets` to /run/muos/levelbar): Volume-, a D-pad
#      press (the GUI only redraws on input), next frame grabbed
#      (/run/muos/levelbar-grab): the progress bar's track and fill in the
#      theme's colours where levelbar.conf puts them; Volume+ back
#   3. cursor: the VOP cursor plane (win2) stays off during TurboTableTennis
#      (SDL2 patch 0004); the bar in it (Godot frt, SDL_GL_SwapWindow)
#   4. the bar in the official PICO-8 (SDL_RenderPresent), if installed
#   5. the bar in the standalone emulators with test content on the bench
#      (Mupen64Plus, PPSSPP 2021, Flycast, DraStic; t2-standalone.sh writes
#      their frame rate and CPU share to the log)
# Frame grabs in build/logs/m12/levelbar-*.ppm.
#   t2-levelbar.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
out=build/logs/m12; log=$out/t2-levelbar.log; mkdir -p "$out"; : > "$log"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; r "$restore" > /dev/null; exit 1; }
r() { "$dev" run "$@" 2>> "$log" < /dev/null; }
db=/opt/muos/share/info/gamecontrollerdb/retro.txt
restore="[ ! -f /run/t2-retro.txt ] || { cat /run/t2-retro.txt > $db; rm -f /run/t2-retro.txt; }"
r '[ -f /usr/lib/muos-levelbar.so ]' || fail "no /usr/lib/muos-levelbar.so (image before v1.1.1)"
# grab NAME KEY: Volume- (to 5 from t2-standalone's 10), KEY (or none), the
# next frame, Volume+; the track's right end and the fill's left end must be
# the theme's colours (opaque ones; levelbar.conf scaled to the frame)
grab() {
    r 'rm -f /run/muos/levelbar-grab*; /opt/muos/script/device/audio.sh D
       touch /run/muos/levelbar-grab; [ '"$2"' = none ] || /usr/libexec/muos-press '"$2"'
       for _ in $(seq 20); do [ -e /run/muos/levelbar-grab ] || break; sleep 0.2; done
       /opt/muos/script/device/audio.sh U' || return 1
    r 'cat /run/muos/levelbar-grab.ppm' > "$out/levelbar-$1.ppm" || return 1
    r 'cat /run/muos/levelbar/levelbar.conf' > "$out/levelbar.conf" || return 1
    python3 port/scripts/t2-levelbar-check.py "$out/levelbar-$1.ppm" "$out/levelbar.conf"
}
# 1. + 2. PortMaster's GUI
r "cp $db /run/t2-retro.txt && grep -v ',muOS-Keys,' /run/t2-retro.txt > $db" || fail "1: store"
r 'printf %s /opt/muos/share/application/PortMaster > /run/muos/application; echo app > /run/muos/action
   for q in $(pidof muxfrontend); do kill -TERM "$q"; done'
ok=; for _ in $(seq 40); do r 'pgrep -f pugwash' > /dev/null && { ok=1; break; }; sleep 1; done
[ -n "$ok" ] || fail "1: PortMaster's GUI did not start"
sleep 12
r 'tr "\0" "\n" < /proc/$(pgrep -f pugwash | head -n 1)/environ | grep -q "^SDL_GAMECONTROLLERCONFIG=.*,a:b1,"' ||
    fail "1: no board mapping in the GUI"
say "ok   1: fresh store -> board mapping (a:b1) in PortMaster's GUI"
grab pm down || fail "2: no bar in PortMaster's GUI"
say "ok   2: bar in PortMaster's GUI (pysdl2, dlsym)"
r '/usr/libexec/muos-press fn+start'
for _ in $(seq 20); do r 'pgrep -f pugwash' > /dev/null || break; sleep 1; done
r 'pgrep -f pugwash' > /dev/null && fail "2: PortMaster's GUI still running after Fn+Start"
r "$restore"
# 3. TurboTableTennis: cursor plane, bar
r 'grep -q " /sys/kernel/debug " /proc/mounts || mount -t debugfs none /sys/kernel/debug'
port/scripts/t2-standalone.sh port-ttt external Ports TurboTableTennis.sh frt_3.5.2 30 >> "$log" 2>&1 < /dev/null &
t=$!
ok=; for _ in $(seq 90); do r 'pidof frt_3.5.2' > /dev/null && { ok=1; break; }; sleep 1; done
[ -n "$ok" ] || fail "3: TurboTableTennis did not start"
sleep 8
r 'sed -n "/win2-0/,/win2-1/p" /sys/kernel/debug/dri/0/summary | grep -q "win2-0: DISABLED"' ||
    fail "3: cursor plane on"
grab ttt none || fail "3: no bar in TurboTableTennis"
say "ok   3: TurboTableTennis: no cursor plane, bar (frt)"
wait "$t" || fail "3: t2-standalone"
# back in the menu before the next launch
for _ in $(seq 20); do r 'pidof muxfrontend' > /dev/null && break; sleep 1; done
sleep 3
# 4. the official PICO-8
if r '[ -f /mnt/mmc/MUOS/bios/pico8/pico8_64 ]'; then
    port/scripts/t2-standalone.sh pico8-scale ext-pico8-scale PICO-8 ld45.p8 pico8_64 25 schedutil >> "$log" 2>&1 < /dev/null &
    t=$!
    ok=; for _ in $(seq 90); do r 'pidof pico8_64' > /dev/null && { ok=1; break; }; sleep 1; done
    [ -n "$ok" ] || fail "4: PICO-8 did not start"
    sleep 8
    grab p8 none || fail "4: no bar in PICO-8"
    say "ok   4: bar in the official PICO-8"
    wait "$t" || fail "4: t2-standalone"
else
    say "skip 4: no official PICO-8"
fi
# 5. standalone emulators: NAME CORE DIR FILE (_ = space) PROCESS
while read -r n core dir file p; do
    file=${file//_/ }
    r "[ -f '/mnt/mmc/ROMS/$dir/$file' ]" || { say "skip 5: $n (no $dir/$file)"; continue; }
    for _ in $(seq 20); do r 'pidof muxfrontend' > /dev/null && break; sleep 1; done
    sleep 3
    port/scripts/t2-standalone.sh "lb-$n" "$core" "$dir" "$file" "$p" 30 > "$out/lb-$n.log" 2>&1 < /dev/null &
    t=$!
    ok=; for _ in $(seq 90); do r "pidof $p" > /dev/null && { ok=1; break; }; sleep 1; done
    [ -n "$ok" ] || fail "5: $n did not start"
    sleep 15
    grab "$n" none || fail "5: no bar in $n"
    wait "$t" || fail "5: $n t2-standalone ($(tail -n 1 "$out/lb-$n.log"))"
    say "ok   5: bar in $n; $(grep -a -m1 "^ *[0-9]" "$out/lb-$n.log" | tr -s ' ' | cut -c1-80)"
done << 'LIST'
n64 ext-mupen64plus-rice N64 Mario_Kart_64_(USA).z64 mupen64plus
psp ext-ppsspp-2021 PSP God_of_War_-_Chains_of_Olympus_(USA).iso PPSSPPSDL
dc ext-flycast DC Power_Stone_2_(USA).cue flycast
nds ext-drastic NDS New_Super_Mario_Bros._(USA).nds drastic
LIST
say PASS
