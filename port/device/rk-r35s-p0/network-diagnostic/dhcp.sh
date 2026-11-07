#!/bin/sh
# SPDX-License-Identifier: MIT
# udhcpc hook: no persistent writes and no resolver changes in this increment.
set -eu
state=/run/muos/c07
[ -r "$state/interface" ] || exit 1
[ "${interface:-}" = "$(cat "$state/interface")" ] || exit 1
ipv4() {
    printf '%s\n' "$1" | awk -F. 'NF!=4 {exit 1} {for(i=1;i<=4;i++) if($i !~ /^[0-9]+$/ || $i>255) exit 1}'
}
case "${1:-}" in
    deconfig)
        ifconfig "$interface" 0.0.0.0
        rm -f "$state/address"
        ;;
    bound|renew)
        ipv4 "${ip:-}" && ipv4 "${subnet:-}" || exit 1
        ifconfig "$interface" "$ip" netmask "$subnet" up
        # Local SSH only; DNS/default routes are unnecessary for this test.
        printf '%s\n' "$ip" > "$state/address.tmp"
        mv "$state/address.tmp" "$state/address"
        ;;
    *) exit 0 ;;
esac
