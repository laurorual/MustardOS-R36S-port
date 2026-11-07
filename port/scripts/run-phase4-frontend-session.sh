#!/usr/bin/env bash
# Run the full native UI in an ephemeral rootfs with an independent restorer.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
f="$repo/build/phase4/frontend-session"
[[ $# == 2 && $1 =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && ( $2 == frontend-inspect || $2 == frontend-video || $2 == frontend-audio ) ]] || exit 2
stage=$(cat "$f/latest-staging")
[[ $stage == "$f/"staging.* ]]
python3 - "$f" "$stage" "$2" <<'PY'
from pathlib import Path
import hashlib,json,sys
f,s=map(Path,sys.argv[1:3]);mode=sys.argv[3]
m=json.loads((s/'staging-manifest.json').read_text())
with (s/'core-staging.tar.gz').open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==m['staging_sha256']
assert m['qemu_mapper_link_passed'] and not m['redistribution_approved']
if mode!='frontend-inspect':
 r=json.loads((f/'inspect-approved.json').read_text());assert r['passed'] and r['staging_sha256']==m['staging_sha256']
if mode=='frontend-audio':
 r=json.loads((f/'video-approved.json').read_text());assert r['user_confirmed']
 if r['staging_sha256']!=m['staging_sha256']:
  assert m.get('board_delta')=='0006: normalized virtual volume only; raw PMIC index unchanged'
  assert r['base_image_sha256']==m['base_foundation']['rootfs']['ext4']['sha256']
PY
work=$(mktemp -d "$f/$2.XXXXXX")
cp --reflink=auto "$stage/core-staging.tar.gz" "$stage/staging-manifest.json" "$work/"
cp "$repo/port/scripts/phase4-core-session.py" "$repo/port/scripts/phase4-core-namespace.py" \
 "$repo/port/scripts/phase4-input-native.py" "$repo/port/scripts/phase4-frontend-native.py" "$work/"
cp "$repo/port/device/rk-r35s-p0/session-hotkeys.json" "$work/"
(cd "$work" && sha256sum core-staging.tar.gz ./*.py ./*.json > session-SHA256SUMS)
options=(-o StrictHostKeyChecking=yes -o ConnectTimeout=10)
[[ -z ${MUOS_SSH_CONTROL:-} ]] || options+=(-S "$MUOS_SSH_CONTROL" -o BatchMode=yes)
session=$(ssh "${options[@]}" "$1" 'mktemp -d /tmp/muos-r35s-p4-core.XXXXXX')
[[ $session =~ ^/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+$ ]]
printf '%s\n' "$session" > "$work/remote-session"
printf '%s\n' "$work" > "$f/latest-$2"
tar -C "$work" -cf - . | ssh "${options[@]}" "$1" "tar -xf - -C '$session'"
ssh "${options[@]}" "$1" "cd '$session' && sha256sum -c session-SHA256SUMS && mkdir rootfs && sudo -n tar -xpf core-staging.tar.gz -C rootfs"
echo "REMOTE_FULL_FRONTEND=$session"
ssh "${options[@]}" "$1" "sudo -n python3 '$session/phase4-core-session.py' '$2'" 2>&1 | tee "$work/native-session.log"
