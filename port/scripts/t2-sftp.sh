#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T2 (M3c): file transfer to the ROM library over dropbear + sftp-server.
# A random file whose name has spaces and brackets goes to
# /userdata/ROMS/T2SFTP with sftp (put, ls, get, rename, rm) and with
# OpenSSH scp in its default (SFTP) mode, both ways; every copy is compared
# by SHA256 on host and device. Prints throughput. The folder is removed.
#   t2-sftp.sh [MiB]   (default 32)
set -euo pipefail
export LC_ALL=C
here=$(cd "$(dirname "$0")" && pwd); dev=$here/device.sh
mib=${1:-32}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"; "$dev" run "rm -rf /userdata/ROMS/T2SFTP" >/dev/null 2>&1 || :' EXIT
name='T2 game (USA) [!].bin'
head -c $((mib * 1048576)) /dev/urandom > "$tmp/$name"
want=$(sha256sum "$tmp/$name" | cut -d' ' -f1)
fail() { echo "FAIL $*"; exit 1; }
devsum() { "$dev" run "sha256sum \"/userdata/ROMS/T2SFTP/$1\" | cut -d' ' -f1"; }
"$dev" run 'rm -rf /userdata/ROMS/T2SFTP; test -x /usr/libexec/sftp-server' || fail "no /usr/libexec/sftp-server"

# 1. sftp put + ls + get + rename + rm
cat > "$tmp/put.b" <<EOF
mkdir /userdata/ROMS/T2SFTP
cd /userdata/ROMS/T2SFTP
put "$tmp/$name"
ls -l
get "$name" "$tmp/back.bin"
rename "$name" "renamed.bin"
EOF
t0=$(date +%s.%N)
"$dev" sftp -q -b "$tmp/put.b" > "$tmp/sftp.out" 2>&1 || { cat "$tmp/sftp.out"; fail "sftp batch"; }
t1=$(date +%s.%N)
[ "$(sha256sum "$tmp/back.bin" | cut -d' ' -f1)" = "$want" ] || fail "sftp get differs"
[ "$(devsum renamed.bin)" = "$want" ] || fail "sftp put differs on device"
printf 'rm /userdata/ROMS/T2SFTP/renamed.bin\n' > "$tmp/rm.b"
"$dev" sftp -q -b "$tmp/rm.b" >/dev/null 2>&1 || fail "sftp rm"
"$dev" run 'test ! -e /userdata/ROMS/T2SFTP/renamed.bin' || fail "sftp rm left the file"
sftp_s=$(echo "$t1 - $t0" | bc)

# 2. OpenSSH scp in its default protocol (SFTP).
t0=$(date +%s.%N)
"$dev" scp -q "$tmp/$name" dev:/userdata/ROMS/T2SFTP/ || fail "scp put (SFTP mode)"
"$dev" scp -q "dev:/userdata/ROMS/T2SFTP/$name" "$tmp/back2.bin" || fail "scp get (SFTP mode)"
t1=$(date +%s.%N)
[ "$(devsum "$name")" = "$want" ] || fail "scp put differs on device"
[ "$(sha256sum "$tmp/back2.bin" | cut -d' ' -f1)" = "$want" ] || fail "scp get differs"
scp_s=$(echo "$t1 - $t0" | bc)
grep -qF "$name" "$tmp/sftp.out" || fail "sftp ls did not list the file"
printf 'PASS sftp+scp %s MiB: sftp put+get %.1f s (%.2f MiB/s), scp put+get %.1f s (%.2f MiB/s)\n' \
    "$mib" "$sftp_s" "$(echo "2 * $mib / $sftp_s" | bc -l)" "$scp_s" "$(echo "2 * $mib / $scp_s" | bc -l)"
