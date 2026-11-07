#!/usr/bin/env bash
# Collect dependency sources/licenses offline for the additive SDK profile.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/foundation/active" ]] || { echo "Foundation profile owns the mutable output; use its controllers." >&2; exit 1; }
[[ $(cat "$work/menu/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
name=muos-r35s-phase4-graphics-legal
if podman container exists "$name"; then
 [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
 podman rm "$name" >/dev/null
fi
podman run --detach --name "$name" --network=none --read-only \
 --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
 --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
 -w /work/buildroot "$(cat "$work/rootfs-container.iid")" sh -c '
 trap '\''rc=$?; printf "%s\n" "$rc" > /work/menu/legal-info.exit'\'' EXIT
 make O=/work/graphics-config/output BR2_DL_DIR=/work/rootfs-downloads \
   LINUX_HEADERS_HASH_FILES=/port/device/rk-r35s-p0/phase4-linux-headers.hash legal-info \
   > /work/menu/legal-info.log 2>&1 || exit $?
 git archive --format=tar --output=/work/graphics-config/output/legal-info/buildroot-source.tar HEAD \
   && gzip -n -f /work/graphics-config/output/legal-info/buildroot-source.tar
 '
