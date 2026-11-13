#!/bin/sh
# SPDX-License-Identifier: MIT
# muOS R35S port wrapper (installed by firmware-post-build.sh over the
# pinned upstream opt/muos/script/device/{audio,bright}.sh, which move to
# *-muos.sh): input boost, then the original script unchanged, except
# volume steps (audio.sh U/D), which go through muos-volume-step (no wpctl
# process; M3d step 3) and fall back to the original when it can't.
/usr/libexec/muos-boost 2
case "${0##*/}:${1:-}" in
    audio.sh:U|audio.sh:D) /usr/libexec/muos-volume-step "$1" && exit 0 ;;
esac
exec "${0%.sh}-muos.sh" "$@"
