#!/usr/bin/env bash
# Private diagnostic overlay in RAM. No rootfs/firmware image is installed.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
candidate="$repo/build/phase4/mali-r13"
[[ $# == 2 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && ( $2 == egl-context || $2 == graphics-r13 ) ]] || exit 2
python3 - "$candidate" "$2" <<'PY'
from pathlib import Path
import hashlib,json,sys
c=Path(sys.argv[1]);m=json.loads((c/'diagnostic-manifest.json').read_text())
with (c/'diagnostic-staging.tar.gz').open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==m['staging_sha256']
assert m['qemu_contract_passed'] and not m['redistribution_approved']
if sys.argv[2]=='graphics-r13':
 result=json.loads((c/'native-context-result.json').read_text())
 assert result['staging_sha256']==m['staging_sha256'] and result['native_context_passed']
PY
work=$(mktemp -d "$candidate/$2.XXXXXX")
cp --reflink=auto "$candidate/diagnostic-staging.tar.gz" "$work/core-staging.tar.gz"
cp "$candidate/diagnostic-manifest.json" "$candidate/source-manifest.json" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
    "$repo/port/scripts/phase4-r13-native.py" "$repo/port/scripts/phase4-graphics-native.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py ./*.json > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$candidate/latest-$2"
echo "REMOTE_R13_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' '$2'"
