#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016,SC2034
# T2 (M8 thermal block): sustained heavy play with one set of power knobs,
# sampled every second on the device (SoC/GPU temperature, CPU/GPU/DMC
# clocks, the CPU and GPU cooling states, battery current) and joined with
# the game's real speed (t2-coremeter.sh: the core's audio frames per
# second; libretro games only).
#   t2-thermal.sh [opts] NAME     log build/logs/m8f/thermal/NAME.{log,txt}
#     --game dc        Power Stone 2 from the user's fight (MUOS/t2/dc-fight-2022)
#     --minutes N      play time (default 8); the summary skips minute 1
#     --cool C         wait in the menu until the SoC is below C (default 55)
#     --cap KHZ        danger/cpu_max for the run (muos-governor applies it)
#     --gpu HZ         GPU devfreq max_freq after the start (520/480/400 MHz)
#     --dmc HZ         DMC devfreq max_freq after the start (786/666/528 MHz)
#     --sp MW          soc-thermal sustainable_power (stock 750)
#     --kpu N --kpo N  soc-thermal power_allocator k_pu / k_po (stock 102/51)
#     --policy P       soc-thermal policy (power_allocator, step_wise)
# Everything is restored on exit; volume 10 for the run.
set -euo pipefail
cd "$(dirname "$0")/../.."
dev=port/scripts/device.sh
# shellcheck source=port/scripts/t2-game.lib.sh
. port/scripts/t2-game.lib.sh
game=dc minutes=8 cool=55 cap='' gpu='' dmc='' sp='' kpu='' kpo='' policy=''
while [ $# -gt 1 ]; do
    case $1 in
    --game) game=$2 ;; --minutes) minutes=$2 ;; --cool) cool=$2 ;; --cap) cap=$2 ;;
    --gpu) gpu=$2 ;; --dmc) dmc=$2 ;; --sp) sp=$2 ;; --kpu) kpu=$2 ;; --kpo) kpo=$2 ;;
    --policy) policy=$2 ;;
    *) fail "unknown option $1" ;;
    esac
    shift 2
done
name=${1:?NAME}
out=build/logs/m8f/thermal; mkdir -p "$out"
tz=/sys/class/thermal/thermal_zone0 g=/sys/class/devfreq/ff400000.gpu d=/sys/class/devfreq/dmc
case $game in
dc) rom="Power Stone 2 (USA).cue" dir=DC game_state=/userdata/MUOS/t2/dc-fight-2022 ;;
*) fail "unknown game $game" ;;
esac

env_pw='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run'
saved=$(r "echo \$(cat /opt/muos/config/settings/general/volume) \$(cat /opt/muos/config/danger/cpu_max) \
    \$(cat $tz/policy) \$(cat $tz/sustainable_power) \$(cat $tz/k_pu) \$(cat $tz/k_po)")
read -r vol capwas polwas spwas kpuwas kpowas <<< "$saved"
restore() {
    r "kill \$(cat /run/t2-thermal.pid 2>/dev/null) 2>/dev/null; rm -f /run/t2-thermal.pid
       echo $capwas > /opt/muos/config/danger/cpu_max
       echo $polwas > $tz/policy; echo $spwas > $tz/sustainable_power; echo $kpuwas > $tz/k_pu; echo $kpowas > $tz/k_po
       echo \$(cat $g/available_frequencies | tr ' ' '\n' | sort -n | tail -1) > $g/max_freq
       echo \$(cat $d/available_frequencies | tr ' ' '\n' | sort -n | tail -1) > $d/max_freq
       $env_pw; /opt/muos/script/device/audio.sh $vol >/dev/null 2>&1" || :
}
trap restore EXIT

# cool down in the menu first, so every run starts from the same point
for _ in $(seq 1 120); do
    t=$(r "cat $tz/temp"); [ $((t / 1000)) -lt "$cool" ] && break; sleep 5
