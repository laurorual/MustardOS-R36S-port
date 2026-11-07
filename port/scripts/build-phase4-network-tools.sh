#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Add only network packages to the existing SDK; never generate/deploy an image.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
out="$work/network-tools"
job=muos-r35s-phase4-network-tools
stage=${1:-status}
case "$stage" in
 status)
  if podman container exists "$job"; then
   podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$job"
  fi
  for name in fetch build; do
   [[ ! -f "$out/$name.exit" ]] || cat "$out/$name.exit"
  done
  exit 0 ;;
 fetch|build) ;;
 *) echo 'Usage: fetch|build|status' >&2; exit 2 ;;
esac
mkdir -p "$out"
exec 9>"$out/controller.lock"
flock -n 9
[[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
[[ -f "$work/foundation/active" ]]
# Other historical controllers share this SDK. Refuse concurrent builds.
[[ -z $(podman ps --format '{{.Names}}' | rg '^muos-r35s-phase4-' || :) ]]
if podman container exists "$job"; then podman rm "$job" >/dev/null; fi
if [[ -e "$out/baseline.config" ]]; then
 cmp "$out/baseline.config" "$work/graphics-config/output/.config"
else
 cp "$work/graphics-config/output/.config" "$out/baseline.config"
fi
cp "$out/baseline.config" "$out/network.defconfig"
cfg="$work/buildroot/utils/config"
"$cfg" --file "$out/network.defconfig" \
 --enable BR2_PACKAGE_DROPBEAR --enable BR2_PACKAGE_DROPBEAR_SMALL \
 --disable BR2_PACKAGE_DROPBEAR_CLIENT --enable BR2_PACKAGE_DROPBEAR_DISABLE_REVERSEDNS \
 --disable BR2_PACKAGE_DROPBEAR_WTMP --disable BR2_PACKAGE_DROPBEAR_LASTLOG \
 --disable BR2_PACKAGE_DROPBEAR_LEGACY_CRYPTO \
 --enable BR2_PACKAGE_WPA_SUPPLICANT --enable BR2_PACKAGE_WPA_SUPPLICANT_NL80211 \
 --enable BR2_PACKAGE_WPA_SUPPLICANT_WEXT --enable BR2_PACKAGE_WPA_SUPPLICANT_CTRL_IFACE \
 --enable BR2_PACKAGE_WPA_SUPPLICANT_CLI --disable BR2_PACKAGE_WPA_SUPPLICANT_DBUS \
 --disable BR2_PACKAGE_WPA_SUPPLICANT_WPS --disable BR2_PACKAGE_WPA_SUPPLICANT_AP_SUPPORT \
 --enable BR2_PACKAGE_USB_MODESWITCH
network=none
if [[ $stage == fetch ]]; then network=slirp4netns; fi
if [[ $stage == build ]]; then [[ $(cat "$out/fetch.exit") == 0 ]]; fi
rm -f "$out/$stage.exit"
podman run --rm --name "$job" --network="$network" --read-only --cap-drop=all \
 --security-opt=no-new-privileges --userns=keep-id --memory=6g --pids-limit=1024 \
 --tmpfs /tmp:rw,nosuid,nodev,size=1g -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
 -w /work/buildroot -e NETWORK_STAGE="$stage" "$(cat "$work/rootfs-container.iid")" sh -c '
 set -eu
 unset PKG_CONFIG_LIBDIR PKG_CONFIG_SYSROOT_DIR PKG_CONFIG_PATH
 output=/work/graphics-config/output
 record=/work/network-tools
 finish() {
  rc=$?
  trap - EXIT
  cp "$record/baseline.config" "$output/.config"
  if ! make O="$output" BR2_EXTERNAL=/port/buildroot olddefconfig >> "$record/restore.log" 2>&1; then rc=1; fi
  if ! cmp "$record/baseline.config" "$output/.config"; then rc=1; fi
  printf "%s\n" "$rc" > "$record/$NETWORK_STAGE.exit"
  exit "$rc"
 }
 trap finish EXIT
 make O="$output" BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG="$record/network.defconfig" defconfig \
  > "$record/$NETWORK_STAGE.log" 2>&1
 cp "$output/.config" "$record/resolved.config"
 if [ "$NETWORK_STAGE" = fetch ]; then
  make O="$output" BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
   BR2_WGET="wget -nd -t 2 --connect-timeout=10 --read-timeout=25" \
   dropbear-all-source wpa_supplicant-all-source usb_modeswitch-all-source >> "$record/fetch.log" 2>&1
 else
  make O="$output" BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads BR2_JLEVEL=4 \
   dropbear wpa_supplicant usb_modeswitch >> "$record/build.log" 2>&1
 fi
 '
cmp "$out/baseline.config" "$work/graphics-config/output/.config"
echo "Network package $stage completed; foundation config restored; no image or device access."
