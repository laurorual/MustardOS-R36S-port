#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Flash a make-recovery-image.sh image onto a microSD card.
#
#   flash-card.sh darkosen IP IMAGE.img.zst [--grow]
#       original32 (dArkOSen) boots in slot 1 with "Remote services" on;
#       the target card is in slot 2 (/dev/mmcblk1). Copies the image to
#       the dArkOSen user's home (default ark, env DARKOSEN_USER) and writes
#       it with sudo in one interactive session: expect the SSH password
#       once and the sudo password once.
#   flash-card.sh host /dev/sdX IMAGE.img.zst [--grow]
#       a card reader on this host (uses sudo).
#
# Both refuse the disk holding the running root or a card that is too
# small, unmount the target's partitions, write the raw image, re-read it
# with caches dropped and compare the SHA256 from the manifest. --grow then
# extends p3 to the end of the card (sfdisk, e2fsck, resize2fs).
set -euo pipefail
export LC_ALL=C

mode=${1:-} where=${2:-} image=${3:-} grow=0
[ "${4:-}" = --grow ] && grow=1
case "$mode" in darkosen|host) ;; *) sed -n '3,17p' "$0"; exit 2 ;; esac
manifest=${image%.img.zst}.manifest
[ -s "$image" ] && [ -s "$manifest" ] || { echo "missing image or manifest" >&2; exit 1; }
raw_sha=$(sed -n 's/^raw_sha256=//p' "$manifest")
raw_bytes=$(sed -n 's/^raw_bytes=//p' "$manifest")
(cd "$(dirname "$image")" && sha256sum -c --quiet "$(basename "$image").sha256")

# Runs as root on the machine that holds the card; image arrives on stdin.
flash_script() { # DEV
    cat <<EOF
set -eu
dev=$1
[ -b "\$dev" ] || { echo "no block device \$dev" >&2; exit 1; }
root=\$(findmnt -no SOURCE /)
case "\$root" in "\$dev"*) echo "refusing: \$dev holds the running root" >&2; exit 1 ;; esac
size=\$((\$(cat /sys/class/block/\${dev##*/}/size) * 512))
[ "\$size" -ge $raw_bytes ] || { echo "card too small (\$size bytes)" >&2; exit 1; }
unmount_all() { for m in \$(awk -v d="\$dev" 'index(\$1, d) == 1 {print \$2}' /proc/mounts); do umount "\$m"; done; }
unmount_all
echo "writing \$dev (\$size bytes)"
dd of="\$dev" bs=4M conv=fsync 2>/dev/null
sync; blockdev --flushbufs "\$dev"; echo 3 > /proc/sys/vm/drop_caches
echo "SHA=\$(head -c $raw_bytes "\$dev" | sha256sum | cut -d' ' -f1)"
if [ $grow = 1 ]; then
    p=\$dev; case "\$dev" in *mmcblk*|*nvme*|*loop*) p=\${dev}p ;; esac
    blockdev --rereadpt "\$dev" 2>/dev/null || partprobe "\$dev" || :
    sleep 2; unmount_all
    echo ', +' | sfdisk -q --no-reread -N 3 "\$dev"
    blockdev --rereadpt "\$dev" 2>/dev/null || partprobe "\$dev"
    sleep 2; unmount_all
    e2fsck -f -y "\${p}3" >/dev/null || [ \$? -le 1 ]
    resize2fs "\${p}3" 2>&1 | tail -n1
    e2fsck -fn "\${p}3" >/dev/null && echo "p3 grown and clean"
fi
sync
EOF
}

out=$(mktemp); trap 'rm -f "$out"' EXIT
if [ "$mode" = darkosen ]; then
    user=${DARKOSEN_USER:-ark}
    ctl=$(mktemp -u /tmp/muos-flash-ssh.XXXXXX)
    ssh_opts=(-oControlMaster=auto -oControlPath="$ctl" -oControlPersist=300 -oStrictHostKeyChecking=accept-new)
    echo "== copy image to $user@$where (SSH password once)"
    ssh "${ssh_opts[@]}" "$user@$where" 'df -h "$HOME" | tail -n1'
    zstd -dc --long=27 "$image" | gzip -1 | ssh "${ssh_opts[@]}" "$user@$where" 'cat > "$HOME/muos-flash.img.gz"'
    echo "== write /dev/mmcblk1 (sudo password)"
    script=$(flash_script /dev/mmcblk1)
    ssh -t "${ssh_opts[@]}" "$user@$where" \
        "gzip -dc \"\$HOME/muos-flash.img.gz\" | sudo sh -c $(printf '%q' "$script"); rm -f \"\$HOME/muos-flash.img.gz\"" | tee "$out"
    ssh -O exit "${ssh_opts[@]}" "$user@$where" 2>/dev/null || :
elif [ -n "${MUOS_FLASH_TEST_FILE:-}" ]; then
    # T1 only: a regular file stands in for the card (no block-device steps).
    f=$MUOS_FLASH_TEST_FILE
    zstd -dc --long=27 "$image" | dd of="$f" bs=4M conv=notrunc 2>/dev/null
    echo "SHA=$(head -c "$raw_bytes" "$f" | sha256sum | cut -d' ' -f1)" | tee "$out"
else
    echo "== write $where (sudo)"
    sudo -v
    zstd -dc --long=27 "$image" | sudo sh -c "$(flash_script "$where")" | tee "$out"
fi

got=$(tr -d '\r' < "$out" | sed -n 's/^SHA=//p')
[ "$got" = "$raw_sha" ] || { echo "VERIFY FAILED: card ${got:-?} != image $raw_sha" >&2; exit 1; }
echo "verified raw_sha256=$got"
echo "DONE: power off, move the card to slot 1 (slot 2 empty), power on."
