#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# M12 T2: PICO-8 on the bench (developer image). Carts in ROMS/PICO-8
# (test content: FAKE-08's ld45.p8 and cartparsetest.p8.png, from its
# source tarball in build/m3c/cores/cache).
#   1. Picante8 (the folder's default) and FAKE-08: 30 s of ld45.p8 at
#      ~60 fps (t2-nes-fps.sh; the folder's core.cfg swapped and restored)
#   2. with the user's official PICO-8 in MUOS/bios/pico8 (else skipped):
#      "Standalone" and "Pixel-Perfect" through the menu's content
#      handoff, Fn+Start back (t2-standalone.sh); PICO-8's log names the
#      muOS-Keys pad; Applications -> Splore runs 25 s, Fn+Start back
#   t2-pico8.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
log=build/logs/m12/t2-pico8.log; mkdir -p "${log%/*}"; : > "$log"
say() { echo "$*" | tee -a "$log"; }
fail() { say "FAIL $*"; exit 1; }
r() { "$dev" run "$@" 2>> "$log" < /dev/null; }
cfg=/mnt/mmc/MUOS/port/info-content/PICO-8/core.cfg
r "[ -f /mnt/mmc/ROMS/PICO-8/ld45.p8 ] && [ -f $cfg ]" || fail "no ld45.p8 or no PICO-8 assignment"
[ "$(r "head -n 1 $cfg")" = picante8_libretro.so ] || fail "1: the folder's core is not Picante8"
fps() { port/scripts/t2-nes-fps.sh --dir PICO-8 --rom "$1" 30 "$2" < /dev/null 2> /dev/null | tail -n 1; }
out=$(fps ld45.p8 picante8); echo "$out" | grep -qE 'fps avg=(59|60)\.' || fail "1: Picante8: $out"
say "ok   1: Picante8 ${out#*fps }"
r "cp $cfg /run/t2-pico8-core.cfg && sed -i '1s/.*/fake08_libretro.so/; 5s/.*/mu-fake-08/' $cfg"
out=$(fps ld45.p8 fake08)
r "cp /run/t2-pico8-core.cfg $cfg"
echo "$out" | grep -qE 'fps avg=(59|60)\.' || fail "1: FAKE-08: $out"
say "ok   1: FAKE-08 ${out#*fps }"
if ! r '[ -f /mnt/mmc/MUOS/bios/pico8/pico8_64 ] && [ -f /mnt/mmc/MUOS/bios/pico8/pico8.dat ]'; then
    say "skip 2: no official PICO-8 in MUOS/bios/pico8"; say PASS; exit 0
fi
r '[ -x /mnt/mmc/MUOS/application/Splore/mux_launch.sh ]' || fail "2: no Splore app"
for m in scale pixel; do
    port/scripts/t2-standalone.sh "pico8-$m" "ext-pico8-$m" PICO-8 ld45.p8 pico8_64 20 schedutil >> "$log" 2>&1 < /dev/null ||
        fail "2: official $m"
    say "ok   2: official PICO-8 ($m) ran and quit"
done
r 'grep -aq "Controller 0: muOS-Keys" /mnt/mmc/MUOS/save/pico8/log.txt' || fail "2: PICO-8 did not see muOS-Keys"
r 'printf %s /mnt/mmc/MUOS/application/Splore > /run/muos/application; echo app > /run/muos/action
   for q in $(pidof muxfrontend); do kill -TERM "$q"; done'
ok=; for _ in $(seq 30); do r 'pidof pico8_64' > /dev/null && { ok=1; break; }; sleep 1; done
[ -n "$ok" ] || fail "2: Splore did not start"
sleep 25
r 'pidof pico8_64' > /dev/null || fail "2: Splore died"
r 'grep -aq splore_init /mnt/mmc/MUOS/save/pico8/log.txt' || fail "2: no splore_init"
r '/usr/libexec/muos-press fn+start'; sleep 5
r 'pidof pico8_64' > /dev/null && fail "2: Splore still running after Fn+Start"
say "ok   2: Splore ran 25 s, quit on Fn+Start"
say PASS
