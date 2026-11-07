#!/bin/sh
# SPDX-License-Identifier: MIT
# Synthetic data inside the owned C52 loop image only. No ROM or card path.
set -eu
umask 077
op=${1:-};store=${2:-};bin=${3:-};capsule=${bin%/*}
[ "$#" = 3 ]
case "$capsule" in /run/muos-prefs-ext4.??????) ;; *) exit 64;;esac
[ "$bin" = "$capsule/muos-save-store" ] && [ "$store" = "$capsule/mnt/store" ]
[ "$(findmnt -rn -M "$capsule/mnt" -o FSTYPE)" = ext4 ]
id=abababababababababababababababababababababababababababababababab
simple() { "$bin" "$1" "$store" "$id" >/dev/null; }
transfer() { "$bin" "$1" "$store" "$id" "$2" >/dev/null; }
refuse() {
    want=$1;shift;rc=0;"$@" >/dev/null 2>&1 || rc=$?
    [ "$rc" = "$want" ]
}
compare() {
    for n in quicksave.state states.ini quicksave.png;do cmp "$1/$n" "$2/$n";done
}
case "$op" in
 write)
    [ ! -e "$store" ] && [ ! -L "$store" ]
    mkdir -m 700 "$store"
    printf 'MUOS-R35S-SAVES-V1\n' > "$store/.muos-saves-v1"
    simple init
    transfer commit "$capsule/source-a"
    transfer commit "$capsule/source-b"
    cp "$store/HEAD" "$capsule/head-before"
    # A correctly owned, valid ext4 source must still be refused: input is RAM-only.
    mkdir -m 700 "$capsule/mnt/source"
    cp "$capsule/source-a/"* "$capsule/mnt/source/"
    refuse 64 transfer commit "$capsule/mnt/source"
    cmp "$store/HEAD" "$capsule/head-before"
    printf 'C52_EXT4_WRITE_OK\n'
    ;;
 verify-ro)
    mkdir -m 700 "$capsule/export-b"
    simple status
    transfer export "$capsule/export-b"
    compare "$capsule/source-b" "$capsule/export-b"
    refuse 64 simple init
    refuse 64 transfer commit "$capsule/source-a"
    cmp "$store/HEAD" "$capsule/head-before"
    printf 'C52_EXT4_REMOUNT_RO_OK\n'
    ;;
 recover)
    # Corrupt only the known synthetic second generation, then preserve it.
    printf 'CORRUPTED' | dd of="$store/00000002.bundle" bs=1 seek=140 conv=notrunc 2>/dev/null
    sha256sum "$store/00000002.bundle" > "$capsule/corrupt-before.sha256"
    mkdir -m 700 "$capsule/refused-export"
    refuse 64 transfer export "$capsule/refused-export"
    simple recover
    sha256sum -c "$capsule/corrupt-before.sha256" >/dev/null
    printf 'C52_EXT4_RECOVERY_OK\n'
    ;;
 verify-recovered)
    mkdir -m 700 "$capsule/export-a"
    transfer export "$capsule/export-a"
    compare "$capsule/source-a" "$capsule/export-a"
    sha256sum -c "$capsule/corrupt-before.sha256" >/dev/null
    printf 'C52_EXT4_RECOVERED_REMOUNT_OK\n'
    ;;
 *) exit 64;;
esac
