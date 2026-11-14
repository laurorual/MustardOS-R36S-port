#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2/T3 (M3e step 3): a logged full battery discharge, down to the
# low-battery poweroff (muos-lowbattery: <= 3% and < 3.5 V for 3 checks)
# or to the PMIC cutting power, whichever comes first.
#   t2-discharge.sh start    charger must be unplugged; plays the NES test
#                            game (r35s-flight.nes: no user saves) and logs
#                            one line a minute to p3 MUOS/log/discharge.csv
#                            (synced each time, survives the power loss);
#                            volume 10 for the run (the user's level is
#                            saved and restored by report)
#   t2-discharge.sh switch DIR ROM   play another game during the run (e.g.
#                            PSX "CTR - Crash Team Racing (USA).cue"): its
#                            states and saves are backed up to p3 first
#   t2-discharge.sh log-start   idle variant (M4a night run): no game; the
#                            logger is a p3 user init script (MUOS/init,
#                            settings/advanced/user_init = 1), so it
#                            restarts after every reboot; extra columns:
#                            boot id, the gauge's coulomb counter (mAh),
#                            rsoc, dsoc and FCC (dbg_level for 6 s a minute)
#   t2-discharge.sh log-stop    removes the init script, restores user_init
#   t2-discharge.sh status   the last log lines
#   t2-discharge.sh report   after the user charged and powered on: pulls
#                            the log, the battery and shutdown logs, prints
#                            a summary, restores resume.ini and the volume,
#                            and puts back the switched game's states and
#                            saves (what the run's autosave wrote is removed)
# Columns: epoch, uptime s, capacity % (kernel), muOS capacity %, status,
# mV, mA (negative = discharging), SoC C, CPU MHz, backlight, game alive.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
logs=$(cd ../.. && pwd)/build/logs; mkdir -p "$logs"
. ./t2-game.lib.sh
csv=/userdata/MUOS/log/discharge.csv
keep=/userdata/MUOS/log/discharge

logger='#!/bin/sh
B=/sys/class/power_supply/battery csv='"$csv"'
[ -s $csv ] || echo "epoch,uptime,cap,muos_cap,status,mv,ma,soc_c,cpu_mhz,backlight,game" > $csv
while :; do
    g=0; for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/muxretro ] && g=1 && break; done
    echo "$(date +%s),$(cut -d" " -f1 /proc/uptime),$(cat $B/capacity),$(cat /run/muos/battery/capacity 2>/dev/null),$(cat $B/status),$(( $(cat $B/voltage_now) / 1000 )),$(( $(cat $B/current_now) / 1000 )),$(( $(cat /sys/class/thermal/thermal_zone0/temp) / 1000 )),$(( $(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq) / 1000 )),$(cat /sys/class/backlight/*/brightness | head -n1),$g" >> $csv
    sync
    sleep 60
done'

# Idle logger, started by S98muos-user-init on every boot (one instance).
plogger='#!/bin/sh
exec 9> /run/muos-discharge-log.lock
flock -n 9 || exit 0
B=/sys/class/power_supply/battery csv='"$csv"' D=/sys/module/rk817_battery/parameters/dbg_level
[ -s $csv ] || echo "epoch,uptime,cap,muos_cap,status,mv,ma,soc_c,cpu_mhz,backlight,game,boot,cc_mah,rsoc,dsoc,fcc" > $csv
boot=$(cut -c1-8 /proc/sys/kernel/random/boot_id)
g() { dmesg | sed -n "s/.*rk817-bat: info: $1 = \\(-*[0-9]*\\).*/\\1/p" | tail -n 1; }
while :; do
    echo 1 > $D; sleep 6; echo 0 > $D
    cc=$(g remain_cap); [ -z "$cc" ] || cc=$((cc / 1000))
    gm=0; for p in /proc/[0-9]*; do [ "$(readlink $p/exe)" = /opt/muos/frontend/muxretro ] && gm=1 && break; done
    echo "$(date +%s),$(cut -d" " -f1 /proc/uptime),$(cat $B/capacity),$(cat /run/muos/battery/capacity 2>/dev/null),$(cat $B/status),$(( $(cat $B/voltage_now) / 1000 )),$(( $(cat $B/current_now) / 1000 )),$(( $(cat /sys/class/thermal/thermal_zone0/temp) / 1000 )),$(( $(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq) / 1000 )),$(cat /sys/class/backlight/*/brightness | head -n1),$gm,$boot,$cc,$(g rsoc),$(g dsoc),$(g FCC)" >> $csv
    sync
    sleep 54
