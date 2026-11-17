#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: in-game frame rate while volume / brightness change (M3b T3 report:
# fps drops during the change, recovers after). Runs NES (t2-game.lib.sh)
# with muxretro's frame-time capture and measures one 15 s phase per
# capture dump (performance.csv every 15 s): the frames from 14.5 s to 1 s
# before the dump, i.e. while the phase's action ran. Per phase: fps
# (frames / time), p95 and max frame interval, frames > 20 ms, the whole-SoC
# CPU busy % (4 cores = 400) and muxretro's own CPU %.
#   t2-level-fps.sh [--diag | --phases "P..."] [--max-drop PCT] [--max-slow N]
#                   [--max-missed N] [LABEL]
# Phases: base (no input), vol (Vol+/Vol- presses via muos-press, i.e.
# muhotkey -> audio.sh -> wpctl, plus the overlay), bright (Menu+Vol);
# vol-hold / bright-hold (M3e: the key held 1 s down, then 1 s up, so
# muhotkey repeats; gated like vol/bright; levels restored at the end).
# --diag adds: vol-script (audio.sh's wpctl calls alone) and bright-script
# (bright.sh transient: no config write), both without the overlay;
# vol-osd / bright-osd (the overlay alone: the config value written, no
# script, no hardware change). --phases only: vol-sh (audio.sh run from the
# shell, overlay included, no key event); custom (the device shell action
# in $LEVEL_CUSTOM, for experiments). A trailing digit repeats a phase.
# Findings (M3b, docs/hardware-findings.md): base 0 frames > 20 ms; the
# overlay alone ~1 dropped frame per change; vol 30-70 per phase, noisy.
# FAIL when vol or bright is more than --max-drop % (default 3) below base,
# or has more than --max-slow frames > 20 ms or --max-missed frames > 25 ms
# (1.5 refresh periods: a frame shown twice; unset: not checked). M3d step 3
# gate: --max-slow 6 --max-missed 0 (options in this order).
# Summary on stdout; details in build/logs/level-fps.log.
set -euo pipefail
# shellcheck disable=SC2034 # kept for the sourced helpers
dev=$(dirname "$0")/device.sh
logs=$(cd "$(dirname "$0")/../.." && pwd)/build/logs; mkdir -p "$logs"
phases="base vol bright"
[ "${1:-}" = --diag ] && { phases="$phases vol-script bright-script vol-osd bright-osd base2"; shift; }
[ "${1:-}" = --phases ] && { phases=$2; shift 2; }
maxdrop=3; [ "${1:-}" = --max-drop ] && { maxdrop=$2; shift 2; }
maxslow=; [ "${1:-}" = --max-slow ] && { maxslow=$2; shift 2; }
maxmiss=; [ "${1:-}" = --max-missed ] && { maxmiss=$2; shift 2; }
label=${1:-run}
. "$(dirname "$0")/t2-game.lib.sh"

