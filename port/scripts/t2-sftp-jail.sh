#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4g): the menu's SFTP (web/sftp, port 2022) jailed as upstream:
# dropbear -G muos -c musftpjail, user muos / password muos.
#   login     muos/muos lists the jail root: "Primary Storage" and
#             "Internal", no etc/dev/usr (the jail hides its support files)
#   transfer  a random file put to Primary Storage/ROMS/T2JAIL, found on
#             p3 (/mnt/mmc/ROMS/T2JAIL) with the same SHA256, got back,
#             renamed, removed; the folder is removed
#   escape    "/.." is the jail root; /etc/shadow and /usr are absent
#   refused   root/root and muos/wrong are refused on 2022
# web/sftp is switched on for the test and restored afterwards.
#   t2-sftp-jail.sh [MiB]   (default 8)
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh
r() { "$dev" run "$@"; }
mib=${1:-8}
repo=$(cd ../.. && pwd)
ip=$(cat "$repo/build/device/ip")
tmp=$repo/build/device/t2-sftp-jail
rm -rf "$tmp"; mkdir -p "$tmp"
sed "s/^[^ ]*/[$ip]:2022/" "$repo/build/device/known_hosts" > "$tmp/known"
printf '#!/bin/sh\nprintf "%%s\\n" "$T2_PASS"\n' > "$tmp/askpass"; chmod 700 "$tmp/askpass"
rc=0
pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; rc=1; }

# sf USER PASSWORD: sftp batch from stdin, password through SSH_ASKPASS
# (BatchMode=no first: -b turns it on, which disables passwords).
sf() {
    T2_PASS=$2 SSH_ASKPASS=$tmp/askpass SSH_ASKPASS_REQUIRE=force DISPLAY=none \
        setsid -w sftp -q -oBatchMode=no -b - -P 2022 -oUserKnownHostsFile="$tmp/known" -oStrictHostKeyChecking=yes \
        -oPubkeyAuthentication=no -oPreferredAuthentications=password -oNumberOfPasswordPrompts=1 \
        -oConnectTimeout=10 "$1@$ip" 2>&1
}

old=$(r 'cat /opt/muos/config/web/sftp 2>/dev/null || echo 0')
r 'echo 1 > /opt/muos/config/web/sftp; /usr/libexec/muos-network/worker service sftp; sleep 1
   /usr/libexec/muos-network/worker status | grep -x sftp=up' > /dev/null || { fail 'sftp service not up'; }

# login
out=$(echo 'ls -1 /' | sf muos muos)
if printf '%s\n' "$out" | grep -q 'Primary Storage' && printf '%s\n' "$out" | grep -q 'Internal' &&
   ! printf '%s\n' "$out" | grep -q -E '^/?(etc|dev|usr)$'; then pass "login ($(printf '%s\n' "$out" | grep -c . ) entries)"
else fail "login: $out"; fi

# transfer
head -c "$((mib * 1048576))" /dev/urandom > "$tmp/t2 jail [x].bin"
want=$(sha256sum "$tmp/t2 jail [x].bin" | cut -d' ' -f1)
t0=$(date +%s.%N)
out=$(sf muos muos <<EOF
-mkdir "/Primary Storage/ROMS/T2JAIL"
put "$tmp/t2 jail [x].bin" "/Primary Storage/ROMS/T2JAIL/t2 jail [x].bin"
EOF
)
t1=$(date +%s.%N)
dsum=$(r 'sha256sum "/mnt/mmc/ROMS/T2JAIL/t2 jail [x].bin" | cut -d" " -f1; stat -c %U "/mnt/mmc/ROMS/T2JAIL/t2 jail [x].bin"')
out2=$(sf muos muos <<EOF
get "/Primary Storage/ROMS/T2JAIL/t2 jail [x].bin" "$tmp/back.bin"
rename "/Primary Storage/ROMS/T2JAIL/t2 jail [x].bin" "/Primary Storage/ROMS/T2JAIL/renamed.bin"
rm "/Primary Storage/ROMS/T2JAIL/renamed.bin"
rmdir "/Primary Storage/ROMS/T2JAIL"
EOF
)
back=$(sha256sum "$tmp/back.bin" 2>/dev/null | cut -d' ' -f1)
left=$(r 'ls -d /mnt/mmc/ROMS/T2JAIL 2>/dev/null || echo gone')
if [ "$(printf '%s\n' "$dsum" | head -n1)" = "$want" ] && [ "$back" = "$want" ] && [ "$left" = gone ]; then
    pass "transfer ${mib} MiB put $(awk -v a="$t0" -v b="$t1" -v m="$mib" 'BEGIN{printf "%.1f", m/(b-a)}') MiB/s, owner $(printf '%s\n' "$dsum" | tail -n1)"
else fail "transfer: device=$dsum back=$back left=$left $out $out2"; fi

# escape
a=$(echo 'ls -1 /' | sf muos muos | grep -v '^sftp>' | sed 's#^/##' | sort)
b=$(echo 'ls -1 /..' | sf muos muos | grep -v '^sftp>' | sed 's#^/\.\./##; s#^\.\./##' | sort)
e1=$(echo 'get /etc/shadow /dev/null' | sf muos muos); e2=$(echo 'ls /usr' | sf muos muos)
if [ "$a" = "$b" ] && printf '%s\n' "$e1" | grep -q -i 'not found\|no such' &&
   printf '%s\n' "$e2" | grep -q -i 'not found\|no such'; then pass 'escape'
else fail "escape: root=[$a] up=[$b] shadow=[$e1] usr=[$e2]"; fi

# refused
x1=$(echo 'ls /' | sf root root; echo "rc=$?"); x2=$(echo 'ls /' | sf muos wrong; echo "rc=$?")
if ! printf '%s\n' "$x1" | grep -qx 'rc=0' && ! printf '%s\n' "$x2" | grep -qx 'rc=0'; then pass 'refused root and a wrong password'
else fail "refused: root=[$x1] wrong=[$x2]"; fi

r "echo $old > /opt/muos/config/web/sftp; /usr/libexec/muos-network/worker service sftp" > /dev/null
rm -rf "$tmp"
exit "$rc"
