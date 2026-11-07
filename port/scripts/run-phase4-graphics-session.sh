#!/usr/bin/env bash
# Stage in RAM with the common bounded supervisor; no installed library changes.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
candidate="$repo/build/phase4/graphics-config"
[[ $# == 1 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ ]] || exit 2
[[ $(cat "$candidate/audit.exit") == 0 ]]
python3 - "$candidate" <<'PY'
from pathlib import Path
import hashlib,json,sys
c=Path(sys.argv[1]);m=json.loads((c/'native-staging-manifest.json').read_text())
with (c/'graphics-staging.tar.gz').open('rb') as f:
 assert hashlib.file_digest(f,'sha256').hexdigest()==m['staging_sha256']
assert m['audited_rootfs_sha256']==json.loads((c/'audit/host-audit.json').read_text())['rootfs']['ext4']['sha256']
rejection=c/'native-result.json'
if rejection.exists():
 r=json.loads(rejection.read_text())
 assert not (r.get('rootfs_sha256')==m['audited_rootfs_sha256'] and r.get('native_graphics_passed') is False), 'This exact candidate was rejected by the native Mali ABI test; select and audit a compatible provider before retrying'
PY
work=$(mktemp -d "$candidate/native-session.XXXXXX")
cp --reflink=auto "$candidate/graphics-staging.tar.gz" "$work/core-staging.tar.gz"
cp "$candidate/native-staging-manifest.json" "$candidate/audit/host-audit.json" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
    "$repo/port/scripts/phase4-graphics-native.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py ./*.json > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$candidate/latest-native-session"
echo "REMOTE_GRAPHICS_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' graphics"
