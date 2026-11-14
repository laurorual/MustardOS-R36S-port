#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T0/T1 (M4a): refuse a public card image that holds any developer identity.
#
#   check-public-image.sh IMAGE(.img|.img.zst) [BASE_P2.img]
#
# Reads the partitions with debugfs/mtools (no mount, no root). Checks:
# - p2: no Wi-Fi config, SSH host key, authorized key, root .ssh, RNG seed;
#   root has a password hash; SSH/SFTP toggles off; no developer key file;
# - p3: only lost+found and the data marker (no profiles, saves, logs);
# - the raw image contains none of the developer's secrets: with BASE_P2
#   (a developer p2, e.g. the M2 base's) every line of its network.conf
#   PSK/SSID values and the authorized key's base64 blob is searched for in
#   the whole image (the values are never printed).
set -euo pipefail
export LC_ALL=C
[ $# -ge 1 ] || { sed -n '5p' "$0"; exit 2; }
img=$1 base_p2=${2:-}
work=$(mktemp -d "${TMPDIR:-/tmp}/check-public.XXXXXX")
trap 'rm -rf "$work"' EXIT
case "$img" in
    *.zst) zstd -q -dc --long=27 "$img" | dd of="$work/card.img" bs=1M conv=sparse status=none; img=$work/card.img ;;
esac
fail=0
check() { local d=$1; shift; if "$@"; then echo "ok   $d"; else echo "FAIL $d" >&2; fail=1; fi; }
part() { # N -> start size (sectors)
    sfdisk -d "$img" 2>/dev/null | sed -n "s|^.*[^0-9]$1 : start= *\([0-9]*\), size= *\([0-9]*\),.*|\1 \2|p"
}
read -r s2 n2 < <(part 2); read -r s3 n3 < <(part 3)
dd if="$img" of="$work/p2.img" bs=512 skip="$s2" count="$n2" conv=sparse status=none
dd if="$img" of="$work/p3.img" bs=512 skip="$s3" count="$n3" conv=sparse status=none
# shellcheck disable=SC2329 # called through check()
absent() { ! debugfs -R "stat $1" "$work/p2.img" 2>/dev/null | grep -q '^Inode:'; }
for p in /var/lib/muos-network/network.conf /var/lib/muos-network/dropbear_ed25519_host_key \
    /etc/muos-network-authorized_key /root/.ssh/authorized_keys /etc/dropbear/dropbear_ed25519_host_key \
    /var/lib/seedrng/seed.credit /var/lib/seedrng/seed.no-credit; do
    check "p2 has no $p" absent "$p"
done
# shellcheck disable=SC2329 # called through check()
root_hash() { debugfs -R 'cat /etc/shadow' "$work/p2.img" 2>/dev/null | awk -F: '$1 == "root" { exit !($2 ~ /^\$[0-9a-z]+\$/) }'; }
check "root has a password hash" root_hash
# shellcheck disable=SC2329
cfg_off() { [ "$(debugfs -R "cat /opt/muos/config/web/$1" "$work/p2.img" 2>/dev/null)" = 0 ]; }
check "web/sshd off by default" cfg_off sshd
check "web/sftp off by default" cfg_off sftp
# shellcheck disable=SC2329
p3_clean() {
    local l
    l=$(debugfs -R 'ls -p /' "$work/p3.img" 2>/dev/null | awk -F/ 'NF > 5 && $6 != "." && $6 != ".." { print $6 }' | sort | tr '\n' ' ')
    [ "$l" = '.muos-r35s-data-v1 lost+found ' ] || { echo "     p3 root: $l" >&2; return 1; }
}
check "p3 holds only the data marker" p3_clean
if [ -n "$base_p2" ]; then
    # Secrets of the developer image: values of ssid/psk lines and the key blob.
    debugfs -R 'cat /var/lib/muos-network/network.conf' "$base_p2" 2>/dev/null |
        sed -n 's/^[ \t]*\(ssid\|psk\)=//p' | tr -d '"' > "$work/secrets"
    debugfs -R 'cat /etc/muos-network-authorized_key' "$base_p2" 2>/dev/null | awk '{ print $2 }' >> "$work/secrets"
    # The SSID also in clear text (wpa_supplicant configs may store it as hex).
    first=$(sed -n '1p' "$work/secrets")
    ! grep -qx '[0-9a-f]*' <<< "$first" || { xxd -r -p <<< "$first"; echo; } >> "$work/secrets"
    [ "$(grep -c . "$work/secrets")" -ge 2 ] || { echo 'FAIL no developer secrets read from BASE_P2' >&2; exit 1; }
    # shellcheck disable=SC2329
    no_secret() { ! grep -aqF -f "$work/secrets" "$img"; }
    check "no developer Wi-Fi/SSH value in the raw image ($(grep -c . "$work/secrets") strings)" no_secret
fi
exit $fail
