#!/bin/sh
# SPDX-License-Identifier: MIT
# Buildroot post-build (firmware.defconfig): install the SHA256-pinned
# prebuilt inputs from the build/m3a/inputs store into the target, then
# the port's adjustments to them (the rootfs overlay is already in TARGET):
# - the coredb's per-system governors from core-assign.txt;
# - the volume/brightness scripts wrapped with the input boost
#   (level-wrapper.sh as audio.sh/bright.sh, the originals as *-muos.sh);
# - the WirePlumber rules from core-wireplumber.conf.
# $1 is TARGET_DIR. Runs inside the build container (paths as
# build-image.sh mounts).
set -eu
python3 /port/scripts/firmware-inputs.py install \
    /port/packaging/firmware-inputs.json /m3a/inputs "$1"
python3 /port/scripts/coredb-governors.py "$1/usr/share/muos-r35s/core-assign.txt" \
    "$1/opt/muos/share/info/manifest/core.json"
d=$1/opt/muos/script/device
for n in audio bright; do
    mv "$d/$n.sh" "$d/$n-muos.sh"
    cp /port/device/rk-r35s-p0/level-wrapper.sh "$d/$n.sh"
    chmod 0755 "$d/$n.sh" "$d/$n-muos.sh"
done
# The WirePlumber rules S80pipewire installs at start: the port's copy
# (state.restore-props off for the sink, M3d step 3) over the pinned one.
cp /port/device/rk-r35s-p0/core-wireplumber.conf "$1/opt/muos/device/control/wireplumber.conf"
chmod 0644 "$1/opt/muos/device/control/wireplumber.conf"
echo "post-build: coredb governors, level-script boost wrappers, wireplumber rules"
