#!/bin/sh
# SPDX-License-Identifier: MIT
# T2 helper, runs on the device (device.sh run "sh -s PROC" < t2-threads.sh):
# per-thread CPU % of one core and voluntary context switches/s over 5 s for process $1 (device side)
p=$(pidof "$1") || exit 1
snap() { for t in /proc/$p/task/*; do echo "${t##*/} $(cut -d')' -f2 $t/stat | awk '{print $12+$13}') $(awk '/^voluntary/{print $2}' $t/status) $(cat $t/comm)"; done; }
snap > /tmp/t0; sleep 5; snap > /tmp/t1
awk 'NR==FNR{a[$1]=$2; c[$1]=$3; next} {d=$2-a[$1]; if (d>5) printf "%s %d%% vcs/s=%d %s\n", $1, d/5, ($3-c[$1])/5, $4}' /tmp/t0 /tmp/t1 | sort -k2 -n -r
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq /sys/class/thermal/thermal_zone0/temp