done'
init=/userdata/MUOS/init/zz-discharge-log.sh
ui=/opt/muos/config/settings/advanced/user_init

# The pickles of a played game (states, SRAM) by DIR and ROM name.
rom_paths='p=/userdata/MUOS/pickles; for d in "$p"/state/*/"$dir" "$p"/sram/*/"$dir"; do [ -d "$d" ] || continue; for f in "$d/$n" "$d/$n".*; do [ -e "$f" ] && echo "${f#/}"; done; done'

case "${1:-}" in
switch)
    [ $# -eq 3 ] || { echo 'usage: switch DIR ROM' >&2; exit 2; }
    r "pgrep -f muos-discharge-log >/dev/null" || fail 'no discharge run in progress'
    d=$2 rom=$3 n=${3%.*}
    r "test -f '/userdata/ROMS/$d/$rom'" || fail "no ROM $d/$rom"
    # start played the NES test game (its pickles snapshot is in /run).
    game_rom_name=${DISCHARGE_FROM:-r35s-flight} game_dir=${DISCHARGE_FROM_DIR:-NES}
    game_stop
    r "dir='$d' n='$n'; $rom_paths" > "$logs/discharge-switch.paths"
    r "cd /; dir='$d' n='$n'; l=\$($rom_paths); printf '%s\t%s\n' '$d' '$n' > $keep/game; if [ -n \"\$l\" ]; then printf '%s\n' \"\$l\" | tar -cf $keep/game-before.tar -T -; else rm -f $keep/game-before.tar; fi; sync"
    game_start "$rom" "$d"
    echo "switched to $d/$rom (backed up: $(wc -l < "$logs/discharge-switch.paths") paths)"
    ;;
start)
    [ "$(r 'cat /sys/class/power_supply/battery/status')" = Discharging ] ||
        fail 'battery not discharging: unplug the charger first'
    [ "$(r 'cat /sys/class/power_supply/ac/online /sys/class/power_supply/usb/online' | tr -d '\n')" = 00 ] ||
        fail 'charger still online'
    r "pgrep -f muos-discharge-log >/dev/null" && fail 'a discharge log is already running'
    r "mkdir -p $keep; rm -f $csv; cp -a /userdata/MUOS/pickles/resume.ini $keep/resume.ini.before 2>/dev/null; :"
    r "cat /opt/muos/config/settings/general/volume > $keep/volume.before; export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run; /opt/muos/script/device/audio.sh 10 >/dev/null 2>&1"
    printf '%s\n' "$logger" | r 'cat > /run/muos-discharge-log && chmod +x /run/muos-discharge-log'
    game_start r35s-flight.nes NES
    r 'setsid nohup /run/muos-discharge-log > /dev/null 2>&1 < /dev/null &'
    sleep 3
    r "cat $csv"
    echo "started: NES test game + discharge log ($csv)"
    ;;
log-start)
    [ "$(r 'cat /sys/class/power_supply/battery/status')" = Discharging ] ||
        fail 'battery not discharging: unplug the charger first'
    r "pgrep -f '[m]uos-discharge-log|[z]z-discharge-log' >/dev/null" && fail 'a discharge log is already running'
    r "mkdir -p $keep /userdata/MUOS/init; rm -f $csv; cat $ui > $keep/user_init.before 2>/dev/null || echo 0 > $keep/user_init.before"
    printf '%s\n' "$plogger" | r "cat > $init.tmp && mv $init.tmp $init && echo 1 > $ui && sync"
    r "setsid sh $init < /dev/null > /dev/null 2>&1 &"
    sleep 9
    r "cat $csv"
    echo "started: idle discharge log ($csv), restarted at every boot by $init"
    ;;
