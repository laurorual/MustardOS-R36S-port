#!/usr/bin/env bash
# Collect licenses/sources offline, with the actual pinned BSP COPYING hash.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
name=muos-r35s-phase4-rootfs-legal
[[ $(cat "$work/rootfs-build.exit" 2>/dev/null) == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-rootfs) == false ]]
if [[ -f "$work/core/active" ]]; then
    [[ $(cat "$work/core/build.exit") == 0 ]]
    [[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-core) == false ]]
fi
if podman container exists "$name"; then
    [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
    cp "$work/rootfs-legal-info.log" "$work/rootfs-legal-info-previous.log"
    podman rm "$name" >/dev/null
fi
rm -f "$work/rootfs-legal-info.exit"
podman run --detach --name "$name" --network=none --read-only \
    --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
    --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
    -w /work/buildroot "$(cat "$work/rootfs-container.iid")" sh -c '
    make O=/work/rootfs-output BR2_DL_DIR=/work/rootfs-downloads \
        LINUX_HEADERS_HASH_FILES=/port/device/rk-r35s-p0/phase4-linux-headers.hash \
        legal-info > /work/rootfs-legal-info.log 2>&1
    result=$?
    if [ "$result" = 0 ]; then
        git archive --format=tar --output=/work/rootfs-output/legal-info/buildroot-source.tar HEAD \
            && gzip -n -f /work/rootfs-output/legal-info/buildroot-source.tar
        result=$?
    fi
    printf "%s\n" "$result" > /work/rootfs-legal-info.exit
    exit "$result"
    '
