#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Flash a make-recovery-image.sh image onto a microSD card.
#
#   flash-card.sh darkosen IP IMAGE.img.zst [--grow]
#       original32 (dArkOSen) boots in slot 1, the target card is in slot 2
#       (/dev/mmcblk1). The image is streamed over SSH as root. The first
#       run asks once for the dArkOSen user's sudo password to install our
#       public key for root (env DARKOSEN_USER, default ark).
#   flash-card.sh host /dev/sdX IMAGE.img.zst [--grow]
#       a card reader on this host (uses sudo).
#
# Both modes refuse the disk holding the running root, write the raw image,
# re-read it from the card (caches dropped) and compare the SHA256 from the
# manifest. --grow then extends p3 to the end of the card (sfdisk, e2fsck,
# resize2fs).
set -euo pipefail
export LC_ALL=C

repo=$(cd "$(dirname "$0")/../.." && pwd)
key=${MUOS_DEVICE_KEY:-$repo/build/phase4/private/c07-client}
mode=${1:-} where=${2:-} image=${3:-} grow=0
[ "${4:-}" = --grow ] && grow=1
case "$mode" in darkosen|host) ;; *) sed -n '3,17p' "$0"; exit 2 ;; esac
[ -s "$image" ] && [ -s "${image%.img.zst}.manifest" ] || { echo "missing image or manifest" >&2; exit 1; }
raw_sha=$(sed -n 's/^raw_sha256=//p' "${image%.img.zst}.manifest")
raw_bytes=$(sed -n 's/^raw_bytes=//p' "${image%.img.zst}.manifest")
(cd "$(dirname "$image")" && sha256sum -c --quiet "$(basename "$image").sha256")

if [ "$mode" = darkosen ]; then
    ip=$where dev=/dev/mmcblk1
    known=$repo/build/device/darkosen_known_hosts
    mkdir -p "$(dirname "$known")"
    sshopts=(-i "$key" -oIdentitiesOnly=yes -oUserKnownHostsFile="$known" -oStrictHostKeyChecking=accept-new -oConnectTimeout=10)
    if ! ssh "${sshopts[@]}" -oBatchMode=yes "root@$ip" true 2>/dev/null; then
        pub=$(ssh-keygen -y -f "$key")
        echo "Installing our key for root on dArkOSen (enter the ${DARKOSEN_USER:-ark} sudo password if asked)"
        ssh -t -oUserKnownHostsFile="$known" -oStrictHostKeyChecking=accept-new "${DARKOSEN_USER:-ark}@$ip" \
            "sudo sh -c 'mkdir -p /root/.ssh && chmod 700 /root/.ssh && echo \"$pub\" >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys'"
    fi
    R() { ssh "${sshopts[@]}" -oBatchMode=yes "root@$ip" "$1"; }
    W() { ssh "${sshopts[@]}" -oBatchMode=yes "root@$ip" "$1"; }
elif [ -n "${MUOS_FLASH_TEST_FILE:-}" ]; then
    # T1 only: a regular file stands in for the card; no block-device steps.
    dev=$MUOS_FLASH_TEST_FILE grow=0
    R() { case "$1" in *sha256sum) head -c "$raw_bytes" "$dev" | sha256sum ;; *) : ;; esac; }
    W() { sh -c "${1/conv=fsync/conv=notrunc}"; }
else
    dev=$where
    R() { sudo sh -c "$1"; }
    W() { sudo sh -c "$1"; }
fi

echo "== target checks ($mode $dev)"
R "set -e
   [ -b $dev ]
   root=\$(findmnt -no SOURCE /)
   case \"\$root\" in ${dev}*) echo 'refusing: $dev holds the running root' >&2; exit 1;; esac
   size=\$((\$(cat /sys/class/block/${dev##*/}/size) * 512))
   [ \$size -ge $raw_bytes ] || { echo 'card too small' >&2; exit 1; }
   echo \"card bytes=\$size\"
   for m in \$(awk '\$1 ~ \"^${dev}p?[0-9]\" {print \$2}' /proc/mounts); do umount \"\$m\"; done
   ! grep -q '^${dev}' /proc/mounts"

echo "== write"
zstd -dc --long=27 "$image" | gzip -1 | W "gzip -dc | dd of=$dev bs=4M conv=fsync 2>/dev/null && sync"

echo "== verify"
got=$(R "sync; blockdev --flushbufs $dev; echo 3 > /proc/sys/vm/drop_caches; head -c $raw_bytes $dev | sha256sum" | cut -d' ' -f1)
[ "$got" = "$raw_sha" ] || { echo "VERIFY FAILED $got != $raw_sha" >&2; exit 1; }
echo "verified raw_sha256=$got"

if [ "$grow" = 1 ]; then
    echo "== grow p3"
    R "set -e
       p=${dev}; case $dev in *mmcblk*|*nvme*) p=${dev}p;; esac
       blockdev --rereadpt $dev || partprobe $dev || :
       sleep 2
       for m in \$(awk '\$1 ~ \"^${dev}p?[0-9]\" {print \$2}' /proc/mounts); do umount \"\$m\"; done
       echo ', +' | sfdisk -q --no-reread -N 3 $dev
       blockdev --rereadpt $dev || partprobe $dev
       sleep 2
       e2fsck -f -y \${p}3 >/dev/null || [ \$? -le 1 ]
       resize2fs \${p}3 2>&1 | tail -n1
       e2fsck -fn \${p}3 >/dev/null
       sync"
fi
echo "DONE: power off, move the card to slot 1 (no card in slot 2), power on."
