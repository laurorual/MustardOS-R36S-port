#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
[ "$#" = 1 ] || exit 64
exec python3 "$(dirname "$0")/apply-phase4-runtime-profile.py" --target "$1"
