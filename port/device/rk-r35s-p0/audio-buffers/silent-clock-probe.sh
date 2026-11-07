#!/bin/sh
# SPDX-License-Identifier: MIT
# Run only in the existing session mount namespace helper, under a held lease
# lock. PCM input is digital zero; no microphone, UI or tone is opened.
set -eu
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
dir=${1:-}
route=${2:-original}
case "$route" in original|profile215) ;; *) exit 64 ;; esac
case "$dir" in /run/muos-clock.??????) ;; *) exit 64 ;; esac
[ -d "$dir" ] && [ ! -L "$dir" ]
[ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
if findmnt -rn -M /sys/kernel/debug >/dev/null; then exit 64; fi
[ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
amixer -c 0 contents > "$dir/mixer-before.txt"
alsactl -f "$dir/mixer.state" store 0
mounted=0; player=; player_start=
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ -n "$player" ] && [ -r /proc/"$player"/stat ] &&
       [ "$(awk '{print $22}' /proc/"$player"/stat)" = "$player_start" ]; then
        kill -TERM "$player" 2>/dev/null || :
        wait "$player" 2>/dev/null || :
    fi
    alsactl -f "$dir/mixer.state" restore 0 || result=1
    amixer -c 0 contents > "$dir/mixer-after.txt" || result=1
    cmp "$dir/mixer-before.txt" "$dir/mixer-after.txt" || result=1
    [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ] || result=1
    if [ "$mounted" = 1 ]; then umount /sys/kernel/debug || result=1; fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 143' HUP INT TERM
mount -t debugfs -o ro,nosuid,nodev,noexec debugfs /sys/kernel/debug
mounted=1
variants='MMAP_S32_LE MMAP_S16_LE RW_SMALL_S32_LE'
if [ "$route" = profile215 ]; then
    amixer -c 0 cset name='Playback Path' SPK_HP > "$dir/route-set.log"
    amixer -c 0 cset name='Playback Volume' 215,215 > "$dir/gain-set.log"
    amixer -c 0 cget name='Playback Path' | grep -qx '  : values=3'
    amixer -c 0 cget name='Playback Volume' | grep -qx '  : values=215,215'
    amixer -c 0 contents > "$dir/mixer-active.txt"
    variants=MMAP_S32_LE
fi
for variant in $variants; do
    case "$variant" in
        MMAP_S32_LE) format=S32_LE; set -- -M ;;
        MMAP_S16_LE) format=S16_LE; set -- -M ;;
        RW_SMALL_S32_LE) format=S32_LE; set -- ;;
    esac
    /usr/libexec/muos-session/bin/muos-run-bounded 12 \
        /usr/bin/aplay -q "$@" -D hw:0,0 -t raw -f "$format" -c 2 -r 44100 \
        --period-size=512 --buffer-size=2048 -d 5 /dev/zero \
        > "$dir/$variant-player.log" 2>&1 &
    player=$!
    player_start=$(awk '{print $22}' /proc/"$player"/stat)
    sleep 1
    cat /proc/asound/card0/pcm0p/sub0/hw_params > "$dir/$variant-params.txt"
    { echo UPTIME; cat /proc/uptime; cat /proc/asound/card0/pcm0p/sub0/status; } > "$dir/$variant-first.txt"
    awk 'NR<3 || /i2s1|pll_gpll|pll_npll/' /sys/kernel/debug/clk/clk_summary > "$dir/$variant-clocks.txt"
    sleep 2
    { echo UPTIME; cat /proc/uptime; cat /proc/asound/card0/pcm0p/sub0/status; } > "$dir/$variant-second.txt"
    wait "$player"; player=
    [ "$(cat /proc/asound/card0/pcm0p/sub0/status)" = closed ]
done
echo SILENT_PCM_MMAP_AND_SMALL_RW_COMPLETE
