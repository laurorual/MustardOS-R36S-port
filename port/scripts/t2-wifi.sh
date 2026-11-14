#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016
# T2 (M4a): the muOS Wi-Fi profile contract of usr/libexec/muos-network/worker
# through upstream's S02network.sh, on a developer image. Device-side and
# detached (each connect drops SSH for a few seconds):
#   Home    = the private network.conf's network as a muOS profile -> rc 0
#   BadPass = same SSID, wrong PSK                                 -> rc 2
#   Nowhere = an absent SSID                                       -> rc 3
# after each failure the address must come back (previous network), and a
# scan (web/ssid.sh) must list SSIDs. Home.ini stays (autoconnect, priority
# 1: private like the card); the other two are removed. Volume untouched.
set -u
cd "$(dirname "$0")" || exit 1
dev=./device.sh out=/userdata/MUOS/log/t2-wifi.log
logs=$(cd ../.. && pwd)/build/logs; mkdir -p "$logs"
remote='out='"$out"'
P=/run/muos/storage/network S=/opt/muos/script/init/async/S02network.sh
c=/var/lib/muos-network/network.conf
ssid=$(printf "$(sed -n "s/^[ \t]*ssid=//p" $c | head -n1 | tr -d "\"" | sed "s/../\\\\x&/g")")
psk=$(sed -n "s/^[ \t]*psk=//p" $c | head -n1 | tr -d "\"")
mk() { printf "[network]\nssid=%s\npass=%s\ntype=dhcp\nautoconnect=%s\npriority=%s\n" "$2" "$3" "$4" "$5" > "$P/$1.ini"; }
mk Home "$ssid" "$psk" 1 1
mk BadPass "$ssid" 0000000000000000000000000000000000000000000000000000000000000000 0 5
mk Nowhere no-such-ap-t2 1111111111111111111111111111111111111111111111111111111111111111 0 5
sync; : > $out
back() { n=0; while [ $n -lt 60 ] && [ ! -s /run/muos/network/address ]; do sleep 1; n=$((n+1)); done; echo "back $1 ${n}s $([ -s /run/muos/network/address ] && echo ok || echo none)" >> $out; }
run() { t0=$(date +%s); $S connect "$1"; rc=$?; echo "connect $1 rc=$rc $(( $(date +%s) - t0 ))s status=$(cat /run/muos/network/$1.status 2>/dev/null) active=$(cat /opt/muos/config/network/active)" >> $out; sync; }
run Home; run BadPass; back BadPass; run Nowhere; back Nowhere
/opt/muos/script/web/ssid.sh; echo "scan $(grep -vc "^\[!\]" /tmp/net_scan)" >> $out
rm -f $P/BadPass.ini $P/Nowhere.ini; echo done >> $out; sync'
printf '%s\n' "$remote" | "$dev" run 'cat > /run/t2-wifi.sh; setsid sh /run/t2-wifi.sh < /dev/null > /dev/null 2>&1 &' || exit 1
sleep 20
for _ in $(seq 1 40); do
    "$dev" run "grep -q '^done' $out" 2>/dev/null && break
    sleep 5
done
"$dev" run "cat $out" | tee "$logs/t2-wifi.log"
ok=1
grep -q '^connect Home rc=0 .*status=CONNECTED active=Home' "$logs/t2-wifi.log" || ok=0
grep -q '^connect BadPass rc=2 .*INVALID_PASSWORD' "$logs/t2-wifi.log" || ok=0
grep -q '^connect Nowhere rc=3 .*AP_NOT_FOUND' "$logs/t2-wifi.log" || ok=0
[ "$(grep -c '^back .* ok$' "$logs/t2-wifi.log")" = 2 ] || ok=0
grep -q '^scan [1-9]' "$logs/t2-wifi.log" || ok=0
if [ "$ok" = 1 ]; then echo 'PASS wifi profiles'; else echo 'FAIL wifi profiles'; exit 1; fi
