#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: objective audio health without ears. Prints one line per sample:
#   boot=<id8> up=<s> s95=<rc> att=<audio attempts> pcm=<state> rate=<hw_ptr frames/s> path=<n> vol=<l,r>
#   regs=<RK817 codec 0x12..0x4f hex>
# PipeWire keeps hw:0,0 RUNNING, so a healthy codec advances hw_ptr at about
# 44100/s; about half that is the "half-rate after reboot" fault, ~0 a dead
# I2S clock. The codec range is REGCACHE_NONE and has no read-to-clear
# registers, so the i2cget reads are side-effect free.
#   t2-audio-state.sh [--reboots N]   (N warm reboots, one sample after each)
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
echo "boot=$(cut -c1-8 /proc/sys/kernel/random/boot_id) up=$(cut -d. -f1 /proc/uptime) s95=$s95 att=$att pcm=$st rate=$rate path=$path vol=$vol regs=$regs"'
diag='
. /opt/muos/script/var/audio.sh >/dev/null 2>&1
echo "--- diag $(cut -c1-8 /proc/sys/kernel/random/boot_id)"
grep -i -E "core|audio|pipewire" /run/muos-rc.log | tail -8
ls /run/muos/core/; tail -5 /run/muos/core/*.log 2>/dev/null
pidof pipewire wireplumber muxfrontend; wpctl status 2>&1 | sed -n "/Sinks:/,/Sources:/p"
dmesg | grep -i -E "rk817|i2s|asoc|snd" | tail -12
echo "--- end"'
# On a non-RUNNING PCM, collect the evidence before the next reboot loses it.
sample() {
    out=$("$dev" run "$probe"); echo "$out"
    case "$out" in *pcm=RUNNING*) ;; *) "$dev" run "$diag" || : ;; esac
}
n=0; [ "${1:-}" = --reboots ] && n=${2:?}
sample
for _ in $(seq 1 "$n"); do
    "$dev" reboot >/dev/null
    "$dev" wait 180 >/dev/null
    # S95 brings audio up before the menu; let PipeWire settle.
    sleep 20
    sample
done
