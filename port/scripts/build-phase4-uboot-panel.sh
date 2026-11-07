#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Compile only a display DTB. No upstream make.sh, bootloader or flasher runs.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
source_dir="$work/uboot-base"
lock="$repo/port/device/rk-r35s-p0/phase4-uboot-sources.json"
read_lock() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$lock" "$1"; }
revision=$(read_lock revision)
if [[ ! -d "$source_dir/.git" ]]; then
 git init "$source_dir"
 git -C "$source_dir" remote add origin "$(read_lock url)"
fi
[[ -z $(git -C "$source_dir" status --porcelain) ]]
if ! git -C "$source_dir" cat-file -e "$revision^{commit}" 2>/dev/null; then
 git -C "$source_dir" fetch --depth=1 origin "$revision"
fi
git -C "$source_dir" checkout --detach "$revision"
[[ $(git -C "$source_dir" rev-parse HEAD) == "$revision" ]]
[[ $(cat "$work/kernel-container.iid") == "$(read_lock container_image_id)" ]]
python3 - "$lock" "$source_dir" <<'PY'
from pathlib import Path
import hashlib,json,sys
lock=json.load(open(sys.argv[1]));source=Path(sys.argv[2])
for name,digest in lock['recipe_payload_sha256'].items():
 assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
PY
mkdir -p "$work/uboot-panel"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
 "$(cat "$work/kernel-container.iid")" sh -eu -c '
 gcc --version > /work/uboot-panel/compiler.txt
 dtc --version > /work/uboot-panel/dtc-version.txt
 gcc -E -nostdinc -undef -D__DTS__ -x assembler-with-cpp \
  -I /work/uboot-base/arch/arm/dts -I /work/uboot-base/include \
  /port/device/rk-r35s-p0/rk3326-muos-r35s-panel0-uboot.dts -o /work/uboot-panel/panel.preprocessed.dts
 dtc -I dts -O dtb -o /work/uboot-panel/rk3326-muos-r35s-panel0-uboot.dtb /work/uboot-panel/panel.preprocessed.dts
 ' > "$work/uboot-panel/build.log" 2>&1
python3 "$repo/port/scripts/verify-phase4-uboot-panel.py" \
 "$work/uboot-panel/rk3326-muos-r35s-panel0-uboot.dtb" \
 "$work/panel-reference/rg351mp-uboot.dtb" > "$work/uboot-panel/panel-audit.json"
cp "$lock" "$work/uboot-panel/sources.json"
printf '%s\n' 'U-Boot display DTB host comparison passed. No executable bootloader built or run.'
