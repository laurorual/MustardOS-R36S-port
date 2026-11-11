#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# T1: every AArch64 ELF in a target rootfs resolves its libraries with the
# target's own ld.so (qemu-user, LD_TRACE_LOADED_OBJECTS: a real ldd), and
# a few tools actually run. Usage: t1-elf-deps.sh TARGET_DIR
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
target=$(realpath "$1")
podman run --rm --network=none -v "$target:/t:ro,z" "$(cat "$repo/build/phase4/rootfs-container.iid")" bash -euc '
cd /t
n=0 bad=0
while IFS= read -r -d "" f; do
    head -c 4 "$f" | grep -q "ELF" || continue
    file -b "$f" | grep -q "ARM aarch64" || continue
    case "$f" in ./lib/modules/*|*.o|*.ko) continue ;; esac
    file -b "$f" | grep -q -e "dynamically linked" -e "shared object" || continue
    n=$((n + 1))
    # The frontend and muxretro load their private libs from /opt/muos/frontend/lib.
    out=$(LD_TRACE_LOADED_OBJECTS=1 qemu-aarch64 -L /t \
        -E LD_LIBRARY_PATH=/opt/muos/frontend/lib:/usr/lib/pipewire-0.3:/usr/lib/spa-0.2 \
        -E LD_TRACE_LOADED_OBJECTS=1 /t/lib/ld-linux-aarch64.so.1 --list "/t/${f#./}" 2>&1) || :
    if grep -q "not found" <<< "$out"; then
        bad=$((bad + 1)); echo "MISSING ${f#.}: $(grep "not found" <<< "$out" | awk "{print \$1}" | tr "\n" " ")"
    fi
done < <(find . -type f \( -perm -u+x -o -name "*.so*" \) -print0)
echo "checked $n dynamic ELFs, $bad with missing libraries"
for c in "bin/busybox true" "sbin/e2fsck -V" "usr/sbin/e2fsck -V" "usr/bin/jq --version" \
         "usr/sbin/dropbear -V" "usr/bin/wpctl --version" "usr/sbin/wpa_supplicant -v"; do
    read -r p args <<< "$c"
    [ -e "/t/$p" ] || continue
    # shellcheck disable=SC2086 # args are words
    out=$(qemu-aarch64 -L /t "/t/$p" $args 2>&1 | head -1) || :
    echo "run /$p: ${out:0:70}"
done
[ "$bad" = 0 ]'
