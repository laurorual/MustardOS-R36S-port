#!/usr/bin/env bash
# The new frontend uses only the private overlay, never the rejected GPU image.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
menu="$repo/build/phase4/menu"
[[ $# == 2 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && ( $2 == menu-inspect || $2 == menu-video || $2 == menu-audio ) ]] || exit 2
stage=$(cat "$menu/latest-staging")
[[ $stage == "$menu/"staging.* ]]
python3 - "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
s=Path(sys.argv[1]);m=json.loads((s/'staging-manifest.json').read_text())
with (s/'menu-staging.tar.gz').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['staging_sha256']
assert m['qemu_link_load_passed'] and not m['mali_redistribution_approved']
PY
if [[ $2 != menu-inspect ]]; then
 python3 - "$menu" "$stage" <<'PY'
from pathlib import Path
import json,sys
m,s=map(Path,sys.argv[1:]);r=json.loads((m/'native-inspect-result.json').read_text())
assert r['passed'] and r['staging_sha256']==json.loads((s/'staging-manifest.json').read_text())['staging_sha256']
PY
fi
work=$(mktemp -d "$menu/$2.XXXXXX")
cp --reflink=auto "$stage/menu-staging.tar.gz" "$work/core-staging.tar.gz"
cp "$stage/staging-manifest.json" "$menu/source-manifest.json" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
 "$repo/port/scripts/phase4-input-native.py" "$repo/port/scripts/phase4-menu-native.py" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py ./*.json > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$menu/latest-$2"
echo "REMOTE_MENU_SESSION=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' '$2'"
