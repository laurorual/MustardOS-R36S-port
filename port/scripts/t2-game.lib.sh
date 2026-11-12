# SPDX-License-Identifier: MIT
# shellcheck shell=bash disable=SC2016,SC2154
# Shared T2 helpers for in-game tests; source from a port/scripts/t2-*.sh.
# Needs $dev (device.sh path). Provides r, pids_of, module, wait_module,
# fail, game_rom, game_start ROM [DIR], game_stop. DIR (default NES) must
# have a core assignment (info/content/DIR/core.cfg: core, system, launch).
# game_start snapshots the ROM's pickles (state/*/DIR, sram/*/DIR and
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
# menu launch (governor: $game_gov if set, else the folder's core.gov). Arms muxretro's frame-time capture (MUXRETRO_PERF_CAPTURE via
# /run/muos/perf-capture; performance.csv every 15 s, last 1024 frames).
game_start() { # ROM [DIR]
    local rom=$1 dir=${2:-NES} cfg core sys launch
    cfg=$(r "cat '/opt/muos/share/info/content/$dir/core.cfg'") || fail "no core assignment for $dir"
    core=$(sed -n 1p <<< "$cfg") sys=$(sed -n 2p <<< "$cfg") launch=$(sed -n 5p <<< "$cfg")
    r "test -f '/userdata/ROMS/$dir/$rom' && test -f '/opt/muos/share/core/$core'" || fail "missing ROMS/$dir/$rom or core $core"
    game_rom_name=${rom%.*} game_dir=$dir
    game_snapshot save
    wait_module muxlaunch 40 || { for _ in 1 2 3; do r '/usr/libexec/muos-press b'; sleep 2; done; wait_module muxlaunch 10 || fail "not at launcher"; }
    r 'touch /run/muos/perf-capture; rm -f /run/muos/storage/pickles/performance.csv
       printf "%s\n" "'"$game_rom_name"'" "'"$core"'" "'"$sys"'" 0 0 "'"$launch"'" /mnt/mmc/ROMS "/'"$dir"'" "'"$rom"'" > /run/muos/content
       gov='"${game_gov:-}"'; [ -n "$gov" ] || gov=$(cat "/opt/muos/share/info/content/'"$dir"'/core.gov" 2>/dev/null || cat /opt/muos/device/config/cpu/default)
       printf "%s\n" "$gov" > /run/muos/governor; echo explore > /run/muos/action
       '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
    wait_module muxretro 20 || fail "$dir/$rom did not start (got $(module))"
}

game_stop() { # back to the launcher
    r 'rm -f /run/muos/perf-capture'
    r '/usr/libexec/muos-press fn+start'; wait_module muxplore 15 || :
    for _ in 1 2 3; do [ "$(module)" = muxlaunch ] && break; r '/usr/libexec/muos-press b'; sleep 2; done
    game_snapshot restore
}

# save|restore the user's pickles for $game_rom_name in $game_dir (any
# core). Copies files in place (never replaces directories:
# /run/muos/storage/pickles is a bind mount).
game_snapshot() {
    r 'p=/userdata/MUOS/pickles snap=/run/t2-pickles n="'"$game_rom_name"'" dir="'"${game_dir:-NES}"'"
       case '"$1"' in
       save) rm -rf $snap; mkdir -p $snap
             for d in "$p"/state/*/"$dir" "$p"/sram/*/"$dir"; do
                 [ -d "$d" ] || continue; rel=${d#"$p"/}
                 [ -d "$d/$n" ] && { mkdir -p "$snap/$rel"; cp -a "$d/$n" "$snap/$rel/"; }
                 for f in "$d/$n".*; do [ -e "$f" ] && { mkdir -p "$snap/$rel"; cp -a "$f" "$snap/$rel/"; }; done
             done
             cp -a $p/resume.ini $snap/ 2>/dev/null; touch $snap/.ok ;;
       restore) [ -e $snap/.ok ] || { echo "no pickles snapshot"; exit 1; }
             for d in "$p"/state/*/"$dir" "$p"/sram/*/"$dir"; do
                 [ -d "$d" ] || continue; rel=${d#"$p"/}
                 rm -rf "${d:?}/$n"; rm -f "$d/$n".*
                 [ -d "$snap/$rel" ] && cp -a "$snap/$rel/." "$d/"
             done
             [ -e $snap/resume.ini ] && cp -a $snap/resume.ini $p/
             rm -rf $snap; sync ;;
       esac'
}