log-stop)
    r "pkill -f '[z]z-discharge-log'; rm -f $init; cp $keep/user_init.before $ui 2>/dev/null || echo 0 > $ui; echo 0 > /sys/module/rk817_battery/parameters/dbg_level; sync"
    echo stopped
    ;;
status)
    r "wc -l < $csv; tail -n 3 $csv"
    ;;
report)
    out=$logs/discharge; rm -rf "$out"; mkdir -p "$out"
    "$dev" scp "dev:$csv" "$out/discharge.csv" > /dev/null 2>&1 || fail 'no discharge log on p3'
    r 'cd /userdata/MUOS/log; for d in system system.prev system.prev2 system.prev3; do [ -f $d/battery-port.log ] && { echo "== $d"; cat $d/battery-port.log; }; done; echo "== rc-last"; cat rc-last.log' > "$out/battery-and-shutdown.txt" 2>&1
    r "[ -f $keep/resume.ini.before ] && cp -a $keep/resume.ini.before /userdata/MUOS/pickles/resume.ini; sync" || :
    r "[ -f $keep/game ] || exit 0; IFS='	' read -r dir n < $keep/game; cd / && $rom_paths | while IFS= read -r f; do rm -rf \"/\$f\"; done; [ ! -f $keep/game-before.tar ] || tar -xf $keep/game-before.tar -C /; rm -f $keep/game; sync" || :
    r "v=\$(cat $keep/volume.before 2>/dev/null) && export PIPEWIRE_RUNTIME_DIR=/run XDG_RUNTIME_DIR=/run && /opt/muos/script/device/audio.sh \$v >/dev/null 2>&1" || :
    python3 -I - "$out/discharge.csv" "$out/battery-and-shutdown.txt" <<'PY'
import csv, sys
rows = [r for r in csv.DictReader(open(sys.argv[1])) if r["mv"]]
if not rows:
    sys.exit("FAIL empty log")
first, last = rows[0], rows[-1]
mins = (int(last["epoch"]) - int(first["epoch"])) / 60
mah = sum(-int(r["ma"]) for r in rows if int(r["ma"]) < 0) / 60
jumps = [(a["cap"], b["cap"], b["epoch"]) for a, b in zip(rows, rows[1:])
         if abs(int(b["cap"]) - int(a["cap"])) > 2]
print(f"run: {mins:.0f} min, {first['cap']}% {first['mv']} mV -> {last['cap']}% {last['mv']} mV")
print(f"drawn: ~{mah:.0f} mAh (1-min samples), mean {mah / max(mins, 1) * 60:.0f} mA")
print(f"% jumps > 2 between samples: {len(jumps)} {jumps[:5]}")
for lo in (25, 10, 5, 3):
    hit = next((r for r in rows if int(r["cap"]) <= lo), None)
    if hit:
        print(f"first <= {lo}%: {hit['mv']} mV after {(int(hit['epoch']) - int(first['epoch'])) / 60:.0f} min")
txt = open(sys.argv[2]).read()
clean = "critical battery" in txt
print("end:", "clean low-battery poweroff (muos-lowbattery)" if clean
      else "no low-battery poweroff logged: power was cut (PMIC) or the run was stopped")
gauge = [l for l in txt.splitlines() if "muos-gauge: boot" in l]
if gauge:
    print("first boot after:", gauge[0].split("muos-gauge: ", 1)[1][:160])
PY
    echo "details: $out"
    ;;
*) echo 'usage: t2-discharge.sh start|switch DIR ROM|status|report' >&2; exit 2 ;;
esac
