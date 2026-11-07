#!/usr/bin/env bash
# Mutable build ownership moves from menu to foundation; archive checkpoints stay.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
out="$work/foundation"
job=muos-r35s-phase4-graphics
case "${1:-status}" in
 configure|reconfigure)
  [[ -f "$out/provider-manifest.json" ]]
  if [[ $1 == configure ]]; then [[ ! -e "$out/active" ]]; else [[ -e "$out/active" ]]; fi
  for name in "$job" muos-r35s-phase4-graphics-legal muos-r35s-phase4-core; do
   if podman container exists "$name"; then [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]; fi
  done
  [[ -e "$out/baseline.config" ]] || cp "$work/graphics-config/output/.config" "$out/baseline.config"
  cat "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" "$repo/port/device/rk-r35s-p0/phase4-graphics.fragment" \
   "$repo/port/device/rk-r35s-p0/phase4-menu.fragment" "$repo/port/device/rk-r35s-p0/phase4-foundation.fragment" > "$out/candidate.defconfig"
  touch "$out/active"
  podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
   --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" -w /work/buildroot \
   "$(cat "$work/rootfs-container.iid")" make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot \
   BR2_DEFCONFIG=/work/foundation/candidate.defconfig defconfig > "$out/configure.log" 2>&1
  ;;
 provider|busybox|module-tools|image)
  stage=$1
  [[ -f "$out/active" ]]
  python3 - "$out" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
out=Path(sys.argv[1]);stage=sys.argv[2]
provider=json.loads((out/'provider-manifest.json').read_text())
assert provider['redistribution_approved'] is False
for name,h in provider['provider_files'].items():
 p=out/'provider-source'/name
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,name
if stage=='image':
 assert (out/'provider.exit').read_text().strip()=='0'
 assert (out/'frontend-compile.exit').read_text().strip()=='0'
 for name,h in json.loads((out/'overlay-manifest.json').read_text())['overlay_sha256'].items():
  with (out/'overlay'/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,name
PY
  for name in "$job" muos-r35s-phase4-graphics-legal muos-r35s-phase4-core; do
   if podman container exists "$name"; then [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]; fi
  done
  rm -f "$out/$stage.exit"
  if podman container exists "$job"; then podman rm "$job" >/dev/null; fi
  podman run --detach --name "$job" --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
   --userns=keep-id --memory=12g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g \
   -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" -w /work/buildroot -e FOUNDATION_STAGE="$stage" \
   "$(cat "$work/rootfs-container.iid")" sh -c '
   trap '\''rc=$?; printf "%s\n" "$rc" > /work/foundation/"$FOUNDATION_STAGE".exit'\'' EXIT
   unset PKG_CONFIG_LIBDIR PKG_CONFIG_SYSROOT_DIR PKG_CONFIG_PATH
   if [ "$FOUNDATION_STAGE" = provider ]; then
    make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
     BR2_JLEVEL=8 rockchip-mali > /work/foundation/provider.log 2>&1
   elif [ "$FOUNDATION_STAGE" = busybox ]; then
    make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
     BR2_JLEVEL=8 busybox-reconfigure > /work/foundation/busybox.log 2>&1
   elif [ "$FOUNDATION_STAGE" = module-tools ]; then
    make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
     BR2_JLEVEL=8 host-kmod kmod-reconfigure > /work/foundation/module-tools.log 2>&1
   else
    make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
     BR2_JLEVEL=8 all > /work/foundation/image.log 2>&1
   fi'
  ;;
 status)
  podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$job"
  ;;
 *) echo 'Usage: configure|reconfigure|provider|busybox|module-tools|image|status' >&2; exit 2 ;;
esac
