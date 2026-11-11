#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T0/T1 build check: the runtime contract the prebuilt muOS binaries rely on,
# read from the p2 ext4 image itself (debugfs, no mount, no root).
#
#   check-rootfs-contract.sh P2.img
#
# muOS runs every SDL client with SDL_AUDIODRIVER=pipewire and
# SDL_VIDEODRIVER=KMSDRM. Buildroot's SDL2 auto-detects PipeWire at
# configure time without depending on it (pipewire depends on sdl2), so a
# clean build silently drops the backend: every boot is silent (M3a). The
# library must carry both drivers, and the PipeWire client library it
# dlopens must be in the image.
set -euo pipefail
export LC_ALL=C
[ $# -eq 1 ] || { sed -n '5p' "$0"; exit 2; }
img=$1 fail=0
# shellcheck disable=SC2329 # called through check()
has() { # PATH STRING: the file contains STRING (grep reads it all: no SIGPIPE under pipefail)
    debugfs -R "cat $1" "$img" 2>/dev/null | grep -aF "$2" > /dev/null
}
sdl=$(debugfs -R "stat /usr/lib/libSDL2-2.0.so.0" "$img" 2>/dev/null | sed -n 's/^Fast link dest: "\(.*\)"/\1/p')
[ -n "$sdl" ] || { echo 'FAIL libSDL2-2.0.so.0 missing' >&2; exit 1; }
sdl=/usr/lib/$sdl
check() { # DESCRIPTION, then the command
    local d=$1; shift
    if "$@"; then echo "ok   $d"; else echo "FAIL $d" >&2; fail=1; fi
}
check "SDL2 audio driver pipewire ($sdl)" has "$sdl" libpipewire-0.3.so.0
check "SDL2 video driver KMSDRM" has "$sdl" KMSDRM
check "SDL2 audio driver alsa (fallback)" has "$sdl" libasound.so.2
check "libpipewire-0.3.so.0 present" sh -c "debugfs -R 'stat /usr/lib/libpipewire-0.3.so.0' '$img' 2>/dev/null | grep -q Inode:"
exit $fail
