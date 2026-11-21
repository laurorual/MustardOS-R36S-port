#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T2 (M8e): libretro core speed meter (t2-coremeter.c, preloaded into
# muxretro by muos-frontend while /run/muos/perf-capture exists).
#   t2-coremeter.sh build      cross-build build/m8e/coremeter.so (SDK container)
#   t2-coremeter.sh arm        push it to /run/muos, arm perf-capture, clear the log
#   t2-coremeter.sh mark       clear the log (start of a measured window)
#   t2-coremeter.sh report [RATE]  per-second log and a summary: audio frames
#                              per second as % of RATE (default 44100), core
#                              video frames and dupes per second
#   t2-coremeter.sh disarm
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
dev=$repo/port/scripts/device.sh so=$repo/build/m8e/coremeter.so
case "${1:-}" in
build)
    mkdir -p "$repo/build/m8e"
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id -v "$repo/build/phase4:/work:ro,z" -v "$repo/port/scripts:/src:ro,z" \
        -v "$repo/build/m8e:/out:rw,z" "$(cat "$repo/build/phase4/rootfs-container.iid")" sh -c \
        't=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-
         ${t}gcc -O2 -Wall -Wextra -shared -fPIC -o /out/coremeter.so /src/t2-coremeter.c -ldl -lpthread && ${t}strip /out/coremeter.so'
    ls -la "$so" ;;
arm)
    "$dev" push "$so" /run/muos >/dev/null
    "$dev" run 'chmod 755 /run/muos/coremeter.so; touch /run/muos/perf-capture; rm -f /run/coremeter.log' ;;
mark) "$dev" run 'rm -f /run/coremeter.log' ;;
report)
    "$dev" run 'cat /run/coremeter.log 2>/dev/null' | awk -v rate="${2:-44100}" '
        { n++; a[n]=$2; v+=$3; d+=$4; s+=$2; printf "%s", (n>1 ? " " : "") int($2*100/rate+0.5) }
        END { if (!n) { print "no samples"; exit }
              asort(a); printf "\n%d s: audio %.1f %% of %d (p10 %.1f %%, min %.1f %%), video %.1f/s, dupes %.1f/s\n",
              n, s/n*100/rate, rate, a[int(n/10)+1]*100/rate, a[1]*100/rate, v/n, d/n }' ;;
disarm) "$dev" run 'rm -f /run/muos/perf-capture /run/muos/coremeter.so' ;;
*) sed -n '3,12p' "$0"; exit 2 ;;
esac
