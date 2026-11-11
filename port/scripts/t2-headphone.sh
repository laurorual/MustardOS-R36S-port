#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2: headphone switching + per-output volume without hands. Flipping
# device/config/audio/jack_inverted (tmpfs copy) makes muos-headphone see a
# plug/unplug. Checks the Playback Path, the muOS headphone flag and that
# each output restores its own level (set through muOS device/audio.sh, as
# the volume keys do). Leaves the speaker at its starting level.
set -euo pipefail
dev=$(dirname "$0")/device.sh
r() { "$dev" run ". /opt/muos/script/var/audio.sh >/dev/null 2>&1; cd /; $*"; }
inv=/opt/muos/device/config/audio/jack_inverted
fail() { echo "FAIL $*"; r 'tail -6 /opt/muos/log/headphone.log' || :; r "rm -f $inv" || :; exit 1; }
state() { r 'printf "%s %s %s\n" "$(amixer -c0 sget "Playback Path" | sed -n "s/.*Item0: .\(.*\)./\1/p")" \
    "$([ -e /run/muos/headphones ] && echo hp || echo spk)" \
    "$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk "{printf \"%d\", \$2*100+0.5}")"'; }
expect() { got=$(state); [ "$got" = "$1" ] || fail "$2: want '$1' got '$got'"; echo "ok $2: $got"; }
r "[ ! -e $inv ]" || fail "jack_inverted already set"
spk=$(r 'GET_SAVED_AUDIO_VOLUME')
expect "SPK_HP spk $spk" "start"
r "echo 1 > $inv"; sleep 3
hp=$(r 'GET_SAVED_AUDIO_VOLUME')
expect "HP hp $hp" "plug"
want=$(( spk < 50 ? spk + 40 : spk - 30 ))
r "/opt/muos/script/device/audio.sh $want >/dev/null 2>&1"
expect "HP hp $want" "raise on HP"
r "rm -f $inv"; sleep 3
expect "SPK_HP spk $spk" "unplug restores speaker level"
r "echo 1 > $inv"; sleep 3
expect "HP hp $want" "replug restores HP level"
r "rm -f $inv"; sleep 3
expect "SPK_HP spk $spk" "final"
echo PASS
