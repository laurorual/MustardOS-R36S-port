#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Host-only, resumable U-Boot executable probe. No media/SSH/flasher access.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
out="$work/uboot-sd"
job=muos-r35s-phase4-uboot-sd
mkdir -p "$out"
case "${1:-status}" in
 prepare)
  if podman container exists "$job"; then [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]; fi
  python3 "$repo/port/scripts/prepare-phase4-uboot-sd.py"
  ;;
 build)
  stage=$(cat "$out/latest-build")
  [[ "$stage" == "$out"/probe.* && -f "$stage/inputs.json" ]]
  python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,stage=map(Path,sys.argv[1:]);record=json.loads((stage/'inputs.json').read_text())
for name,digest in record['port_inputs'].items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest,name
for name,digest in record['source_files'].items():assert hashlib.sha256((stage/'source'/name).read_bytes()).hexdigest()==digest,name
PY
  if podman container exists "$job"; then
   [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
   podman rm "$job" >/dev/null
  fi
  rm -f "$stage/build.exit"
  epoch=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source_date_epoch"])' "$stage/inputs.json")
  podman run --detach --name "$job" --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
   --userns=keep-id --memory=6g --pids-limit=1024 --tmpfs /tmp:rw,nosuid,nodev,size=1g \
   -v "$work:/work:rw,z" -e UBOOT_PROBE_REL="${stage#"$work/"}" -e SOURCE_DATE_EPOCH="$epoch" \
   "$(cat "$work/kernel-container.iid")" sh -eu -c '
   stage=/work/$UBOOT_PROBE_REL
   trap '\''rc=$?; printf "%s\n" "$rc" > "$stage/build.exit"'\'' EXIT
   export KBUILD_BUILD_USER=muos KBUILD_BUILD_HOST=r35s-port
   export CROSS_COMPILE=/work/linaro6/bin/aarch64-linux-gnu-
   "$CROSS_COMPILE"gcc --version > "$stage/compiler.txt"
   cd "$stage/source"
   make O="$stage/output" HOSTCFLAGS="-O2 -fcommon" muos_r35s_panel0_sd_defconfig > "$stage/configure.log" 2>&1
   make O="$stage/output" HOSTCFLAGS="-O2 -fcommon" -j6 u-boot.bin u-boot.dtb System.map u-boot.cfg > "$stage/build.log" 2>&1
   ' 
  ;;
 status)
  if podman container exists "$job"; then podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$job"; fi
  if [[ -e "$out/latest-build" ]]; then cat "$out/latest-build"; fi
  ;;
 *) echo 'Usage: prepare|build|status' >&2; exit 2 ;;
esac
