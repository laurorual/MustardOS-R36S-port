#!/bin/sh
# SPDX-License-Identifier: MIT
# muOS R35S port wrapper (installed by firmware-post-build.sh over the
# pinned upstream opt/muos/script/device/{audio,bright}.sh, which move to
# *-muos.sh): input boost, then the original script unchanged.
/usr/libexec/muos-boost 2
exec "${0%.sh}-muos.sh" "$@"
