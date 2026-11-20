#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M7): the release soak, unattended (no hands needed). In order:
#  1. t2-long-play.sh: NES, SNES, GBA, MD (or megadrive), 32X, PCE (first
#     ROM of each folder, empty ones skipped; NES = game_rom) MINUTES each;
#  2. PSX: CTR mid-race from the fixed test state (p3 MUOS/port/t2/ctr-race,
#     t2-game.lib.sh $game_state) MINUTES;
#  3. N64: Mario Kart 64 through the folder default (standalone Rice)
#     MINUTES with t2-swapstat.so: VI/s, process alive, SoC temperature;
#     Fn+Start (autosave), the user's N64 state restored;
#  4. t2-sleep-cycle.sh --game CYCLES (sleep/resume in a game);
#  5. t2-sleep-cycle.sh CYCLES (menu).
#   t2-soak.sh [--minutes N] [--cycles N]   (defaults 10 and 5)
# Volume 10 for the run (the scripts restore the user's level). Summary on
# stdout and in build/logs/m7/soak/summary.txt; each step's log beside it.
set -euo pipefail
cd "$(dirname "$0")/../.."
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
minutes=10 cycles=5
while [ $# -gt 0 ]; do
    case $1 in
    --minutes) minutes=$2; shift 2 ;;
    --cycles) cycles=$2; shift 2 ;;
    *) sed -n '3,15p' "$0"; exit 2 ;;
    esac
done
out=build/logs/m7/soak; mkdir -p "$out"; sum=$out/summary.txt; : > "$sum"
say() { echo "$*" | tee -a "$sum"; }
bad=0
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol0=$(r 'cat /opt/muos/config/settings/general/volume')
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1"
trap 'r "$env_pw; /opt/muos/script/device/audio.sh $vol0 >/dev/null 2>&1" || :' EXIT
step() { # NAME CMD...: run, keep the last lines, count failures
    local name=$1; shift
    if ( "$@" ) > "$out/$name.txt" 2>&1; then say "PASS $name: $(tail -n 3 "$out/$name.txt" | tr '\n' ' ')"
    else bad=$((bad + 1)); say "FAIL $name: $(tail -n 3 "$out/$name.txt" | tr '\n' ' ')"; fi
}

games=("NES=$(game_rom)")
for d in SNES GBA MD:megadrive 32X PCE; do # MD: the first non-empty folder
    rom=
    for f in ${d//:/ }; do
        rom=$(r "ls '/userdata/ROMS/$f' 2>/dev/null | head -n1") || rom=
        [ -z "$rom" ] || { games+=("$f=$rom"); break; }
    done
    [ -n "$rom" ] || say "SKIP ${d%%:*}: no ROM"
done
step games port/scripts/t2-long-play.sh --minutes "$minutes" --log m7/soak/games-long-play "${games[@]}"
step psx port/scripts/t2-long-play.sh --minutes "$minutes" --state /userdata/MUOS/port/t2/ctr-race \
    --log m7/soak/psx-long-play 'PSX=CTR - Crash Team Racing (USA).cue'

n64() { # runs in step's subshell: fail and the EXIT trap stay inside it
    local i t pid pid0
    n64s='/run/muos/storage/pickles/state/mupen64plus_sa/N64/Mario Kart 64 (USA)'; local s=$n64s
    r 'export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; cat /opt/muos/config/settings/general/volume > /run/t2-vol
       /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1; rm -rf /run/t2-n64; mkdir -p /run/t2-n64 "'"$s"'"; cp -a "'"$s"'"/. /run/t2-n64/'
    trap 'r "s=\"${n64s:?}\"; rm -f \"\${s:?}\"/*; cp -a /run/t2-n64/. \"\$s\"/; export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; /opt/muos/script/device/audio.sh \$(cat /run/t2-vol) >/dev/null 2>&1" || :' EXIT
    port/scripts/t2-swapstat.sh arm
    wait_module muxlaunch 40 || fail "not at launcher"
    r 'c=/opt/muos/share/info/content/N64/core.cfg
       printf "%s\n" "Mario Kart 64 (USA)" "$(sed -n 1p $c)" "$(sed -n 2p $c)" 0 0 "$(sed -n 5p $c)" /mnt/mmc/ROMS /N64 "Mario Kart 64 (USA).z64" > /run/muos/content
       cat /opt/muos/share/info/content/N64/core.gov > /run/muos/governor; echo explore > /run/muos/action
       '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
    sleep 20; pid0=$(r 'pidof mupen64plus') || fail "mupen64plus did not start"
    for i in $(seq 1 "$minutes"); do
        sleep 60
        pid=$(r 'pidof mupen64plus') || pid=none; t=$(r 'cat /sys/class/thermal/thermal_zone0/temp')
        echo "min $i pid=$pid temp=$t"
        [ "$pid" = "$pid0" ] || fail "mupen64plus gone after $i min"
    done
    port/scripts/t2-swapstat.sh report 20
    port/scripts/t2-swapstat.sh disarm
    r '/usr/libexec/muos-press fn+start'; sleep 8
    r 'pidof mupen64plus' >/dev/null && fail "mupen64plus still running after Fn+Start"
    r "test -s '$s/autosave.st'" || fail "no autosave on Fn+Start"
    echo "PASS n64: $minutes min, autosave written"
}
step n64 n64
step sleep-game port/scripts/t2-sleep-cycle.sh --game "$cycles"
step sleep-menu port/scripts/t2-sleep-cycle.sh "$cycles"
if [ "$bad" = 0 ]; then say "PASS soak"; else say "FAIL soak: $bad step(s)"; exit 1; fi
