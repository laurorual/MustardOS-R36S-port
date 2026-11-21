#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M8, M8 T3 3: PSP slow): presented frames/s of the standalone PPSSPP
# from a fixed save state, per settings variant. Launches through the
# frontend content handoff (as t2-game.lib.sh), boots the state
# (/run/muos/ppsspp-state -> muos-ppsspp --state=), frame timing by
# swapstat.so (t2-swapstat.sh build/arm), quits with SIGTERM. The user's
# ppsspp.ini is copied before and put back afterwards; KEY=VALUE arguments
# are set in the copy the run uses (keys are unique in ppsspp.ini). With
# FrameSkip = 0 presented frames = emulated frames (God of War: 30 = full
# speed); CPU MHz and SoC temperature are sampled.
#   t2-psp-fps.sh LABEL [SECS] [KEY=VALUE...]
#   env: T2_PSP_CORE (default ext-ppsspp-2021, the PSP default; ext-ppsspp
#        = v1.20.4), T2_CAP (CPU cap kHz), T2_PSP_ROM (default God of War), T2_PSP_STATE (PPSSPP_STATE file),
#        T2_PSP_EMU (the PPSSPPSDL directory, default the image's),
#        T2_PSP_BYKEY=1: v1.12.3 dies (SIGBUS) loading a state from the
#        command line: the state goes to slot 0 for the run (the user's
#        slot 0 kept in /run and put back), the game boots and L3 (Load
#        State) loads it after 30 s
#        T2_PSP_GRAB=1: a screenshot every 5 s (t2-swapstat.sh grab) into
#        build/logs/m8/psp-LABEL-N.png
set -euo pipefail
dev=$(dirname "$0")/device.sh
repo=$(cd "$(dirname "$0")/../.." && pwd)
label=${1:?label}; secs=${2:-40}; shift; [ $# -gt 0 ] && shift
logs=$repo/build/logs/m8; mkdir -p "$logs"
rom=${T2_PSP_ROM:-God of War - Chains of Olympus (USA).iso}
state=${T2_PSP_STATE:-/userdata/MUOS/port/ppsspp/PSP/PPSSPP_STATE/UCUS98653_1.00_0.ppst}
# shellcheck source=port/scripts/t2-game.lib.sh
. "$(dirname "$0")/t2-game.lib.sh"
ini=/userdata/MUOS/port/ppsspp/PSP/SYSTEM/ppsspp.ini
[ "${T2_PSP_CORE:-ext-ppsspp-2021}" = ext-ppsspp ] || ini=/userdata/MUOS/port/ppsspp-2021/ppsspp/PSP/SYSTEM/ppsspp.ini
r "test -f '$state' && test -f '/userdata/ROMS/PSP/$rom'" || fail "missing state or ROM"
# volume 10 for the run (T2 rule); T2_CAP: CPU cap in kHz for the run
env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
vol=$(r 'cat /opt/muos/config/settings/general/volume') capwas=$(r 'cat /opt/muos/config/danger/cpu_max')
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1" || :
[ -z "${T2_CAP:-}" ] || r "echo $T2_CAP > /opt/muos/config/danger/cpu_max"
trap 'r "${trap_slot:-} cp -a /run/t2-ppsspp.ini.user $ini 2>/dev/null; rm -f /run/muos/ppsspp-state /run/muos/ppsspp-emu /run/muos/perf-capture; echo $capwas > /opt/muos/config/danger/cpu_max; $env_pw; /opt/muos/script/device/audio.sh $vol >/dev/null 2>&1" || :' EXIT
for kv in "$@"; do printf 's|^%s = .*|%s = %s|\n' "${kv%%=*}" "${kv%%=*}" "${kv#*=}"; done |
    r "cat > /run/t2-ppsspp.sed; cp -a $ini /run/t2-ppsspp.ini.user; sed -i -f /run/t2-ppsspp.sed $ini"
stick=/userdata/MUOS/port/ppsspp; [ "${T2_PSP_CORE:-ext-ppsspp-2021}" = ext-ppsspp ] || stick=/userdata/MUOS/port/ppsspp-2021/ppsspp
slot=$stick/PSP/PPSSPP_STATE/UCUS98653_1.00_0.ppst
if [ -n "${T2_PSP_BYKEY:-}" ]; then
    r "cp -a '$slot' /run/t2-slot0.ppst && cp '$state' '$slot'" || fail "slot 0 swap"
    trap_slot="cp -a /run/t2-slot0.ppst '$slot';"
else
    r "printf '%s\n' '$state' > /run/muos/ppsspp-state"
fi
r " ${T2_PSP_EMU:+echo '$T2_PSP_EMU' > /run/muos/ppsspp-emu;} echo 1 > /dev/null"
"$(dirname "$0")/t2-swapstat.sh" arm
wait_module muxlaunch 5 || { for _ in 1 2 3; do r "/usr/libexec/muos-press b"; sleep 2; done; wait_module muxlaunch 10 || fail "not at launcher"; }
core=${T2_PSP_CORE:-ext-ppsspp-2021}
r 'printf "%s\n" "t2" '"$core"' "Sony PlayStation Portable" 0 0 '"$core"' /mnt/mmc/ROMS /PSP "'"$rom"'" > /run/muos/content
   echo performance > /run/muos/governor; echo explore > /run/muos/action
   '"$(pids_of muxfrontend)"' | while read -r q; do kill -TERM "$q"; done'
for _ in $(seq 1 20); do r 'pidof PPSSPPSDL >/dev/null' && break; sleep 1; done
r 'pidof PPSSPPSDL >/dev/null' || fail "PPSSPP did not start"
if [ -n "${T2_PSP_BYKEY:-}" ]; then sleep 30; r '/usr/libexec/muos-press l3'; fi
sleep 15  # boot + state load (the report skips the first 15 s of swaps)
: > "$logs/psp-$label.samples"
for i in $(seq 1 $((secs / 5))); do
    sleep 5
    [ -z "${T2_PSP_GRAB:-}" ] || "$(dirname "$0")/t2-swapstat.sh" grab "$logs/psp-$label-$i.png" >/dev/null || :
    r 'echo "$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq) $(cat /sys/class/thermal/thermal_zone0/temp) $(cat /sys/class/devfreq/dmc/cur_freq) $(cat /sys/class/devfreq/ff400000.gpu/cur_freq)"' >> "$logs/psp-$label.samples"
done
rep=$("$(dirname "$0")/t2-swapstat.sh" report $(( ${T2_PSP_BYKEY:+30} + 15 )))
r 'cp /run/swapstat.log /run/t2-psp-swap.log; kill -TERM $(pidof PPSSPPSDL) 2>/dev/null; rm -f /run/muos/ppsspp-state /run/muos/ppsspp-emu /run/muos/perf-capture'
sleep 4
wait_module muxplore 20 || :
for _ in 1 2 3; do [ "$(module)" = muxlaunch ] && break; r '/usr/libexec/muos-press b'; sleep 2; done
hw=$(awk '{m+=$1; if ($2>t) t=$2; d=$3; g=$4; n++} END {if (n) printf "cpu %.0f MHz, max %.1f C, ddr %d MHz, gpu %d MHz", m/n/1000, t/1000, d/1e6, g/1e6}' "$logs/psp-$label.samples")
line="$(date -u +%FT%TZ) psp $label [$*]: $rep; $hw"
echo "$line" | tee -a "$logs/psp-fps.log"
