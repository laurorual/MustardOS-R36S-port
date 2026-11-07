#!/usr/bin/env bash
# Nonexclusive RAM-only contract test: no input/audio/GPU or block devices.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
f="$repo/build/phase4/foundation"
[[ $# == 1 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ ]]
[[ $(cat "$f/audit.exit") == 0 ]]
stage=$(cat "$f/latest-staging")
[[ $stage == "$f/"staging.* ]]
python3 - "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
s=Path(sys.argv[1]);m=json.loads((s/'staging-manifest.json').read_text())
with (s/'core-staging.tar.gz').open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==m['staging_sha256']
assert m['qemu_link_load_passed'] and not m['redistribution_approved'] and not m['frontend_autostart']
PY
work=$(mktemp -d "$f/native-storage.XXXXXX")
cp --reflink=auto "$stage/core-staging.tar.gz" "$stage/staging-manifest.json" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
 "$repo/port/scripts/phase4-storage-native.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py ./*.json > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$f/latest-native-storage"
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
echo "REMOTE_FOUNDATION_INSPECT=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' inspect" 2>&1 | tee "$work/native-session.log"
