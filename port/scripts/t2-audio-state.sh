#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: objective audio health without ears. One line per sample, then a verdict:
#   boot=<id8> up=<s> s95=<rc> att=<audio attempts> pcm=<state> rate=<hw_ptr frames/s>
#   streams=<PipeWire output streams: binaries> sdl=<this boot's SDL audio init>
#   sdlopen=<driver@rate of a fresh SDL client (muos-sdl-audio-probe)>
#   path=<n> vol=<l,r> regs=<RK817 codec 0x12..0x4f hex>
#   PASS|FAIL audio <reasons>
# Healthy with the UI (menu or game) up: the frontend's SDL_mixer device or
# muxretro holds a PipeWire output stream, so hw:0,0 is RUNNING and hw_ptr
# advances at about 44100/s. About half that is the "half-rate after
# reboot" fault, ~0 a dead I2S clock; pcm=closed with no stream is the M3a
# fault (SDL2 built without its pipewire driver: "SDL Init Failed").
# The codec range is REGCACHE_NONE and has no read-to-clear registers, so
# the i2cget reads are side-effect free.
#   t2-audio-state.sh [--reboots N]   (N warm reboots, one sample after each)
# Exit status: 0 if every sample passed.
set -euo pipefail
dev=$(dirname "$0")/device.sh
probe='
s=/proc/asound/card0/pcm0p/sub0/status
st=$(sed -n "s/^state: //p" $s); st=${st:-closed}
rate=0
if [ "$st" = RUNNING ]; then
    a=$(sed -n "s/hw_ptr *: //p" $s); t1=$(cut -d" " -f1 /proc/uptime); sleep 2
    b=$(sed -n "s/hw_ptr *: //p" $s); t2=$(cut -d" " -f1 /proc/uptime)
    rate=$(awk -v a="$a" -v b="$b" -v t1="$t1" -v t2="$t2" "BEGIN{printf \"%d\", (b-a)/(t2-t1)}")
fi
path=$(amixer -c0 cget numid=1 | sed -n "s/.*: values=//p")
vol=$(amixer -c0 cget numid=3 | sed -n "s/.*: values=//p")
# BusyBox i2cget parses a bare number as hex: always pass 0x-prefixed.
regs=; r=18; while [ $r -le 79 ]; do regs="$regs$(i2cget -f -y 0 0x20 "$(printf 0x%02x $r)" b | cut -c3-)"; r=$((r+1)); done
att=$(cat /run/muos/core/audio-attempts 2>/dev/null); s95=$(sed -n "s/.*S95muos-core start rc=\([0-9]*\).*/\1/p" /run/muos-rc.log)
streams=$(XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run pw-dump 2>/dev/null | awk -F\" "
    /\"application.process.binary\"/ {b=\$4} /\"media.class\": \"Stream\\/Output\\/Audio\"/ {o=o (o?\",\":\"\") (b?b:\"?\")}
    /^  [}]/ {b=\"\"} END {print o}")
# This boot: the uptime prefix ([15.68]) restarts at each boot of the day.
log=$(ls /userdata/MUOS/log/system/*_audio.log 2>/dev/null | tail -n1)
sdl=$(awk -F"[][]" "{u=\$2+0} u<p {ok=0; bad=0} {p=u} /SDL Init Success/ {ok++} /SDL Init Failed/ {bad++}
    END {print (bad ? \"fail\" bad : (ok ? \"ok\" : \"none\"))}" ${log:-/dev/null})
# A fresh SDL client with the frontend environment (silence, 1 s).
o=$(XDG_RUNTIME_DIR=/run PIPEWIRE_RUNTIME_DIR=/run SDL_AUDIODRIVER=pipewire /usr/libexec/muos-sdl-audio-probe 1 2>&1 | grep -E "^(OK|FAIL)")
case "$o" in OK*) sdlopen=$(echo "$o" | sed -n "s/.*driver=\([^ ]*\) freq=\([0-9]*\).*/\1@\2/p");; *) sdlopen=fail;; esac
echo "boot=$(cut -c1-8 /proc/sys/kernel/random/boot_id) up=$(cut -d. -f1 /proc/uptime) s95=$s95 att=$att pcm=$st rate=$rate streams=${streams:-none} sdl=$sdl sdlopen=$sdlopen path=$path vol=$vol regs=$regs"'
diag='
. /opt/muos/script/var/audio.sh >/dev/null 2>&1
echo "--- diag $(cut -c1-8 /proc/sys/kernel/random/boot_id)"
grep -i -E "core|audio|pipewire" /run/muos-rc.log | tail -8
ls /run/muos/core/; tail -5 /run/muos/core/*.log 2>/dev/null
pidof pipewire wireplumber muxfrontend; wpctl status 2>&1 | sed -n "/Sinks:/,/Sources:/p"
dmesg | grep -i -E "rk817|i2s|asoc|snd" | tail -12
echo "--- end"'
verdict() { # the probe line -> PASS/FAIL with every failed criterion
    local why='' v
    v=$(sed -n 's/.* pcm=\([^ ]*\).*/\1/p' <<< "$1"); [ "$v" = RUNNING ] || why+=" pcm=$v"
    v=$(sed -n 's/.* rate=\([0-9]*\).*/\1/p' <<< "$1")
    (( ${v:-0} >= 40000 && ${v:-0} <= 50000 )) || why+=" rate=${v:-?}"
    v=$(sed -n 's/.* streams=\([^ ]*\).*/\1/p' <<< "$1"); [ "$v" != none ] || why+=" no-stream"
    v=$(sed -n 's/.* sdl=\([^ ]*\).*/\1/p' <<< "$1"); [ "$v" = ok ] || why+=" sdl=$v"
    v=$(sed -n 's/.* sdlopen=\([^ ]*\).*/\1/p' <<< "$1"); [ "$v" = pipewire@44100 ] || why+=" sdlopen=${v:-?}"
    if [ -z "$why" ]; then echo 'PASS audio'; else echo "FAIL audio:$why"; return 1; fi
}
# On a failed sample, collect the evidence before the next reboot loses it.
sample() {
    out=$("$dev" run "$probe"); echo "$out"
    verdict "$out" && return 0
    "$dev" run "$diag" || :
    return 1
}
n=0 bad=0; [ "${1:-}" = --reboots ] && n=${2:?}
sample || bad=$((bad + 1))
for _ in $(seq 1 "$n"); do
    "$dev" reboot >/dev/null
    "$dev" wait 180 >/dev/null
    # S95 brings audio up before the menu; let PipeWire settle.
    sleep 20
    sample || bad=$((bad + 1))
done
echo "audio samples: $((n + 1)) failed: $bad"
[ "$bad" -eq 0 ]