# One phase on the device: wait for a dump, run ACTION repeatedly for 14 s,
# wait for the next dump, print "NAME fps p95 max slow busy% retro%".
phase() { # NAME ACTION
    r 'csv=/run/muos/storage/pickles/performance.csv
       dump() { m0=$(stat -c %Y $csv 2>/dev/null || echo 0); i=0
                while [ "$(stat -c %Y $csv 2>/dev/null || echo 0)" = "$m0" ]; do
                    i=$((i+1)); [ $i -lt 250 ] || return 1; sleep 0.1; done; sleep 0.3; }
       cpu() { awk "/^cpu /{print \$2+\$3+\$4+\$7+\$8, \$5+\$6}" /proc/stat; }
       rpid=$('"$(pids_of muxretro)"' | head -n1)
       rcpu() { awk "{print \$14+\$15}" /proc/$rpid/stat; }
       dump || { echo "'"$1"' no-dump"; exit 0; }
       set -- $(cpu); b0=$1 i0=$2; r0=$(rcpu); t0=$(cut -d" " -f1 /proc/uptime)
       end=$(( $(date +%s) + 14 ))
       while [ "$(date +%s)" -lt $end ]; do '"$2"'; done
       set -- $(cpu); b1=$1 i1=$2; r1=$(rcpu); t1=$(cut -d" " -f1 /proc/uptime)
       dump || { echo "'"$1"' no-dump"; exit 0; }
       awk -v name='"$1"' -v busy=$(( (b1-b0) * 400 / (b1-b0+i1-i0+1) )) \
           -v retro="$(awk -v a=$r0 -v b=$r1 -v t0=$t0 -v t1=$t1 "BEGIN{printf \"%d\", (b-a)/(t1-t0)}")" "
         /^frame_interval_ms/ {on=1; next} on && !NF {on=0} on {f[n++]=\$1}
         END { t=0; k=0
           for (i=n-1; i>=0; i--) { t+=f[i]; if (t<1000) continue; if (t>14500) break; v[k++]=f[i]; s+=f[i]; if (f[i]>20) slow++; if (f[i]>25) miss++; if (f[i]>mx) mx=f[i] }
           if (!k) { print name, \"no-frames\"; exit }
           for (i=0;i<k;i++) for (j=i+1;j<k;j++) if (v[j]<v[i]) { x=v[i]; v[i]=v[j]; v[j]=x }
           printf \"%s %.2f %.2f %.2f %d %d %d %d\\n\", name, k*1000/s, v[int(k*0.95)], mx, slow, busy, retro, miss }" $csv
       cp $csv /run/level-fps-'"$1"'.csv'
}
cfg=/opt/muos/config/settings/general
scr=/opt/muos/script/device
# Alternate up/down so the level stays where it was.
p_vol='/usr/libexec/muos-press volup voldown'
p_bright='/usr/libexec/muos-press fn+volup fn+voldown'
p_vol_hold='MUOS_PRESS_HOLD=1 /usr/libexec/muos-press hold:voldown hold:volup'
p_bright_hold='MUOS_PRESS_HOLD=1 /usr/libexec/muos-press hold:fn+voldown hold:fn+volup'
wp='export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; wpctl get-volume @DEFAULT_AUDIO_SINK@ >/dev/null; wpctl set-volume @DEFAULT_AUDIO_SINK@'
p_vol_script="v=\$(cat $cfg/volume); $wp \$((v+5))%; wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; sleep 0.5; $wp \$v%; wpctl set-mute @DEFAULT_AUDIO_SINK@ 0; sleep 0.5"
p_bright_script="$scr/bright.sh U transient; sleep 0.5; $scr/bright.sh D transient; sleep 0.5"
p_vol_sh="export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; $scr/audio.sh U; sleep 0.5; $scr/audio.sh D; sleep 0.5"
p_vol_osd="v=\$(cat $cfg/volume); echo \$((v+5)) > $cfg/volume; sleep 0.65; echo \$v > $cfg/volume; sleep 0.65"
p_bright_osd="v=\$(cat $cfg/brightness); echo \$((v+5)) > $cfg/brightness; sleep 0.65; echo \$v > $cfg/brightness; sleep 0.65"

# Action for a phase name; a trailing digit repeats a phase (vol-sh2).
action() {
    case ${1%[0-9]} in
        base) echo 'sleep 1' ;;
        vol) echo "$p_vol" ;; bright) echo "$p_bright" ;;
        vol-hold) echo "$p_vol_hold" ;; bright-hold) echo "$p_bright_hold" ;;
        # audio.sh writes the volume config itself, so vol-script runs its
        # wpctl calls (the costly part) directly instead.
        vol-script) echo "$p_vol_script" ;; bright-script) echo "$p_bright_script" ;;
        vol-sh) echo "$p_vol_sh" ;;
        vol-osd) echo "$p_vol_osd" ;; bright-osd) echo "$p_bright_osd" ;;
        custom) [ -n "${LEVEL_CUSTOM:-}" ] && echo "$LEVEL_CUSTOM" ;;
        *) return 1 ;;
    esac
}
for p in $phases; do action "$p" > /dev/null || fail "unknown phase $p"; done

rom=$(game_rom)
r "echo \$(cat $cfg/volume) \$(cat $cfg/brightness)" > "$logs/level-fps.before"
game_start "$rom"
sleep 8
out=$logs/level-fps.phases; : > "$out"
for p in $phases; do phase "$p" "$(action "$p")" >> "$out"; done
game_stop
# Hold phases drift the levels: put back what was there before.
read -r v0 b0 < "$logs/level-fps.before"
r "export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; $scr/audio.sh $v0; $scr/bright.sh $b0" > /dev/null 2>&1 || :
# Each phase's capture (with muxretro's slow_frames stage trace): host copy
# and a per-phase summary of what the slow frames spent their time on.
rm -rf "$logs/level-fps"; mkdir -p "$logs/level-fps"
r 'cd /run && tar -cf - level-fps-*.csv' | tar -xf - -C "$logs/level-fps" || :
r 'rm -f /run/level-fps-*.csv'
python3 "$(dirname "$0")/slow-frames.py" "$logs/level-fps"/*.csv > "$logs/level-fps/slow-frames.txt" 2>&1 || :
r "echo \$(cat $cfg/volume) \$(cat $cfg/brightness)" > "$logs/level-fps.after"
cmp -s "$logs/level-fps.before" "$logs/level-fps.after" || echo "WARN volume/brightness changed: $(cat "$logs/level-fps.before") -> $(cat "$logs/level-fps.after")"
summary=$(awk -v label="$label" -v maxdrop="$maxdrop" -v slowmax="$maxslow" -v missmax="$maxmiss" '
  $2 !~ /^[0-9.]+$/ { bad=bad " " $1 "=" $2; next }
  { fps[$1]=$2; slow[$1]=$5; miss[$1]=$8; line=line sprintf(" %s=%.1ffps(p95 %.1f max %.0f slow %d missed %d cpu %d%% retro %d%%)", $1, $2, $3, $4, $5, $8, $6, $7) }
  END {
    if (bad != "" || !fps["base"]) { printf "FAIL level-fps %s: phases without data:%s\n", label, bad; exit }
    r="PASS"; for (p in fps) if ((p ~ /^(vol|bright)(-hold)?$/) && fps[p] < fps["base"]*(1-maxdrop/100)) r="FAIL"
    if (slowmax != "") for (p in slow) if ((p ~ /^(vol|bright)(-hold)?$/) && slow[p] > slowmax+0) r="FAIL"
    if (missmax != "") for (p in miss) if ((p ~ /^(vol|bright)(-hold)?$/) && miss[p] > missmax+0) r="FAIL"
    printf "%s level-fps %s:%s\n", r, label, line }' "$out")
{ date -u +%FT%TZ; echo "$summary"; cat "$out"; } >> "$logs/level-fps.log"
echo "$summary"
