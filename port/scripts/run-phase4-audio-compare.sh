#!/usr/bin/env bash
# Separate diagnostic payload; never overwrite the archived core proof.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
artifact="$repo/dist/phase4/core-native"
[[ $# == 1 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ ]] || exit 2
(cd "$artifact" && sha256sum --check --status SHA256SUMS)
work=$(mktemp -d "$repo/build/phase4/core/audio-compare.XXXXXX")
cp --reflink=auto "$artifact/core-staging.tar.gz" "$artifact/core-tone.wav" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
    "$repo/port/scripts/phase4-audio-compare.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz core-tone.wav ./*.py > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$repo/build/phase4/core/latest-audio-compare"
echo "REMOTE_CORE_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' audio-compare"
