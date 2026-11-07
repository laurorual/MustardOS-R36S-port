#!/usr/bin/env bash
# Stage a bounded test in RAM. Never install, flash, or change boot files.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
artifact="$repo/dist/phase4/core-native"
[[ $# == 2 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && ( $2 == inspect || $2 == audio ) ]] || {
    echo 'Usage: run-phase4-core-session.sh user@host inspect|audio' >&2; exit 2;
}
(cd "$artifact" && sha256sum --check --status SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$artifact" -cf - core-staging.tar.gz phase4-core-session.py phase4-core-namespace.py session-SHA256SUMS core-tone.wav \
    | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$repo/build/phase4/core/remote-session"
echo "REMOTE_CORE_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' '$2'"