done
start_c=$((t / 1000))
r "$env_pw; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1" || :
[ -z "$cap" ] || r "echo $cap > /opt/muos/config/danger/cpu_max"
[ -z "$policy" ] || r "echo $policy > $tz/policy"
[ -z "$sp" ] || r "echo $sp > $tz/sustainable_power"
[ -z "$kpu" ] || r "echo $kpu > $tz/k_pu"
[ -z "$kpo" ] || r "echo $kpo > $tz/k_po"
port/scripts/t2-coremeter.sh arm
game_start "$rom" "$dir"
sleep 15; r '/usr/libexec/muos-press a'   # the fight state is paused: Cancel
[ -z "$gpu" ] || r "echo $gpu > $g/max_freq"
[ -z "$dmc" ] || r "echo $dmc > $d/max_freq"
port/scripts/t2-coremeter.sh mark
r "rm -f /run/t2-thermal.log; (while :; do read -r up _ < /proc/uptime
     echo \"\${up%.*} \$(cat $tz/temp /sys/class/thermal/thermal_zone1/temp \
       /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq $g/cur_freq $d/cur_freq \
       /sys/class/thermal/cooling_device0/cur_state /sys/class/thermal/cooling_device1/cur_state \
       /sys/class/power_supply/battery/current_now | tr '\n' ' ')\"; sleep 1; done >> /run/t2-thermal.log) \
     </dev/null >/dev/null 2>&1 & echo \$! > /run/t2-thermal.pid"
sleep $((minutes * 60))
r 'cat /run/t2-thermal.log' > "$out/$name.log"
r 'cat /run/coremeter.log 2>/dev/null' > "$out/$name.speed" || :
alive=$(module)
game_stop
port/scripts/t2-coremeter.sh disarm
# Per minute: temperature, clocks, cooling states, battery mA, game speed
# (% of 44100 audio frames/s), its worst second, seconds below 95 %.
{
echo "$name: game $game, cap ${cap:-default} gpu ${gpu:-max} dmc ${dmc:-max} sp ${sp:-750} k_pu ${kpu:-stock} k_po ${kpo:-stock} policy ${policy:-power_allocator}; start ${start_c} C; end module $alive"
awk -v rate=44100 '
    FNR == NR { split($1, s, "."); sp[s[1]] = $2; next }
    { t0 = t0 ? t0 : $1; m = int(($1 - t0) / 60) + 1; n[m]++
      T[m] += $2 / 1000; if ($2 / 1000 > TX[m]) TX[m] = $2 / 1000
      C[m] += $4 / 1000; if (!CN[m] || $4 / 1000 < CN[m]) CN[m] = $4 / 1000
      G[m] += $5 / 1e6; D[m] += $6 / 1e6; Q[m] += $7; QG[m] += $8; B[m] += -$9 / 1000
      if ($1 in sp) { v = sp[$1] * 100 / rate; S[m] += v; SN[m]++
          if (!SW[m] || v < SW[m]) SW[m] = v; if (v < 95) SL[m]++ } }
    END { printf "%3s %5s %5s %6s %6s %5s %5s %5s %5s %6s %6s %5s %4s\n", "min", "temp", "max", "cpu", "cpumin", "gpu", "dmc", "cdev", "gdev", "mA", "speed", "worst", "<95"
          for (i = 1; i in n; i++) {
              printf "%3d %5.1f %5.1f %6.0f %6.0f %5.0f %5.0f %5.1f %5.1f %6.0f %6.1f %5.1f %4d\n", i, T[i]/n[i], TX[i], C[i]/n[i], CN[i], G[i]/n[i], D[i]/n[i], Q[i]/n[i], QG[i]/n[i], B[i]/n[i], SN[i] ? S[i]/SN[i] : 0, SW[i], SL[i]
              if (i > 1) { aT += T[i]; aC += C[i]; aN += n[i]; aS += S[i]; aSN += SN[i]; aL += SL[i]; aB += B[i] } }
          if (aN) printf "min 2+: temp %.1f C, cpu %.0f MHz, %.0f mA, speed %.1f %%, %d s below 95 %%\n", aT/aN, aC/aN, aB/aN, aSN ? aS/aSN : 0, aL }
' "$out/$name.speed" "$out/$name.log"
} | tee "$out/$name.txt"
