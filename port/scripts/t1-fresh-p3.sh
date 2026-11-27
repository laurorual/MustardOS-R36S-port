#!/usr/bin/env bash
# shellcheck disable=SC2016
# SPDX-License-Identifier: MIT
# T1 (M4a): the first boot of an image with an empty p3 (the public
# variant), without a device. The Buildroot target (build/m3a/output/target)
# runs as a rootless podman container (overlay, nothing written back;
# aarch64 through the host's qemu binfmt). p3 is a tmpfs with only the
# data marker (S89's mount is simulated, fstype check relaxed); then S90
# storage, S91 runtime (seeding), S98 user init and the network worker
# (no profiles -> radio off, "idle"); M4d: the time-zone link. Prints a verdict.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
target=$repo/build/m3a/output/target
logs=$repo/build/logs; mkdir -p "$logs"
[ -d "$target/etc/init.d" ] || { echo "no $target" >&2; exit 1; }
script='export PATH=/usr/sbin:/usr/bin:/sbin:/bin
mount -t tmpfs tmpfs /run && mount -t tmpfs tmpfs /userdata || exit 9
mkdir -p /userdata/MUOS/log /userdata/ROMS /mnt/mmc
printf "MUOS-R35S-DATA-V1\n" > /userdata/.muos-r35s-data-v1
echo fstype=tmpfs > /etc/default/muos-storage
/etc/init.d/S90muos-storage start; echo "S90 rc=$?"
/etc/init.d/S91muos-runtime start > /dev/null; echo "S91 rc=$?"
echo "seeded=$([ -e /userdata/MUOS/port/.seeded ] && echo yes || echo no) roms=$(ls /userdata/ROMS | wc -l) board_network=$(cat /opt/muos/device/config/board/network) sshd=$(cat /opt/muos/config/web/sshd) user_init=$(cat /opt/muos/config/settings/advanced/user_init)"
/etc/init.d/S98muos-user-init start; echo "S98 rc=$?"
# M4d: the zone (UTC on a new card), then a zone change as the menu does it
# (M13, frontend 0004: the zone as text on p3, the link in /run).
z0=$(cat /opt/muos/config/localtime); z1=$(date -d @1794888000 "+%H:%M %Z")
printf "/usr/share/zoneinfo/America/Sao_Paulo" > /opt/muos/config/localtime; ln -sfn /usr/share/zoneinfo/America/Sao_Paulo /run/muos/localtime
echo "zone0=$z0 utc=$z1 zone=$(cat /userdata/MUOS/port/config/localtime) local=$(date -d @1794888000 "+%H:%M %Z")"
/usr/libexec/muos-network/worker up; echo "worker rc=$? idle=$([ -e /run/muos/network/idle ] && echo yes || echo no)"'
podman run --rm --privileged --network=none --rootfs "$target:O" /bin/sh -c "$script" > "$logs/t1-fresh-p3.log" 2>&1 || :
cat "$logs/t1-fresh-p3.log"
if grep -q 'S90 rc=0' "$logs/t1-fresh-p3.log" && grep -q 'S91 rc=0' "$logs/t1-fresh-p3.log" &&
   grep -q 'seeded=yes roms=[1-9][0-9]* board_network=1 sshd=0 user_init=0' "$logs/t1-fresh-p3.log" &&
   grep -q 'S98 rc=0' "$logs/t1-fresh-p3.log" && grep -q 'worker rc=0 idle=yes' "$logs/t1-fresh-p3.log" &&
   grep -q 'zone0=/usr/share/zoneinfo/Etc/UTC utc=04:00 UTC zone=/usr/share/zoneinfo/America/Sao_Paulo local=01:00 -03' "$logs/t1-fresh-p3.log"; then
    echo 'PASS fresh p3 first boot'
else
    echo 'FAIL fresh p3 first boot'; exit 1
fi
