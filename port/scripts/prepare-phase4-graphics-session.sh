#!/usr/bin/env bash
# Extract the audited image under fakeroot; never use the intermediate TARGET_DIR.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
candidate="$work/graphics-config"
[[ $(cat "$candidate/audit.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
python3 - "$candidate" <<'PY'
from pathlib import Path
import hashlib,json,sys
c=Path(sys.argv[1]);m=json.loads((c/'audit/host-audit.json').read_text())
with (c/'output/images/rootfs.ext4').open('rb') as f:
 assert hashlib.file_digest(f,'sha256').hexdigest()==m['rootfs']['ext4']['sha256']
assert not (c/'native-staging').exists(), 'Existing session staging; use a fresh directory for a new image'
(c/'native-staging').mkdir()
PY
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
    "$(cat "$work/rootfs-container.iid")" sh -eu -c '
    c=/work/graphics-config
    "$c/output/host/bin/fakeroot" -s "$c/native-staging.fakeroot" \
        debugfs -R "rdump / $c/native-staging" "$c/output/images/rootfs.ext4" > "$c/native-extract.log" 2>&1
    mkdir -p "$c/native-staging/opt/port-probes"
    cp "$c/audit/graphics-contract" "$c/audit/gbm-contract" "$c/audit/drm-mode-probe" \
       "$c/audit/sdl-video-probe" "$c/native-staging/opt/port-probes/"
    "$c/output/host/bin/fakeroot" -i "$c/native-staging.fakeroot" \
        tar -C "$c/native-staging" --exclude=./dev --exclude=./proc --exclude=./sys \
        --exclude=./tmp --exclude=./run -czf "$c/graphics-staging.tar.gz" .
    '
python3 - "$candidate" <<'PY'
from pathlib import Path
import hashlib,json,sys
c=Path(sys.argv[1])
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
m={'audited_rootfs_sha256':json.loads((c/'audit/host-audit.json').read_text())['rootfs']['ext4']['sha256'],
   'staging_sha256':sha(c/'graphics-staging.tar.gz'),
   'probe_sha256':{p:sha(c/'audit'/p) for p in ('graphics-contract','gbm-contract','drm-mode-probe','sdl-video-probe')}}
(c/'native-staging-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
PY
echo 'Audited graphics image staged; no SSH or hardware access'
