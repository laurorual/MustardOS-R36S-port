#!/bin/sh
# SPDX-License-Identifier: MIT
# Buildroot post-build (firmware.defconfig): install the SHA256-pinned
# prebuilt inputs from the build/m3a/inputs store into the target. $1 is
# TARGET_DIR. Runs inside the build container (paths as build-image.sh mounts).
set -eu
exec python3 /port/scripts/firmware-inputs.py install \
    /port/packaging/firmware-inputs.json /m3a/inputs "$1"
