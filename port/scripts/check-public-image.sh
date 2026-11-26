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
repo=$(cd "$(dirname "$0")/../.." && pwd)
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
# M9 (LICENSING.md, decisions 33-35, 38): a complete image with the
# licence state the release notes describe
# shellcheck disable=SC2329
p2_sha() { [ "$(debugfs -R "cat $1" "$work/p2.img" 2>/dev/null | sha256sum | cut -d' ' -f1)" = "$2" ]; }
# shellcheck disable=SC2329
p2_ls() { debugfs -R "ls -p $1" "$work/p2.img" 2>/dev/null | awk -F/ 'NF > 5 && $6 != "." && $6 != ".." { print $6 }' | sort | tr '\n' ' '; }
# shellcheck disable=SC2329
p2_grep() { debugfs -R "cat $1" "$work/p2.img" 2>/dev/null | grep -qF -- "$2"; }
check "p2 has no Bluetooth firmware" absent /lib/firmware/rtl_bt
check "libmali is the unmodified Hardkernel r13p0 binary" \
    p2_sha /usr/lib/libmali-bifrost-g31-rxp0-gbm.so 2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea
check "DraStic r2.5.2.2 is included" \
    p2_sha /opt/muos/share/emulator/drastic/drastic dab3275ef772451b9235b78e64b2d0d041a28ac22937668231088c76b709e218
# shellcheck disable=SC2329
only_640() { [ "$(p2_ls /opt/muos/share/emulator/drastic/resources/bg)" = '640x480 ' ]; }
check "DraStic layouts: only steward-fu's 640x480" only_640
check "THIRD-PARTY.txt states the unofficial port and support" \
    p2_grep /usr/share/muos-r35s/THIRD-PARTY.txt 'not made, approved or supported by the MustardOS team'
check "updates come from laurorual/MustardOS-R36S-port" p2_grep /etc/muos-update.conf 'repo=laurorual/MustardOS-R36S-port'
# M9 rc1 T3: a fresh card starts in English at 50 % volume
# shellcheck disable=SC2329
p2_is() { [ "$(debugfs -R "cat $1" "$work/p2.img" 2>/dev/null)" = "$2" ]; }
check "first boot in English" p2_is /opt/muos/config/settings/general/language English
check "first boot volume 50 %" p2_is /opt/muos/config/settings/general/volume 50
check "startup volume mode: previous (not the maximum)" p2_is /opt/muos/config/settings/advanced/volume 0
check "debug_mode 0" p2_is /opt/muos/config/system/debug_mode 0
check "/etc/issue names the unofficial port" p2_grep /etc/issue 'MustardOS for R36S/R35S (unofficial port)'
# M10: the Wi-Fi firmware with its licences, the models and their selectors
check "Wi-Fi firmware: mt7601u with its MediaTek licence" p2_grep \
    /usr/share/licenses/linux-firmware/LICENCE.ralink_a_mediatek_company_firmware 'MediaTek'
check "Wi-Fi firmware: the rtlwifi licence" p2_grep /usr/share/licenses/linux-firmware/LICENCE.rtlwifi_firmware.txt 'Realtek'
# shellcheck disable=SC2329
models_ok() {
    local n
    n=$(debugfs -R 'cat /usr/share/muos-r35s/boot/dtb-variants.txt' "$work/p2.img" 2>/dev/null | grep -c '^m-')
    [ "$n" = "$(grep -vc '^#' "$repo/port/packaging/models.txt")" ] || { echo "     $n model keys" >&2; return 1; }
    for f in models.txt select-model.bat select-model.sh select-model.command; do
        debugfs -R "stat /usr/share/muos-r35s/boot/$f" "$work/p2.img" 2>/dev/null | grep -q '^Inode:' || { echo "     no $f" >&2; return 1; }
    done
}
check "every model DTB, models.txt and the selectors ship" models_ok
# M11: PortMaster is downloaded on the device, never shipped (gptokeyb GPL,
# 7zzs LGPL); its launcher, Python and the THIRD-PARTY note are there
check "PortMaster not in the image (p2 has no PortMaster tree or zip)" absent /usr/share/muos-r35s/portmaster
check "PortMaster launcher, app folder and Python 3 ship" p2_grep /opt/muos/share/application/PortMaster/mux_launch.sh 'muos-portmaster run'
check "Python 3 runtime ships" p2_grep /usr/lib/python3.12/os.pyc 'posix'
check "THIRD-PARTY says PortMaster is not included" p2_grep /usr/share/muos-r35s/THIRD-PARTY.txt 'PortMaster is NOT included'
# M12: the free PICO-8 cores ship; the official PICO-8 (the user's) never
check "PICO-8 cores Picante8 and FAKE-08 ship" eval '! absent /opt/muos/share/core/picante8_libretro.so && ! absent /opt/muos/share/core/fake08_libretro.so'
check "no official PICO-8 binary in the image" eval 'absent /opt/muos/share/emulator/pico8/pico8_64 && absent /usr/share/muos-r35s/pico8/pico8_64'
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
