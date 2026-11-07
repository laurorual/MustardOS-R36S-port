#!/usr/bin/env bash
# Add only the native process fixture to the image-derived RAM staging.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
f="$work/init-services"
[[ $(cat "$work/foundation/audit.exit") == 0 ]]
base=$(cat "$work/foundation/latest-staging")
[[ $base == "$work/foundation/"staging.* ]]
stage=$(mktemp -d "$f/staging.XXXXXX")
python3 - "$base" "$stage" "$f" <<'PY'
from pathlib import Path
import hashlib,json,sys
b,s,f=map(Path,sys.argv[1:]);m=json.loads((b/'staging-manifest.json').read_text())
assert m['overlay']['init_services'] is not None
(s/'rootfs').mkdir()
binary=f/'bin/service-child';h=hashlib.sha256(binary.read_bytes()).hexdigest()
assert h==json.loads((f/'build-manifest.json').read_text())['bin_sha256']['service-child']
with (f.parent/'graphics-config/output/images/rootfs.ext4').open('rb') as stream:
 assert hashlib.file_digest(stream,'sha256').hexdigest()==m['rootfs']['ext4']['sha256']
(s/'base-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
PY
export INIT_STAGE_REL=${stage#"$work/"}
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges --userns=keep-id \
 --tmpfs /tmp:rw,nosuid,nodev -e INIT_STAGE_REL -v "$work:/work:rw,z" "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 s=/work/$INIT_STAGE_REL
 /work/graphics-config/output/host/bin/fakeroot -s "$s/base.fakeroot" debugfs \
  -R "rdump / $s/rootfs" /work/graphics-config/output/images/rootfs.ext4 > "$s/image-extract.log" 2>&1
 mkdir -p "$s/rootfs/opt/port-probes"
 cp /work/init-services/bin/service-child "$s/rootfs/opt/port-probes/service-child"
 /work/graphics-config/output/host/bin/fakeroot -i "$s/base.fakeroot" tar -C "$s/rootfs" \
  --exclude=./dev --exclude=./proc --exclude=./sys --exclude=./tmp --exclude=./run -czf "$s/core-staging.tar.gz" .
 '
python3 - "$stage" "$f" <<'PY'
from pathlib import Path
import hashlib,json,sys
s,f=map(Path,sys.argv[1:]);m={'base':json.loads((s/'base-manifest.json').read_text()),
 'fixture_only':'/opt/port-probes/service-child','native_boot_tested':False}
with (s/'core-staging.tar.gz').open('rb') as stream:m['staging_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
(s/'staging-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(f/'latest-staging').write_text(str(s)+'\n')
print('Init test staging:',s)
PY
