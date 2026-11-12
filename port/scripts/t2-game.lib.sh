# SPDX-License-Identifier: MIT
# shellcheck shell=bash disable=SC2016,SC2154
# Shared T2 helpers for in-game tests; source from a port/scripts/t2-*.sh.
# Needs $dev (device.sh path). Provides r, pids_of, module, wait_module,
# fail, game_rom, game_start ROM, game_stop.
# game_start snapshots the ROM's pickles (state/, sram/ and
# resume.ini) to /run and game_stop puts them back, so a test run's exit
# autosave never replaces the user's.
r() { "$dev" run "cd /; $*"; }
# Match on /proc/PID/exe: pgrep -f would also match this SSH command line.
pids_of() { echo 'for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/'"$1"' ] && echo ${p#/proc/}; done'; }
module() { r "for q in \$($(pids_of muxretro); $(pids_of muxfrontend)); do cat /proc/\$q/comm 2>/dev/null; done | head -n1"; }
wait_module() { for _ in $(seq 1 "$2"); do [ "$(module)" = "$1" ] && return 0; sleep 1; done; return 1; }
fail() { echo "FAIL $*"; exit 1; }

# Default ROM: "Super Mario Bros. 3 (USA) (Rev 1).nes" (MMC3, title/attract
# loop without input) when installed, else the MIT demo r35s-flight.nes.
game_rom() {
    local rom="Super Mario Bros. 3 (USA) (Rev 1).nes"
    r "test -f '/userdata/ROMS/NES/$rom'" || rom=r35s-flight.nes
    echo "$rom"
}

# Explore remembers its last folder and lists wrap, so blind navigation is
# not deterministic. Launch through the frontend's own content handoff
# instead: the 9-line ROM_GO record + governor request muxplore writes,
# then a safe quit of muxfrontend; the frontend loop runs muxretro as for a
# menu launch. Arms muxretro's frame-time capture (MUXRETRO_PERF_CAPTURE via
# /run/muos/perf-capture; performance.csv every 15 s, last 1024 frames).
game_start() { # ROM (a file in ROMS/NES)
    local rom=$1
    game_rom_name=${rom%.nes}
    game_snapshot save
    wait_module muxlaunch 40 || { for _ in 1 2 3; do r '/usr/libexec/muos-press b'; sleep 2; done; wait_module muxlaunch 10 || fail "not at launcher"; }
    r 'touch /run/muos/perf-capture; rm -f /run/muos/storage/pickles/performance.csv
       printf "%s\n" "'"${rom%.nes}"'" fceumm_libretro.so "Nintendo NES - Famicom" 0 0 mu-fceumm /mnt/mmc/ROMS /NES "'"$rom"'" > /run/muos/content
       gov=$(cat /opt/muos/share/info/content/NES/core.gov 2>/dev/null || cat /opt/muos/device/config/cpu/default)
       printf "%s\n" "$gov" > /run/muos/governor; echo explore > /run/muos/action
       '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
    wait_module muxretro 20 || fail "NES did not start (got $(module))"
}

game_stop() { # back to the launcher
    r 'rm -f /run/muos/perf-capture'
    r '/usr/libexec/muos-press fn+start'; wait_module muxplore 15 || :
    for _ in 1 2 3; do [ "$(module)" = muxlaunch ] && break; r '/usr/libexec/muos-press b'; sleep 2; done
    game_snapshot restore
}

# save|restore the user's pickles for $game_rom_name. Copies files in place
# (never replaces directories: /run/muos/storage/pickles is a bind mount).
game_snapshot() {
    r 'p=/userdata/MUOS/pickles snap=/run/t2-pickles n="'"$game_rom_name"'"
       case '"$1"' in
       save) rm -rf $snap; mkdir -p $snap
             for d in state/fceumm/NES sram/fceumm/NES; do
                 [ -d "$p/$d/$n" ] && { mkdir -p "$snap/$d"; cp -a "$p/$d/$n" "$snap/$d/"; }
                 for f in "$p/$d/$n".*; do [ -e "$f" ] && { mkdir -p "$snap/$d"; cp -a "$f" "$snap/$d/"; }; done
             done
             cp -a $p/resume.ini $snap/ 2>/dev/null; touch $snap/.ok ;;
       restore) [ -e $snap/.ok ] || { echo "no pickles snapshot"; exit 1; }
             for d in state/fceumm/NES sram/fceumm/NES; do
                 rm -rf "$p/$d/$n"; rm -f "$p/$d/$n".*
                 [ -d "$snap/$d" ] && cp -a "$snap/$d/." "$p/$d/"
             done
             [ -e $snap/resume.ini ] && cp -a $snap/resume.ini $p/
             rm -rf $snap; sync ;;
       esac'
}
