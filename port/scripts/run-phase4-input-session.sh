#!/usr/bin/env bash
# Test the archived core image in RAM, with a separate diagnostic fixture.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
artifact="$repo/dist/phase4/core-native"
[[ $# == 2 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && ( $2 == input-smoke || $2 == input-capture ) ]] || exit 2
(cd "$artifact" && sha256sum --check --status SHA256SUMS)
work=$(mktemp -d "$repo/build/phase4/core/$2.XXXXXX")
cp --reflink=auto "$artifact/core-staging.tar.gz" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
    "$repo/port/scripts/phase4-input-native.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$repo/build/phase4/core/latest-$2"
echo "REMOTE_INPUT_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' '$2'"
