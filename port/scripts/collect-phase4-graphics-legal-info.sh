#!/usr/bin/env bash
# Collect the separate graphics candidate's licenses and sources offline.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
name=muos-r35s-phase4-graphics-legal
[[ $(cat "$work/graphics-config/build.exit") == 0 ]]
[[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
for job in muos-r35s-phase4-graphics muos-r35s-phase4-core; do
    [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
done
if podman container exists "$name"; then
    [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
    podman rm "$name" >/dev/null
fi
python3 - "$work/graphics-config/legal-info.exit" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
cp "$work/graphics-config/report.json" "$work/graphics-config/legal-input-report.json"
podman run --detach --name "$name" --network=none --read-only \
    --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
    --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
    -w /work/buildroot "$(cat "$work/rootfs-container.iid")" sh -c '
    make O=/work/graphics-config/output BR2_DL_DIR=/work/rootfs-downloads \
        LINUX_HEADERS_HASH_FILES=/port/device/rk-r35s-p0/phase4-linux-headers.hash \
        legal-info > /work/graphics-config/legal-info.log 2>&1
    result=$?
    if [ "$result" = 0 ]; then
        git archive --format=tar --output=/work/graphics-config/output/legal-info/buildroot-source.tar HEAD \
            && gzip -n -f /work/graphics-config/output/legal-info/buildroot-source.tar
        result=$?
    fi
    if [ "$result" = 0 ]; then
        cp /work/graphics-config/legal-input-report.json /work/graphics-config/output/legal-info/port-input-report.json
        result=$?
    fi
    printf "%s\n" "$result" > /work/graphics-config/legal-info.exit
    exit "$result"
    '
