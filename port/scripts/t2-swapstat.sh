#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T2 (M7): frame timing of the standalone Mupen64Plus (t2-swapstat.c).
#   t2-swapstat.sh build    cross-build build/m7/swapstat.so (SDK container)
#   t2-swapstat.sh arm      push it to /run/muos/swapstat.so, arm the hook
#                           (/run/muos/perf-capture), clear /run/swapstat.log
#   t2-swapstat.sh disarm   remove the hook file
#   t2-swapstat.sh grab FILE   next frame as PNG/PPM (host FILE)
#   t2-swapstat.sh report [FROM_S]   per-second lines of /run/swapstat.log
#                           from FROM_S s after the first line: mean swaps/s,
#                           worst gap; mean VI/s (60 = full speed), seconds
#                           under 58 and under 55 VI/s; ms per second spent
#                           inside the swap (vsync and GPU waits)
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
dev=$repo/port/scripts/device.sh so=$repo/build/m7/swapstat.so
case "${1:-}" in
build)
    mkdir -p "$repo/build/m7"
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
        --userns=keep-id -v "$repo/build/phase4:/work:ro,z" -v "$repo/port/scripts:/src:ro,z" \
        -v "$repo/build/m7:/out:rw,z" "$(cat "$repo/build/phase4/rootfs-container.iid")" sh -c \
        't=/work/graphics-config/output/host/bin/aarch64-buildroot-linux-gnu-
         ${t}gcc -O2 -Wall -Wextra -shared -fPIC -o /out/swapstat.so /src/t2-swapstat.c -ldl && ${t}strip /out/swapstat.so'
    ls -la "$so" ;;
arm)
    "$dev" push "$so" /run/muos >/dev/null
    "$dev" run 'chmod 755 /run/muos/swapstat.so; touch /run/muos/perf-capture; rm -f /run/swapstat.log' ;;
disarm) "$dev" run 'rm -f /run/muos/perf-capture' ;;
grab)
    out=${2:?host file}
    "$dev" run 'rm -f /run/swapstat-grab.ppm; touch /run/swapstat-grab
        for _ in 1 2 3 4 5 6 7 8 9 10; do [ -e /run/swapstat-grab ] || break; sleep 0.3; done
        sleep 0.3; cat /run/swapstat-grab.ppm' > "$out.ppm"
    python3 -c 'import sys,zlib,struct
d=open(sys.argv[1],"rb").read(); h=d.split(b"\n",3); w,hh=map(int,h[1].split()); px=h[3]
raw=b"".join(b"\0"+px[y*w*3:(y+1)*w*3] for y in range(hh))
c=lambda t,b: struct.pack(">I",len(b))+t+b+struct.pack(">I",zlib.crc32(t+b))
open(sys.argv[2],"wb").write(b"\x89PNG\r\n\x1a\n"+c(b"IHDR",struct.pack(">IIBBBBB",w,hh,8,2,0,0,0))+c(b"IDAT",zlib.compress(raw))+c(b"IEND",b""))' "$out.ppm" "$out" && rm -f "$out.ppm"
    ls -la "$out" ;;
report)
    "$dev" run 'cat /run/swapstat.log' | awk -v from="${2:-0}" '
        NR == 1 { t0 = $1 } $1 - t0 < from { next }
        { n++; s += $2; v += $5; sw += $6; if ($5 < 58) u58++; if ($5 < 55) u55++; if ($3 > w) w = $3 }
        END { if (n) printf "%d s: %.1f swaps/s, worst gap %.0f ms; %.1f VI/s, <58: %d s, <55: %d s; in swap %.0f ms/s\n", n, s / n, w, v / n, u58, u55, sw / n }' ;;
*) sed -n '3,11p' "$0"; exit 2 ;;
esac
